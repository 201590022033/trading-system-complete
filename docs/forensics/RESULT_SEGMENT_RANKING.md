# Result Segment Ranking

The table preserves all 24 frozen ticker/horizon combinations. “Net vs cash” is
the reconstructed adaptive/raw-technical conditional mean net return relative
to a zero-return, zero-turnover cash benchmark. It is **not** excess return over
full production legacy; that comparison is `INSUFFICIENT HISTORICAL INPUTS`.
H1/H2 are temporal-half net returns and Adj is the fraction of the ticker's four
horizons with positive net return.

| Rank | Ticker | Profile | Horizon | N | Net vs cash | H1 / H2 | Adj | Technical score | Tier |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 1 | ABSPJ | banks_financials | 3 | 55 | 0.142% | 0.216% / 0.016% | 75% | 64.76 | C |
| 2 | SASOL | energy_sasol | 5 | 46 | 1.105% | -0.011% / 2.251% | 75% | 61.26 | C |
| 3 | ABSPJ | banks_financials | 5 | 55 | 0.230% | 0.511% / -0.252% | 75% | 60.40 | C |
| 4 | BHP | diversified_mining | 1 | 40 | 0.170% | 0.179% / 0.158% | 50% | 58.84 | C |
| 5 | SASOL | energy_sasol | 20 | 43 | 1.917% | 2.251% / 1.521% | 75% | 57.10 | C |
| 6 | SASOL | energy_sasol | 3 | 46 | 0.539% | -0.354% / 1.432% | 75% | 55.68 | C |
| 7 | BHP | diversified_mining | 3 | 40 | 0.219% | -0.096% / 0.640% | 50% | 51.92 | C |
| 8 | ABSPJ | banks_financials | 20 | 52 | 0.191% | 0.526% / -0.480% | 75% | 48.94 | C |
| 9 | SASOL | energy_sasol | 1 | 46 | -0.183% | -0.746% / 0.380% | 75% | 47.86 | C |
| 10 | SHPJ | retail_consumer | 1 | 50 | -0.081% | -0.399% / 0.209% | 25% | 46.82 | C |
| 11 | ABSPJ | banks_financials | 1 | 55 | -0.140% | -0.071% / -0.257% | 75% | 45.23 | C |
| 12 | BHP | diversified_mining | 5 | 40 | -0.054% | -0.623% / 0.705% | 50% | 45.17 | C |
| 13 | SHPJ | retail_consumer | 3 | 50 | -0.059% | -0.238% / 0.105% | 25% | 44.24 | C |
| 14 | SHPJ | retail_consumer | 20 | 50 | 0.157% | 0.120% / 0.190% | 25% | 42.96 | C |
| 15 | SHPJ | retail_consumer | 5 | 50 | -0.235% | -0.100% / -0.358% | 25% | 29.09 | C |
| 16 | NPN | offshore_earner | 1 | 46 | -0.158% | -0.207% / -0.093% | 0% | 28.51 | C |
| 17 | NPN | offshore_earner | 3 | 46 | -0.356% | -0.255% / -0.489% | 0% | 21.08 | C |
| 18 | BHP | diversified_mining | 20 | 40 | -0.572% | -0.390% / -0.814% | 50% | 19.53 | C |
| 19 | NPN | offshore_earner | 5 | 46 | -0.281% | -0.176% / -0.418% | 0% | 19.40 | C |
| 20 | IMPJ | pgm_mining | 20 | 44 | -0.243% | 0.004% / -0.644% | 0% | 16.75 | C |
| 21 | IMPJ | pgm_mining | 1 | 44 | -0.905% | -0.871% / -0.960% | 0% | 11.34 | C |
| 22 | NPN | offshore_earner | 20 | 44 | -0.589% | -0.103% / -1.287% | 0% | 6.52 | C |
| 23 | IMPJ | pgm_mining | 3 | 44 | -1.460% | -1.060% / -2.108% | 0% | 0.00 | C |
| 24 | IMPJ | pgm_mining | 5 | 44 | -1.061% | -0.873% / -1.366% | 0% | 0.00 | C |

The technical-candidate score uses absolute net result, statistical/sample
evidence, adjacent-horizon robustness, temporal halves and downside behavior.
It contains no inactive-legacy delta. Every row fails the Diamond incremental-
value gate because adaptive score/action is exactly identical to the simple
non-adaptive raw-technical benchmark. Full matched records and fields are in
`analysis/results/forensic_analysis.json`.
