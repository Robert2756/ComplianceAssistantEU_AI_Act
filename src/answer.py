import time
from index import build_context
from llm import generate_stream

import re, json
from bs4 import BeautifulSoup

MODEL = "llama3.1:8b"   # shown in `ollama list`

def label(c):
    if c.get("annex"):
        return f"Annex {c['annex']}" + (f", Art. {c['article']}" if c.get("article") else "")
    return f"Art. {c['article']}"

def build_prompt_RAG(question, k=5):
    hits = build_context(question, k)
    context = "\n\n".join(
        f"[{label(c)}, {c['title']}]\n{c['text']}" for c, _ in hits)
    return f"""Answer the question using ONLY the sources below.
Cite the article for every claim, e.g. (Art. 5).
If the sources do not contain the answer, say so.

SOURCES:
{context}

QUESTION: {question}
ANSWER:"""

def build_prompt_noRAG(question):
    text = open("data/ai_act_clean.txt", encoding="utf-8").read()

    return f"""Answer the question using ONLY the sources below.
Cite the article for every claim, e.g. (Art. 5).
If the sources do not contain the answer, say so.

SOURCES:
{text}

QUESTION: {question}
ANSWER:"""

print("Prompt: ", build_prompt_RAG("Which AI systems are prohibited?", k=5), "\n\n")

# with RAG
print("RAG")
answer = generate_stream(build_prompt_RAG("Which AI systems are prohibited?", k=5), MODEL)
print("Answer RAG: ", answer, "\n\n")

# no RAG
print("NO RAG")
text = build_prompt_noRAG("Which AI systems are prohibited?")
print(len(text), "characters, about", len(text) // 4, "tokens") # 339892 characters, about 84973 tokens
answer = generate_stream(text, MODEL, num_ctx=110000, timeout=3600) # increase context length of model to max -> whole cleaned ai act fits in
print("Answer no RAG: ", answer, "\n\n")