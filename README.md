# MailToolsBox

MailToolsBox is a modern, pragmatic email toolkit for Python. It gives you clean, production‑grade SMTP sending and a capable IMAP client in one package. The design favors explicit security controls, sane defaults, and simple APIs that scale from quick scripts to services.

---

## What you get

- SMTP sender with sync and async APIs
- IMAP client with search, fetch, flags, move, delete, export
- Security modes: `auto`, `starttls`, `ssl`, `none`
- Optional OAuth2 XOAUTH2 for both SMTP and IMAP
- Gmail and Exchange Online presets
- Jinja2 templates with auto plain text fallback
- MIME smart attachment handling
- Bulk sending helpers
- Email validation
- Environment variable configuration
- Backward compatibility shim `SendAgent`

---

## Install

```bash
pip install MailToolsBox
```

---

## Quick start

### Send a basic email

```python
from MailToolsBox import EmailSender

sender = EmailSender(
    user_email="you@example.com",
    server_smtp_address="smtp.example.com",
    user_email_password="password",
    port=587,                        # typical for STARTTLS
    security_mode="starttls"         # or "auto"
)

sender.send(
    recipients=["to@example.com"],
    subject="Hello",
    message_body="Plain text body"
)
```

### Read emails

```python
from MailToolsBox.imap_client import ImapClient  # or the path you placed it under

with ImapClient(
    email_account="you@example.com",
    password="password",
    server_address="imap.example.com",
    port=993,
    security_mode="ssl"
) as imap:
    imap.select("INBOX")
    uids = imap.search("UNSEEN")
    messages = imap.fetch_many(uids[:10])
    for m in messages:
        print(m.subject, m.from_[0].email if m.from_ else None)
```

> Tip: If you installed the package as a single module, import paths may be `from MailToolsBox import ImapClient`. Keep them consistent with your package layout.

---

## SMTP in depth

### Security modes

- `auto`:
  - If port is 465 use implicit SSL.
  - Otherwise attempt STARTTLS if the server advertises it. If not available, stay plain.
- `starttls`: force STARTTLS upgrade.
- `ssl`: implicit SSL on connect, typical for port 465.
- `none`: no TLS. Use only inside trusted networks.

### Gmail and Exchange recipes

```python
# Gmail with app password
sender = EmailSender.for_gmail_app_password("you@gmail.com", "abcd abcd abcd abcd")
sender.send(["to@example.com"], "Hi", "Body")

# Exchange Online with SMTP AUTH
exchange = EmailSender.for_exchange_smtp_auth("you@company.com", "password")
exchange.send(["person@company.com"], "Status", "Body")
```

### OAuth2 XOAUTH2

```python
oauth_sender = EmailSender(
    user_email="you@gmail.com",
    server_smtp_address="smtp.gmail.com",
    port=587,
    security_mode="starttls",
    oauth2_access_token="ya29.a0Af..."  # obtain via your OAuth flow
)
oauth_sender.send(["to@example.com"], "OAuth2", "Sent with XOAUTH2")
```

### HTML with plain fallback and attachments

```python
html = "<h1>Report</h1><p>See attachment.</p>"
sender.send(
    recipients=["to@example.com"],
    subject="Monthly report",
    message_body=html,
    html=True,
    attachments=["/path/report.pdf", "/path/chart.png"]
)
```

### Async sending

```python
import asyncio

async def main():
    await sender.send_async(
        recipients=["to@example.com"],
        subject="Async",
        message_body="Non blocking send"
    )

asyncio.run(main())
```

### Bulk helpers

```python
sender.send_bulk(
    recipients=["a@example.com", "b@example.com"],
    subject="Announcement",
    message_body="Sent individually to protect privacy"
)
```

### Environment variables

```bash
export EMAIL=you@example.com
export EMAIL_PASSWORD=apppass
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=465
export EMAIL_SECURITY=ssl
export EMAIL_REPLY_TO=noreply@example.com
```

```python
sender = EmailSender.from_env()
```

---

## IMAP in depth

The `ImapClient` provides safe defaults with flexible control when you need it.

### Connect and select

```python
imap = ImapClient(
    email_account="you@example.com",
    password="password",
    server_address="imap.example.com",
    port=993,
    security_mode="ssl"
)
imap.login()
imap.select("INBOX")
```

Or use context manager:

```python
with ImapClient.from_env() as imap:
    imap.select("INBOX")
    print(imap.list_mailboxes())
```

Environment variables:

```bash
export IMAP_EMAIL=you@example.com
export IMAP_PASSWORD=apppass
export IMAP_SERVER=imap.gmail.com
export IMAP_PORT=993
export IMAP_SECURITY=ssl
# Optional OAuth token
export IMAP_OAUTH2_TOKEN=ya29.a0Af...
```

### Search and fetch

```python
uids = imap.search("UNSEEN", "SINCE", "01-Jan-2025")
item = imap.fetch(uids[0])
print(item.subject, item.date, item.flags)
print(item.text or item.html)
```

### Attachments and export

```python
paths = imap.save_attachments(item, "./attachments")
eml_path = imap.save_eml(item, "./message.eml")
```

### Flags, move, delete

```python
imap.mark_seen(item.uid)
imap.add_flags(item.uid, "\Flagged")
imap.move([item.uid], "Archive")
imap.delete(item.uid)
imap.expunge()
```

### Legacy style exports

```python
# Dump mailbox to one text file
imap.download_mail_text(path="./dumps", mailbox="INBOX")

# Export selected emails as JSON
imap.download_mail_json(lookup="UNSEEN", save=True, path="./dumps", file_name="mail.json")

# Save each message to .eml
imap.download_mail_eml(directory="./eml", lookup="ALL", mailbox="INBOX")
```

### OAuth2 XOAUTH2

```python
imap = ImapClient(
    email_account="you@gmail.com",
    password=None,
    server_address="imap.gmail.com",
    port=993,
    security_mode="ssl",
    oauth2_access_token="ya29.a0Af..."
)
with imap:
    imap.select("INBOX")
    uids = imap.search("ALL")
```

---

## Validation and templates

- Addresses are normalized with `email-validator` when validation is enabled.
- Templates use Jinja2 with autoescape for HTML and XML.
- HTML sending includes a plain text alternative for better deliverability.

Template example `templates/welcome.html`:

```html
<h1>Welcome, {{ user }}</h1>
<p>Activate your account: <a href="{{ link }}">activate</a></p>
```

Send with template:

```python
sender = EmailSender(
    user_email="you@example.com",
    server_smtp_address="smtp.example.com",
    user_email_password="pw",
    template_dir="./templates"
)

sender.send_template(
    recipient="to@example.com",
    subject="Welcome",
    template_name="welcome.html",
    context={"user": "Alex", "link": "https://example.com/activate"}
)
```

---

## Backward compatibility

`SendAgent` stays available for older codebases. It is thin and delegates to `EmailSender`. Prefer `EmailSender` in new code.

```python
from MailToolsBox import SendAgent
legacy = SendAgent("you@example.com", "smtp.example.com", "pw", port=587)
legacy.send_mail(["to@example.com"], "Subject", "Body", tls=True)
```

---

## Security notes

- Prefer `ssl` on 465 or `starttls` on 587.
- Use app passwords when your provider offers them.
- Prefer OAuth2 tokens for long term services.
- Use `none` only on trusted networks.

---

## Troubleshooting

- Authentication errors on Gmail usually mean you need an app password or OAuth2.
- If a STARTTLS upgrade fails in `auto`, set `security_mode="ssl"` on 465 or `security_mode="starttls"` on 587.
- For corporate relays that do not support TLS, set `security_mode="none"` and ensure the network is trusted.
- Enable logging in your application to capture SMTP or IMAP server responses.

```python
import logging
logging.basicConfig(level=logging.INFO)
```

---

## Contributing

PRs are welcome. Keep changes focused and covered with tests. Add docs for new behavior. Use ruff and black for formatting.

---

## License

MIT. See LICENSE for details.
