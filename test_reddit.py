"""Debug Reddit fetcher directly."""
from jse_adapter import RedditFetcher

f = RedditFetcher()
print("praw active:", f._praw is not None)

items = f.fetch_recent(limit=10)
print("reddit items:", len(items))
for i in items:
    print(f"  [{i.sentiment_label.value}] {i.headline[:80]} ({i.source})")
