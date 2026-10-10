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

def search(query, k=5, per_article=2):
    # take only the top 2 chunks per article so that the following LLM prompt receives chunks from other articles
    # remove since articles are incomplete
    q = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
    scores = emb @ q
    out, seen = [], {}
    for i in np.argsort(-scores):
        c = chunks[i]
        key = c["id"].rsplit("-", 1)[0]
        # if seen.get(key, 0) >= per_article:
        #     continue
        # seen[key] = seen.get(key, 0) + 1
        out.append((c, float(scores[i])))
        if len(out) == k:
            break
    return out