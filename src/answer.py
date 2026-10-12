from index import build_context
from llm import generate_stream

import re, json
from bs4 import BeautifulSoup

MODEL = "llama3.1:8b" # shown in `ollama list`

def pick_num_ctx(prompt, answer_room=3000):
    est = len(prompt) // 4 + answer_room # rough token estimate
    return min(131072, ((est + 2047) // 2048) * 2048) # round up to a multiple of 2048

def label(c):
    if c.get("annex"):
        return f"Annex {c['annex']}" + (f", Art. {c['article']}" if c.get("article") else "")
    return f"Art. {c['article']}"

def build_prompt_RAG(question):
    context = build_context(question)
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

# print("Prompt: ", build_prompt_RAG("Which AI systems are prohibited?", k=5), "\n\n")

# with RAG
print("RAG")
text_RAG = build_prompt_RAG("Which AI systems are prohibited?", k=5)
answer = generate_stream(text_RAG, MODEL, num_ctx=pick_num_ctx(text_RAG), timeout=3600)
# print("Answer RAG: ", answer, "\n\n")

# no RAG
print("NO RAG")
text_NORAG = build_prompt_noRAG("Which AI systems are prohibited?")
print(len(text_NORAG), "characters, about", len(text_NORAG) // 4, "tokens") # 339892 characters, about 84973 tokens
answer = generate_stream(text_NORAG, MODEL, num_ctx=pick_num_ctx(text_NORAG), timeout=3600) # increase context length of model to max -> whole cleaned ai act fits in
# print("Answer no RAG: ", answer, "\n\n")