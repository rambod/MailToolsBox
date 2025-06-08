import builtins
import smtplib
from unittest import mock
import types
import sys
import pytest

# Provide dummy aiosmtplib to satisfy imports
sys.modules.setdefault(
    "aiosmtplib",
    types.SimpleNamespace(SMTP=None, errors=types.SimpleNamespace(SMTPException=Exception)),
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


