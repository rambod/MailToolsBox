import builtins
import smtplib
from unittest import mock
import types
import sys
from pathlib import Path
from email.mime.multipart import MIMEMultipart
import time
import pytest

# Provide dummy aiosmtplib to satisfy imports
sys.modules.setdefault(
    "aiosmtplib",
    types.SimpleNamespace(SMTP=None, errors=types.SimpleNamespace(SMTPException=Exception)),
)
# Minimal stub for aiofiles
sys.modules.setdefault(
    "aiofiles",
    types.SimpleNamespace(open=lambda *args, **kwargs: None),
)
# Minimal stub for jinja2
sys.modules.setdefault(
    "jinja2",
    types.SimpleNamespace(
        Environment=lambda **kwargs: types.SimpleNamespace(get_template=lambda name: types.SimpleNamespace(render=lambda **kw: "")),
        FileSystemLoader=lambda *args, **kwargs: None,
        select_autoescape=lambda x: None,
    ),
)
sys.modules.setdefault(
    "email_validator",
    types.SimpleNamespace(
        validate_email=lambda email, check_deliverability=False: types.SimpleNamespace(normalized=email),
        EmailNotValidError=Exception,
    ),
)

from MailToolsBox.mailSender import EmailSender


def test_email_sender_send(monkeypatch):
    smtp_instance = mock.MagicMock()
    smtp_instance.__enter__.return_value = smtp_instance
    smtp_instance.__exit__.return_value = None

    smtp_class = mock.MagicMock(return_value=smtp_instance)
    monkeypatch.setattr(smtplib, "SMTP", smtp_class)

    sender = EmailSender(
        user_email="user@example.com",
        server_smtp_address="smtp.example.com",
        user_email_password="pass",
        port=25,
    )

    sender.send(
        recipients=["to@example.com"],
        subject="Subj",
        message_body="Body",
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
        use_tls=True,
    )

    smtp_class.assert_called_with("smtp.example.com", 25, timeout=10)
    smtp_instance.starttls.assert_called()
    smtp_instance.login.assert_called_with("user@example.com", "pass")
    smtp_instance.send_message.assert_called()

    args, kwargs = smtp_instance.send_message.call_args
    msg = args[0]
    to_addrs = kwargs["to_addrs"]
    assert set(to_addrs) == {"to@example.com", "cc@example.com", "bcc@example.com"}
    assert msg["To"] == "to@example.com"
    assert msg["Cc"] == "cc@example.com"


def test_email_sender_from_env(monkeypatch):
    monkeypatch.setenv("EMAIL", "env@example.com")
    monkeypatch.setenv("SMTP_SERVER", "smtp.env.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_PORT", "2525")

    sender = EmailSender.from_env()

    assert sender.user_email == "env@example.com"
    assert sender.server_smtp_address == "smtp.env.com"
    assert sender.user_email_password == "secret"
    assert sender.port == 2525


def test_send_bulk(monkeypatch):
    sent = []

    class DummySender(EmailSender):
        def __init__(self):
            pass

        def send(self, recipients, subject, message_body, **kwargs):
            sent.append(recipients[0])

    sender = DummySender()

    result = sender.send_bulk(["a@example.com", "b@example.com"], "subj", "body")

    assert sent == ["a@example.com", "b@example.com"]
    assert result["sent"] == ["a@example.com", "b@example.com"]
    assert result["failed"] == {}


def test_send_bulk_continues_on_failure(monkeypatch):
    sent = []

    class DummySender(EmailSender):
        def __init__(self):
            pass

        def send(self, recipients, subject, message_body, **kwargs):
            recipient = recipients[0]
            if recipient == "b@example.com":
                raise ValueError("boom")
            sent.append(recipient)

    sender = DummySender()

    result = sender.send_bulk(
        ["a@example.com", "b@example.com", "c@example.com"], "subj", "body"
    )

    assert sent == ["a@example.com", "c@example.com"]
    assert result["sent"] == ["a@example.com", "c@example.com"]
    assert list(result["failed"].keys()) == ["b@example.com"]


def test_send_template_passes_bcc(monkeypatch):
    sender = EmailSender(
        user_email="user@example.com",
        server_smtp_address="smtp.example.com",
        user_email_password="pass",
        port=25,
    )

    captured = {}

    def fake_send(recipients, subject, message_body, **kwargs):
        captured["recipients"] = recipients
        captured.update(kwargs)

    monkeypatch.setattr(sender, "send", fake_send)

    sender.send_template(
        recipient="to@example.com",
        subject="Subj",
        template_name="tmpl.html",
        context={},
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
    )

    assert captured["recipients"] == ["to@example.com"]
    assert captured["bcc"] == ["bcc@example.com"]
    assert captured["cc"] == ["cc@example.com"]


def test_send_template_custom_directory(monkeypatch):
    loader_called = {}

    def fake_loader(path):
        loader_called["path"] = path
        return "loader"

    def fake_env(loader=None, autoescape=None):
        loader_called["loader"] = loader
        return types.SimpleNamespace(
            get_template=lambda name: types.SimpleNamespace(
                render=lambda **kw: "rendered"
            )
        )

    from MailToolsBox import mailSender as ms

    monkeypatch.setattr(ms, "FileSystemLoader", fake_loader)
    monkeypatch.setattr(ms, "Environment", fake_env)

    sender = EmailSender(
        user_email="user@example.com",
        server_smtp_address="smtp.example.com",
        user_email_password="pass",
        template_dir="/tmp/custom",
    )

    captured = {}

    def fake_send(recipients, subject, message_body, **kwargs):
        captured["recipients"] = recipients
        captured["body"] = message_body

    monkeypatch.setattr(sender, "send", fake_send)

    sender.send_template(
        recipient="to@example.com",
        subject="Subj",
        template_name="tmpl.html",
        context={},
    )

    assert loader_called["path"] == "/tmp/custom"
    assert loader_called["loader"] == "loader"
    assert captured["recipients"] == ["to@example.com"]
    assert captured["body"] == "rendered"


class DummyAsyncSMTP:
    def __init__(self):
        self.started_tls = False
        self.logged_in = None
        self.sent_message = None
        self.to_addrs = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def starttls(self, context=None):
        self.started_tls = True

    async def login(self, user, password):
        self.logged_in = (user, password)

    async def send_message(self, msg, to_addrs):
        self.sent_message = msg
        self.to_addrs = to_addrs


def test_send_async_uses_async_attachment(monkeypatch):
    smtp_instance = DummyAsyncSMTP()
    monkeypatch.setattr(sys.modules["aiosmtplib"], "SMTP", lambda **kw: smtp_instance)

    sender = EmailSender(
        user_email="user@example.com",
        server_smtp_address="smtp.example.com",
        user_email_password="pass",
        port=25,
    )

    called = {}

    async def fake_add(msg, attachments):
        called["attachments"] = attachments

    monkeypatch.setattr(sender, "_add_attachments_async", fake_add)

    import asyncio

    async def run():
        await sender.send_async(
            recipients=["to@example.com"],
            subject="Subj",
            message_body="Body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            attachments=["file1"],
            use_tls=True,
        )

    asyncio.run(run())

    assert called["attachments"] == ["file1"]
    assert smtp_instance.started_tls
    assert smtp_instance.logged_in == ("user@example.com", "pass")
    assert set(smtp_instance.to_addrs) == {"to@example.com", "cc@example.com", "bcc@example.com"}


def test_add_attachments_async(monkeypatch):
    from MailToolsBox import mailSender as ms
    msg = MIMEMultipart()
    sender = EmailSender(
        user_email="user@example.com",
        server_smtp_address="smtp.example.com",
        user_email_password="pass",
    )

    monkeypatch.setattr(Path, "exists", lambda self: True, raising=False)

    class DummyFile:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def read(self):
            return b"data"

    monkeypatch.setattr(ms.aiofiles, "open", lambda *a, **k: DummyFile())

    import asyncio

    asyncio.run(sender._add_attachments_async(msg, ["/tmp/file.txt"]))

    part = msg.get_payload()[0]
    assert part.get_filename() == "file.txt"
    assert part.get_payload(decode=True) == b"data"


def test_send_accepts_generator(monkeypatch):
    smtp_instance = mock.MagicMock()
    smtp_instance.__enter__.return_value = smtp_instance
    smtp_instance.__exit__.return_value = None
    smtp_class = mock.MagicMock(return_value=smtp_instance)
    monkeypatch.setattr(smtplib, "SMTP", smtp_class)

    sender = EmailSender(
        user_email="user@example.com",
        server_smtp_address="smtp.example.com",
        user_email_password="pass",
    )

    def gen():
        yield "to@example.com"
        yield "other@example.com"

    sender.send(recipients=gen(), subject="Subj", message_body="Body")

    args, kwargs = smtp_instance.send_message.call_args
    to_addrs = kwargs["to_addrs"]
    assert set(to_addrs) == {"to@example.com", "other@example.com"}


def test_send_async_accepts_generator(monkeypatch):
    smtp_instance = DummyAsyncSMTP()
    monkeypatch.setattr(sys.modules["aiosmtplib"], "SMTP", lambda **kw: smtp_instance)

    sender = EmailSender(
        user_email="user@example.com",
        server_smtp_address="smtp.example.com",
        user_email_password="pass",
    )

    async def run():
        def gen():
            yield "to@example.com"
            yield "other@example.com"

        await sender.send_async(recipients=gen(), subject="Subj", message_body="Body")

    import asyncio
    asyncio.run(run())

    assert set(smtp_instance.to_addrs) == {"to@example.com", "other@example.com"}


def test_send_bulk_async(monkeypatch):
    sent = []

    class DummySender(EmailSender):
        def __init__(self):
            pass

        async def send_async(self, recipients, subject, message_body, **kwargs):
            sent.append(recipients[0])

    sender = DummySender()

    import asyncio

    result = asyncio.run(
        sender.send_bulk_async(["a@example.com", "b@example.com"], "subj", "body")
    )

    assert sent == ["a@example.com", "b@example.com"]
    assert result["sent"] == ["a@example.com", "b@example.com"]
    assert result["failed"] == {}


def test_send_bulk_async_continues_on_failure(monkeypatch):
    sent = []

    class DummySender(EmailSender):
        def __init__(self):
            pass

        async def send_async(self, recipients, subject, message_body, **kwargs):
            recipient = recipients[0]
            if recipient == "b@example.com":
                raise ValueError("boom")
            sent.append(recipient)

    sender = DummySender()

    import asyncio

    result = asyncio.run(
        sender.send_bulk_async(
            ["a@example.com", "b@example.com", "c@example.com"], "subj", "body"
        )
    )

    assert sent == ["a@example.com", "c@example.com"]
    assert result["sent"] == ["a@example.com", "c@example.com"]
    assert list(result["failed"].keys()) == ["b@example.com"]


def test_send_bulk_async_concurrent(monkeypatch):
    start = {}
    end = {}

    class DummySender(EmailSender):
        def __init__(self):
            pass

        async def send_async(self, recipients, subject, message_body, **kwargs):
            r = recipients[0]
            start[r] = time.perf_counter()
            await asyncio.sleep(0.05)
            end[r] = time.perf_counter()

    sender = DummySender()

    import asyncio

    asyncio.run(
        sender.send_bulk_async(["a@example.com", "b@example.com"], "s", "b")
    )

    assert start["b@example.com"] < end["a@example.com"]


