# Monday brief and research flags

## Current context — 5 October 2026

The original module/design contract below is retained. Its delivered/planned labels describe that scope/checkpoint; use the current snapshot for later integration and deployment state.

Manual Monday briefs and local Ollama research cases now extend the existing source catalog. Distinct-publisher corroboration gates the +0.05 research attention boost; it never changes trade weights. Current single-publisher cases have zero flags, and historic SENS/event retrieval remains planned. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

Actual acceptance: 28 September/5 October briefs imported; CPU scan took about 6m38s; EARNINGS and INFLATION cases both referenced Moneyweb. They remain SOURCE_REVIEW_REQUIRED, with zero flags, zero boosts and zero historical samples. The latest fix admits only previously FLAGGED matching cases into history; uncorroborated cases cannot accumulate retrospective evidence.

---

Open Market AI / News → Sources → Monday market brief & research flags. Existing
source controls also pause the local weekly scan. Import editions through the form
after unlocking Portfolio controls, or use the private local importer:

`python scripts/weekly_news_research.py --brief-file PATH --edition-date YYYY-MM-DD`

Private local configuration reuses `SWING_RESEARCH_URL` and
`SWING_DATA_UPLOAD_TOKEN`; do not paste them into chat. Set
`WEEKLY_NEWS_RESEARCH_ENABLED=1` locally to include scans in the existing daily
collector, after a successful OHLC upload. The scanner calls local Ollama only,
using existing `OLLAMA_HOST` / `OLLAMA_LOCAL_MODEL`; an optional
`WEEKLY_NEWS_OLLAMA_MODEL` selects an installed model for this scan alone.
It requires the PC and model
to be available. One automatic attempt per UTC day; saved output retries cost no model call.
After repairing a local model failure, `--retry-failed` allows at most four additional manual
attempts that day. Failures appear in the dashboard. Local research defaults to CPU
inference to avoid the observed incompatible CUDA driver and has a bounded
480-second request timeout; existing news scans retain their45-second default.
An explicit `python scripts/weekly_news_research.py` performs the same bounded scan.

Local briefs, attempt receipts, outboxes, provenance and category cases live in
ignored `runtime/weekly-news-research/`. Raw daily prices remain in the existing
local archive. Railway receives derived relationships and descriptive observations.
The existing web source feed remains the source of current article inputs.

Research priority receives up to five percentage points when linked articles
come from distinct publishers and pass conservative duplicate checks. This does
not change a trade's score. Semantic relationships are hypotheses; source
independence and market correlations remain unproven. Historical flags start a
local archive check, but meaningful statistics require a dated event archive.
Initial waiting states are expected. Capitec and instruments outside the current
cash-share research catalogue are not silently mapped to another stock.

The imported brief has no verified publication timestamp/source links, so its
claims remain unverified regardless of labels in its prose. Historical returns
are calculated after actual local receipt, never backdated to the nominal edition
or article date. The current screen is not the proposed six-family strategy
backtest, a volume test, or a numerical correlation estimator.

Future ChatGPT task editions need manual import. Automatic task-to-dashboard
delivery, historical SENS/article collection, sector-adjusted return controls and
the six-hypothesis workflow remain follow-up milestones.
