MailToolsBox
------------

MailToolsBox is a Python library for dealing with Email handling in easy way.

Installation
------------
Use the package manager https://pypi.org/project/MailToolsBox/ to install MailToolsBox.


.. code-block:: bash

        pip install MailToolsBox

Send SMTP Usage
---------------

.. code-block:: pycon

    import MailToolsBox.mailSender
    mail = MailToolsBox.mailSender.SendAgent(user_email='username@gmail.com', server_smtp_address='smtp.gmail.com', user_email_password='User Password', port=587)
    mail.send_mail(recipent_email='user@gmail.com', subject='This is Subject Text', message_Body='This is  Body Text')



IMAP CLIENT Usage
-----------------

.. code-block:: pycon

        from MailToolsBox.imapClient import ImapAgent

        EMAIL_ACCOUNT = "myaddress@gmail.com"
        PASSWORD = "mypassword"
        SERVER_ADDRESS = ('my server address or domain name or ip ex:"imap.gmail.com" ')

        x = ImapAgent(email_account=EMAIL_ACCOUNT, password=PASSWORD, server_address=SERVER_ADDRESS)
        x.download_mail_text() # optional parameter : (lookup='ALL',save=True,path='/home/user/')
        x.download_mail_json() # return json format | optional parameter : (lookup='ALL',save=True,filename='filename.json',path='/home/user/')
        x.download_mail_msg() # optional parameter : (lookup='ALL',path='/home/user/')


Contributing
------------

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

License
-------
MIT | https://choosealicense.com/licenses/mit/
