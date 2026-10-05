# ADR 0047 — isolated deterministic local replay contracts

Date: 5 October 2026. Status: Accepted for local research implementation.

The owner authorized B1–B5 after B0. Extend the existing platform through a separate pure `domain.backtest` core, an exact frozen-policy bridge and existing experiment/metric contracts. Existing replay cannot provide portfolio capital/accounting or product-specific execution without changing immutable profile semantics; the new version provides those contracts and reconciles the frozen benchmark on shared fixtures. No runtime entry point imports it.

Daily execution remains a hypothetical completed-close proxy, not an executable broker guarantee. Raw corporate actions and declared calendars are mandatory; unsupported adjusted histories, missing sessions, costs or conversions fail closed. Only full-fill assumptions are supported. FX/gold use explicit adapters; theoretical rand gold and rolled continuous prices cannot supply fills. Synthetic correctness and real-data execution acceptance are separate gates. B5 cannot be marked accepted without independently verified data, calendars, actions, costs and liquidity.

See [implementation evidence](../research/LOCAL_BACKTEST_IMPLEMENTATION.md) and [acceptance contract](../research/LOCAL_BACKTEST_ENGINE_SPEC.md). No cloud/paper wiring, default ranking changes, external orders or automatic promotion are authorized by this ADR.
