import re, json
import time
from bs4 import BeautifulSoup

def split_long(body, max_words=250, overlap=40):
    # split articles into chunks
    
    # split at numbered paragraphs: "1." -> keep (a), (b), ... connected for now
    paras = re.split(r"\n(?=(?:\d+\.)\s)", body)

    # pack small paragraphs together, window-split oversized ones
    out, cur = [], ""
    for para in paras:
        words = para.split()
        if len(words) > max_words: # if paragraph on its own exceeds max words
            if cur:
                out.append(cur) # stop building previous chunk and build it
                cur = "" # reset current chunk
            step = max_words - overlap # each new chunk starts 210 words later, 40 words overlap
            for i in range(0, len(words), step): # split huge chunk into smaller overlapping chunks: Start index(0, 210, 420, ...) of length 250
                out.append(" ".join(words[i:i + max_words]))
                if i + max_words >= len(words):
                    break
        elif len((cur + "\n" + para).split()) > max_words: # if adding the next paragraph exceeds max words
            out.append(cur)
            cur = para
        else:
            cur = (cur + "\n" + para).strip()
    if cur:
        out.append(cur)
    return out

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

# what to additionally cut
# everything from SECTION to Article x -> discard
# everything from CHAPTER to Article x OR CHAPTER to SECTION -> discard

# an "Article N" splitten
parts = re.split(
    r"\n(?=(?:Article\s+\d+|ANNEX\s+[IVXLCDM]+|CHAPTER\s+(?:\d+|[IVXLCDM]+)|SECTION\s+\d+)\s*\n)",
    text
)

# drop everything before "Article 1", then discard CHAPTER/SECTION parts
parts = parts[1:]
parts = [p for p in parts if not re.match(r"(?:CHAPTER|SECTION)\s", p)]

# trim the last part at the signature block
last = parts[-1]
cut = re.search(r"\nDone at Brussels", last)
if cut:
    parts[-1] = last[:cut.start()]

# # debug slicing 
# with open("data/text.txt", "w", encoding="utf-8") as f:
#     for part in parts:
#         f.write(part)
#         f.write("\n\n")

chunks = []
for p in parts:
    m = re.match(r"Article\s+(\d+)\n(.*?)\n", p)
    if m:
        kind, num, title = "art", m.group(1), m.group(2).strip()
        header = f"Article {num} - {title}"
    else:
        m = re.match(r"ANNEX\s+([IVXLCDM]+)\n(.*?)\n", p)
        if not m:
            continue
        kind, num, title = "annex", m.group(1), m.group(2).strip()
        header = f"Annex {num} - {title}"

    body = p[m.end():].strip()
    for i, piece in enumerate(split_long(body)):
        chunks.append({
            "id": f"{kind}{num}-{i}",
            "article": int(num) if kind == "art" else None,
            "annex": num if kind == "annex" else None,
            "title": title,
            "part": i,
            "text": f"{header}\n{piece}",
        })

json.dump(chunks, open("data/chunks.json", "w"), ensure_ascii=False, indent=1)
print(len(chunks), "chunks")