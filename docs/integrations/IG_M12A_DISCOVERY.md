# M12A — IG Discovery, Authentication & Canonical Market Mapping

## Status

**BLOCKED — candidate implementation complete; external validation required**

The adapter is read-only and does not connect to strategy, dashboard, Railway
worker, portfolio or execution paths. No credentials or session tokens are
stored in the repository or persistence layer.

## Adapter boundary

`domain.broker.ig.IGReadOnlyAdapter` uses the IG REST discovery endpoints for
session authentication, account listing, market search and market detail. It
normalizes account and market metadata and produces `IGMapping` records that
retain the canonical instrument ID, broker, environment, EPIC and product
variant. Cash, CFD, rolling, dated and other variants are not merged.

Authentication uses `IG_API_KEY`, `IG_USERNAME`, `IG_PASSWORD`, optional
`IG_ACCOUNT_ID` and `IG_ENVIRONMENT`. The environment is `DEMO` by default and
must be explicitly `DEMO` or `LIVE`; it never defaults to LIVE. The base URLs
are selected centrally by `IGConfig`.

Session credentials are held only in memory. They are never printed, persisted,
included in audit payloads or included in exception text. The CLI prints only
normalized/redacted discovery results.

## Operator validation

Set these environment variables through the operator’s secret manager or local
process environment only:

```text
IG_API_KEY
IG_USERNAME
IG_PASSWORD
IG_ACCOUNT_ID (optional)
IG_ENVIRONMENT=DEMO
```

Run from the repository root:

```text
python -m scripts.ig_discovery status
python -m scripts.ig_discovery accounts
python -m scripts.ig_discovery search "Brent"
python -m scripts.ig_discovery market "<EPIC returned by search>"
```

Use DEMO first. These commands perform authentication, account discovery,
market search and one market metadata lookup only. Do not paste secrets or raw
headers into chat. No dealing command exists in this milestone.

## Suitability and deferrals

Normalized IG metadata can inform M12 suitability facts such as broker support,
execution mapping and contract metadata, but it does not rescore historical
attractiveness. Canonical identities remain separate from IG EPICs. Historical
price ingestion, execution-grade 5-minute validation, streaming, positions,
orders and opportunity ranking remain deferred to later milestones.
