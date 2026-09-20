# Connected cash and manual demo workflow

Implementation: ADR 0026, within the Operational demo workspace milestone.

1. Open **Portfolio & demo**. The headline sums connected broker **available
   funds**, separately for DEMO and LIVE. It is not equity, leverage, or a common
   account from which an order can spend. The simulator's R100,000 is excluded.
2. Select an account tab. IG returns original USD available funds and balance;
   the rand display uses a dated Yahoo USD/ZAR observation, never a hardcoded
   rate. Rates older than four days, future timestamps, invalid currency or
   stale account reads make the total incomplete. Original currency cash remains
   visible when only conversion is unavailable. Standard Bank is not connected.
3. Unlock using the existing Railway web-service `PAPER_CONTROL_TOKEN`. Never
   enter the IG password in this app's journal unlock form.
4. Execute a DEMO trade yourself in IG, then record instrument/EPIC, quantity,
   side, actual entry time/price, initial stop/target, planned monetary loss,
   broker reference and rationale. Select My own idea or App-inspired. The latter
   is not verified linkage to a historical recommendation.
5. After closing it yourself in the broker, choose **Record outcome**. Supply
   actual exit time/price and net P&L AFTER ALL COSTS in the account currency.
   Contract multipliers and FX are not guessed from price changes.
6. Review net result, planned-risk R multiple, incomplete/risk-exceeded warnings,
   rationale and outcome notes. Per-instrument/idea-source counts and net results
   accumulate from up to the latest 1,000 entries per account. These are descriptive,
   self-reported statistics, not evidence of profitable predictive skill.

Entries and closures are immutable, idempotent by trade UUID and stored in the
existing PostgreSQL/SQLite ledger under `manual-demo-journal:<account-key>`,
with distinct `manual_demo_entry`/`manual_demo_close` kinds. Database transactions
serialize duplicate saves. Occurrence times cannot be future; availability is
server recording time. As-of reviews exclude later records, even when a user
reports an earlier trade date. No new schema, balance debits, reservations,
broker order endpoint, simulator fill, or canonical strategy outcome is created.

The separate internal simulator remains available under its collapsed section;
its aggression slider affects only that simulator. This change does not wire
IG CFDs to M14/M15, continuous IG streaming, automatic broker reconciliation,
or canonical learning promotion. Other providers need factual read-only adapters
before they can contribute. No real-money order path is enabled.

Validation before deployment: full offline suite 688 tests; 54 protected artifacts;
JavaScript syntax; local browser entry/closure, account switching and disabled
unconnected account; actual read-only IG DEMO USD20,100 and dated FX retrieval.
No synthetic journal trade was created in production.
