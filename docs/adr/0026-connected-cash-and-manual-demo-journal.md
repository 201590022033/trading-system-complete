# ADR 0026 — Connected cash and account-linked manual demo journal

2026-09-20. Extension of the sole ACTIVE operational demo workspace milestone.

The headline must not use the internal simulator's invented starting capital.
Aggregate broker-reported available funds by environment and currency, with a
dated, indicative ZAR conversion. Never combine real money with demo money or
use this display aggregate to fund orders. Missing accounts/rates remain missing,
not zero or guessed. Keep original currency, cash field semantics and timestamps.
Reuse the existing read-only IG adapter and Yahoo chart source for USD/ZAR;
future providers must supply the same normalized account contract. Standard Bank
is explicitly not connected. No new broker integration is implied.

Implement in order:
1. Pure aggregation and cached provider reads with freshness checks and tests.
2. Authenticated manual entry/closure journal over existing durable paper tables,
   under an isolated namespace and distinct record kinds. No schema migration.
3. Connected-account headline/tabs and manual journal forms; retain simulator in
   a clearly labelled collapsed diagnostic section, outside cash totals.
4. Test restart durability, causal visibility, validation, isolation and UI;
   run safe suite and protected artifacts, commit, then verify deployment.
5. A later presentation-only extension may print a canonical research worksheet
   and hand its identity/direction into the same journal form. It must leave all
   actual execution facts blank, preserve App-inspired as unverified attribution,
   and create no proposed-order persistence or broker action.

Manual trades are self-reported observations, not broker-verified fills. Capture
the chosen account, exact instrument, direction, quantity, entry time/price,
optional stop/target and planned monetary risk, idea source and rationale. On
closure require actual net P&L in the account currency; never guess CFD contract
multipliers from price differences. Record separate occurrence and availability
clocks. Review only information known by the evaluation time. Retrospective
entries cannot establish an ex-ante plan. Profit is not proof of decision quality.
Show descriptive outcomes and R multiples when planned risk is supplied, without
claiming statistical strategy validation or retraining an LLM.

Reuse paper ledger transactions, immutable records and operator authentication.
Journal records are NOT canonical strategy outcomes and cannot enter M11/M13
learning without a later explicit attribution/validation design. Recording does
not place any order, debit cash, reserve funds or change simulator settings.
