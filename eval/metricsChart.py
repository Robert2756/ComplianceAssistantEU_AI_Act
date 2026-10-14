import json
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

ARMS = [("none", "No RAG", "#9AA0A6"),
        ("rag", "RAG", "#0072B2"),
        ("full", "Full context", "#CC79A7")]

records = {}
with open("./eval/results.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            r = json.loads(line)
            records[(r["arm"], r["id"])] = r

def mean_of(arm, key):
    vals = [r[key] for (a, _), r in records.items() if a == arm]
    return np.mean(vals)

labels = [label for _, label, _ in ARMS]
colors = [c for _, _, c in ARMS]
lat = [mean_of(arm, "total_s") for arm, _, _ in ARMS]
tok = [mean_of(arm, "prompt_tokens") for arm, _, _ in ARMS]

fig, axes = plt.subplots(1, 2, figsize=(10, 4))

for ax, vals, title, unit in [
    (axes[0], lat, "Latency per question", " s"),
    (axes[1], tok, "Prompt tokens per question", ""),
]:
    bars = ax.bar(labels, vals, color=colors, width=0.55)
    ax.bar_label(bars, labels=[f"{v:,.0f}{unit}" for v in vals], padding=3)
    ax.set_yscale("log")
    ax.set_ylim(10, max(vals) * 4)
    ax.set_title(title, loc="left")
    ax.spines[["top", "right"]].set_visible(False)

axes[0].set_ylabel("mean, log scale")

plt.tight_layout()
plt.show()