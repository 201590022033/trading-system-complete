"""Manual local Ollama verification for OI3.

This script is intentionally excluded from the safe test suite. It requires a
running local Ollama service and a configured model. It does not print or
persist credentials.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sentiment_analyzer import _LLM_PROMPT  # noqa: E402
from sentiment_providers import SentimentProviders  # noqa: E402


def main():
    providers = SentimentProviders()
    print("Provider states before scan:")
    for p in providers.statuses():
        print(f"  {p['provider']}: {p['state']} (model={p['model']})")

    eligible = providers.begin_scan(budget=3)
    print(f"\nEligible for analysis: {eligible}")

    if not eligible:
        print("\nLocal Ollama is not ready. Check that the service is running and")
        print("the configured model is installed. Set OLLAMA_LOCAL_MODEL and")
        print("OLLAMA_LOCAL_OPTIONS in .env if needed.")
        return 1

    headline = "Sasol profits rise on stronger oil price and rand weakness"
    source = "Moneyweb"
    text = "Sasol reported stronger earnings as Brent crude climbed and the rand weakened."
    prompt = _LLM_PROMPT.format(headline=headline, source=source, text=text[:800])

    result = providers.analyze(prompt)
    print("\nAnalysis result:")
    print(json.dumps(result, indent=2, default=str))

    if not result:
        print("\nAnalysis failed. Verify Ollama can generate structured JSON.")
        return 1

    required = {"summary", "sentiment", "score", "assets", "_provider", "_model"}
    missing = required - set(result.keys())
    if missing:
        print(f"\nMissing expected fields: {missing}")
        return 1

    print("\nVerification passed: local Ollama returned structured, attributed output.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
