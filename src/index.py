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
def rank_articles(question):
    q = model.encode([f"query: {question}"], normalize_embeddings=True)[0]
    scores = emb @ q
    best = {}
    for i in np.argsort(-scores): # best chunk first
        key = chunks[i]["id"].rsplit("-", 1)[0]
        best.setdefault(key, float(scores[i])) # first hit = best score for that article
    return list(best.items()) # [(article_key, score), ...] sorted desc


def build_context(question, budget_words=4000, max_articles=3, margin=0.04):
    ranked = rank_articles(question)
    top = ranked[0][1]
    blocks, selected, used = [], [], 0
    for n, (key, score) in enumerate(ranked[:max_articles]):
        if n > 0 and score < top - margin:
            break
        full = articles[key]
        w = len(full.split())
        if n > 0 and used + w > budget_words:
            continue
        blocks.append(full); selected.append(key); used += w
    return {"text": "\n\n".join(blocks), "keys": selected,
            "ranking": ranked, "words": used}