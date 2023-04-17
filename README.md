# MailToolsBox

MailToolsBox is a Python package that provides two classes to help you
interact with emails.

# Installation

Use the package manager <https://pypi.org/project/MailToolsBox/> to
install MailToolsBox.

You can install MailToolsBox via pip:

``` bash
pip install MailToolsBox
```

SendAgent Class (Send SMTP Usage) \-\-\-\-\-\-\-\-\-\-\-\-\-\--The
SendAgent class allows you to send emails through SMTP. Here is an
example of how to use this class:

``` pycon
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

# ImapAgent Class

The ImapAgent class provides functionality for connecting to an email
server via the Internet Message Access Protocol (IMAP) and downloading
emails from the server.

# IMAP CLIENT Usage

To use the ImapAgent class, you first need to create an instance of the
class and provide your email account information and the address of the
email server that you want to connect to:

``` pycon
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

# Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

# License

MIT \| <https://choosealicense.com/licenses/mit/>
