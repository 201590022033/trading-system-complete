# Alternative Broker/API Research

Research date: 2026-09-04. Capabilities are useful only where the required
instrument is available to the particular South African account.

| Provider | Confirmed official interface | Paper/sandbox | JSE/SA fit | Important limitation | Assessment |
|---|---|---|---|---|---|
| IG South Africa | REST trading plus Lightstreamer prices/account/trade events | Demo account/API | South African regulated CFD provider; local-market instrument list must be queried per account | OTC API; DMA unavailable; equity streaming restrictions documented | Best immediately testable API for CFDs/FX/indices, not proven replacement for JSE cash equities or SSFs |
| Saxo OpenAPI | REST, websocket streaming, portfolio, quotes and orders; FIX offered separately | Public simulation environment | Saxo officially identifies a Standard Bank/Shyft partnership | Retail Shyft entitlement to Saxo OpenAPI is UNKNOWN; exact JSE derivatives unknown | Most relevant technology path to ask Standard Bank about |
| Interactive Brokers | Web/TWS APIs, websocket market data, orders and paper accounts | Paper account | South African residents/account eligibility and product permissions are account-dependent | Direct JSE venue/instrument coverage was not confirmed in official product search | Strong global API; unsuitable until exact JSE symbols are confirmed |
| EasyEquities | No public official retail trading API found | UNKNOWN | Strong local retail equity relevance | API, streaming, order and sandbox support UNKNOWN | Manual platform only unless provider confirms an interface |

Approximate costs are `UNKNOWN` except where a provider's current account and
instrument schedule is consulted; spreads, commission, subscriptions and
financing vary materially. Do not compare headline fees across cash equities and CFDs.

Official sources accessed:

- IG South Africa API: https://www.ig.com/za/trading-platforms/trading-apis
- IG REST/streaming/demo documentation: https://labs.ig.com/gettingstarted and https://labs.ig.com/streaming-api-guide.html
- Saxo OpenAPI and simulation: https://www.developer.saxo/ and https://www.developer.saxo/openapi/learn/environments
- Saxo partnership reference: https://www.home.saxo/institutional-and-partners/banks-wealth-and-brokerage-solutions
- IBKR API and paper environment: https://www.interactivebrokers.com/campus/ibkr-api-page/ and https://www.interactivebrokers.com/campus/glossary-terms/paper-trading-account/

No provider should be selected solely for its API. First obtain a symbol-level
coverage and cost sample for the target JSE equities, index/equity derivatives,
CFDs, USD/ZAR and commodity exposures.
