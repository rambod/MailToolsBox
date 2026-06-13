"""Tests for connection reuse, bulk retry/reconnect, and structured errors."""

from MailToolsBox.exceptions import AuthenticationError, SendError
from MailToolsBox.mailSender import EmailSender
from MailToolsBox.retry import RetryPolicy


def make_sender(**kw):
    return EmailSender("u@example.com", "smtp.example.com", "pw", **kw)


class FakeServer:
    def __init__(self):
        self.sent = []
        self.quit_called = False

    def send_message(self, msg, to_addrs):
        self.sent.append(to_addrs)

    def quit(self):
        self.quit_called = True


def test_open_session_reuses_one_connection(monkeypatch):
    sender = make_sender()
    fake = FakeServer()
    monkeypatch.setattr(sender, "_open_authed", lambda **kw: fake)

    with sender.open_session() as session:
        mid1 = session.send(["a@example.com"], "s", "b")
        mid2 = session.send(["b@example.com"], "s", "b")

    assert len(fake.sent) == 2
    assert fake.quit_called
    assert mid1 and mid2 and mid1 != mid2  # unique Message-IDs


def test_session_send_wraps_smtp_errors(monkeypatch):
    import smtplib

    sender = make_sender()

    class BoomServer(FakeServer):
        def send_message(self, msg, to_addrs):
            raise smtplib.SMTPException("boom")

    monkeypatch.setattr(sender, "_open_authed", lambda **kw: BoomServer())
    with sender.open_session() as session:
        try:
            session.send(["a@example.com"], "s", "b")
            raise AssertionError("expected SendError")
        except SendError:
            pass


def test_send_bulk_retries_and_reconnects(monkeypatch):
    sender = make_sender(retry_policy=RetryPolicy(max_attempts=3, base_delay=0, jitter=0))
    opens = {"n": 0}

    def fake_open(**kw):
        opens["n"] += 1
        return FakeServer()

    fail_once = {"b@example.com": True}

    def fake_send_over(server, recipients, subject, body, **kw):
        recipient = recipients[0]
        if fail_once.get(recipient):
            fail_once[recipient] = False
            raise OSError("connection dropped")
        return "<id>"

    monkeypatch.setattr(sender, "_open_authed", fake_open)
    monkeypatch.setattr(sender, "_send_over", fake_send_over)

    result = sender.send_bulk(["a@example.com", "b@example.com"], "s", "b")

    assert set(result["sent"]) == {"a@example.com", "b@example.com"}
    assert result["failed"] == {}
    # 'b' dropped once and triggered a reconnect, so more than one connection opened
    assert opens["n"] >= 2


def test_send_returns_message_id(monkeypatch):
    import smtplib
    from unittest import mock

    smtp_instance = mock.MagicMock()
    smtp_instance.__enter__.return_value = smtp_instance
    smtp_instance.__exit__.return_value = None
    monkeypatch.setattr(smtplib, "SMTP", mock.MagicMock(return_value=smtp_instance))

    sender = make_sender(port=25)
    mid = sender.send(["to@example.com"], "Subj", "Body")
    assert isinstance(mid, str) and mid.startswith("<")


def test_login_auth_error_is_translated(monkeypatch):
    import smtplib
    from unittest import mock

    smtp_instance = mock.MagicMock()
    smtp_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad creds")
    monkeypatch.setattr(smtplib, "SMTP", mock.MagicMock(return_value=smtp_instance))

    sender = make_sender(port=25)
    try:
        sender.send(["to@example.com"], "Subj", "Body")
        raise AssertionError("expected AuthenticationError")
    except AuthenticationError:
        pass
