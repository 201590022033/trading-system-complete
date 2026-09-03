# Agent Constitution

These rules are non-negotiable unless the user explicitly changes them.

## 1. Evolution before replacement
- Existing code is presumptively valuable.
- Search for overlapping functionality before creating a module, class, collector, indicator or API integration.
- Prefer extension, adapters and small refactors over replacement.
- Duplication requires an ADR explaining why reuse was rejected.
- Preserve public interfaces unless a migration is documented and tested.

## 2. Linear, dependency-driven execution
- Exactly one roadmap milestone may be ACTIVE.
- Do not start Milestone N+1 until N has passed acceptance criteria.
- No parallel feature sprawl.
- Within a milestone, order work by dependency and finish vertical slices.

## 3. Evidence before promotion
- New signals may run in research/shadow mode immediately.
- They may not change production/default signal weights until walk-forward evidence is recorded.
- Compare win rate, aligned return, drawdown, turnover, costs/slippage sensitivity, sample size and stability across periods.
- Avoid look-ahead leakage and survivorship bias where practical.
- Prefer interpretable weights before opaque end-to-end prediction.

## 4. Documentation is persistent project memory
Before coding, read the mandatory files in `AGENTS.md`.
After each completed task:
- update `CURRENT_MILESTONE.md`;
- update `ROADMAP.md` if reality changed;
- update architecture/domain docs if interfaces or assumptions changed;
- create an ADR for architectural decisions;
- add concise change notes.

## 5. Tests before claims
- Run the narrowest relevant tests after each change.
- Run the full available suite before milestone completion.
- If the current repo has weak tests, first add characterization tests around behaviour being modified.
- Do not call a task complete while a relevant test is failing without documenting the failure and why it is pre-existing.

## 6. Git discipline
- Inspect `git status` before work.
- Never commit `.env`, browser profiles, cookies, API keys, passwords or generated secrets.
- Preserve the user's existing uncommitted work. Establish a safe baseline commit only after secret checks and baseline tests.
- Make milestone-sized commits with descriptive messages.
- Never use destructive reset/clean/rebase against user work unless explicitly told.

## 7. Cost/token discipline
- Do not repeatedly reread the whole repository.
- Use `AGENTS.md` + architecture + current milestone as compressed memory.
- Read only files needed for the active task.
- Do not invoke cloud LLMs or paid APIs in bulk tests unless explicitly required; mock them where possible.
- Cache/reuse fetched research data where terms allow.

## 8. Source integrity
Every evidence item should eventually carry provenance fields: source name, source class, URL/id where available, observed/published time, ingestion time, asset/ticker mapping, sentiment/claim, parser version and reliability metadata.

## 9. Social-media boundary
- Publicly accessible pages/feeds and supported APIs may be integrated subject to platform terms.
- Do not build credential-sharing or password scraping for private Facebook groups or other private communities.
- Never bypass access controls, CAPTCHAs or anti-bot protections.
- Social content is a lead/sentiment layer, never authoritative truth.

## 10. Trading safety boundary
- Keep Standard Bank OST and other broker connections read-only during this roadmap.
- Paper/shadow decisions are allowed.
- Live execution requires a separate explicit user decision, risk controls and an ADR.

## 11. Stop conditions
Continue autonomously through the roadmap unless one of these occurs:
- a required secret/API subscription is unavailable and no mock/public fallback exists;
- a destructive migration is unavoidable;
- live trading authority would be required;
- user data or credentials could be exposed;
- two architectural choices are materially irreversible and evidence is genuinely insufficient.
If blocked, document the blocker and continue with any remaining non-dependent work rather than improvising.
