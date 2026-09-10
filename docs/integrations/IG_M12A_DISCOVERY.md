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

Authentication uses `IG_API_KEY`, `IG_IDENTIFIER`, `IG_PASSWORD`, optional
`IG_ACCOUNT_ID` and `IG_ENVIRONMENT`. IG defines the v2 `/session` JSON
`identifier` as the client login identifier and constrains it to 1-30 ASCII
letters, digits, hyphens or underscores. Enter the unique IG API login username,
not an email address and not the account ID. `IG_USERNAME` remains a
backward-compatible alias only when `IG_IDENTIFIER` is unset. The environment is
`DEMO` by default and must be explicitly `DEMO` or `LIVE`; it never defaults to
LIVE. The base URLs are selected centrally by `IGConfig`.

Session credentials are held only in memory. They are never printed, persisted,
included in audit payloads or included in exception text. The CLI prints only
normalized/redacted discovery results.

## Authentication troubleshooting

`python -m scripts.ig_discovery status` now performs a real read-only session
authentication attempt. A failure prints only these sanitized fields:
`authenticated`, `environment`, `http_status`, `ig_error_code`,
`error_category` and `message`. The original IG error code is retained when the
response provides one, but credentials, account IDs, session tokens, request
payloads, headers and cookies are never returned.

Categories distinguish supported evidence for invalid API keys, rejected
credentials, explicit environment mismatches, two-factor requirements,
permission failures, rate limiting, network failures and malformed responses.
Ambiguous responses remain `UNKNOWN_IG_ERROR`; the adapter does not guess a
more specific cause. HTTP 400 is reported as `MALFORMED_REQUEST`.

If `TWO_FACTOR_REQUIRED` is returned, follow the account's normal IG security
process. M12A does not append a security code to the password, prompt for one,
or automate two-factor authentication. Do not paste the diagnostic together
with secrets or raw HTTP headers.

Focused mocked coverage exercises successful authentication, IG error-code
preservation, HTTP 400/401/403/429 and unexpected failures, network and malformed
responses, two-factor reporting, secret redaction and the disabled execution
boundary. The complete safe suite passes 329 tests.

## Operator validation

Set these environment variables through the operator’s secret manager or local
process environment only:

```text
IG_API_KEY
IG_IDENTIFIER
IG_PASSWORD
IG_ACCOUNT_ID (optional)
IG_ENVIRONMENT=DEMO
```

Older local configurations may use `IG_USERNAME` as the identifier alias. New
configuration should use `IG_IDENTIFIER`. `IG_ACCOUNT_ID` selects or records an
account after authentication and is never substituted into the login payload.

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
