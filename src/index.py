import json, numpy as np
import time
from sentence_transformers import SentenceTransformer

MODEL = "intfloat/multilingual-e5-base"   # alternativ ein kleineres Modell zum Testen
model = SentenceTransformer(MODEL)
chunks = json.load(open("data/chunks.json"))
articles = json.load(open("data/articles.json"))

# create embedding as vector of numbers for each chunk of text
emb = model.encode([f"passage: {c['text']}" for c in chunks],
                   normalize_embeddings=True, show_progress_bar=True)
np.save("data/emb.npy", emb) # embeddings shape: (126, 768)
print("embeddings shape:", emb.shape)

# rank chunks by the best score out of its article chunks
def build_context(question, budget_words=4000, max_articles=3, margin=0.04):
    hits = search(question, 20)      # sorted by score
    ranked, by_key, best = [], {}, {} # ranked -> list of article keys in order, by_key -> dict of article key to list of chunks, best -> dict of article key to best score
    for c, s in hits:
        key = c["id"].rsplit("-", 1)[0] # extract article key
        if key not in by_key:
            by_key[key] = []
            ranked.append(key)
            best[key] = s # first hit = best score for this article
        by_key[key].append(c)

    top = best[ranked[0]]
    blocks, used = [], 0
    for n, key in enumerate(ranked[:max_articles]):
        if n > 0 and best[key] < top - margin:
            break # too far behind the top article
        full = articles[key]
        w = len(full.split())
        if n > 0 or used + w <= budget_words: # never dropt the first article no matter its length otherwise context empty
            if w > budget_words:
                continue # article does not fit -> drop it, better dropping instead of incomplete
            blocks.append(full)
            used += w
    return "\n\n".join(blocks)

def search(query, k=5):
    # remove per_article since articles are incomplete
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