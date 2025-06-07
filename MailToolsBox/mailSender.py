import smtplib
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import COMMASPACE, formatdate
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
from typing import List, Optional, Iterable
from pathlib import Path
import logging
from ssl import create_default_context
from email_validator import validate_email, EmailNotValidError

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class EmailSender:
    """Modern email sender with sync/async support and enhanced features."""

    def __init__(
            self,
            user_email: str,
            server_smtp_address: str,
            user_email_password: str,
            port: int = 587,
            timeout: int = 10,
            validate_emails: bool = True
    ) -> None:
        self.user_email = self._validate_email(user_email) if validate_emails else user_email
        self.user_email_password = user_email_password
        self.server_smtp_address = server_smtp_address
        self.port = port
        self.timeout = timeout
        self.validate_emails = validate_emails
        self.template_env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.ssl_context = create_default_context()

    def _validate_email(self, email_address: str) -> str:
        """Validate and normalize email address using email-validator."""
        try:
            result = validate_email(email_address, check_deliverability=False)
            return result.normalized
        except EmailNotValidError as e:
            logger.error(f"Invalid email address: {email_address}")
            raise ValueError(f"Invalid email address: {email_address}") from e

    def _create_base_message(
            self,
            subject: str,
            recipients: Iterable[str],
            cc: Optional[Iterable[str]] = None,
            bcc: Optional[Iterable[str]] = None
    ) -> MIMEMultipart:
        """Create MIME message with proper headers."""
        msg = MIMEMultipart()
        msg['From'] = self.user_email
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)

        if self.validate_emails:
            recipients = [self._validate_email(r) for r in recipients]

        msg['To'] = COMMASPACE.join(recipients)

        if cc:
            validated_cc = [self._validate_email(c) for c in cc] if self.validate_emails else cc
            msg['Cc'] = COMMASPACE.join(validated_cc)

        if bcc:
            validated_bcc = [self._validate_email(b) for b in bcc] if self.validate_emails else bcc
            msg['Bcc'] = COMMASPACE.join(validated_bcc)

        return msg

    def _add_attachments(self, msg: MIMEMultipart, attachments: Iterable[str]) -> None:
        """Add multiple attachments to the message."""
        for file_path in attachments:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Attachment not found: {file_path}")
                continue

            with open(path, 'rb') as f:
                part = MIMEApplication(
                    f.read(),
                    Name=path.name
                )
            part['Content-Disposition'] = f'attachment; filename="{path.name}"'
            msg.attach(part)


    def send(
            self,
            recipients: Iterable[str],
            subject: str,
            message_body: str,
            cc: Optional[Iterable[str]] = None,
            bcc: Optional[Iterable[str]] = None,
            attachments: Optional[Iterable[str]] = None,
            use_tls: bool = True,
            html: bool = False
    ) -> None:
        """Synchronous email sending with improved error handling."""
        msg = self._create_base_message(subject, recipients, cc, bcc)
        msg.attach(MIMEText(message_body, 'html' if html else 'plain'))

        if attachments:
            self._add_attachments(msg, attachments)

        try:
            with smtplib.SMTP(self.server_smtp_address, self.port, timeout=self.timeout) as server:
                if use_tls:
                    server.starttls(context=self.ssl_context)
                server.login(self.user_email, self.user_email_password)
                server.send_message(msg)
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    async def send_async(
            self,
            recipients: Iterable[str],
            subject: str,
            message_body: str,
            cc: Optional[Iterable[str]] = None,
            bcc: Optional[Iterable[str]] = None,
            attachments: Optional[Iterable[str]] = None,
            use_tls: bool = True,
            html: bool = False
    ) -> None:
        """Asynchronous email sending using aiosmtplib."""
        msg = self._create_base_message(subject, recipients, cc, bcc)
        msg.attach(MIMEText(message_body, 'html' if html else 'plain'))

        if attachments:
            self._add_attachments(msg, attachments)

        try:
            async with aiosmtplib.SMTP(hostname=self.server_smtp_address, port=self.port, timeout=self.timeout) as server:
                if use_tls:
                    await server.starttls(context=self.ssl_context)
                await server.login(self.user_email, self.user_email_password)
                await server.send_message(msg)
        except aiosmtplib.errors.SMTPException as e:
            logger.error(f"SMTP error occurred: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    def send_template(
            self,
            recipient: str,
            subject: str,
            template_name: str,
            context: dict,
            cc: Optional[Iterable[str]] = None,
            attachments: Optional[Iterable[str]] = None,
            use_tls: bool = True
    ) -> None:
        """Send email using Jinja2 template with autoescaping."""
        template = self.template_env.get_template(template_name)
        html_content = template.render(**context)
        self.send([recipient], subject, html_content, cc=cc, attachments=attachments, use_tls=use_tls, html=True)



# Backward compatibility layer
class SendAgent(EmailSender):
    """Legacy compatibility layer maintaining original interface."""

    def send_mail(
            self,
            recipient_email: Optional[List[str]],
            subject: str,
            message_body: str,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
            attachments: Optional[List[str]] = None,
            tls: bool = True
    ) -> None:
        logger.warning("SendAgent is deprecated, use EmailSender instead")

        # Convert parameters to new format
        self.send(
            recipients=recipient_email,
            subject=subject,
            message_body=message_body,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            use_tls=tls
        )


    def send_mail_with_template(
            self,
            recipient_email: str,
            subject: str,
            template_path: str,
            template_vars: dict,
            cc: Optional[List[str]] = None,
            attachments: Optional[List[str]] = None,
            tls: bool = True
    ) -> None:
        logger.warning("send_mail_with_template is deprecated, use send_template instead")

        self.send_template(
            recipient=recipient_email,
            subject=subject,
            template_name=template_path,
            context=template_vars,
            cc=cc,
            attachments=attachments,
            use_tls=tls
        )



# Example usage
if __name__ == "__main__":
    sender = EmailSender(
        user_email="your@email.com",
        server_smtp_address="smtp.example.com",
        user_email_password="password",
        port=587
    )

    # Sync send
    sender.send(
        recipients=["gh.rambod@gmail.com"],
        subject="Modern Email",
        message_body="<h1>HTML Content</h1>",
        html=True,
        attachments=["important.pdf"]
    )

    # Async send
    import asyncio

    async def run():
        await sender.send_async(
            recipients=["gh.rambod@gmail.com"],
            subject="Modern Email Async",
            message_body="<h1>HTML Content Async</h1>",
            html=True,
            attachments=["important.pdf"]
        )

    asyncio.run(run())
