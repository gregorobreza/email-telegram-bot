from PyPDF2 import PdfReader
import json

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


print(data)