"""Standalone test for the macro sentiment scanner."""
import json

from sentiment_analyzer import MacroSentimentScanner

scanner = MacroSentimentScanner()
print(f"LLM available: {scanner.use_llm}")

report = scanner.scan(moneyweb_limit=8, sens_limit=5)
out = report.to_dict()

print(f"\nItems analyzed: {len(out['items'])}")
print("\n--- MACRO ASSETS ---")
for name, data in out["macro"].items():
    if data["mentions"]:
        print(f"  {name}: score={data['score']} ({data['mentions']} mentions)")

print("\n--- TICKERS MENTIONED ---")
for name, data in out["tickers"].items():
    print(f"  {name}: score={data['score']} ({data['mentions']} mentions)")
    for h in data["headlines"][:2]:
        print(f"      - {h}")

print("\n--- SAMPLE ITEMS ---")
for item in out["items"][:5]:
    tags = ", ".join(f"{a['name']}({a['direction']:+d})" for a in item["assets"])
    print(f"  [{item['sentiment']} {item['score']}] {item['headline'][:70]}")
    if tags:
        print(f"      assets: {tags}")
