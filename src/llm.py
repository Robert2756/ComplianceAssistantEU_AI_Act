import requests

def generate(prompt: str, model: str, num_ctx: int = 8192, timeout: int = 300) -> str:
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_ctx": num_ctx}, # context number of tokens
        },
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()["response"]