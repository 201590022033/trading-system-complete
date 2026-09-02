"""Poll macro scan and confirm AI mode is active."""
import json
import time
import urllib.request

for i in range(40):
    time.sleep(5)
    d = json.loads(urllib.request.urlopen("http://127.0.0.1:5000/api/macro-sentiment", timeout=30).read().decode())
    if d["status"] != "scanning" and d["report"]:
        print("status:", d["status"], "|", d["message"])
        print("AI mode:", d["report"]["llm_used"])
        ai_items = [x for x in d["report"]["items"] if x["llm_used"]]
        print(f"AI-analyzed headlines: {len(ai_items)} of {len(d['report']['items'])}")
        for x in ai_items[:3]:
            tags = ",".join(a["name"] for a in x["assets"])
            print(f"  [{x['sentiment']}] {x['headline'][:65]} -> {tags}")
        break
