import imaplib
import email
import json
import datetime
import os
from typing import List


class ImapAgent:
    """Simple IMAP client used to fetch messages from a mail server.

    It provides ``login_account`` and ``logout_account`` helpers for
    managing the connection and several download methods—
    ``download_mail_text``, ``download_mail_json`` and
    ``download_mail_msg``—to retrieve emails in different formats.
    """
    def __init__(self, email_account, password, server_address):
        self.email_account = email_account
        self.password = password
        self.server_address = server_address
        self.mail = None

    @classmethod
    def from_env(cls) -> "ImapAgent":
        """Create :class:`ImapAgent` from environment variables.

        Required variables are ``IMAP_EMAIL``, ``IMAP_PASSWORD`` and
        ``IMAP_SERVER``.
        """
        email_account = os.environ["IMAP_EMAIL"]
        password = os.environ["IMAP_PASSWORD"]
        server = os.environ["IMAP_SERVER"]
        return cls(email_account, password, server)

    def __enter__(self) -> "ImapAgent":
        self.login_account()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.logout_account()

    def login_account(self):
        self.mail = imaplib.IMAP4_SSL(self.server_address)
        self.mail.login(self.email_account, self.password)

    def logout_account(self):
        if self.mail is not None:
            try:
                self.mail.logout()
            finally:
                self.mail = None

    def download_mail_text(self, path='', mailbox='INBOX'):
        """Download all emails in ``mailbox`` and write them as plain text.

        This method now ensures that a connection to the IMAP server has been
        established before attempting to access any mailbox.  If no connection
        exists, :py:meth:`login_account` is invoked to create one.
        """
        if self.mail is None:
            self.login_account()

        file_path = os.path.join(path, 'email.txt')
        with open(file_path, 'w') as f:
            self.mail.select(mailbox)
            _, data = self.mail.uid('search', None, 'ALL')
            uids = data[0].split()
            for uid in uids:
                _, email_data = self.mail.uid('fetch', uid, '(RFC822)')
                raw_email = email_data[0][1]
                raw_email_string = raw_email.decode('utf-8')
                email_message = email.message_from_string(raw_email_string)

                # Header Details
                date_tuple = email.utils.parsedate_tz(email_message['Date'])
                if date_tuple:
                    local_date = datetime.datetime.fromtimestamp(
                        email.utils.mktime_tz(date_tuple))
                    local_message_date = local_date.strftime(
                        "%a, %d %b %Y %H:%M:%S")
                email_from = str(email.header.make_header(
                    email.header.decode_header(email_message['From'])))
                email_to = str(email.header.make_header(
                    email.header.decode_header(email_message['To'])))
                subject = str(email.header.make_header(
                    email.header.decode_header(email_message['Subject'])))

                # Body details
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True)
                        f.write(
                            f"From: {email_from}\nTo: {email_to}\nDate: {local_message_date}\nSubject: {subject}\n\nBody:\n\n{body.decode('utf-8')}\n\n")
        self.mail.close()
        self.logout_account()


    def download_mail_json(self, lookup: str = 'ALL', save: bool = False, path: str = '', file_name: str = 'mail.json') -> str:
        save_json = save

        with imaplib.IMAP4_SSL(self.server_address) as mail:
            mail.login(self.email_account, self.password)
            mail.select("inbox")
            result, data = mail.uid('search', None, lookup)  # (ALL/UNSEEN)
            uids = data[0].split()
            mail_items: List[dict] = []

            for uid in uids:
                result, email_data = mail.uid('fetch', uid, '(RFC822)')
                raw_email = email_data[0][1]
                raw_email_string = raw_email.decode('utf-8')
                email_message = email.message_from_string(raw_email_string)
                date_tuple = email.utils.parsedate_tz(email_message['Date'])
                if date_tuple:
                    local_date = datetime.datetime.fromtimestamp(
                        email.utils.mktime_tz(date_tuple))
                    local_message_date = f"{local_date.strftime('%a, %d %b %Y %H:%M:%S')}"
                email_from = str(email.header.make_header(
                    email.header.decode_header(email_message['From'])))
                email_to = str(email.header.make_header(
                    email.header.decode_header(email_message['To'])))
                subject = str(email.header.make_header(
                    email.header.decode_header(email_message['Subject'])))
                body = ''

                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8')
                        break
                else:
                    continue

                mail_items.append({
                    'email_from': email_from,
                    'email_to': email_to,
                    'local_message_date': local_message_date,
                    'subject': subject,
                    'body': body,
                })

            mail.close()
            mail.logout()

        mail_items_json = json.dumps(mail_items)

        if save_json:
            file_path = os.path.join(path, file_name)
            with open(file_path, 'w') as f:
                f.write(mail_items_json)

        return mail_items_json

    def download_mail_msg(self, path='', lookup='ALL'):
        self.login_account()
        result, data = self.mail.uid('search', None, lookup)  # (ALL/UNSEEN)
        for i, latest_email_uid in enumerate(data[0].split()):
            result, email_data = self.mail.uid(
                'fetch', latest_email_uid, '(RFC822)')
            raw_email = email_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            file_name = os.path.join(path, f"email_{i}.msg")
            with open(file_name, 'wb') as f:
                f.write(email_message.as_bytes())
        self.mail.close()
        self.logout_account()
