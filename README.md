# MailToolsBox

MailToolsBox is a modern, feature-rich Python package designed for sending and managing emails with ease. It provides robust functionality for handling SMTP email sending, template-based emails using Jinja2, attachments, CC/BCC support, and email validation. Additionally, MailToolsBox ensures backward compatibility with legacy implementations.

## Features

- **Send emails via SMTP with ease**
- **Support for multiple recipients (To, CC, BCC)**
- **HTML and plain text email support**
- **Attachment handling**
- **Template-based email rendering using Jinja2**
- **Secure email transactions with TLS/SSL**
- **Asynchronous email sending via `send_async`**
- **Email address validation**
- **Logging for debugging and monitoring**
- **Bulk email sending with `send_bulk`**
- **Convenient configuration via environment variables using `from_env`**
- **Backward compatibility with `SendAgent`**

---

## Installation

Install MailToolsBox from PyPI using pip:

```bash
pip install MailToolsBox
```

---

## Getting Started

### 1. **Sending a Basic Email**

The `EmailSender` class is the primary interface for sending emails. Below is an example of sending a simple plain text email:

```python
from MailToolsBox import EmailSender

# Email configuration
sender = EmailSender(
    user_email="your@email.com",
    server_smtp_address="smtp.example.com",
    user_email_password="yourpassword",
    port=587
)

# Sending email
sender.send(
    recipients=["recipient@example.com"],
    subject="Test Email",
    message_body="Hello, this is a test email!"
)
```

---

### 2. **Sending an HTML Email with Attachments**

```python
sender.send(
    recipients=["recipient@example.com"],
    subject="HTML Email Example",
    message_body="""<h1>Welcome!</h1><p>This is an <strong>HTML email</strong>.</p>""",

    html=True,
    attachments=["/path/to/document.pdf"]
)
```

---

### 3. **Using Email Templates (Jinja2)**

MailToolsBox allows sending emails using Jinja2 templates stored in the `templates/` directory.
Ensure this directory exists alongside your code or provide its path via the `template_dir` argument when instantiating `EmailSender`.

```python
sender = EmailSender(
    user_email="you@example.com",
    server_smtp_address="smtp.example.com",
    user_email_password="secret",
    template_dir="/path/to/templates",
)
```

#### **Example Template (`templates/welcome.html`)**:

```html
<html>
<head>
    <title>Welcome</title>
</head>
<body>
    <h1>Welcome, {{ username }}!</h1>
    <p>Click <a href="{{ activation_link }}">here</a> to activate your account.</p>
</body>
</html>
```

#### **Sending an Email with a Template**:

```python
context = {
    "username": "John Doe",
    "activation_link": "https://example.com/activate"
}

sender.send_template(
    recipient="recipient@example.com",
    subject="Welcome to Our Service",
    template_name="welcome.html",
    context=context,
    bcc=["bcc@example.com"]
)
```

---

### 4. **CC, BCC, and Multiple Recipients**

```python
sender.send(
    recipients=["recipient@example.com"],
    subject="CC & BCC Example",
    message_body="This email has CC and BCC recipients!",
    cc=["cc@example.com"],
    bcc=["bcc@example.com"]
)
```

---

### 5. **Asynchronous Email Sending**

Send emails without blocking using `send_async` and `asyncio`:

```python
import asyncio

async def main():
    await sender.send_async(
        recipients=["recipient@example.com"],
        subject="Async Example",
        message_body="This email was sent asynchronously!"
    )

asyncio.run(main())
```

---

### 6. **Bulk Email Sending**

Send the same message to many recipients individually, ensuring privacy:

```python
sender.send_bulk(
    recipients=["user1@example.com", "user2@example.com"],
    subject="Announcement",
    message_body="This email is sent separately to each recipient!",
)
```

---

### 7. **Backward Compatibility with `SendAgent`**

For those migrating from earlier versions, `SendAgent` ensures seamless compatibility:

```python
from MailToolsBox import SendAgent

legacy_sender = SendAgent(
    user_email="your@email.com",
    server_smtp_address="smtp.example.com",
    user_email_password="yourpassword",
    port=587
)

legacy_sender.send_mail(
    recipient_email=["recipient@example.com"],
    subject="Legacy Compatibility Test",
        message_body="Testing backward compatibility."
)
```

---

### 8. **Retrieving Emails via IMAP**

`ImapAgent` can be used to fetch messages from an IMAP mailbox. It supports
loading configuration from environment variables with `from_env` and can be
used as a context manager to ensure connections are closed properly.

```python
from MailToolsBox import ImapAgent

# Using environment variables IMAP_EMAIL, IMAP_PASSWORD and IMAP_SERVER
agent = ImapAgent.from_env()

with agent as imap:
    imap.download_mail_text(path="/tmp/")
```


---

## Configuration & Security Best Practices

- **Use environment variables** instead of hardcoding credentials.
- **Enable 2FA** on your email provider and use app passwords if required.
- **Use TLS/SSL** to ensure secure email delivery.

Example using environment variables:

```python
sender = EmailSender.from_env()
```

---

## Error Handling & Logging

MailToolsBox provides built-in logging to help debug issues:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Example of handling exceptions:

```python
try:
    sender.send(
        recipients=["recipient@example.com"],
        subject="Error Handling Test",
        message_body="This is a test email."
    )
except Exception as e:
    print(f"Failed to send email: {e}")
```

---

## Contributing

MailToolsBox is an open-source project. Contributions are welcome! To contribute:

1. Fork the repository on GitHub.
2. Create a new feature branch.
3. Implement changes and write tests.
4. Submit a pull request for review.

For discussions, visit **[rambod.net](https://www.rambod.net)**. **[mailtoolsbox](https://rambod.net/portfolio/mailtoolsbox/)**

---

## License

MailToolsBox is licensed under the MIT License. See the [LICENSE](https://choosealicense.com/licenses/mit/) for details.
