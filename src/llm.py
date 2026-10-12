import requests, json, time, threading

def generate_stream(prompt, model, num_ctx=8192, timeout=3600, seed=42, num_predict=1500):
    t0 = time.time()
    stop = threading.Event()

    def ticker():
        while not stop.wait(15):
            print(f"  [{time.time() - t0:.0f}s elapsed]", flush=True)
    threading.Thread(target=ticker, daemon=True).start()

    out, stats = [], {}
    try:
        with requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": True,
                  "options": {"temperature": 0, "seed": seed,"num_ctx": num_ctx, "num_predict": num_predict}},
            stream=True, timeout=timeout,
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                d = json.loads(line)
                if d.get("response"):
                    if not out:
                        print(f"\nfirst token after {time.time() - t0:.0f}s\n", flush=True)
                    print(d["response"], end="", flush=True)
                    out.append(d["response"])
                if d.get("done"):
                    stats = d
    finally:
        stop.set()

    print(f"\n\nprompt tokens: {stats.get('prompt_eval_count')} | num_ctx: {num_ctx}")
    print(f"load: {stats.get('load_duration', 0) / 1e9:.1f}s | "
          f"prompt processing: {stats.get('prompt_eval_duration', 0) / 1e9:.1f}s | "
          f"generation: {stats.get('eval_duration', 0) / 1e9:.1f}s "
          f"({stats.get('eval_count')} tokens)")
    return "".join(out)