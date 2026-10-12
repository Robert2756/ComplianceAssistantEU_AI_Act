import re, json
from bs4 import BeautifulSoup

def split_long(body, max_words=250, overlap=40):
    # split articles into chunks

    # split at numbered paragraphs: "1." -> keep (a), (b), ... connected for now
    paras = re.split(r"\n(?=(?:\d+\.)\s)", body)

    # pack small paragraphs together, window-split oversized ones over 250 words
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

html = open("data/ai_act.html", encoding="utf-8").read()
text = BeautifulSoup(html, "lxml").get_text("\n")
text = re.sub(r"\n\s*\n+", "\n", text)

# cut recitals -> start from the first article
start = re.search(r"HAVE ADOPTED THIS REGULATION:?", text, re.I)
assert start, "recital marker not found"
text = text[start.end():].strip()

# cut everything between articles and annex -> remove sources
sig = text.find("Done at Brussels")
annex1 = re.compile(r"\nANNEX\s+I\s*\n").search(text, sig)
assert sig != -1 and annex1, "signature or Annex I marker not found"
text = text[:sig].rstrip() + "\n" + text[annex1.start() + 1:]

# chunk text for RAG at headings
parts = re.split(
    r"\n(?=(?:Article\s+\d+|ANNEX\s+[IVXLCDM]+|CHAPTER\s+(?:\d+|[IVXLCDM]+)|SECTION\s+\d+)\s*\n)",
    text
)

# drop CHAPTER and SECTION headings -> they are not relevant for the RAG prompt
parts = [p for p in parts if not re.match(r"(?:CHAPTER|SECTION)\s", p)]

# sanity checks
n_art = sum(p.startswith("Article") for p in parts)
n_annex = sum(p.startswith("ANNEX") for p in parts)
print(n_art, "articles,", n_annex, "annexes")      # expected: 113 and 13

# shared clean text for RAG prompt and no RAG prompt
clean_text = "\n\n".join(parts)
open("data/ai_act_clean.txt", "w", encoding="utf-8").write(clean_text)

articles = {}
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
    articles[f"{kind}{num}"] = f"{header}\n{body}"
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
json.dump(articles, open("data/articles.json", "w"), ensure_ascii=False, indent=1)
print(len(chunks), "chunks")

# compute embeddings for all chunks once and save them
import numpy as np, hashlib
from sentence_transformers import SentenceTransformer

EMB_MODEL = "intfloat/multilingual-e5-base"
model = SentenceTransformer(EMB_MODEL)

emb = model.encode(
    [f"passage: {c['text']}" for c in chunks],   # e5 needs the "passage: " prefix
    normalize_embeddings=True,
    show_progress_bar=True,
)
assert emb.shape[0] == len(chunks)
np.save("data/emb.npy", emb)

# fingerprint so index.py can detect stale embeddings (chunks changed, emb not rebuilt)
meta = {
    "model": EMB_MODEL,
    "n_chunks": len(chunks),
    "chunks_sha": hashlib.sha256(
        json.dumps(chunks, ensure_ascii=False).encode()
    ).hexdigest(),
}
json.dump(meta, open("data/emb_meta.json", "w"), indent=1)
print("embeddings shape:", emb.shape)