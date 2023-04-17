import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from jinja2 import Template
import os
from typing import List, Optional


class SendAgent:
    def __init__(self, user_email: str, server_smtp_address: str, user_email_password: str, port: int) -> None:
        self.user_email = user_email
        self.user_email_password = user_email_password
        self.server_smtp_address = server_smtp_address
        self.port = port
        self.msg = MIMEMultipart()
        self.msg['From'] = self.user_email
        self.server = smtplib.SMTP(self.server_smtp_address, self.port)

    def send_mail(self, recipient_email: str, subject: str, message_body: str, cc: Optional[List[str]] = None,
                  attachments: Optional[List[str]] = None, tls: bool = True, server_quit: bool = False) -> None:
        try:
            self.msg['Subject'] = subject
            self.msg['To'] = recipient_email
            if cc:
                self.msg['Cc'] = COMMASPACE.join(cc)
            if tls:
                self.server.starttls()
            self.server.login(self.user_email, self.user_email_password)

            body = MIMEText(message_body, 'html')
            self.msg.attach(body)

            if attachments:
                for attachment in attachments:
                    with open(attachment, "rb") as attachment_file:
                        attachment_data = attachment_file.read()
                    attachment_part = MIMEApplication(
                        attachment_data, Name=os.path.basename(attachment))
                    attachment_part[
                        'Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                    self.msg.attach(attachment_part)

            recipients = [recipient_email] + cc if cc else [recipient_email]
            self.server.sendmail(
                self.user_email, recipients, self.msg.as_string())

        except (smtplib.SMTPException, FileNotFoundError) as e:
            print(f"An error occurred while sending the email: {e}")
        finally:
            if server_quit:
                self.server.quit()

    def send_mail_multiple_recipients(self, recipients_email: List[str], subject: str, message_body: str,
                                      cc: Optional[List[str]] = None, attachments: Optional[List[str]] = None,
                                      tls: bool = True, server_quit: bool = False) -> None:
        try:
            for recipient_email in recipients_email:
                self.send_mail(recipient_email, subject,
                               message_body, cc, attachments, tls=False)
        except (smtplib.SMTPException, FileNotFoundError) as e:
            print(f"An error occurred while sending the email: {e}")
        finally:
            if server_quit:
                self.server.quit()

    def send_mail_with_template(self, recipient_email: str, subject: str, template_path: str,
                                template_vars: dict, cc: Optional[List[str]] = None,
                                attachments: Optional[List[str]] = None, tls: bool = True,
                                server_quit: bool = False) -> None:
        with open(template_path) as template_file:
            template_content = template_file.read()
        template = Template(template_content)
        message_body = template.render(**template_vars)

        self.send_mail(recipient_email, subject, message_body,
                       cc, attachments, tls, server_quit)

        if server_quit:
            self.server.quit()
