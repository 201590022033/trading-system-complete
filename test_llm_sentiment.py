"""Test the sentiment analyzer's LLM path with the cloud key on real headlines."""
from sentiment_analyzer import MacroSentimentScanner

scanner = MacroSentimentScanner()
print("LLM available:", scanner.use_llm)

if not scanner.use_llm:
    print("LLM not detected — check .env")
    raise SystemExit(1)

report = scanner.scan(moneyweb_limit=4, sens_limit=3)
out = report.to_dict()
print("llm_used on report:", out["llm_used"])
print()

for item in out["items"]:
    if item["llm_used"]:
        tags = ", ".join(f"{a['name']}({a['direction']:+d},{a['strength']:.2f})" for a in item["assets"])
        print(f"[{item['sentiment']} {item['score']}] {item['headline'][:70]}")
        print(f"    AI summary: {item['summary'][:120]}")
        if tags:
            print(f"    assets: {tags}")
        print()
