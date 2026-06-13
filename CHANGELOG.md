# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/).

## [3.0.0] - 2026-06-13

### Fixed
- **Async sending was broken against aiosmtplib 2.x.** `send_async` /
  `send_bulk_async` called `send_message(..., to_addrs=...)`, `starttls(context=...)`
  and `ehlo(positional)` using smtplib's argument names, which aiosmtplib rejects
  (`recipients=`, `tls_context=`, `hostname=`). All async sends now use the correct
  API. Async XOAUTH2 also now passes `bytes` to `execute_command` as required.
- **IMAP one-shot export methods no longer tear down a caller-owned connection.**
  `download_mail_text` / `download_mail_json` / `download_mail_eml` previously
  called `login()`/`logout()` unconditionally, breaking usage inside a
  `with ImapClient(...) as c:` block. They now only close a connection they opened.
- `send_bulk` no longer opens a fresh connection (TLS handshake + AUTH) per recipient.

### Added
- **Bulk performance:** `EmailSender.open_session()` reuses a single authenticated
  connection across many messages; `send_bulk` reuses one connection with automatic
  reconnect on failure.
- **Resilience:** configurable `RetryPolicy` (exponential backoff + jitter) and
  `RateLimiter` (token bucket), applied by `send_bulk` / `send_bulk_async`.
- `send_bulk_async` now bounds concurrency via `max_concurrency` (default 10).
- Structured exception hierarchy under `MailToolsBoxError`
  (`AuthenticationError`, `SendError`, `IMAPError`, `EmailValidationError`, …).
- `send` / `send_async` / `SmtpSession.send` now return the generated `Message-ID`.
- `py.typed` marker so downstream type checkers consume the bundled types.
- Public re-exports: `SecurityMode`, `RetryPolicy`, `RateLimiter`, `MailItem`,
  `MailAddress`, `MailPart`, `SmtpSession`, and the exception classes.
- End-to-end integration tests against an in-process SMTP server (aiosmtpd).

### Changed
- Packaging migrated to `pyproject.toml` (PEP 621); `setup.py` removed.
- `SecurityMode` is now defined once in `MailToolsBox.security` and shared by the
  SMTP and IMAP clients (previously duplicated).
- SMTP/IMAP errors are now raised as `SendError` / `AuthenticationError` /
  `IMAPError` instead of raw `smtplib`/`RuntimeError` types.
- Version is now sourced from a single location (`MailToolsBox._version`).
- Init-time log line dropped to `DEBUG` and no longer logs the account address.

### Migration notes
- If you previously caught `smtplib.SMTPException` or `RuntimeError` around send/IMAP
  calls, catch `MailToolsBoxError` (or the specific subclass) instead.
- `EmailValidationError` subclasses `ValueError`, so existing `except ValueError`
  handlers continue to work.
