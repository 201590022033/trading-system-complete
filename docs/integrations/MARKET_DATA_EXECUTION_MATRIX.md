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

Sources: Standard Bank ViewPoint page,
https://onlinesharetrading.standardbank.co.za/pages/OST/ViewPoint.html; Shyft
Trader offering, https://www.shyft.co.za/en-ZA/what-shyft-trader-offers;
migration notice, https://www.shyft.co.za/en-ZA/shyft-trading-platforms-migration;
terms, https://www.shyft.co.za/en-ZA/terms-and-conditions.

## Fastest safe execution-path ranking

| Rank | Path | Latency | Reliability/complexity | Compliance and error risk |
|---:|---|---|---|---|
| 1 | Manual Shyft entry from validated system ticket | Medium | High / low | Supported platform path; transcription risk |
| 2 | Official deep link/pre-populated ticket | Low | UNKNOWN / medium | Best assisted path if officially supported |
| 3 | Official API + human confirmation | Lowest | UNKNOWN / high | Preferred eventual path if contracted and sandboxed |
| 4 | Alternative broker official API | Low | Provider-dependent / high | Consider if Shyft API unavailable; coverage must be verified |

Browser-click automation is excluded. The eventual ticket should contain
instrument, side, current price and timestamp, entry/order type, target, stop,
horizon, size, maximum risk, confidence/evidence, rationale, cost estimate,
stale-data warning and market status.
