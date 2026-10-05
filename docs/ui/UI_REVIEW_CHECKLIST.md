# Dashboard review checklist — current application

Reviewed 5 October 2026. Start using [Quick Start](../../QUICKSTART.md); see [current dashboard behavior](DECISION_UI.md). The old simulated-ticker checklist is [archived](../history/UI_REVIEW_CHECKLIST_PRE_2026-10-05.md).

Review the six dashboard sections against [current state](../CURRENT_STATE.md):

- Portfolio & demo: distinguish simulated capital from connected cash, Demo from Live, original currency from dated ZAR conversion, and self-reported journal entries from verified broker fills.
- Trading Strategies: cards reflect backend capability/limitation state; Swing default is 1.0.1; Intraday CFD and Long-Term Investment have truthful development states. Selecting a card changes no strategy weights or execution mode.
- Canonical Top-5: committed opportunities expose source freshness and policy/risk blocks. Read-only refresh does not start another pipeline or reconnect the old multi-agent score.
- Technical Intelligence: show real-data provenance, blocked dates and explicit estimated display flags. No estimated OHLC or invented volume enters replay. A chart is not evidence of licensed historical intraday access.
- Market AI / News: identify unverified brief claims, article references, actual receipt times, publisher independence, failures and pending states. A single publisher earns no corroboration boost/flag.
- System: distinguish web/database health and worker completion from data availability or strategy performance.

Check empty/error/stale states as well as success. Read-only profile discovery must work without credentials. Protected worksheet/journal/brief imports require existing operator authentication; do not expose tokens in links or screenshots. Print a worksheet only as a local review artifact; it must not submit an order.

Current acceptance includes zero closed first cloud holdout trades and zero first-news historical flags. The proposed local six-family backtest/radar workflow is not a completed dashboard feature. No UI control can override M15 or enable Live execution.

| Screen/element | Observed issue | Desired change | Priority | Evidence/data dependency |
| --- | --- | --- | --- | --- |
| | | | | |
