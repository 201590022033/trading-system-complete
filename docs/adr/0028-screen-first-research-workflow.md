# ADR 0028 — Screen-first research workflow and explicit instrument-class gates

Date: 2026-09-23. Status: accepted within the active Operational demo workspace.

## Context

The canonical public-research refresh already screens the configured 18-share
cash-equity universe before ranking the Top 5. The dashboard did not explain
that ordering. Its Technical Intelligence workspace emphasized a separate
six-share legacy benchmark, disabled those controls for the other twelve cash
shares and made the operator appear responsible for running five repetitive
analyses after ranking.

The UI also silently presented only cash shares. Index ETFs, CFDs and
single-stock futures were absent without exposing whether they were unsupported,
blocked or merely unconfigured.

## Decision

The dashboard presents the research workflow in its actual order:

1. choose an admitted instrument universe;
2. run the automatic canonical daily screen across that universe;
3. rank the shortlist;
4. review a candidate's technical evidence;
5. resolve entry, stop, target and risk size downstream; and
6. optionally print the existing paper worksheet.

Every Top 5 card links to a primary automatic-screen view. That view reads the
canonical opportunity evidence already produced by the backend; it does not
calculate signals or risk in the browser. The old full-analysis controls remain
available and clearly labelled as a separate six-share legacy benchmark.

The public-universe API now declares instrument classes and states. JSE cash
shares are available. Four verified JSE index ETF securities are
`CHART_ONLY_NOT_RANKED` pending liquidity and cost profiles. CFDs and SSFs are
`BLOCKED_CONTRACT_EVIDENCE` pending their respective contract, cost, financing,
margin, currency, expiry/roll and session facts. Unavailable classes remain
visible but cannot be selected.

The separate Market chart selector may show actual listed ETF charts and
explicitly labelled public underlying/index proxies for CFD investigation.
Proxy charts are never described as the broker contract price and do not enter
ranking, geometry, sizing or execution.

## Consequences

- Operators no longer need to infer that the Top 5 has already been screened.
- All configured cash shares can display their canonical technical inputs even
  when the legacy full benchmark is unavailable.
- Market liquidity remains an upstream suitability input; operator position
  size remains downstream of entry and stop geometry.
- No ETF, CFD or SSF identity is invented and cash-equity sizing is not reused
  for derivatives.
- Ranking, signal mathematics, risk policy, paper scheduling and broker
  execution behavior are unchanged. Live execution remains disabled.
