from distutils.core import setup

long_description = '''# MailToolsBox ##

MailToolsBox is a Python library for dealing with Email handling in easy way.

## Installation ##

Use the package manager [pip](https://pypi.org/project/MailToolsBox/) to install MailToolsBox.

```bash
pip install MailToolsBox
```

## Usage ##

- Send Usage


import MailToolsBox.mailSender
mail = MailToolsBox.mailSender.SendAgent(user_email='username@gmail.com', server_smtp_address='smtp.gmail.com', user_email_password='User Password', port=587)
mail.send_mail(recipent_email='user@gmail.com', subject='This is Subject Text', message_Body='This is  Body Text')


- Imap Usage

from MailToolsBox.imapClient import ImapAgent

EMAIL_ACCOUNT = "myaddress@gmail.com"
PASSWORD = "mypassword"
SERVER_ADDRESS = ('my server address or domain name or ip ex:"imap.gmail.com" ')

x = ImapAgent(email_account=EMAIL_ACCOUNT, password=PASSWORD, server_address=SERVER_ADDRESS)
x.download_mail_text() # optional parameter : (lookup='ALL',save=True,path='/home/user/')
x.download_mail_json() # return json format | optional parameter : (lookup='ALL',save=True,filename='filename.json',path='/home/user/')
x.download_mail_msg() # optional parameter : (lookup='ALL',path='/home/user/')


## Contributing ##
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)

'''


setup(
  name = 'MailToolsBox',
  packages = ['MailToolsBox'],
  version = '0.0.4.0',
  license='MIT',
  description = 'Mail Tools boxes to make developer life easier on build mail sender or even mail server',   # Give a short description about your library
  long_description=long_description,
  long_description_content_type="text/markdown",
  author = 'Rambod Ghashghai',                   # Type in your name
  author_email = 'rambod@ramai.io',      # Type in your E-Mail
  url = 'https://www.ramai.io',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/rambod/MailToolsBox/archive/0.0.4.tar.gz',    # I explain this later on
  keywords = ['Mail', 'Server', 'smtp' ,  'send' , 'email', 'tools', 'box'],   # Keywords that define your package best
  install_requires=[
    # I get to this in a second
      ],
  classifiers=[
    'Development Status :: 4 - Beta',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Communications :: Email',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
  ],
)