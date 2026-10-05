# ADR 0049: directional published OST costs for local cash replay

Accepted 5 October 2026 for B5 software verification only. Full external-data acceptance remains blocked.

The generic local fee model could not apply purchase-only STT or the published OST component minimums. Extend its fee call with an optional transaction direction, retaining the existing generic arithmetic and defaults. Add opt-in `OSTCashShareCosts`, reusing the independently tested published-fee diagnostic; do not duplicate that formula or alter canonical policy costs.

The adapter is limited to ZAR cash-equity manifests, forbids stacking generic fees, includes all rates and its schedule version in the immutable config hash, and charges direction-aware fees during affordability sizing and entry/exit accounting. Spread and slippage remain separately declared sensitivities. Rates are from the public 5 October OST page; VAT on the levy and component rounding remain assumptions. This is not a dated account tariff or broker invoice.

Independent nine-share accounting ends at R1,766.24 from R2,000, with R269.76 fees and R36 gross gain. The minimum fee and purchase tax make ten shares exceed the R1,100 order budget. A disposable wrong-side-tax mutation is caught. Existing equity/FX/gold examples retain identical semantic hashes; no runtime wiring, orders, ranking or default strategy changes.

Unresolved provider metadata, actions and execution evidence must not be represented as verified to obtain a passing B5 status. Unsupported real markets remain blocked under the existing scoped-acceptance contract.
