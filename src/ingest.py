import re, json
import time
from bs4 import BeautifulSoup

def roman_to_int(s):
    values = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000
    }

    total = 0
    prev = 0

    for char in reversed(s):
        value = values[char]
        if value < prev:
            total -= value
        else:
            total += value
        prev = value
    return total

html = open("data/ai_act.html", encoding="utf-8").read()
text = BeautifulSoup(html, "lxml").get_text("\n")
text = re.sub(r"\n\s*\n+", "\n", text)

# an "Article N" splitten
# parts = re.split(r"\n(?=Article\s+\d+\s*\n)", text)
parts = re.split(
    r"\n(?=(?:Article\s+\d+|ANNEX\s+[IVXLCDM]+)\s*\n)",
    text
) # include ANNEXes
parts = parts[1:]  # drop everything before "Article 1"

# trim the last part at the signature block
last = parts[-1]
cut = re.search(r"\nDone at Brussels", last)
if cut:
    parts[-1] = last[:cut.start()]

# Debug slicing 
with open("data/text.txt", "w", encoding="utf-8") as f:
    for part in parts:
        f.write(part)
        f.write("\n\n")

chunks = []
for p in parts:
    m = re.match(r"Article\s+(\d+)\n(.*?)\n", p)
    if not m:
        m = re.match(r"ANNEX\s+([IVXLCDM]+)\n(.*?)\n", p)
        if not m:
            continue
        annex, title = m.group(1), m.group(2).strip()
        chunks.append({
            "id": f"annex{roman_to_int(annex)}",
            "article": None,
            "annex": roman_to_int(annex),
            "title": title,
            "text": p.strip(),
        })
    else:
        art, title = m.group(1), m.group(2).strip()
        # lange Artikel in Absätze teilen: "1. ", "2. " am Zeilenanfang
        # paras = re.split(r"\n(?=\d+\.\s)", p)
        chunks.append({
            "id": f"art{art}",
            "article": int(art),
            "annex": None,
            "title": title,
            "text": p.strip(),
        })

json.dump(chunks, open("data/chunks.json", "w"), ensure_ascii=False, indent=1)
print(len(chunks), "chunks")