import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
with open(sys.argv[2], "w", encoding="utf-8") as f:
    for q in dict.fromkeys(r["id"] for r in rows):
        rs = [r for r in rows if r["id"] == q]
        f.write("=" * 80 + f"\n{q}: {rs[0]['question']}\n" + "=" * 80 + "\n\n")
        for r in rs:
            f.write(f"--- {r['arm'].upper()} | {r['total_s']:.0f}s | prompt {r['prompt_tokens']} tok | "
                    f"out {r['output_tokens']} tok | ctx {r['num_ctx']}"
                    + (f" | retrieved: {', '.join(r['retrieved'])}" if r.get("retrieved") else "") + " ---\n"
                    + r["answer"].strip() + "\n\n")