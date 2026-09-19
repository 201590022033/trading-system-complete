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
3. Record factual history and market eligibility. The known Brent product
   CC.D.LCO.BMU.IP currently reports EDITS_ONLY, not TRADEABLE. A six-hour
   HOUR history request returned seven out-of-range records and zero accepted
   bars; inspect timestamps before claiming usable research history.
4. Verify safe tests, commit/push, and verify the deployed account view. Update
   roadmap and report exact remaining runtime/research/execution connections.

## Reopened acceptance gates

| Boundary | Verified now | Still required |
| --- | --- | --- |
| M12A / M26 | Local and Railway DEMO authentication, enabled USD CFD account, zero positions | Rate-bounded production polling and account-change handling |
| M12B / M25 | History endpoint responds | Usable requested-range bars, factual calendar/costs, frozen HR11 evaluation |
| M24 | Concrete transport authenticated, subscription acknowledged, Brent snapshot received in bounded local validation | Fresh open-market quote validation and durable runtime ingestion |
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
EDITS_ONLY/EDIT, and no order was submitted. The new transport is not yet
composed into the Railway worker or connected to ranking/learning. Deployment
of this code alone does not activate continuous streaming.

The history probe's seven returned UTC timestamps were 04:00–10:00 for the
requested 12:00–18:00 range. No timezone correction has been guessed or applied.

References: https://labs.ig.com/streaming-api-reference.html,
https://labs.ig.com/streaming-api-guide.html, https://labs.ig.com/faq.html.
