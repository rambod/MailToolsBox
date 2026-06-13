"""End-to-end tests against a real in-process SMTP server (aiosmtpd).

These exercise the genuine smtplib / aiosmtplib code paths rather than mocks,
so they catch real protocol/API mismatches that unit-level fakes can hide.
"""

import asyncio
import socket

import pytest

aiosmtpd_controller = pytest.importorskip("aiosmtpd.controller")
from aiosmtpd.controller import Controller  # noqa: E402

from MailToolsBox.mailSender import EmailSender, SecurityMode  # noqa: E402


class RecordingHandler:
    def __init__(self):
        self.messages = []

    async def handle_DATA(self, server, session, envelope):
        self.messages.append(
            {
                "from": envelope.mail_from,
                "rcpt": list(envelope.rcpt_tos),
                "data": envelope.content,
            }
        )
        return "250 Message accepted"


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def smtp_server():
    handler = RecordingHandler()
    port = _free_port()
    controller = Controller(handler, hostname="127.0.0.1", port=port)
    controller.start()
    try:
        yield port, handler
    finally:
        controller.stop()


def _sender(port: int) -> EmailSender:
    return EmailSender(
        user_email="from@example.com",
        server_smtp_address="127.0.0.1",
        port=port,
        security_mode=SecurityMode.NONE,
    )


def test_real_sync_send_with_cc_and_bcc(smtp_server):
    port, handler = smtp_server
    _sender(port).send(
        ["to@example.com"],
        "Hello",
        "Body",
        cc=["cc@example.com"],
        bcc=["bcc@example.com"],
    )
    assert len(handler.messages) == 1
    assert set(handler.messages[0]["rcpt"]) == {
        "to@example.com",
        "cc@example.com",
        "bcc@example.com",
    }


def test_real_async_send_with_cc(smtp_server):
    port, handler = smtp_server
    asyncio.run(
        _sender(port).send_async(["to@example.com"], "Hello", "Body", cc=["cc@example.com"])
    )
    assert len(handler.messages) == 1
    assert set(handler.messages[0]["rcpt"]) == {"to@example.com", "cc@example.com"}


def test_real_bulk_send_reuses_connection(smtp_server):
    port, handler = smtp_server
    result = _sender(port).send_bulk(
        ["a@example.com", "b@example.com", "c@example.com"], "Hello", "Body"
    )
    assert set(result["sent"]) == {"a@example.com", "b@example.com", "c@example.com"}
    assert result["failed"] == {}
    assert len(handler.messages) == 3


def test_real_session_send(smtp_server):
    port, handler = smtp_server
    with _sender(port).open_session() as session:
        session.send(["a@example.com"], "Hello", "A")
        session.send(["b@example.com"], "Hello", "B")
    assert len(handler.messages) == 2


def test_real_html_send_has_plaintext_alternative(smtp_server):
    port, handler = smtp_server
    _sender(port).send(["to@example.com"], "Hello", "<h1>Hi</h1><p>There</p>", html=True)
    raw = handler.messages[0]["data"].decode("utf-8", "replace")
    assert "multipart/alternative" in raw
    assert "text/plain" in raw and "text/html" in raw
