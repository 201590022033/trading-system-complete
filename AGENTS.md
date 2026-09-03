# AGENTS.md — Mandatory Entry Point

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

`MASTER_VSCODE_AGENT_PROMPT.md` is the execution mandate; the Constitution is the governing contract.

## Non-negotiable rules
- Evolve existing code; do not rewrite without an ADR.
- Exactly one ACTIVE milestone at a time. Finish, test, document and commit it before advancing.
- Preserve legacy signal behavior as a benchmark; adaptive signals remain shadow-only until evidence supports promotion.
- Never commit or expose `.env`, credentials, API keys, browser profiles or cookies.
- Broker integrations remain read-only/paper/shadow. Never place live orders during this roadmap.
- Do not bypass CAPTCHAs, access controls or private-community restrictions.
- Do not claim accuracy without walk-forward evidence, costs/slippage context, sample size and uncertainty.
