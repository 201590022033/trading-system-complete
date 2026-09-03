# Point-in-Time Data Policy

## Three-clock rule

Every historical value must carry timezone-aware UTC timestamps:

- `event_time`: when the market event occurred or the economic reference period
  ended;
- `available_time`: earliest defensible time the system could access this exact
  value/revision;
- `decision_time`: timestamp of the reconstructed decision.

A record is eligible only when `available_time <= decision_time`. Event time
alone never establishes availability.

## Revisions

Revision state is `not_applicable`, `initial`, `revised`, or `final`. A revision
is a new append-only record with its own availability time and `supersedes_id`;
old values are not overwritten. An as-of query returns only the latest revision
available at that historical cutoff. Current revised CPI, rates, fundamentals,
constituents or adjusted prices must not be backfilled as originally known.

## Market bars and events

- A daily bar becomes usable only at its defensible publication/session-close
  availability time. Features for a close decision cannot include later bars.
- Intraday features require genuine timestamped intraday OHLCV capability.
- News/SENS uses original publication plus observed/ingestion availability; a
  corrected story is a revision.
- Source deletion or unavailable archives are recorded as a capability gap, not
  reconstructed from memory.
- Forward returns and labels are outcomes, never decision features.

## Missing data

Missing is not neutral. Unavailable features use an explicit false capability,
null value and reason. Models must select matched eligible timestamps or expose
the changing sample; they may not silently replace missing historical
sentiment/macro/source data with zero and call it a full replay.

## Versioning and reproducibility

Raw retrievals carry source/retrieval identity and licensing notes. Derived
records list input record IDs and formula version. Provider revisions require a
new frozen retrieval ID. Research outputs must name dataset/store and feature
versions, eligibility filters, costs and split boundaries.

## Training and evaluation

Training/calibration ends before the test interval. Regimes are calculated from
prefix data only. Confirmation patterns become available only after the
confirming bar. Walk-forward weights may use prior outcomes only after their
horizon has elapsed. Production/default weights remain frozen; all HR features
and learned weights are shadow-only.
