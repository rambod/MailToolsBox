from __future__ import annotations

import imaplib
import email
import ssl
import os
import json
import datetime as dt
import base64
from dataclasses import dataclass, field
from typing import List, Optional, Iterable, Tuple, Dict, Any
from pathlib import Path
from enum import Enum
from email.header import decode_header, make_header
from email.message import Message


# ----------------------------- Security -----------------------------

class SecurityMode(str, Enum):
    AUTO = "auto"       # 993 -> SSL on connect, else try STARTTLS if server advertises it
    STARTTLS = "starttls"
    SSL = "ssl"         # implicit TLS on connect
    NONE = "none"       # plaintext, only for trusted LANs


# ----------------------------- Models -------------------------------

@dataclass
class MailAddress:
    name: Optional[str]
    email: Optional[str]


@dataclass
class MailPart:
    content_type: str
    charset: Optional[str]
    content: bytes
    filename: Optional[str] = None
    is_attachment: bool = False


@dataclass
class MailItem:
    uid: str
    subject: str
    from_: List[MailAddress] = field(default_factory=list)
    to: List[MailAddress] = field(default_factory=list)
    cc: List[MailAddress] = field(default_factory=list)
    date: Optional[dt.datetime] = None
    flags: List[str] = field(default_factory=list)
    text: Optional[str] = None
    html: Optional[str] = None
    attachments: List[MailPart] = field(default_factory=list)
    raw: bytes = b""


# --------------------------- Utilities ------------------------------

def _decode_header_value(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value

def _parse_addresses(value: Optional[str]) -> List[MailAddress]:
    if not value:
        return []
    addrs = email.utils.getaddresses([value])
    out: List[MailAddress] = []
    for name, addr in addrs:
        out.append(MailAddress(_decode_header_value(name) or None, addr or None))
    return out

def _to_local_datetime(date_hdr: Optional[str]) -> Optional[dt.datetime]:
    if not date_hdr:
        return None
    try:
        t = email.utils.parsedate_tz(date_hdr)
        if not t:
            return None
        timestamp = email.utils.mktime_tz(t)
        return dt.datetime.fromtimestamp(timestamp)
    except Exception:
        return None


# ----------------------------- Client --------------------------------

class ImapClient:
    """
    Improved IMAP client with:
    - Security modes: auto, starttls, ssl, none
    - Optional XOAUTH2 token authentication
    - List, search, move, delete, flag, and fetch utilities
    - Correct header decoding and body extraction
    - Attachment saving
    - Context manager support
    """

    def __init__(
        self,
        email_account: str,
        password: Optional[str],
        server_address: str,
        *,
        port: int = 993,
        security_mode: SecurityMode = SecurityMode.AUTO,
        oauth2_access_token: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        allow_invalid_certs: bool = False,
        timeout: int = 30,
    ) -> None:
        self.email_account = email_account
        self.password = password
        self.server_address = server_address
        self.port = int(port)
        self.security_mode = SecurityMode(security_mode)
        self.oauth2_access_token = oauth2_access_token
        self.timeout = timeout

        ctx = ssl_context or ssl.create_default_context()
        if allow_invalid_certs:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        self.ssl_context = ctx

        self.conn: Optional[imaplib.IMAP4] = None
        self.selected_mailbox: Optional[str] = None

    # --------- factories

    @classmethod
    def from_env(cls) -> "ImapClient":
        """
        Required: IMAP_EMAIL, IMAP_SERVER
        Optional: IMAP_PASSWORD, IMAP_PORT, IMAP_SECURITY, IMAP_OAUTH2_TOKEN, IMAP_ALLOW_INVALID_CERTS
        """
        email_account = os.environ["IMAP_EMAIL"]
        server = os.environ["IMAP_SERVER"]
        password = os.getenv("IMAP_PASSWORD") or None
        port = int(os.getenv("IMAP_PORT", "993"))
        security = os.getenv("IMAP_SECURITY", "auto")
        token = os.getenv("IMAP_OAUTH2_TOKEN") or None
        allow_invalid = os.getenv("IMAP_ALLOW_INVALID_CERTS", "0") in {"1", "true", "True"}

        return cls(
            email_account=email_account,
            password=password,
            server_address=server,
            port=port,
            security_mode=security,
            oauth2_access_token=token,
            allow_invalid_certs=allow_invalid,
        )

    # --------- context manager

    def __enter__(self) -> "ImapClient":
        self.login()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.logout()

    # --------- connection

    def _open(self) -> imaplib.IMAP4:
        mode = self.security_mode
        if mode == SecurityMode.AUTO and self.port == 993:
            mode = SecurityMode.SSL

        if mode == SecurityMode.SSL:
            conn = imaplib.IMAP4_SSL(self.server_address, self.port, ssl_context=self.ssl_context)
            conn.timeout = self.timeout
            return conn

        conn = imaplib.IMAP4(self.server_address, self.port)
        conn.timeout = self.timeout
        if mode == SecurityMode.STARTTLS or (mode == SecurityMode.AUTO and "STARTTLS" in conn.capabilities):
            conn.starttls(self.ssl_context)
            # capabilities may change after STARTTLS
            conn.capabilities = conn.capability()[1][0].split()  # refresh
        return conn

    def _auth(self, conn: imaplib.IMAP4) -> None:
        if self.oauth2_access_token:
            # XOAUTH2: base64("user=<email>\x01auth=Bearer <token>\x01\x01")
            raw = f"user={self.email_account}\x01auth=Bearer {self.oauth2_access_token}\x01\x01".encode("utf-8")
            xoauth = base64.b64encode(raw).decode("ascii")
            typ, resp = conn.authenticate("XOAUTH2", lambda _: xoauth)
            if typ != "OK":
                raise RuntimeError(f"XOAUTH2 failed: {resp}")
            return
        if self.password is None:
            raise RuntimeError("No password or OAuth2 token provided for IMAP authentication")
        typ, resp = conn.login(self.email_account, self.password)
        if typ != "OK":
            raise RuntimeError(f"IMAP login failed: {resp}")

    def login(self) -> None:
        if self.conn:
            return
        self.conn = self._open()
        self._auth(self.conn)

    def logout(self) -> None:
        if not self.conn:
            return
        try:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn.logout()
        finally:
            self.conn = None
            self.selected_mailbox = None

    # --------- mailbox ops

    def list_mailboxes(self) -> List[str]:
        self._ensure()
        typ, data = self.conn.list()
        if typ != "OK":
            return []
        names: List[str] = []
        for line in data:
            # format: b'(\\HasNoChildren) "/" "INBOX/Sub"'
            if not line:
                continue
            parts = line.decode("utf-8", errors="ignore").split(" ")
            name = parts[-1].strip('"')
            names.append(name)
        return names

    def select(self, mailbox: str = "INBOX", readonly: bool = True) -> None:
        self._ensure()
        typ, _ = self.conn.select(mailbox, readonly=readonly)
        if typ != "OK":
            raise RuntimeError(f"Cannot select mailbox {mailbox}")
        self.selected_mailbox = mailbox

    # --------- search and fetch

    def search(self, *criteria: str) -> List[str]:
        """
        Search with IMAP criteria. Example:
        client.search('UNSEEN', 'SINCE', '01-Jan-2025', 'FROM', '"alerts@service.com"')
        Returns a list of UIDs as strings.
        """
        self._ensure_selected()
        if not criteria:
            criteria = ("ALL",)
        typ, data = self.conn.uid("search", None, *criteria)
        if typ != "OK" or not data or not data[0]:
            return []
        uids = data[0].decode().split()
        return uids

    def fetch_raw(self, uid: str) -> Tuple[bytes, List[str]]:
        self._ensure_selected()
        typ, data = self.conn.uid("fetch", uid, "(RFC822 FLAGS)")
        if typ != "OK" or not data or not isinstance(data[0], tuple):
            raise RuntimeError(f"Failed to fetch UID {uid}")
        raw: bytes = data[0][1]
        # FLAGS come in a separate item depending on server, normalize
        flags: List[str] = []
        try:
            for item in data:
                if isinstance(item, tuple) and b"FLAGS" in item[0]:
                    flags_blob = item[0].decode(errors="ignore")
                    start = flags_blob.find("(")
                    end = flags_blob.find(")")
                    if start >= 0 and end > start:
                        flags = flags_blob[start + 1:end].split()
                        break
        except Exception:
            flags = []
        return raw, flags

    def _parse_message(self, uid: str, raw: bytes, flags: List[str]) -> MailItem:
        msg: Message = email.message_from_bytes(raw)
        subject = _decode_header_value(msg.get("Subject"))
        from_list = _parse_addresses(msg.get("From"))
        to_list = _parse_addresses(msg.get("To"))
        cc_list = _parse_addresses(msg.get("Cc"))
        date = _to_local_datetime(msg.get("Date"))

        text_body: Optional[str] = None
        html_body: Optional[str] = None
        attachments: List[MailPart] = []

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                dispo = str(part.get("Content-Disposition") or "")
                filename = part.get_filename()
                is_attach = "attachment" in dispo.lower() or bool(filename)
                charset = part.get_content_charset() or "utf-8"

                if is_attach:
                    payload = part.get_payload(decode=True) or b""
                    attachments.append(MailPart(ctype, charset, payload, filename=filename, is_attachment=True))
                    continue

                if ctype == "text/plain":
                    payload = part.get_payload(decode=True) or b""
                    try:
                        text_body = payload.decode(charset, errors="replace")
                    except Exception:
                        text_body = payload.decode("utf-8", errors="replace")
                elif ctype == "text/html":
                    payload = part.get_payload(decode=True) or b""
                    try:
                        html_body = payload.decode(charset, errors="replace")
                    except Exception:
                        html_body = payload.decode("utf-8", errors="replace")
        else:
            ctype = msg.get_content_type()
            charset = msg.get_content_charset() or "utf-8"
            payload = msg.get_payload(decode=True) or b""
            try:
                body_text = payload.decode(charset, errors="replace")
            except Exception:
                body_text = payload.decode("utf-8", errors="replace")
            if ctype == "text/html":
                html_body = body_text
            else:
                text_body = body_text

        return MailItem(
            uid=uid,
            subject=subject,
            from_=from_list,
            to=to_list,
            cc=cc_list,
            date=date,
            flags=flags,
            text=text_body,
            html=html_body,
            attachments=attachments,
            raw=raw,
        )

    def fetch(self, uid: str) -> MailItem:
        raw, flags = self.fetch_raw(uid)
        return self._parse_message(uid, raw, flags)

    def fetch_many(self, uids: Iterable[str]) -> List[MailItem]:
        out: List[MailItem] = []
        for uid in uids:
            try:
                out.append(self.fetch(uid))
            except Exception:
                continue
        return out

    # --------- mutate flags and move

    def add_flags(self, uid: str, *flags: str) -> None:
        self._ensure_selected()
        self.conn.uid("store", uid, "+FLAGS", f"({' '.join(flags)})")

    def remove_flags(self, uid: str, *flags: str) -> None:
        self._ensure_selected()
        self.conn.uid("store", uid, "-FLAGS", f"({' '.join(flags)})")

    def mark_seen(self, uid: str) -> None:
        self.add_flags(uid, "\\Seen")

    def delete(self, uid: str) -> None:
        self.add_flags(uid, "\\Deleted")

    def expunge(self) -> None:
        self._ensure_selected()
        self.conn.expunge()

    def move(self, uid_list: Iterable[str], destination: str) -> None:
        """
        Move messages by copying then marking deleted. Works on servers without MOVE.
        """
        self._ensure_selected()
        ids = ",".join(uid_list)
        typ, _ = self.conn.uid("COPY", ids, destination)
        if typ == "OK":
            self.conn.uid("STORE", ids, "+FLAGS", "(\\Deleted)")

    # --------- exports

    def save_eml(self, item: MailItem, path: str | Path) -> Path:
        p = Path(path)
        p.write_bytes(item.raw)
        return p

    def save_attachments(self, item: MailItem, directory: str | Path) -> List[Path]:
        out: List[Path] = []
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        for part in item.attachments:
            if not part.filename:
                continue
            target = d / part.filename
            target.write_bytes(part.content)
            out.append(target)
        return out

    # --------- legacy style exports (modernized)

    def download_mail_text(self, path: str = "", mailbox: str = "INBOX") -> Path:
        """
        Dump all messages in a mailbox to a single UTF-8 text file.
        """
        self.login()
        self.select(mailbox)
        uids = self.search("ALL")
        lines: List[str] = []
        for uid in uids:
            msg = self.fetch(uid)
            date_str = msg.date.strftime("%a, %d %b %Y %H:%M:%S") if msg.date else ""
            from_str = ", ".join(f"{a.name or ''} <{a.email or ''}>".strip() for a in msg.from_)
            to_str = ", ".join(f"{a.name or ''} <{a.email or ''}>".strip() for a in msg.to)
            body = msg.text or msg.html or ""
            lines.append(
                f"From: {from_str}\nTo: {to_str}\nDate: {date_str}\nSubject: {msg.subject}\n\n{body}\n\n{'-'*60}\n"
            )
        out = Path(path) / "email.txt"
        out.write_text("".join(lines), encoding="utf-8")
        self.logout()
        return out

    def download_mail_json(
        self,
        lookup: str = "ALL",
        save: bool = False,
        path: str = "",
        file_name: str = "mail.json",
        mailbox: str = "INBOX",
    ) -> str:
        """
        Return JSON of selected messages. Optionally save to disk.
        """
        self.login()
        self.select(mailbox)
        uids = self.search(lookup)
        items = self.fetch_many(uids)
        payload: List[Dict[str, Any]] = []
        for m in items:
            payload.append(
                {
                    "uid": m.uid,
                    "subject": m.subject,
                    "from": [{"name": a.name, "email": a.email} for a in m.from_],
                    "to": [{"name": a.name, "email": a.email} for a in m.to],
                    "cc": [{"name": a.name, "email": a.email} for a in m.cc],
                    "date": m.date.isoformat() if m.date else None,
                    "flags": m.flags,
                    "text": m.text,
                    "html": m.html,
                    "attachments": [a.filename for a in m.attachments if a.filename],
                }
            )
        s = json.dumps(payload, ensure_ascii=False, indent=2)
        if save:
            out = Path(path) / file_name
            out.write_text(s, encoding="utf-8")
        self.logout()
        return s

    def download_mail_eml(self, directory: str = "", lookup: str = "ALL", mailbox: str = "INBOX") -> List[Path]:
        """
        Save each selected message as an .eml file.
        """
        self.login()
        self.select(mailbox)
        uids = self.search(lookup)
        out_paths: List[Path] = []
        target_dir = Path(directory or ".")
        target_dir.mkdir(parents=True, exist_ok=True)
        for i, uid in enumerate(uids):
            item = self.fetch(uid)
            file_name = f"email_{i}_{uid}.eml"
            out = target_dir / file_name
            out.write_bytes(item.raw)
            out_paths.append(out)
        self.logout()
        return out_paths

    # --------- internal guards

    def _ensure(self) -> None:
        if not self.conn:
            self.login()

    def _ensure_selected(self) -> None:
        self._ensure()
        if not self.selected_mailbox:
            self.select("INBOX")
