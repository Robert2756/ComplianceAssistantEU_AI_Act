# LLM Prompt
from index import search
from llm import generate

import re, json
from bs4 import BeautifulSoup

MODEL = "llama3.1:8b"   # shown in `ollama list`

def label(c):
    if c.get("annex"):
        return f"Annex {c['annex']}" + (f", Art. {c['article']}" if c.get("article") else "")
    return f"Art. {c['article']}"

def build_prompt_RAG(question, k=5):
    hits = search(question, k)
    context = "\n\n".join(
        f"[{label(c)}, {c['title']}]\n{c['text']}" for c, _ in hits)
    return f"""Answer the question using ONLY the sources below.
Cite the article for every claim, e.g. (Art. 5).
If the sources do not contain the answer, say so.

SOURCES:
{context}

QUESTION: {question}
ANSWER:"""

def build_prompt_noRAG(question, k=5):
    html = open("data/ai_act.html", encoding="utf-8").read()
    text = BeautifulSoup(html, "lxml").get_text("\n")
    text = re.sub(r"\n\s*\n+", "\n", text)
    return f"""Answer the question using ONLY the sources below.
Cite the article for every claim, e.g. (Art. 5).
If the sources do not contain the answer, say so.

SOURCES:
{text}

QUESTION: {question}
ANSWER:"""

print(build_prompt_RAG("Which AI systems are prohibited?", k=5))

# answer = generate(build_prompt_noRAG("Which AI systems are prohibited?", k=5), MODEL)
# print("Answer: ", answer)