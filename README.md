# MailToolsBox

MailToolsBox is a Python package that provides two classes to help you
interact with emails: SendAgent and ImapAgent.

# Installation

Use the package manager PyPI <https://pypi.org/project/MailToolsBox/> to
install MailToolsBox.

You can install MailToolsBox via pip:

```bash
pip install MailToolsBox
```

SendAgent Class (Send SMTP Usage) \-\-\-\-\-\-\-\-\-\-\-\-\-\--The
SendAgent class allows you to send emails through SMTP. Here is an
example of how to use this class:

```pycon
from MailToolsBox import SendAgent

user_email = "example@gmail.com"
user_email_password = "password"
server_smtp_address = "smtp.gmail.com"
port = 587

send_agent = SendAgent(user_email, server_smtp_address, user_email_password, port)
recipient_email = "example@example.com"
subject = "Test email"
message_body = "This is a test email sent from MailToolsBox."
send_agent.send_mail(recipient_email, subject, message_body)
```

# send_mail method

The send_mail method sends an email to one or more recipients and optionally includes attachments.

Parameters:
recipient_email: the email address of the recipient. Can be a string or a list of strings for multiple recipients.
subject: the subject of the email.
message_body: the body of the email.
cc (optional): a list of email addresses to be included in the CC field.
bcc (optional): a list of email addresses to be included in the BCC field.
attachments (optional): a list of file paths to be attached to the email.
tls (optional, default True): enable Transport Layer Security.
server_quit (optional, default False): whether to quit the SMTP server after sending the email.

# ImapAgent Class

The ImapAgent class provides functionality for connecting to an email
server via the Internet Message Access Protocol (IMAP) and downloading
emails from the server.

# IMAP CLIENT Usage

To use the ImapAgent class, you first need to create an instance of the
class and provide your email account information and the address of the
email server that you want to connect to:

```pycon
from MailToolsBox import ImapAgent

email_account = 'your_email@example.com'
password = 'your_email_password'
server_address = 'imap.example.com'

imap_agent = ImapAgent(email_account, password, server_address)
imap_agent.download_mail_text() # optional parameter : (lookup='ALL',save=True,path='/home/user/')
imap_agent.download_mail_json() # return json format | optional parameter : (lookup='ALL',save=True,filename='filename.json',path='/home/user/')
imap_agent.download_mail_msg() # optional parameter : (lookup='ALL',path='/home/user/')

```

# Methods

login_account(): This method connects to the email server and logs in to
your email account using your email address and password.

download_mail_text(): This method downloads the text content of all the
emails in the specified mailbox and saves the content to a text file.
The method takes the following parameters:

path (optional): The path where you want to save the text file. If not
specified, the text file will be saved in the current working directory.

mailbox (optional): The name of the mailbox that you want to download
emails from. If not specified, the emails in the INBOX mailbox will be
downloaded.

# Attachment, CC, and BCC

MailToolsBox provides additional features such as the ability to send email attachments, specify CC and BCC recipients, in addition to the recipient_email parameter.

# Attachments

To include attachments in your email, you can pass a list of file paths to the attachments parameter in the send_mail() method. MailToolsBox will read the attachment files and add them as MIMEApplication objects to your email message.

# CC and BCC

To specify CC and BCC recipients, you can pass a list of email addresses to the cc and bcc parameters in the send_mail() method. The addresses will be added to the email message headers.

Here is an example of how to use the cc and bcc parameters:

```pycon
from MailToolsBox import SendAgent

user_email = "example@gmail.com"
user_email_password = "password"
server_smtp_address = "smtp.gmail.com"
port = 587

send_agent = SendAgent(user_email, server_smtp_address, user_email_password, port)
recipient_email = "example@example.com"
cc = ["example2@example.com", "example3@example.com"]
bcc = ["example4@example.com"]
subject = "Test email"
message_body = "This is a test email sent from MailToolsBox."
attachments = ["path/to/file1.pdf", "path/to/file2.txt"]
send_agent.send_mail(recipient_email, subject, message_body, cc=cc, bcc=bcc, attachments=attachments)

```

In this example, the email is sent to recipient_email, with CC recipients example2@example.com and example3@example.com, and BCC recipient example4@example.com. The email also contains two attachments: file1.pdf and file2.txt.

# Conclusion

MailToolsBox provides a simple and easy-to-use interface for sending and receiving emails. With the SendAgent and ImapAgent classes, you can easily integrate email functionality into your Python applications.

# Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

# License

MIT \| <https://choosealicense.com/licenses/mit/>
