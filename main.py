from dataclasses import dataclass
import imaplib
import email
from datetime import datetime, timedelta, timezone
import os
import pytz
import telegram
from PyPDF2 import PdfReader
import logging
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BillEmailBot:
    time_delay: int = 6  # in hours

    email: str = os.getenv("EMAIL_ADDRESS")
    password: str = os.getenv("EMAIL_PASSWORD")
    server: str = os.getenv("EMAIL_SERVER")
    port: int = os.getenv("EMAIL_PORT")

    api_key: str = os.getenv("TELEGRAM_API_KEY")
    user_id: int = os.getenv("TELEGRAM_USER_ID")

    mail: imaplib.IMAP4_SSL = imaplib.IMAP4_SSL(server, port)
    bot = telegram.Bot(token=api_key)

    def open_inbox(self) -> list:
        mail_ids = []
        self.mail.login(self.email, self.password)
        self.mail.select("inbox")
        status, data = self.mail.search(None, "ALL")
        if status == "OK":
            logging.info("Loged in in inbox")
            for block in data:
                mail_ids += block.split()
            return mail_ids
        else:
            raise Exception("Failed opeing inbox")

    def send_message(self, text):
        self.bot.send_message(chat_id=self.user_id, text=text)

    def send_document(self, document):
        self.bot.send_document(chat_id=self.user_id, document=document)

    def exctract_pdf_info_hisa(self, document: str):
        reader = PdfReader(document)
        page = reader.pages[0]
        text = page.extract_text()
        text_list = text.split("\n")
        data = {}
        for item in text_list:
            if "Sklic:" in item:
                sklic = item.split(":")[1]
                data["sklic"] = f"SI{sklic[1:]}"
            if "Za plačilo EUR:" in item:
                amount = item.split(":")[1]
                data["placilo"] = f"{amount.replace(' ', '')}"
            if "TRR" in item:
                trr = item.split(":")[1]
                data["trr"] = f"{trr[1:]}"
            if "D.O.O." in item:
                data["prejemnik"] = item
        logging.info("Extracted pdf content")
        return data

    def send_bill_info(self, data: dict, date: str, who: str):
        self.bot.send_message(
            chat_id=self.user_id, text=f"There is invoce for {who} recived on {date}:"
        )
        self.bot.send_message(chat_id=self.user_id, text="Prejemnik")
        self.bot.send_message(chat_id=self.user_id, text=data["prejemnik"])
        self.bot.send_message(chat_id=self.user_id, text="TRR")
        self.bot.send_message(chat_id=self.user_id, text=f"{data['trr']}")
        self.bot.send_message(chat_id=self.user_id, text="Plačilo")
        self.bot.send_message(chat_id=self.user_id, text=f"{data['placilo']}")
        self.bot.send_message(chat_id=self.user_id, text="Sklic")
        self.bot.send_message(chat_id=self.user_id, text=f"{data['sklic']}")

    def check_email(self) -> any:
        mail_ids = self.open_inbox()
        for i in mail_ids:
            status, data = self.mail.fetch(i, "(RFC822)")
            for response_part in data:
                if isinstance(response_part, tuple):
                    message = email.message_from_bytes(response_part[1])
                    mail_from = message["from"]
                    mail_subject = message["subject"]
                    mail_date = message["date"]
                    date_obj = datetime.strptime(mail_date, "%a, %d %b %Y %H:%M:%S %z")
                    from_folder_name = str(mail_from).split("<")[1].replace(">", "")
                    date_folder_path = os.path.join(
                        from_folder_name, datetime.strftime(date_obj, "%Y-%m-%d")
                    )
                    if date_obj < datetime.now(
                        pytz.timezone("Europe/Ljubljana")
                    ) - timedelta(hours=self.time_delay):
                        break
                    if message.is_multipart():
                        mail_content = ""
                        for part in message.get_payload():
                            if part.get_content_type() == "text/plain":
                                mail_content += part.get_payload()
                            if part.get_content_type() == "multipart/alternative":
                                for neki in part.get_payload():
                                    if neki.get_content_type() == "text/plain":
                                        mail_content += neki.get_payload()
                            if part.get_content_type() == "application/pdf":
                                if not os.path.isdir(from_folder_name):
                                    os.mkdir(from_folder_name)
                                if not os.path.isdir(date_folder_path):
                                    os.mkdir(date_folder_path)
                                with open(
                                    os.path.join(date_folder_path, part.get_filename()),
                                    "wb",
                                ) as file:
                                    file.write(part.get_payload(decode=True))
                                    file.close()
                                if "eracuni@ap-gost.si" in mail_content:
                                    data = self.exctract_pdf_info_hisa(file.name)
                                    self.send_bill_info(
                                        data,
                                        datetime.strftime(date_obj, "%d-%m-%Y"),
                                        "Dobra hiša",
                                    )
                                    logging.info("Dobra hiša bill")
                                else:
                                    self.send_message(
                                        "A pdf has be recived that couldn't be extracted"
                                    )
                                    logging.info("Some other bill")
                                document = open(file.name, "rb")
                                self.send_document(document)
                                document.close()
                                self.send_message(
                                    "--------------------------------------------------"
                                )
                                logging.info("done writing and sending")

                else:
                    mail_content = message.get_payload()
                    # logging.info("no pdf attachment found")


def main():
    logging.basicConfig(
        filename="billbot.log", format="%(levelname)s: %(message)s  %(asctime)s", level=logging.INFO
    )
    logging.info("Started")
    emailbot = BillEmailBot(time_delay=6)
    emailbot.check_email()
    logging.info("Finished")


if __name__ == "__main__":
    main()
