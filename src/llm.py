import requests

def generate(prompt: str, model: str) -> str:
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_ctx": 8192},
        },
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["response"]