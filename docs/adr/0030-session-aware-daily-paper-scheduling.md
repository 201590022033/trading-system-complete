# ADR 0030 — Session-aware daily paper scheduling

Accepted 2026-10-01 as a corrective extension of ADR 0029 in the sole active
operational demo workspace.

## Context

The first seven `railway-paper-zar-v2` jobs completed without crashes and grew
PostgreSQL by only about 312 KB, but all 18 configured instruments were rejected
on every cycle. The exact 86,400-second freshness limit was incompatible with
the conservative next-day availability clock: jobs ran 13–48 seconds after the
UTC-day boundary, Yahoo could lag a completed JSE session, and weekends plus the
24 September public holiday widened the calendar gap. Consequently no ranked
decision or outcome entered the new learner even though a causal replay of the
frozen inputs produced ranked LONG candidates.

The daily scheduler also stored a full compact chart input on Saturday, Sunday
and other days where the latest causally usable source sessions were unchanged.
The status API reported `AVAILABLE` because the account transaction completed,
even when the committed ranking contained no opportunities and every provider
candidate was unavailable.

## Decision

- Daily bars may be at most four calendar days old. This is a bounded tolerance
  for weekends, public holidays and provider delay, not permission to relabel an
  old bar as current.
- The worker fingerprints the latest causally usable session timestamp for each
  available instrument. After one successful ranking commits that fingerprint,
  a later calendar-day job with the same fingerprint stores only a compact
  `NO_NEW_COMPLETED_SESSION` retry record and performs no new paper cycle.
- A failed or empty ranking does not advance the committed fingerprint, so a
  later job can retry instead of permanently suppressing the session.
- A non-stale empty ranking with unavailable provider candidates reports
  `NO_USABLE_MARKET_DATA`, not `AVAILABLE`.
- Railway starts a new immutable configuration identity,
  `railway-paper-zar-v3`. The empty v2 experiment is not backfilled or relabelled
  as live learning evidence.

## Consequences

- Completed sessions, rather than calendar midnights, control new learning
  decisions; the existing instrument/session decision ID remains the final
  deduplication boundary.
- The last valid ranking remains readable through ordinary weekend closures for
  up to four days. Longer gaps become `STALE` and cannot drive new paper entries.
- Calendar-day job checkpoints remain auditable, but repeated sessions no longer
  duplicate the 60-bar payload or replace the last valid ranking.
- IG streaming remains disabled, execution remains paper-only, and the existing
  three-session/30-sample learning gates are unchanged.
