"""MailToolsBox — modern sync/async SMTP sending and IMAP reading for Python."""

from ._version import __version__
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    EmailValidationError,
    IMAPError,
    MailToolsBoxError,
    SendError,
)
from .imapClient import (
    ImapAgent,
    ImapClient,
    MailAddress,
    MailItem,
    MailPart,
)
from .mailSender import EmailSender, SendAgent, SmtpSession
from .retry import RateLimiter, RetryPolicy
from .security import SecurityMode

__all__ = [
    "__version__",
    # SMTP
    "EmailSender",
    "SmtpSession",
    "SendAgent",
    # IMAP
    "ImapClient",
    "ImapAgent",
    "MailItem",
    "MailAddress",
    "MailPart",
    # Shared
    "SecurityMode",
    "RetryPolicy",
    "RateLimiter",
    # Exceptions
    "MailToolsBoxError",
    "ConfigurationError",
    "ConnectionError",
    "AuthenticationError",
    "SendError",
    "IMAPError",
    "EmailValidationError",
]
