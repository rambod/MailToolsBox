import datetime
import email
import imaplib
import json


class ImapAgent:
    def __init__(self, email_account, password, server_address):
        self.email_account = email_account
        self.password = password
        self.server_address = server_address
        self.mail = imaplib.IMAP4_SSL(self.server_address)

    def login_account(self):
        self.mail.login(self.email_account, self.password)
        self.mail.list()
        self.mail.select('inbox')


    def download_mail_text(self, path='',lookup='ALL'):
        self.login_account()
        result, data = self.mail.uid('search', None, lookup)  # (ALL/UNSEEN)
        i = len(data[0].split())
        for x in range(i):
            latest_email_uid = data[0].split()[x]
            result, email_data = self.mail.uid('fetch', latest_email_uid, '(RFC822)')
            # result, email_data = conn.store(num,'-FLAGS','\\Seen')
            # this might work to set flag to seen, if it doesn't already
            raw_email = email_data[0][1]
            raw_email_string = raw_email.decode('utf-8')
            email_message = email.message_from_string(raw_email_string)

            # Header Details
            date_tuple = email.utils.parsedate_tz(email_message['Date'])
            if date_tuple:
                local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                local_message_date = "%s" % (str(local_date.strftime("%a, %d %b %Y %H:%M:%S")))
            email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
            email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
            subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))


            # Body details
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    file_name = path+"email_" + str(x) + ".txt"
                    output_file = open(file_name, 'w')
                    output_file.write("From: %s\nTo: %s\nDate: %s\nSubject: %s\n\nBody: \n\n%s" % (
                    email_from, email_to, local_message_date, subject, body.decode('utf-8')))
                    output_file.close()
                else:
                    continue

    def download_mail_json(self, lookup,save=False,path='',file_name='mail.json'):
        save_json = save
        self.login_account()
        result, data = self.mail.uid('search', None, lookup)  # (ALL/UNSEEN)
        i = len(data[0].split())
        mail_items = []
        for x in range(i):
            latest_email_uid = data[0].split()[x]
            result, email_data = self.mail.uid('fetch', latest_email_uid, '(RFC822)')
            raw_email = email_data[0][1]
            raw_email_string = raw_email.decode('utf-8')
            email_message = email.message_from_string(raw_email_string)
            date_tuple = email.utils.parsedate_tz(email_message['Date'])
            if date_tuple:
                local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                local_message_date = "%s" % (str(local_date.strftime("%a, %d %b %Y %H:%M:%S")))
            email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
            email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
            subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    mail_items.append({
                        'email_from': email_from,
                        'email_to': email_to,
                        'local_message_date': local_message_date,
                        'subject': subject,
                        'body': body.decode('utf-8'),
                    })
                else:
                    continue
        if save_json == True:
            json_file_name = file_name
            output_file = open(path + json_file_name, 'w')
            output_file.write(json.dumps(mail_items))
            output_file.close()
        return json.dumps(mail_items)

    def download_mail_msg(self, path='' ,lookup='ALL'):
        self.login_account()
        result, data = self.mail.uid('search', None, lookup)  # (ALL/UNSEEN)
        i = len(data[0].split())
        for x in range(i):
            latest_email_uid = data[0].split()[x]
            result, email_data = self.mail.uid('fetch', latest_email_uid, '(RFC822)')
            # result, email_data = conn.store(num,'-FLAGS','\\Seen')
            # this might work to set flag to seen, if it doesn't already
            raw_email = email_data[0][1]
            raw_email_string = raw_email.decode('utf-8')
            email_message = email.message_from_string(raw_email_string)
            str(email_message)
            file_name = path + "email_" + str(x) + ".msg"
            output_file = open(file_name, 'w')
            output_file.write(str(email_message))
            output_file.close()


