# Shyft Trader Research

Accessed 2026-09-04.

## Confirmed

Shyft's current product page lists 14,500 shares/ETFs, 5,600 CFDs, 31
exchange-traded commodity products, 160+ FX crosses including spot precious
metals, and mutual funds. It advertises subscription live pricing, fast routing,
multi-device access, and market, limit, stop-limit, OCO, algo and trailing-stop
orders: https://www.shyft.co.za/en-ZA/what-shyft-trader-offers

The trading page describes shares/ETFs plus CFDs and FX spot and requires a
Shyft wallet, a Trader account and funded trading-currency account:
https://www.shyft.co.za/en-ZA/Trading

The migration comparison documents stop-loss/take-profit workflows and platform
notifications: https://www.shyft.co.za/en-ZA/Online-Share-Trading-Migration-to-Trader

Terms make use personal/non-transferable, restrict extraction/reuse without
consent, specify delayed quotes in some securities workflows, and make execution
confirmation authoritative. They describe exchange/affiliate/third-party
routing and account/portfolio access through the platform:
https://www.shyft.co.za/en-ZA/terms-and-conditions

## Unknown

No official public retail API, developer documentation, sandbox, FIX, REST or
websocket entitlement was found in the reviewed official material. This is
`UNKNOWN`, not proof none exists. Exact JSE cash/SSF/futures availability,
platform technology provider, API-on-request, deep links, manual-confirmation
API, automation permission, MFA scheme and private-app live-data rights require
written answers. Public descriptions of "algo orders" are broker order types,
not permission for customer-built automation.

## Current recommendation

Use a system-generated, read-only trade ticket followed by manual Shyft entry
and user confirmation. Prefer an official API with human confirmation only if
Standard Bank documents access and licensing. Do not use browser-click automation.
