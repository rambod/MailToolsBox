import json
import email
from email.mime.text import MIMEText
from unittest import mock
import os
import types
import sys

import pytest

# Provide dummy aiosmtplib for indirect imports via mailSender
sys.modules.setdefault(
    "aiosmtplib",
    types.SimpleNamespace(SMTP=None, errors=types.SimpleNamespace(SMTPException=Exception)),
)
# Minimal stub for aiofiles used by mailSender imports
sys.modules.setdefault(
    "aiofiles",
    types.SimpleNamespace(open=lambda *args, **kwargs: None),
)
# Minimal stub for jinja2 used by EmailSender imports
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

from MailToolsBox.imapClient import ImapAgent


class DummyMail:
    def __init__(self, message_bytes):
        self.message_bytes = message_bytes
        self.closed = False
        self.logged_in = False
        self.selected = None
    def login(self, user, password):
        self.logged_in = True
    def select(self, mailbox):
        self.selected = mailbox
        return ('OK', [b''])
    def uid(self, command, *args):
        if command == 'search':
            return ('OK', [b'1'])
        elif command == 'fetch':
            return ('OK', [(None, self.message_bytes)])
    def close(self):
        self.closed = True
    def logout(self):
        self.closed = True
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass


def sample_message_bytes():
    msg = MIMEText('body text')
    msg['From'] = 'from@example.com'
    msg['To'] = 'to@example.com'
    msg['Subject'] = 'Test'
    msg['Date'] = 'Wed, 20 Sep 2023 12:00:00 -0000'
    return msg.as_bytes()


def test_login_account(monkeypatch):
    dummy = DummyMail(sample_message_bytes())
    monkeypatch.setattr('imaplib.IMAP4_SSL', lambda addr: dummy)
    agent = ImapAgent('user', 'pass', 'imap.example.com')
    agent.login_account()
    assert agent.mail is dummy
    assert dummy.logged_in


@pytest.mark.parametrize("trailing", [True, False])
def test_download_mail_text(tmp_path, monkeypatch, trailing):
    message_bytes = sample_message_bytes()
    dummy = DummyMail(message_bytes)
    agent = ImapAgent('user', 'pass', 'imap.example.com')
    agent.mail = dummy

    path = str(tmp_path) + (os.sep if trailing else "")
    agent.download_mail_text(path=path)

    file_path = tmp_path / 'email.txt'
    assert file_path.exists()
    content = file_path.read_text()
    assert 'body text' in content
    assert dummy.closed


@pytest.mark.parametrize("trailing", [True, False])
def test_download_mail_json(tmp_path, monkeypatch, trailing):
    message_bytes = sample_message_bytes()
    dummy = DummyMail(message_bytes)
    monkeypatch.setattr(ImapAgent, 'login_account', lambda self: None)
    monkeypatch.setattr('imaplib.IMAP4_SSL', lambda addr: dummy)

    agent = ImapAgent('user', 'pass', 'imap.example.com')
    path = str(tmp_path) + (os.sep if trailing else "")
    result = agent.download_mail_json(save=True, path=path)

    data = json.loads(result)
    assert isinstance(data, list)
    assert data[0]['subject'] == 'Test'
    file_path = tmp_path / 'mail.json'
    assert file_path.exists()
    assert dummy.closed


@pytest.mark.parametrize("trailing", [True, False])
def test_download_mail_msg(tmp_path, trailing):
    message_bytes = sample_message_bytes()
    dummy = DummyMail(message_bytes)
    agent = ImapAgent('user', 'pass', 'imap.example.com')
    agent.login_account = lambda: setattr(agent, 'mail', dummy)

    path = str(tmp_path) + (os.sep if trailing else "")
    agent.download_mail_msg(path=path)

    file_path = tmp_path / 'email_0.msg'
    assert file_path.exists()


def test_from_env(monkeypatch):
    monkeypatch.setenv("IMAP_EMAIL", "env@example.com")
    monkeypatch.setenv("IMAP_PASSWORD", "secret")
    monkeypatch.setenv("IMAP_SERVER", "imap.env.com")

    agent = ImapAgent.from_env()

    assert agent.email_account == "env@example.com"
    assert agent.password == "secret"
    assert agent.server_address == "imap.env.com"


def test_context_manager(monkeypatch):
    dummy = DummyMail(sample_message_bytes())
    monkeypatch.setattr('imaplib.IMAP4_SSL', lambda addr: dummy)

    with ImapAgent('user', 'pass', 'imap.example.com') as agent:
        assert agent.mail is dummy
        assert dummy.logged_in
    assert dummy.closed
    assert agent.mail is None


