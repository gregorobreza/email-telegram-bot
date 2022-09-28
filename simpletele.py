import telegram
from PyPDF2 import PdfReader
import json

api_key = "5504018793:AAEEMKQab78b9q8tdWbpnJ1jwXyCwfUWYhg"
user_id = '823874933'

reader = PdfReader("example.pdf")

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

bot = telegram.Bot(token=api_key)
document = open("example.pdf", "rb") 

bot.send_message(chat_id=user_id, text='There is invoce for Dobra hiša recived on ___:')
bot.send_message(chat_id=user_id, text="TRR")
bot.send_message(chat_id=user_id, text=f"{data['trr']}")
bot.send_message(chat_id=user_id, text="Plačilo")
bot.send_message(chat_id=user_id, text=f"{data['placilo']}")
bot.send_message(chat_id=user_id, text="Sklic")
bot.send_message(chat_id=user_id, text=f"{data['sklic']}")
bot.send_document(chat_id=user_id, document=document)
bot.send_message(chat_id=user_id, text="******************************************")
document.close()
