"""Structured exception hierarchy for MailToolsBox.

All errors raised by the library derive from :class:`MailToolsBoxError`, so
callers can catch everything with a single ``except`` while still being able to
distinguish connection, authentication, send, and validation failures.
"""

from __future__ import annotations


class MailToolsBoxError(Exception):
    """Base class for every error raised by MailToolsBox."""


class ConfigurationError(MailToolsBoxError):
    """Invalid or missing configuration (bad arguments, env vars, etc.)."""


class EmailValidationError(MailToolsBoxError, ValueError):
    """An email address failed validation/normalization."""


class ConnectionError(MailToolsBoxError):
    """Failed to establish or maintain a server connection."""


class AuthenticationError(MailToolsBoxError):
    """The server rejected the supplied credentials or OAuth2 token."""


class SendError(MailToolsBoxError):
    """A message could not be sent."""

    def __init__(self, message: str, *, recipient: str | None = None) -> None:
        super().__init__(message)
        self.recipient = recipient


class IMAPError(MailToolsBoxError):
    """An IMAP operation failed."""
