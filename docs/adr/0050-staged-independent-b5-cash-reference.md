# ADR 0050: Stage independent cash expectations before real-data admission

Status: Accepted for isolated research verification, 5 October 2026.

B5 has observed Sasol prices and verified broad daily sessions, but their RAW/action contract is not certified. The engine's immutable manifest deliberately refuses unverified price/action semantics. Waiting for these contracts need not prevent preparing independently calculated expected accounting results.

Add an offline reference script reading the frozen comparison and calendar. It computes later-close, 3/4/5-session cash expectations for fixed dated probes with disclosed spread/slippage, price risk and current fee assumptions. It never constructs a manifest, calls replay, manufactures bars or reports admitted trades. Its fee arithmetic intentionally duplicates the published formula independently; sharing the production helper would invalidate the oracle's independence. Optional verification compares the production adapter against these independently computed expected fees.

Outputs remain conditional expectations. They cannot establish a passing real-data trade audit, action coverage, intraday reconciliation, historical execution or profitability. Once the source contract passes, a separate manifested replay must be compared with these expected trades, cash and equity. No production interfaces or default behavior change.

This also preserves the specification's existing scope: current fee/fill sensitivity assumptions can support bounded research, while broker invoices, quotes and actual fills concern execution readiness. Unsupported real FX/gold contracts may remain blocked; they are not prerequisites for a verified cash-equity-only acceptance. Required source-quality checks are not weakened.
