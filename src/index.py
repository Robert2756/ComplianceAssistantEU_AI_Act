import json, numpy as np
import time
from sentence_transformers import SentenceTransformer

MODEL = "intfloat/multilingual-e5-base"   # alternativ ein kleineres Modell zum Testen
model = SentenceTransformer(MODEL)
chunks = json.load(open("data/chunks.json"))

# create embedding as vector of numbers for each chunk of text
emb = model.encode([f"passage: {c['text']}" for c in chunks],
                   normalize_embeddings=True, show_progress_bar=True)
np.save("data/emb.npy", emb) # embeddings shape: (126, 768)
print("embeddings shape:", emb.shape)

def label(c):
    base = f"Annex {c['annex']}" if c.get("annex") else f"Art. {c['article']}"
    return f"{base} (part {c['part']+1})"

def search(query, k=5, per_article=2):
    q = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
    scores = emb @ q
    out, seen = [], {}
    for i in np.argsort(-scores):
        c = chunks[i]
        key = c["id"].rsplit("-", 1)[0]
        if seen.get(key, 0) >= per_article:
            continue
        seen[key] = seen.get(key, 0) + 1
        out.append((c, float(scores[i])))
        if len(out) == k:
            break
    return out

# def search(query, k=5):
#     q = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
#     scores = emb @ q
#     top = np.argsort(-scores)[:k]
#     return [(chunks[i], float(scores[i])) for i in top]

# if __name__ == "__main__":
#     for c, s in search("Which AI systems are prohibited?"):
#         if c['article'] == None:
#             print(f"{s:.3f}  Annex {c['annex']}  {c['title']}")
#         else:
#             print(f"{s:.3f}  Art. {c['article']}  {c['title']}")