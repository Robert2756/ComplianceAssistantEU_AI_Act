import json, hashlib
import numpy as np
from sentence_transformers import SentenceTransformer

chunks = json.load(open("data/chunks.json"))
articles = json.load(open("data/articles.json"))
emb = np.load("data/emb.npy")
meta = json.load(open("data/emb_meta.json"))

# fail loudly if ingest was changed but not re-run
sha = hashlib.sha256(json.dumps(chunks, ensure_ascii=False).encode()).hexdigest()
assert emb.shape[0] == len(chunks) and sha == meta["chunks_sha"], \
    "emb.npy is stale: re-run ingest.py"
model = SentenceTransformer(meta["model"])   # only the query side is encoded at runtime -> question

# rank chunks by the best score out of its article chunks
def build_context(question, budget_words=4000, max_articles=3, margin=0.04):
    hits = search(question) # sorted by score
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
        if n > 0 and used + w > budget_words: # never dropt the first article no matter its length otherwise context empty
            continue # article does not fit -> drop it, better dropping instead of incomplete
        blocks.append(full)
        used += w
    return "\n\n".join(blocks)

def search(query):
    # remove per_article since articles are incomplete
    q = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
    scores = emb @ q
    out = []
    for i in np.argsort(-scores):
        c = chunks[i]
        out.append((c, float(scores[i])))
    return out