# AGENTS.md — Mandatory Entry Point

## Current context — 5 October 2026

The requirements below remain governing constraints. This reconciliation adds navigation/current context without weakening the original safety or evidence rules.

The current system centers on the canonical paper workflow, exact strategy lineage, local daily OHLCV collection and isolated AI/news research. The six-family local backtest/radar loop remains proposed; no validated profitability, automatic promotion or Live execution is established. See [current project state](docs/CURRENT_STATE.md) and [document index](docs/DOCUMENTATION_INDEX.md).

---

This repository is an **Adaptive South African Market Intelligence Platform**, not a generic trading bot.

## Before changing code
Read, in order:
1. `AGENTS.md`
2. `docs/agent/CONSTITUTION.md`
3. `docs/architecture/CURRENT_ARCHITECTURE.md`
4. `docs/architecture/TARGET_ARCHITECTURE.md`
5. `docs/roadmap/ROADMAP.md`
6. `docs/roadmap/CURRENT_MILESTONE.md`
7. Only domain docs relevant to the active milestone.

`MASTER_VSCODE_AGENT_PROMPT.md` was referenced by the earlier handoff but is not present in this checkout. Do not invent its contents; use the mandatory files above and the Constitution as the available governing contract.

## Non-negotiable rules
- Evolve existing code; do not rewrite without an ADR.
- Exactly one ACTIVE milestone at a time. Finish, test, document and commit it before advancing.
- Preserve legacy signal behavior as a benchmark; adaptive signals remain shadow-only until evidence supports promotion.
- Never commit or expose `.env`, credentials, API keys, browser profiles or cookies.
- Broker integrations remain read-only/paper/shadow. Never place live orders during this roadmap.
- Do not bypass CAPTCHAs, access controls or private-community restrictions.
- Do not claim accuracy without walk-forward evidence, costs/slippage context, sample size and uncertainty.
