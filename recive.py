import email
import imaplib
from datetime import datetime, timedelta, timezone
import os
import pytz


EMAIL = 'test@sigmadews.com'
PASSWORD = 'Test4064!*'
SERVER = 'imap.hostinger.com'
PORT = 993

# connect to the server and go to its inbox
mail = imaplib.IMAP4_SSL(SERVER, PORT)
mail.login(EMAIL, PASSWORD)
# we choose the inbox but you can select others
mail.select('inbox')


# we'll search using the ALL criteria to retrieve
# every message inside the inbox
# it will return with its status and a list of ids
status, data = mail.search(None, 'ALL')
print(status)
# the list returned is a list of bytes separated
# by white spaces on this format: [b'1 2 3', b'4 5 6']
# so, to separate it first we create an empty list
mail_ids = []
# then we go through the list splitting its blocks
# of bytes and appending to the mail_ids list
for block in data:
    # the split function called without parameter
    # transforms the text or bytes into a list using
    # as separator the white spaces:
    # b'1 2 3'.split() => [b'1', b'2', b'3']
    mail_ids += block.split()


# now for every id we'll fetch the email
# to extract its content
for i in mail_ids:
    # the fetch function fetch the email given its id
    # and format that you want the message to be
    status, data = mail.fetch(i, '(RFC822)')

    # the content data at the '(RFC822)' format comes on
    # a list with a tuple with header, content, and the closing
    # byte b')'
    for response_part in data:
        # so if its a tuple...
        if isinstance(response_part, tuple):
            # we go for the content at its second element
            # skipping the header at the first and the closing
            # at the third
            message = email.message_from_bytes(response_part[1])

            # for part in message.walk():
            #     if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
            #         open(part.get_filename(),'wb').write(part.get_payload(decode=True))
            # with the content we can extract the info about
            # who sent the message and its subject
            mail_from = message['from']
            mail_subject = message['subject']
            mail_date = message["date"]
            date_obj = datetime.strptime(mail_date, "%a, %d %b %Y %H:%M:%S %z")
            # from_folder_name = str(mail_from).translate(
            #     {ord("<"): None, ord(">"): None}).split("@")[1].split(".")[0]
            from_folder_name = str(mail_from).split("<")[1].replace(">", "")
            date_folder_path = os.path.join(
                from_folder_name, datetime.strftime(date_obj, "%Y-%m-%d"))
            print("mail", date_obj)
            print("now", datetime.now(pytz.timezone("Europe/Ljubljana")))
            if (date_obj < datetime.now(pytz.timezone("Europe/Ljubljana")) - timedelta(hours=6)):
                break
            # then for the text we have a little more work to do
            # because it can be in plain text or multipart
            # if its not plain text we need to separate the message
            # from its annexes to get the text
            if message.is_multipart():
                mail_content = ''

                # on multipart we have the text message and
                # another things like annex, and html version
                # of the message, in that case we loop through
                # the email payload
                for part in message.get_payload():
                    # if the content type is text/plain
                    # we extract it
                    if part.get_content_type() == 'text/plain':
                        mail_content += part.get_payload()

                    if part.get_content_type() == 'multipart/alternative':
                        for neki in part.get_payload():
                            if neki.get_content_type() == 'text/plain':
                                mail_content += neki.get_payload()

                    # if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                    if part.get_content_type() == 'application/pdf':

                        if (not os.path.isdir(from_folder_name)):
                            os.mkdir(from_folder_name)
                        if (not os.path.isdir(date_folder_path)):
                            os.mkdir(date_folder_path)
                        with open(os.path.join(date_folder_path, part.get_filename()), 'wb') as file:
                            file.write(part.get_payload(decode=True))
                            
                        print("done writing")
                        # try:
                        #     recive = 
                        #     recive.write(part.get_payload(decode=True))
                        #     recive.close()
                        # finally:
                        #     recive.close()
                        # open(os.path.join(date_folder_path,
                        #      part.get_filename()), 'wb')

            else:
                mail_content = message.get_payload()

            # and then let's show its result
            print(f'From: {mail_from}')
            print(f'Date: {mail_date}')
            print(f'Subject: {mail_subject}')
            # print(f'Content: {mail_content}')


mail.close()
mail.logout()
