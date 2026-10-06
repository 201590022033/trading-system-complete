# ADR 0060 — Forward-only price outcome cohorts

Date: 6 October 2026. Status: Accepted.

Decision: compute local, source-specific 3/4/5 observed-session price-only outcomes from R9 captures. Admit only the newest completed session per actual capture as a first-seen anchor, require later acquired captures for exits, and exclude revised entry/exit values. Show sample and uncertainty context; assume 10 bps round-trip friction for the descriptive net percentage.

Reason: dated captures permit prospective observation even while provider semantics remain unresolved. Older rows in an export cannot establish earlier availability. Source mixing or same-capture entry/exit labels would introduce lookahead.

Consequences: no result exists until real later captures arrive. This is a price movement cohort, not signal efficacy or execution evidence. Calendar, corporate actions, actual spreads/fills and volume eligibility remain unresolved. No historical AI/B5 or live trading gate changes.
