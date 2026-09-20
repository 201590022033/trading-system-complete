# IG operational reassessment — 2026-09-19

Active milestone remains Operational demo workspace (ADR 0025). Historical
component-complete headings do not establish deployed end-to-end acceptance.

## Ordered implementation and acceptance

1. Configure verified credentials only in Railway private variables. Verify
   deployed account/position reads; keep USD CFD capital separate from the
   R100,000 ZAR cash-share PaperBroker. No broker order is part of this step.
2. Repair the existing M24 transport boundary against current IG PRICE fields:
   BIDPRICE1/ASKPRICE1/TIMESTAMP/DLG_FLAG/DELAY, not deprecated MARKET fields.
   Add a real Lightstreamer transport and a bounded, read-only validation entry
   point; distinguish connection, subscription, fresh quotes and delayed data.
   Missing transport, future timestamps and subscription errors must not appear
   as a working price feed. Add offline regressions before external validation.
   **Done:** `workers/ig_streaming.py` composes the existing transport into the
   bounded worker and persists observations to the shadow-learning ledger.
3. Record factual history and market eligibility. The known Brent product
   CC.D.LCO.BMU.IP currently reports EDITS_ONLY, not TRADEABLE. A six-hour
   HOUR history request returned seven out-of-range records and zero accepted
   bars; inspect timestamps before claiming usable research history.
4. Verify safe tests, commit/push, and verify the deployed account view. Update
   roadmap and report exact remaining runtime/research/execution connections.

## 30-minute history probe — 2026-09-20

Using the authenticated Railway Demo environment, a bounded read-only
`MINUTE_30` request for `CC.D.LCO.BMU.IP` from 2026-09-15 through 2026-09-19
returned 165 derived-mid research bars in one page. The response contained zero
malformed, incomplete or duplicate records, 12 valid out-of-range exclusions,
and no truncation. The source timestamps span 2026-09-15T00:00Z through
2026-09-18T16:00Z. This proves source availability and 30-minute normalization,
not research admissibility: the API still reports 12 unclassified discontinuities
and no factual EPIC-specific session calendar was supplied. No bars were
persisted, evaluated, or connected to ranking, paper fills, risk, or execution.

The same read-only metadata lookup identified the EPIC as `Oil - Brent Crude
($1)` and returned bid `10014.8`, offer `10019.6`, tick size `1.0`, lot size
`1.0`, minimum deal size `1.0`, and margin factor `1.5`. The observed 4.8-point
quote is evidence only; `trading_hours` was empty and currency was unavailable,
so no commission, slippage, financing, or currency-aware cost schedule can be
admitted from this response.
An additional authenticated Version 4 market lookup also omitted `openingHours`
and returned an empty currency code, so the absence is not limited to the
adapter's Version 3 normalization.

The read-only IG indicative-costs endpoint also accepted a bounded one-unit BUY
probe using the observed quote and `dealCurrencyCode=ZAR`. It returned instrument
currency `USD`, notional `10019.6`, ZAR notional `622.191153`, opening and
closing spread `0.1475581886496`, opening and closing commission `0`, opening
and closing FX fee `0`, overnight funding `-0.7836692434023048`, and daily FX
fee `0.0077591014198248`. This is a broker indicative quote, not an order or a
historical cost schedule; it remains research evidence until its assumptions,
validity, and session context are versioned.

## Reopened acceptance gates

| Boundary | Verified now | Still required |
| --- | --- | --- |
| M12A / M26 | Local and Railway DEMO authentication, enabled USD CFD account, zero positions | Rate-bounded production polling and account-change handling |
| M12B / M25 | History endpoint responds | Usable requested-range bars, factual calendar/costs, frozen HR11 evaluation |
| M24 | Concrete transport authenticated, subscription acknowledged, Brent snapshot received in bounded local validation; durable worker ingestion implemented with offline tests | Fresh open-market quote validation in deployed worker and observation ledger review |
| Gates 1–5 | Deployed daily ZAR paper loop and canonical Top 5 | Real subsequent-session fills/outcomes and mature learning evidence |
| M14 / M15 with IG | Cash-share geometry/risk exists | CFD units, USD/FX, margin and actual account exposure mapping |
| M27–M30 | Component tests and bounded harness | Independent internal IG ledger, factual reconciliation and all order preflight checks |

Do not use an IG quote in place of a Yahoo share close: instrument, currency,
contract, time and volume semantics differ. IG documents no equity-price
subscriptions. Receiving a Lightstreamer endpoint is not proof of streaming.
No autonomous IG orders, live-money capability or adaptive promotion is enabled.

## Verified streaming checkpoint

The bounded local validation received an IG PRICE snapshot at 13:37 UTC on
2026-09-19. Its source timestamp was 2026-09-18T22:50:22.489Z. Connection and
subscription succeeded; health correctly remained STALE. The broker reported
EDITS_ONLY/EDIT, and no order was submitted. The new transport is now composed
into the bounded Railway worker, but activation still requires the explicit
`IG_STREAM_ENABLED=1` and `IG_STREAM_INSTRUMENTS` variables. Until an enabled
deployment produces fresh ledger observations, this is implementation evidence,
not proof of a live market feed or a ranking/learning connection.

The history probe's seven returned UTC timestamps were 04:00–10:00 for the
requested 12:00–18:00 range. No timezone correction has been guessed or applied.

References: https://labs.ig.com/streaming-api-reference.html,
https://labs.ig.com/streaming-api-guide.html, https://labs.ig.com/faq.html.
