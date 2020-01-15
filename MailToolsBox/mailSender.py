import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class SendAgent:
    def __init__(self, user_email, server_smtp_address, user_email_password, port):
        self.user_email = user_email
        self.user_email_password = user_email_password
        self.server_smtp_address = server_smtp_address
        self.port = port
        self.msg = MIMEMultipart()
        self.msg['From'] = self.user_email
        self.server = smtplib.SMTP(self.server_smtp_address, self.port)

    def send_mail(self, recipient_email, subject, message_body, tls=True, server_quit=False):
        self.msg['Subject'] = subject
        self.msg['To'] = recipient_email
        if tls == True:
            self.server.starttls()
        else:
            pass
        self.server.login(self.user_email, self.user_email_password)
        body = message_body
        self.msg.attach(MIMEText(body, 'plain'))
        text = self.msg.as_string()
        self.server.sendmail(self.user_email, recipient_email, text)
        if server_quit == True:
            self.server.quit()
        else:
            pass

    def send_mail_multiple_recipients(self, recipients_email, subject, message_body, tls=True, server_quit=False):
        for recipient_email in recipients_email:
            self.msg['Subject'] = subject
            self.msg['To'] = recipient_email
            if tls == True:
                self.server.starttls()
            else:
                pass
            self.server.login(self.user_email, self.user_email_password)
            body = message_body
            self.msg.attach(MIMEText(body, 'plain'))
            text = self.msg.as_string()
            self.server.sendmail(self.user_email, recipient_email, text)
        if server_quit == True:
            self.server.quit()
        else:
            pass

