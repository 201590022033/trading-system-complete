# M3 instrument identity mapping

The canonical registry is additive and broker-neutral. Existing operational
identities map to six canonical cash-equity IDs; Yahoo symbols remain data
symbols and are never copied into execution symbols.

| Legacy ID | Canonical ID | Data symbol | Execution symbol |
|---|---|---|---|
| NPN | EQ_ZAR_NASPERS | NPN.JO | unresolved |
| SOL / SASOL | EQ_ZAR_SASOL | SOL.JO | unresolved |
| BHP | EQ_ZAR_BHP | BHG.JO | unresolved |
| IMP / IMPJ | EQ_ZAR_IMPLATS | IMP.JO | unresolved |
| SHP / SHPJ | EQ_ZAR_SHOPRITE | SHP.JO | unresolved |
| ABG / ABSPJ | EQ_ZAR_ABSA | ABG.JO | unresolved |

HR11 proxy and research identities are reconciled from
`intraday_instruments.DEFAULT_REGISTRY`, preserving its data symbols and
optional contract metadata. Enabled HR11 identities are research-governed;
disabled extensions remain disabled. No broker contract values were inferred.

The opportunity scanner's 18-key public discovery universe maps the six known
operational aliases. The remaining discovery tickers are intentionally reported
as unresolved by `discovery_mapping`; scanner ranking and output are unchanged.
