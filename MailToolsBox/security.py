"""Shared transport security primitives used by both SMTP and IMAP clients."""

from __future__ import annotations

import ssl
from enum import Enum


class SecurityMode(str, Enum):
    """How the transport should negotiate TLS.

    - ``AUTO``: implicit SSL when the well-known secure port is used
      (465 for SMTP, 993 for IMAP); otherwise upgrade with STARTTLS if the
      server advertises it, and fall back to plaintext if it does not.
    - ``STARTTLS``: always upgrade an initially plaintext connection.
    - ``SSL``: implicit TLS on connect (wraps the socket immediately).
    - ``NONE``: plaintext only. Use exclusively on trusted networks.
    """

    AUTO = "auto"
    STARTTLS = "starttls"
    SSL = "ssl"
    NONE = "none"


def build_ssl_context(
    ssl_context: ssl.SSLContext | None = None,
    *,
    allow_invalid_certs: bool = False,
) -> ssl.SSLContext:
    """Return an SSL context, optionally relaxing certificate verification.

    ``allow_invalid_certs`` disables hostname and certificate checks and must
    only be used on trusted networks (e.g. on-prem Exchange with a self-signed
    certificate). It is a security downgrade and should never be enabled when
    talking to the public internet.
    """
    ctx = ssl_context or ssl.create_default_context()
    if allow_invalid_certs:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx
