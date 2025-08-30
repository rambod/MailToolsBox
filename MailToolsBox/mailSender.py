"""
MailToolsBox - revamped
- Security modes: auto, starttls, ssl, none
- Works with Gmail, Exchange Online, generic SMTP
- Optional OAuth2 XOAUTH2 (sync and async)
- Backward compatible SendAgent shim
"""

from __future__ import annotations

import os
import ssl
import base64
import smtplib
import aiosmtplib
import aiofiles
import asyncio
import logging
import mimetypes

from enum import Enum
from pathlib import Path
from typing import List, Optional, Iterable, Tuple

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate
from email_validator import validate_email, EmailNotValidError
from jinja2 import Environment, FileSystemLoader, select_autoescape

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ---------------------------------------------------------------------
# Security modes
# ---------------------------------------------------------------------
class SecurityMode(str, Enum):
    AUTO = "auto"        # 465 -> SSL on connect, else try STARTTLS if server advertises, else plain
    STARTTLS = "starttls"
    SSL = "ssl"          # implicit TLS on connect, typical on 465
    NONE = "none"        # plain text connection, only for trusted networks


# ---------------------------------------------------------------------
# Email sender
# ---------------------------------------------------------------------
class EmailSender:
    """
    Modern email sender with sync and async support.

    Highlights:
    - security_mode controls TLS behavior:
        auto     -> if port is 465 use SSL, else try STARTTLS if server advertises it
        starttls -> force STARTTLS upgrade after EHLO
        ssl      -> implicit SSL on connect
        none     -> no TLS at all
    - Supports basic auth (username+password) and optional OAuth2 XOAUTH2
      via access token for SMTP. If both are provided, OAuth2 is preferred.
    - Gmail preset: smtp.gmail.com:465 ssl=True or 587 starttls
    - Exchange Online preset: smtp.office365.com:587 starttls
    """

    def __init__(
        self,
        user_email: str,
        server_smtp_address: str,
        user_email_password: Optional[str] = None,
        *,
        port: int = 587,
        timeout: int = 30,
        validate_emails: bool = True,
        template_dir: Optional[str] = None,
        security_mode: SecurityMode = SecurityMode.AUTO,
        oauth2_access_token: Optional[str] = None,
        allow_invalid_certs: bool = False,
        ehlo_hostname: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> None:
        # Identity
        self.user_email = self._validate_email(user_email) if validate_emails else user_email
        self.server_smtp_address = server_smtp_address
        self.port = int(port)
        self.timeout = timeout
        self.validate_emails = validate_emails
        self.security_mode = SecurityMode(security_mode)
        self.user_email_password = user_email_password
        self.oauth2_access_token = oauth2_access_token
        self.ehlo_hostname = ehlo_hostname
        self.reply_to = self._validate_email(reply_to) if (reply_to and validate_emails) else reply_to

        # Templates
        if template_dir is None:
            template_path = Path(__file__).resolve().parent / "templates"
        else:
            template_path = Path(template_dir)
        self.template_env = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # TLS context
        self.ssl_context = ssl.create_default_context()
        if allow_invalid_certs:
            # Useful only in dev or inside trusted LANs
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

        logger.info(
            "EmailSender initialized for %s (%s:%s, security=%s)",
            self.user_email, self.server_smtp_address, self.port, self.security_mode
        )

    # ----------------- Convenience constructors -----------------

    @classmethod
    def from_env(cls) -> "EmailSender":
        """
        Create EmailSender from environment variables.

        Required: EMAIL, SMTP_SERVER
        Optional: EMAIL_PASSWORD, SMTP_PORT, EMAIL_SECURITY, EMAIL_OAUTH2_TOKEN,
                  EMAIL_ALLOW_INVALID_CERTS, EMAIL_EHLO, EMAIL_REPLY_TO
        """
        user_email = os.environ["EMAIL"]
        server = os.environ["SMTP_SERVER"]
        password = os.getenv("EMAIL_PASSWORD") or None
        port = int(os.getenv("SMTP_PORT", "587"))
        security = os.getenv("EMAIL_SECURITY", "auto")
        token = os.getenv("EMAIL_OAUTH2_TOKEN") or None
        allow_invalid = os.getenv("EMAIL_ALLOW_INVALID_CERTS", "0") in {"1", "true", "True"}
        ehlo = os.getenv("EMAIL_EHLO") or None
        reply_to = os.getenv("EMAIL_REPLY_TO") or None

        return cls(
            user_email=user_email,
            server_smtp_address=server,
            user_email_password=password,
            port=port,
            security_mode=security,
            oauth2_access_token=token,
            allow_invalid_certs=allow_invalid,
            ehlo_hostname=ehlo,
            reply_to=reply_to,
        )

    @classmethod
    def for_gmail_app_password(cls, email: str, app_password: str) -> "EmailSender":
        # Gmail supports 465 SSL and 587 STARTTLS. Pick SSL for simplicity.
        return cls(
            user_email=email,
            user_email_password=app_password,
            server_smtp_address="smtp.gmail.com",
            port=465,
            security_mode=SecurityMode.SSL,
        )

    @classmethod
    def for_exchange_smtp_auth(cls, email: str, password: str) -> "EmailSender":
        # Exchange Online: smtp.office365.com:587 with STARTTLS
        return cls(
            user_email=email,
            user_email_password=password,
            server_smtp_address="smtp.office365.com",
            port=587,
            security_mode=SecurityMode.STARTTLS,
        )

    # ----------------- Validation helpers -----------------

    def _validate_email(self, email_address: str) -> str:
        """Validate and normalize email address using email-validator."""
        try:
            result = validate_email(email_address, check_deliverability=False)
            return result.normalized
        except EmailNotValidError as e:
            logger.error("Invalid email address: %s", email_address)
            raise ValueError(f"Invalid email address: {email_address}") from e

    def _create_base_message(
        self,
        subject: str,
        recipients: Iterable[str],
        cc: Optional[Iterable[str]] = None,
    ) -> Tuple[MIMEMultipart, List[str], Optional[List[str]]]:
        """Create MIME message and return validated recipient lists."""
        msg = MIMEMultipart()
        msg["From"] = self.user_email
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)

        # To
        recipients_list = list(recipients)
        if self.validate_emails:
            recipients_list = [self._validate_email(r) for r in recipients_list]
        if recipients_list:
            msg["To"] = ", ".join(recipients_list)

        # CC
        validated_cc = None
        if cc:
            cc_list = list(cc)
            validated_cc = [self._validate_email(c) for c in cc_list] if self.validate_emails else cc_list
            if validated_cc:
                msg["Cc"] = ", ".join(validated_cc)

        # Reply-To
        if self.reply_to:
            msg["Reply-To"] = self.reply_to

        return msg, recipients_list, validated_cc

    # ----------------- Attachment helpers -----------------

    @staticmethod
    def _guess_mime(file_path: Path) -> MIMEBase:
        ctype, encoding = mimetypes.guess_type(file_path)
        if ctype is None or encoding is not None:
            # Fallback to binary stream
            part = MIMEApplication(file_path.read_bytes(), Name=file_path.name)
        else:
            maintype, subtype = ctype.split("/", 1)
            data = file_path.read_bytes()
            if maintype == "text":
                # Try to decode as UTF-8, fallback to octet-stream
                try:
                    part = MIMEText(data.decode("utf-8"), _subtype=subtype)
                    part.add_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
                    return part
                except UnicodeDecodeError:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(data)
                    encoders.encode_base64(part)
            elif maintype == "application":
                part = MIMEApplication(data, Name=file_path.name)
            else:
                part = MIMEBase(maintype, subtype)
                part.set_payload(data)
                encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
        return part

    def _add_attachments(self, msg: MIMEMultipart, attachments: Iterable[str]) -> None:
        for file_path in attachments:
            path = Path(file_path)
            if not path.exists():
                logger.warning("Attachment not found: %s", file_path)
                continue
            part = self._guess_mime(path)
            msg.attach(part)

    async def _add_attachments_async(self, msg: MIMEMultipart, attachments: Iterable[str]) -> None:
        # Keep async path simple but correct, using Application fallback
        for file_path in attachments:
            path = Path(file_path)
            if not path.exists():
                logger.warning("Attachment not found: %s", file_path)
                continue
            async with aiofiles.open(path, "rb") as f:
                data = await f.read()
            part = MIMEApplication(data, Name=path.name)
            part["Content-Disposition"] = f'attachment; filename="{path.name}"'
            msg.attach(part)

    # ----------------- XOAUTH2 helpers -----------------

    @staticmethod
    def _xoauth2_b64(user: str, access_token: str) -> str:
        # Per Gmail XOAUTH2 spec: base64("user={}\x01auth=Bearer {}\x01\x01")
        raw = f"user={user}\x01auth=Bearer {access_token}\x01\x01".encode("utf-8")
        return base64.b64encode(raw).decode("ascii")

    def _smtp_login_sync(self, server: smtplib.SMTP) -> None:
        """Authenticate on an smtplib server using OAuth2 or username/password."""
        if self.oauth2_access_token:
            token = self._xoauth2_b64(self.user_email, self.oauth2_access_token)
            code, resp = server.docmd("AUTH", "XOAUTH2 " + token)
            # Some servers respond with 334 and expect the token as a second line
            if code == 334:
                code, resp = server.docmd(token)
            if code not in (235, 503):
                raise smtplib.SMTPAuthenticationError(code, resp)
            return

        if self.user_email_password:
            server.login(self.user_email, self.user_email_password)

    async def _smtp_login_async(self, server: aiosmtplib.SMTP) -> None:
        """Authenticate on an aiosmtplib server using OAuth2 or username/password."""
        if self.oauth2_access_token:
            token = self._xoauth2_b64(self.user_email, self.oauth2_access_token)
            # Single line first
            code, resp = await server.execute_command("AUTH", "XOAUTH2 " + token)
            if code == 334:
                code, resp = await server.execute_command(token)
            if code not in (235, 503):
                # aiosmtplib has a namespaced error class, but we raise the generic for compatibility
                raise aiosmtplib.errors.SMTPAuthenticationError(code, resp)  # type: ignore[attr-defined]
            return

        if self.user_email_password:
            await server.login(self.user_email, self.user_email_password)

    # ----------------- Connection helpers -----------------

    def _open_sync(self) -> smtplib.SMTP:
        """Open a synchronous SMTP connection with requested security behavior."""
        mode = self.security_mode
        if mode == SecurityMode.AUTO and self.port == 465:
            mode = SecurityMode.SSL

        if mode == SecurityMode.SSL:
            server = smtplib.SMTP_SSL(
                self.server_smtp_address,
                self.port,
                timeout=self.timeout,
                context=self.ssl_context,
            )
            server.ehlo(self.ehlo_hostname) if self.ehlo_hostname else server.ehlo()
            return server

        # Plain socket, then maybe STARTTLS
        server = smtplib.SMTP(self.server_smtp_address, self.port, timeout=self.timeout)
        server.ehlo(self.ehlo_hostname) if self.ehlo_hostname else server.ehlo()

        if mode == SecurityMode.STARTTLS:
            server.starttls(context=self.ssl_context)
            server.ehlo(self.ehlo_hostname) if self.ehlo_hostname else server.ehlo()
        elif mode == SecurityMode.AUTO:
            # Try upgrade only if server advertises it
            if "starttls" in getattr(server, "esmtp_features", {}):
                server.starttls(context=self.ssl_context)
                server.ehlo(self.ehlo_hostname) if self.ehlo_hostname else server.ehlo()
        # mode NONE means keep plain
        return server

    def _aiosmtp(self) -> aiosmtplib.SMTP:
        """Create an aiosmtplib.SMTP instance with proper TLS flags."""
        mode = self.security_mode
        if mode == SecurityMode.AUTO and self.port == 465:
            mode = SecurityMode.SSL

        use_tls = mode == SecurityMode.SSL
        if mode == SecurityMode.STARTTLS:
            start_tls = True
        elif mode == SecurityMode.NONE:
            start_tls = False
        elif mode == SecurityMode.SSL:
            start_tls = False  # implicit TLS already
        else:
            start_tls = None  # auto upgrade if server advertises STARTTLS

        # Note: no duplicated parameters here
        return aiosmtplib.SMTP(
            hostname=self.server_smtp_address,
            port=self.port,
            timeout=self.timeout,
            use_tls=use_tls,
            start_tls=start_tls,
            tls_context=self.ssl_context,
        )

    # ----------------- Public API: sync -----------------

    def _attach_body(self, msg: MIMEMultipart, body: str, as_html: bool) -> None:
        if as_html:
            # Provide a plain text fallback for better deliverability
            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(self._html_to_text(body), "plain"))
            alt.attach(MIMEText(body, "html"))
            msg.attach(alt)
        else:
            msg.attach(MIMEText(body, "plain"))

    @staticmethod
    def _html_to_text(html: str) -> str:
        # Minimal fallback; keep simple and dependency-free
        # Strip a few common tags
        text = html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        for tag in ("p", "div"):
            text = text.replace(f"<{tag}>", "").replace(f"</{tag}>", "\n")
        # Remove all other angle-bracketed tags naively
        out = []
        in_tag = False
        for ch in text:
            if ch == "<":
                in_tag = True
                continue
            if ch == ">":
                in_tag = False
                continue
            if not in_tag:
                out.append(ch)
        return "".join(out)

    def send(
        self,
        recipients: Iterable[str],
        subject: str,
        message_body: str,
        *,
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
        attachments: Optional[Iterable[str]] = None,
        html: bool = False,
        security_mode: Optional[SecurityMode] = None,
    ) -> None:
        """Send a single message synchronously."""
        recipients_list = list(recipients)
        cc_list = list(cc) if cc else None
        bcc_list = list(bcc) if bcc else None

        msg, validated_to, validated_cc = self._create_base_message(subject, recipients_list, cc_list)
        validated_bcc = None
        if bcc_list:
            validated_bcc = [self._validate_email(b) for b in bcc_list] if self.validate_emails else bcc_list

        self._attach_body(msg, message_body, html)

        if attachments:
            self._add_attachments(msg, attachments)

        # Temporarily override security if provided at call site
        original_mode = self.security_mode
        if security_mode:
            self.security_mode = SecurityMode(security_mode)

        try:
            with self._open_sync() as server:
                self._smtp_login_sync(server)
                all_recipients = list(validated_to)
                if validated_cc:
                    all_recipients.extend(validated_cc)
                if validated_bcc:
                    all_recipients.extend(validated_bcc)
                server.send_message(msg, to_addrs=all_recipients)
        except smtplib.SMTPException as e:
            logger.error("SMTP error: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            raise
        finally:
            self.security_mode = original_mode

    def send_bulk(
        self,
        recipients: Iterable[str],
        subject: str,
        message_body: str,
        **kwargs,
    ) -> dict:
        """Send the same message to many recipients individually."""
        results = {"sent": [], "failed": {}}
        for recipient in recipients:
            try:
                self.send([recipient], subject, message_body, **kwargs)
                results["sent"].append(recipient)
            except Exception as exc:
                logger.exception("Failed sending email to %s", recipient)
                results["failed"][recipient] = exc
        return results

    def send_template(
        self,
        recipient: str,
        subject: str,
        template_name: str,
        context: dict,
        *,
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
        attachments: Optional[Iterable[str]] = None,
        security_mode: Optional[SecurityMode] = None,
    ) -> None:
        """Render a Jinja2 template and send as HTML."""
        template = self.template_env.get_template(template_name)
        html_content = template.render(**context)
        self.send(
            recipients=[recipient],
            subject=subject,
            message_body=html_content,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            html=True,
            security_mode=security_mode,
        )

    # ----------------- Public API: async -----------------

    async def send_async(
        self,
        recipients: Iterable[str],
        subject: str,
        message_body: str,
        *,
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
        attachments: Optional[Iterable[str]] = None,
        html: bool = False,
        security_mode: Optional[SecurityMode] = None,
    ) -> None:
        """Send a single message asynchronously using aiosmtplib."""
        recipients_list = list(recipients)
        cc_list = list(cc) if cc else None
        bcc_list = list(bcc) if bcc else None

        msg, validated_to, validated_cc = self._create_base_message(subject, recipients_list, cc_list)
        validated_bcc = None
        if bcc_list:
            validated_bcc = [self._validate_email(b) for b in bcc_list] if self.validate_emails else bcc_list

        self._attach_body(msg, message_body, html)

        if attachments:
            await self._add_attachments_async(msg, attachments)

        original_mode = self.security_mode
        if security_mode:
            self.security_mode = SecurityMode(security_mode)

        try:
            server = self._aiosmtp()
            await server.connect()
            try:
                await self._smtp_login_async(server)
                all_recipients = list(validated_to)
                if validated_cc:
                    all_recipients.extend(validated_cc)
                if validated_bcc:
                    all_recipients.extend(validated_bcc)
                await server.send_message(msg, to_addrs=all_recipients)
            finally:
                await server.quit()
        except aiosmtplib.errors.SMTPException as e:
            logger.error("SMTP error: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            raise
        finally:
            self.security_mode = original_mode

    async def send_bulk_async(
        self,
        recipients: Iterable[str],
        subject: str,
        message_body: str,
        **kwargs,
    ) -> dict:
        """Asynchronously send the same message to many recipients individually."""
        recipients_list = list(recipients)
        tasks = [self.send_async([r], subject, message_body, **kwargs) for r in recipients_list]

        results = {"sent": [], "failed": {}}
        send_results = await asyncio.gather(*tasks, return_exceptions=True)
        for recipient, res in zip(recipients_list, send_results):
            if isinstance(res, Exception):
                logger.exception("Failed sending email to %s", recipient)
                results["failed"][recipient] = res
            else:
                results["sent"].append(recipient)
        return results


# ---------------------------------------------------------------------
# Backward compatibility layer
# ---------------------------------------------------------------------
class SendAgent(EmailSender):
    """Legacy interface adapter. Prefer EmailSender."""

    def send_mail(
        self,
        recipient_email: Optional[List[str]],
        subject: str,
        message_body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        tls: bool = True,
    ) -> None:
        logger.warning("SendAgent is deprecated, use EmailSender instead")
        self.send(
            recipients=recipient_email or [],
            subject=subject,
            message_body=message_body,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            html=False,
            security_mode=SecurityMode.STARTTLS if tls else SecurityMode.NONE,
        )

    def send_mail_with_template(
        self,
        recipient_email: str,
        subject: str,
        template_path: str,
        template_vars: dict,
        cc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        tls: bool = True,
    ) -> None:
        logger.warning("send_mail_with_template is deprecated, use send_template instead")
        self.send_template(
            recipient=recipient_email,
            subject=subject,
            template_name=template_path,
            context=template_vars,
            cc=cc,
            attachments=attachments,
            security_mode=SecurityMode.STARTTLS if tls else SecurityMode.NONE,
        )
