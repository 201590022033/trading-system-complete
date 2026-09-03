# Data Sources and Evidence Hierarchy

The system should prefer direct/authoritative evidence and treat community sentiment as discovery/context.

## Tier 1 — authoritative/direct
- JSE official product/reference pages and available market data.
- JSE SENS announcements; current repo uses the public Moneyweb SENS listing as a practical ingestion route.
- Issuer results, trading statements, dividend/corporate-action notices and company filings.
- SARB: repo rate/MPC statements, inflation expectations, monetary/financial statistics.
- Stats SA: CPI/PPI, GDP, employment and relevant sector releases.
- National Treasury and official government releases where market relevant.

## Tier 2 — market/macro price data
- Existing Yahoo Finance integration for research price history.
- Existing Finnhub integration where suitable/licensed.
- USD/ZAR and relevant FX crosses.
- Brent crude, spot/futures gold, platinum/PGM references, major commodity proxies.
- US dollar index/proxy, US Treasury yields/real yields where accessible, VIX/risk-aversion proxy.
- JSE Top 40 / broad index and sector/index relative strength.
- JSE equity derivatives data where licensed/available: SSFs, index futures, CFDs, historical tick/order-book datasets.

## Tier 3 — reputable South African financial reporting/research
Already mentioned in project discussions and to be evaluated, not blindly trusted:
- Moneyweb market coverage and SENS tools.
- Business Day / BusinessLIVE markets reporting.
- IG South Africa market data, analysis, client sentiment, technical patterns and economic calendar where accessible under permitted terms.
- Standard Bank / Standard Bank CIB public market commentary where accessible.
- Reuters Markets / Reuters South Africa for global and local event context.
- BlackStone Futures public market commentary/resources if currently active and legally accessible; verify exact endpoints before implementation.

## Tier 4 — trader/community lead generation
- TradingView South African Stocks Ideas and ticker/J200 ideas. Examples of active/recent SA-focused authors should be discovered dynamically rather than permanently privileged. Historical names seen in the public feed include Timonrosso, Herenya, ElliottWaveSpot, Loyiso_BlaqueSoros_Mpeta, SteynTrade, The_Chartroom and others.
- MyBroadband forum JSE/investing/stock-watch threads. Treat as low-frequency community context; do not assume specialist derivatives coverage.
- Reddit `r/PersonalFinanceZA` for local investing discussion; use as context, not a short-term signal authority.
- `r/JSE` only if it exists and is demonstrably active at implementation time; verify rather than assuming.
- X/Twitter public posts from JSE, Moneyweb, Business Day/BusinessLIVE, Reuters markets journalists/feeds, brokers, analysts and selected SA traders. Prefer official API or permitted public-data providers.
- Public Telegram channels from legitimate SA brokers/trading educators only where public access and terms permit. Verify BlackStone Futures/public channels before coding.
- Public Discord communities only where accessible under their API/terms and content is genuinely relevant.

## Facebook/private groups
Do **not** implement username/password automation to scrape private Facebook groups. If a group/page is public and Meta provides an approved API route for the required content, it may be evaluated. Otherwise exclude it.

## Source reliability fields
Each source should support:
- `source_id`, `source_name`, `source_class`, `authority_tier`;
- publication and ingestion timestamps;
- asset/sector/instrument mapping;
- direction/claim/sentiment and confidence;
- horizon label (intraday/1d/3d/5d/etc.);
- outcome after horizon;
- sample count, hit rate, information coefficient or aligned return where meaningful;
- false-positive rate;
- average lead time and signal decay;
- reliability by bull/bear/range/high-volatility regime;
- reliability by sector/ticker;
- recency-weighted score with conservative shrinkage for small samples.

## Access rule
Before writing any scraper, verify whether an official feed/API/RSS or simpler existing collector already solves the need. Respect robots, rate limits, copyright and platform terms.

## M8 verification record — 2026-09-03

`source_catalog.py` is the executable policy record. Only the two already
implemented public Moneyweb routes are enabled by default; all other sources
remain independently disabled until their stated requirement is satisfied.

| Source | Status | Permitted implementation boundary |
| --- | --- | --- |
| JSE official data/SENS | Licence required | JSE documents live/non-live and SENS products plus data agreements; use a licensed feed/distributor, not page scraping. |
| Moneyweb RSS | Existing/live | Public RSS collector retained, five-minute catalogue poll gate. |
| Moneyweb-hosted SENS | Existing/live | Existing public listing parser retained as the practical SENS route. |
| Business Day/BusinessLIVE | Permission not verified | Manual/link evidence only until a licensed feed or written permission exists. |
| Reuters South Africa | Licence required | Manual/link evidence or a licensed API/provider only. |
| IG South Africa | Public pages, no stable ingestion API verified | Manual/link evidence only; do not automate client/platform data. |
| Standard Bank/CIB | No stable public feed verified | Manual/link evidence only; OST remains separately read-only. |
| TradingView ideas | Excluded | Current terms prohibit non-display algorithmic use of TradingView content/data. |
| MyBroadband forums | Permission not verified | Public pages are active, but no automated collector without permission/terms clearance. |
| Reddit r/PersonalFinanceZA | Active but approved API required | OAuth API only after an approved use case; unauthenticated JSON fallback disabled. |
| Reddit r/JSE | Activity not verified | Disabled even if API access is later approved. |
| X | Official API required | Disabled until approved/paid API access and retention terms are configured. |
| BlackStone Futures Telegram | Public channel verified | Manual/link evidence only; no generic page scraper. |
| Other Telegram | Not configured | Official API and channel permission required. |
| Discord | Server permission/API required | Approved bot/API only; message-content permissions and platform policy apply. |

Verification references:
- JSE market-data policies: https://www.jse.co.za/market-data/data-agreements-policies
- JSE market-data technical library: https://clientportal.jse.co.za/technical-library/market-data-documentation
- Moneyweb tools/SENS: https://www.moneyweb.co.za/tools-and-data/
- TradingView terms: https://www.tradingview.com/policies/
- Reddit Data API terms: https://redditinc.com/policies/data-api-terms
- IG South Africa research: https://www.ig.com/za/trading-research
- Discord API/rate limits: https://docs.discord.com/developers/reference
- Discord message-content restrictions: https://docs.discord.com/developers/events/gateway
- BlackStone public channel: https://t.me/s/BSF_Official
