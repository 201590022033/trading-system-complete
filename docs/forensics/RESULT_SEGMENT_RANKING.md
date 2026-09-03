# Result Segment Ranking

The table ranks the frozen reconstruction’s 24 ticker/horizon combinations.
`Δ` is adaptive mean net minus legacy mean net. Legacy made zero trades, so the
delta is not a like-for-like excess-return estimate. H1/H2 are temporal-half
adaptive mean net returns; Adj is the fraction of the ticker’s four horizons
with positive mean net return.

| Rank | Ticker | Profile | Horizon | N | Adaptive net | Δ | H1 / H2 | Adj | Score | Tier |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 1 | SASOL | energy_sasol | 5 | 46 | 1.105% | 1.105% | -0.011% / 2.251% | 75% | 70.94 | B |
| 2 | SASOL | energy_sasol | 20 | 43 | 1.917% | 1.917% | 2.251% / 1.521% | 75% | 67.83 | B |
| 3 | ABSPJ | banks_financials | 3 | 55 | 0.142% | 0.142% | 0.216% / 0.016% | 75% | 62.84 | B |
| 4 | SASOL | energy_sasol | 3 | 46 | 0.539% | 0.539% | -0.354% / 1.432% | 75% | 61.00 | B |
| 5 | ABSPJ | banks_financials | 5 | 55 | 0.230% | 0.230% | 0.511% / -0.252% | 75% | 60.67 | B |
| 6 | BHP | diversified_mining | 1 | 40 | 0.170% | 0.170% | 0.179% / 0.158% | 50% | 58.76 | B |
| 7 | BHP | diversified_mining | 3 | 40 | 0.219% | 0.219% | -0.096% / 0.640% | 50% | 54.18 | C |
| 8 | ABSPJ | banks_financials | 20 | 52 | 0.191% | 0.191% | 0.526% / -0.480% | 75% | 51.59 | C |
| 9 | SHPJ | retail_consumer | 20 | 50 | 0.157% | 0.157% | 0.120% / 0.190% | 25% | 46.68 | C |
| 10 | SHPJ | retail_consumer | 1 | 50 | -0.081% | -0.081% | -0.399% / 0.209% | 25% | 46.60 | C |
| 11 | SASOL | energy_sasol | 1 | 46 | -0.183% | -0.183% | -0.746% / 0.380% | 75% | 46.10 | C |
| 12 | BHP | diversified_mining | 5 | 40 | -0.054% | -0.054% | -0.623% / 0.705% | 50% | 45.71 | C |
| 13 | SHPJ | retail_consumer | 3 | 50 | -0.059% | -0.059% | -0.238% / 0.105% | 25% | 44.94 | C |
| 14 | ABSPJ | banks_financials | 1 | 55 | -0.140% | -0.140% | -0.071% / -0.257% | 75% | 44.68 | C |
| 15 | NPN | offshore_earner | 1 | 46 | -0.158% | -0.158% | -0.207% / -0.093% | 0% | 31.91 | C |
| 16 | SHPJ | retail_consumer | 5 | 50 | -0.235% | -0.235% | -0.100% / -0.358% | 25% | 31.38 | C |
| 17 | NPN | offshore_earner | 3 | 46 | -0.356% | -0.356% | -0.255% / -0.489% | 0% | 23.86 | C |
| 18 | NPN | offshore_earner | 5 | 46 | -0.281% | -0.281% | -0.176% / -0.418% | 0% | 23.54 | C |
| 19 | IMPJ | pgm_mining | 20 | 44 | -0.243% | -0.243% | 0.004% / -0.644% | 0% | 22.02 | C |
| 20 | BHP | diversified_mining | 20 | 40 | -0.572% | -0.572% | -0.390% / -0.814% | 50% | 20.01 | C |
| 21 | NPN | offshore_earner | 20 | 44 | -0.589% | -0.589% | -0.103% / -1.287% | 0% | 10.03 | C |
| 22 | IMPJ | pgm_mining | 1 | 44 | -0.905% | -0.905% | -0.871% / -0.960% | 0% | 9.70 | C |
| 23 | IMPJ | pgm_mining | 3 | 44 | -1.460% | -1.460% | -1.060% / -2.108% | 0% | 0.00 | C |
| 24 | IMPJ | pgm_mining | 5 | 44 | -1.061% | -1.061% | -0.873% / -1.366% | 0% | 0.00 | C |

The score combines net result/delta (45%), statistical/sample evidence (15%),
adjacent-horizon robustness (15%), temporal halves (10%) and downside behavior
(15%). It was specified as a bounded forensic score, not fitted to returns.
Economic plausibility is applied as a tier veto: no row can be Tier A when its
claimed sector mechanism was not observed. Full fields are in
`analysis/results/forensic_summary.json`.
