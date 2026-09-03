# South African Macro and Cross-Asset Relationship Model

These are **hypotheses/features to test**, not immutable trading rules. Effects can flip by regime and company hedging structure.

## Brent crude -> South Africa
South Africa is a net importer of crude/refined energy, so a sustained Brent rise can:
1. raise fuel/import costs and transport input costs;
2. add inflation pressure, directly and indirectly;
3. worsen household disposable-income pressure;
4. affect inflation expectations and therefore the expected SARB policy path;
5. pressure rate-sensitive domestic sectors if markets price rates higher/longer;
6. affect the trade/current-account picture and, in risk-off settings, the rand;
7. simultaneously benefit oil-linked revenue exposures such as Sasol depending on refining/chemical margins, hedges, operational performance and USD/ZAR.

Therefore model Brent through separate channels: `oil_price_change`, `oil_volatility`, `USDZAR`, inflation expectations/rates, and company-specific oil beta. Do not encode `Brent up = JSE down`.

Likely sensitivity examples:
- Sasol: often positive revenue sensitivity to stronger oil/weak rand, but not one-for-one because chemicals, hedges, costs and operations matter.
- Retail/transport/consumer-facing domestics: higher fuel costs can be a headwind.
- Banks/property: second-order sensitivity through inflation, rates, growth and credit quality.
- ALSI/J200: mixed because resources can offset domestic-rate pressure.

## Gold -> risk aversion / safe haven / SA gold miners
Gold often gains support when investors seek defensive assets, when real yields fall, or when confidence in risk assets/currencies weakens. It can also fall during liquidity shocks or when USD/real yields rise; therefore `gold up = risk-off` is not always valid.

For JSE gold miners model at least:
- USD gold price;
- USD/ZAR (rand gold price can rise even if USD gold is flat);
- US real-yield proxy / nominal yields + inflation expectations;
- DXY/USD strength;
- VIX/risk-off proxy;
- company costs, production guidance and operational SENS.

A strong gold signal with weakening ZAR may be materially different for a SA gold producer than gold rising while ZAR strengthens sharply.

## Rand / USDZAR
Model direction consistently: rising USD/ZAR = weaker rand.
Potential beneficiaries: offshore earners/exporters/miners, depending on cost base and hedging.
Potential headwinds: import-heavy businesses and consumers through imported inflation.
Banks/retail/property are influenced indirectly through inflation, rate expectations, confidence and growth; do not use a simple universal sign.

## Rates and SA bonds
Features: SARB repo path, FRA/rate expectations where available, SA government yields and curve slope.
- Financials: net-interest-margin effects can initially benefit from rates, while weak growth/credit losses can reverse the advantage.
- Property/REITs: typically rate/yield sensitive; falling yields can support valuations, but fundamentals matter.
- Retail/consumer: lower rates can improve disposable income/credit demand with a lag.

## Mining and PGMs
Features: commodity-specific spot/futures prices, USD/ZAR, China/global industrial activity proxies, energy/input costs and company SENS.
PGM miners require platinum/palladium/rhodium context rather than a generic `mining` flag.

## Agriculture/agri-linked shares
Where relevant to listed instruments, test rainfall/drought, maize/wheat/soft commodity prices, fertilizer/energy costs, logistics, USD/ZAR and regional export conditions. Liquidity may require slower horizons and stricter spread filters.

## Global risk-on / risk-off
Potential features: VIX, US equity index trend, DXY, UST yields, EM FX basket, gold, credit spreads if available.
Use them to classify regime first; only then adapt indicator/source weights.
