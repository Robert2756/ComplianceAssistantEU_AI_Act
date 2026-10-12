import json, os, sys, time
from datetime import datetime

from index import build_context
from llm import generate_stream

MODEL = "llama3.1:8b"
QUESTIONS = "eval/questions.jsonl"
RESULTS = "eval/results.jsonl"
ARMS = ["none", "rag", "full"] # cheap arms first
SEED = 42
FULL_TEXT = open("data/ai_act_clean.txt", encoding="utf-8").read()


def pick_num_ctx(prompt, answer_room=3000):
    est = len(prompt) // 4 + answer_room
    return min(131072, ((est + 2047) // 2048) * 2048)


# identical wording for rag/full, so the only difference is the sources
TEMPLATE_SRC = """Answer the question using ONLY the sources below.
Cite the article or annex for every claim.
If the sources do not contain the answer, say so.

SOURCES:
{sources}

QUESTION: {question}
ANSWER:"""

TEMPLATE_NONE = """Answer the question about the EU AI Act.
Cite the article or annex for every claim.
If you do not know the answer, say so.

QUESTION: {question}
ANSWER:"""


def make_prompt(arm, question):
    """Returns (prompt, retrieval_info, retrieval_seconds)."""
    if arm == "none":
        return TEMPLATE_NONE.format(question=question), {}, 0.0
    if arm == "full":
        return TEMPLATE_SRC.format(sources=FULL_TEXT, question=question), {}, 0.0
    t0 = time.perf_counter() # arm == "rag" -> embedding retrieval costs time
    ctx = build_context(question)
    r = time.perf_counter() - t0
    if isinstance(ctx, str): # old build_context returning a string
        ctx = {"text": ctx}
    info = {"retrieved": ctx.get("keys"), "context_words": ctx.get("words"),
            "top_ranking": (ctx.get("ranking") or [])[:5]}
    return TEMPLATE_SRC.format(sources=ctx["text"], question=question), info, r


def load_done():
    """Set of (question_id, arm) already stored. Tolerates a half-written last line."""
    done = set()
    if not os.path.exists(RESULTS):
        return done
    with open(RESULTS, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                done.add((r["id"], r["arm"]))
            except (json.JSONDecodeError, KeyError):
                pass
    with open(RESULTS, "rb+") as f: # make sure the next append starts on a new line
        f.seek(0, 2)
        if f.tell() > 0:
            f.seek(-1, 2)
            if f.read(1) != b"\n":
                f.write(b"\n")
    return done


def save(rec):
    with open(RESULTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno()) # survives Ctrl+C / crash right after


def main():
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    questions = [json.loads(l) for l in open(QUESTIONS, encoding="utf-8") if l.strip()]
    done = load_done()
    todo = [(q, a) for q in questions for a in ARMS if (q["id"], a) not in done]
    print(f"{len(done)} runs already stored, {len(todo)} to do")

    for i, (q, arm) in enumerate(todo, 1):
        print(f"\n===== [{i}/{len(todo)}] {q['id']} | {arm} | {q['question']}")
        prompt, info, retrieval_s = make_prompt(arm, q["question"])
        num_ctx = pick_num_ctx(prompt)

        t0 = time.perf_counter()
        answer, st = generate_stream(prompt, MODEL, num_ctx=num_ctx, timeout=3600, seed=SEED)
        llm_s = time.perf_counter() - t0

        ns = lambda k: round(st.get(k, 0) / 1e9, 3)
        save({
            "id": q["id"], "arm": arm, "model": MODEL, "seed": SEED,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "question": q["question"], "prompt": (
                                            prompt.split("SOURCES:", 1)[0] + "SOURCES:"
                                            if arm == "full"
                                            else prompt
                                        ), "answer": answer,
            "num_ctx": num_ctx, "est_prompt_tokens": len(prompt) // 4,
            "prompt_tokens": st.get("prompt_eval_count"),
            "output_tokens": st.get("eval_count"),
            "ctx_full": (st.get("prompt_eval_count") or 0) >= num_ctx - 256,  # truncation suspect
            "retrieval_s": round(retrieval_s, 3),
            "llm_wall_s": round(llm_s, 3),
            "total_s": round(retrieval_s + llm_s, 3),
            "load_s": ns("load_duration"),
            "prompt_eval_s": ns("prompt_eval_duration"),
            "generation_s": ns("eval_duration"),
            **info,
        })
        print(f"saved: total {retrieval_s + llm_s:.1f}s")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted. Finished runs are saved; run again to continue.")
        sys.exit(0)