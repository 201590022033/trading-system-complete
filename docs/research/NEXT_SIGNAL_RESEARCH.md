# Predictive Research Reset

## Why not retune HR9

HR10 rejected all 40 HR9 instrument × horizon cells under uncertainty,
multiple-testing, cost, drawdown and stability gates. Selecting more technical
thresholds after seeing those outcomes would expand researcher degrees of
freedom without adding information. HR9 remains a benchmark, not the basis of
the next strategy.

## Candidate ranking

| Rank | Information family | Predictive rationale | Availability/history | Cost/licensing | Timestamp and short-horizon fit |
|---:|---|---|---|---|---|
| 1 | JSE SENS and structured corporate events | Authoritative, instrument-specific information shocks | Real-time and EOD products exist; historical single-stock API product documented | Licensed JSE/distributor route required | Strong event clock; suitable from intraday through multi-session |
| 2 | Intraday trade/quote liquidity: bid/ask, volume, spread and imbalance | Adds state absent from daily technical data; measures executable conditions | Requires licensed Level 1/2 or broker feed and historical intraday store | Potentially material | Excellent if exchange/source timestamps and auctions are preserved |
| 3 | Causally aligned cross-market leads | USD/ZAR, gold, Brent, PGM, global index/futures and overseas listings may lead JSE names | Daily proxies exist; licensed intraday history still needed | Mixed | Strong only with trading calendars, venue hours and release delays modelled |
| 4 | Scheduled macro/fundamental events | Surprise and regime information beyond prices | SARB/Stats SA/issuer sources; vintage reconstruction required | Often public, engineering intensive | High around events; exact publication/availability clocks essential |
| 5 | Licensed financial news/sentiment | May accelerate interpretation of unscheduled events | Historical full text and redistribution rights difficult | Often expensive | Potentially strong but source timestamps and revisions matter |
| 6 | Uncontrolled social sentiment | Lead discovery in isolated cases | Unstable access and weak authority | Permission/API constraints | Too noisy to be a primary feature |

## Recommended next implementation

Implement one formal dataset milestone combining **JSE SENS event timing and
classification** with issuer mapping. It introduces genuinely new authoritative
information and can first be evaluated on daily/session horizons using the
existing point-in-time store. In parallel only as data procurement—not signal
development—obtain sample licensed Level 1/2 intraday data for one liquid JSE
instrument to assess feasibility.

Intraday 5/15/30/60-minute and same-day targets must be a separate dataset and
evaluation universe. Required fields include exchange event/receive timestamps,
bid/ask and sizes, trades/volume, session/auction state, corrections, instrument
reference data and market calendar. It must not be merged with HR10 results.

JSE documentation confirms live and EOD SENS products, technical samples, live
equity/derivative feeds and FIX/MITCH gateways; access is not necessarily retail:
https://clientportal.jse.co.za/technical-library/trading-and-market-data-documentation
and https://www.jse.co.za/market-data/market-announcements (accessed 2026-09-04).
