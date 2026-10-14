import numpy as np
import matplotlib.pyplot as plt

pipelines = ["No RAG", "RAG", "Full context"]
correct = [0, 7, 8]
partly  = [1, 1, 2]
wrong   = [9, 2, 0]

x = np.arange(len(pipelines))
w = 0.25

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(x - w, correct, w, label="correct", color="#009E73")
ax.bar(x,     partly,  w, label="partly",  color="#E69F00")
ax.bar(x + w, wrong,   w, label="wrong",   color="#D55E00")

ax.set_xticks(x)
ax.set_xticklabels(pipelines)
ax.set_ylabel("Questions (n = 10)")
ax.set_ylim(0, 10)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False)

plt.tight_layout()
plt.show()