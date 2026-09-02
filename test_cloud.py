"""List models available on the Ollama Cloud account and test generation."""
import os

from dotenv import load_dotenv

load_dotenv()

import ollama

key = os.environ.get("OLLAMA_API_KEY", "").strip()
client = ollama.Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {key}"},
    timeout=60,
)

print("--- available models ---")
try:
    models = client.list()
    for m in models.get("models", []):
        print(" ", m.get("name", m.get("model", "?")))
except Exception as e:
    print("list failed:", e)

print("\n--- test generation ---")
for model in ["gpt-oss:20b-cloud", "llama3.1", "llama3.1:8b", "llama3"]:
    try:
        r = client.generate(model=model, prompt="Reply with exactly: OK")
        print(f"  {model}: {r['response'].strip()[:40]}")
        break
    except Exception as e:
        print(f"  {model}: {type(e).__name__} {str(e)[:60]}")
