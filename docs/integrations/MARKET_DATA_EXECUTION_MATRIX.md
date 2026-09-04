# Market Data and Execution Capability Matrix

Accessed 2026-09-04. `UNKNOWN` means no confirming official retail documentation
was found; it does not mean unsupported.

| Capability | Current research source | ViewPoint | Shyft Trader | Future alternative |
|---|---|---|---|---|
| Historical OHLC | Frozen HR2 Yahoo-derived files | Chart/history claimed; export rights UNKNOWN | UNKNOWN | Licensed data API |
| Live quote | No | Real-time claimed; subscription terms UNKNOWN | By subscription | Licensed data API |
| Bid/ask | No | UNKNOWN | UNKNOWN | Licensed streaming API |
| Market depth | No | Level entitlement UNKNOWN | UNKNOWN | Licensed depth feed |
| JSE equities | Six frozen equities | OST relationship confirmed | Migration implies JSE; exact list UNKNOWN | JSE-capable broker |
| JSE futures | No | UNKNOWN | UNKNOWN | JSE derivatives broker |
| CFDs | No | UNKNOWN | 5,600 advertised | Regulated broker API |
| FX | Frozen USD/ZAR proxy | UNKNOWN | 160+ FX crosses advertised | Regulated FX API |
| Order entry | No | Platform order handling claimed | Platform orders confirmed | Official broker API |
| Order status | No | UNKNOWN | Confirmations/platform notifications | Official broker API |
| Portfolio/positions | No | Portfolio guide linked | Account/portfolio terms confirmed | Official broker API |
| Streaming API | No | UNKNOWN | UNKNOWN | Licensed vendor |
| REST API | No | UNKNOWN | UNKNOWN | Official broker/data API |
| Websocket | No | UNKNOWN | UNKNOWN | Official broker/data API |
| Official automation allowed | No | UNKNOWN | UNKNOWN; algo order type is not API permission | Contract-dependent |
| Demo/sandbox | Offline research only | UNKNOWN | UNKNOWN | Broker sandbox |
| Underlying technology | Local files/code | IRESS confirmed | Saxo partnership confirmed | Provider-specific |

Sources: Standard Bank ViewPoint page,
https://onlinesharetrading.standardbank.co.za/pages/OST/ViewPoint.html; Shyft
Trader offering, https://www.shyft.co.za/en-ZA/what-shyft-trader-offers;
migration notice, https://www.shyft.co.za/en-ZA/shyft-trading-platforms-migration;
terms, https://www.shyft.co.za/en-ZA/terms-and-conditions.

## Fastest safe execution-path ranking

| Option | Estimated human time | Data latency | Reliability / development | Compliance risk | JSE/derivatives/live/automation/account |
|---|---|---|---|---|---|
| 1. Manual Shyft entry | 30–120 seconds (workflow estimate) | Subscription-dependent | High / low | Low when normal platform terms followed | JSE confirmed broadly; exact derivatives/live tier varies; no external automation; Shyft account |
| 2. Ticket + copy/paste | 20–90 seconds (estimate) | Same as source feed | Medium-high / low | Low; transcription still required | Coverage follows chosen data source and Shyft account |
| 3. Deep/pre-populated ticket | UNKNOWN | UNKNOWN | UNKNOWN / medium | UNKNOWN until officially supported | All capabilities and account requirements UNKNOWN |
| 4. Official Shyft API + confirmation | UNKNOWN, potentially seconds | UNKNOWN | UNKNOWN / high | Low only under written API/licence terms | Saxo technology exists; retail entitlement and symbol coverage UNKNOWN |
| 5. ViewPoint/IRESS integration | UNKNOWN | Real-time display confirmed | Platform mature / high | Retail interface/licensing UNKNOWN | IRESS ecosystem supports data/FIX; Standard Bank retail API entitlement UNKNOWN |
| 6. Alternative official API | Seconds after review (estimate) | Provider-dependent | Provider-dependent / high | Lower with documented API | IG: CFDs/FX API; Saxo/IBKR: broad APIs; exact JSE instruments must be proven |

Browser-click automation is excluded. The eventual ticket should contain
instrument, side, current price and timestamp, entry/order type, target, stop,
horizon, size, maximum risk, confidence/evidence, rationale, cost estimate,
stale-data warning and market status.
