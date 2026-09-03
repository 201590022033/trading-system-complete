# Indicator Matrix — Research Priorities by Instrument, Regime and Sector

No indicator is assumed to "work" merely because it is listed here. Each row defines **backtest candidates**.

## Core indicator families to add/evaluate
- Trend: EMA/SMA slopes and crossovers, MACD, ADX/DMI.
- Mean reversion: RSI, stochastic, Bollinger Bands/z-score.
- Volatility/risk: ATR, realized volatility, gap size, volatility percentile.
- Price structure: Donchian/channel breakouts, prior-day/week high-low, support/resistance.
- Volume/liquidity: volume, relative volume, OBV/volume trend where data quality supports it, spread/turnover filters.
- Intraday: VWAP and VWAP deviation, opening-range breakout, session high/low, time-of-day filters when intraday data is available.
- Relative strength: ticker vs J200/sector index; sector vs J200; commodity producer vs underlying commodity/rand-price proxy.
- Cross-asset: rolling beta/correlation and divergence to USD/ZAR, Brent, gold, platinum, yields and risk proxies.

## Bull trend
Prefer research on:
- trend persistence (EMA/SMA slope, ADX, MACD);
- pullback entries toward EMA/VWAP rather than blindly shorting high RSI;
- breakouts confirmed by relative volume/ATR;
- relative strength vs index/sector.
RSI overbought can mean strong momentum in trends, so treat it as context rather than automatic SELL.

## Bear trend
Prefer research on:
- price below declining trend filters;
- failed rallies/rejection near EMA/VWAP/resistance;
- downside Donchian/breakout + volume/ATR expansion;
- bearish relative strength;
- RSI/stochastic rebounds from oversold used cautiously as counter-trend, not automatic BUY.

## Range / low-ADX
Mean reversion candidates become more relevant:
- RSI/stochastic extremes;
- Bollinger/z-score reversion;
- VWAP deviation;
- range boundaries.
Suppress breakout/trend weights unless regime changes.

## High-volatility regime
- widen risk distances using ATR rather than fixed percentages;
- reduce position-size confidence;
- require liquidity/spread filters;
- distinguish news gaps from continuous moves;
- avoid interpreting indicator extremes with normal-regime thresholds without evidence.

## JSE Top 40 / ALSI index futures / index CFDs
Priority candidates:
- VWAP + opening range (intraday data required);
- EMA trend + ADX;
- ATR/realized volatility;
- J200 market breadth/constituent strength if data available;
- overnight/global lead: S&P/Europe/China proxies, USD/ZAR, commodities;
- volume/open interest/basis and expiry/close-out context where derivative data is licensed.
Bull: buy pullbacks in confirmed trend / upside range expansion.
Bear: failed VWAP/EMA rallies / downside range expansion.

## Single Stock Futures and share CFDs
Use underlying-share technicals plus leverage-aware controls:
- relative volume/liquidity;
- ATR and gap risk;
- SENS event flags;
- relative strength to sector/J200;
- futures basis/dividend/expiry context for SSFs.
Avoid treating a thinly traded underlying like a liquid Top-40 name.

## Banks / financials
Technical candidates:
- relative strength vs J200;
- EMA/MACD/ADX for trends;
- RSI as pullback/range context;
- volume confirmation.
Context features:
- SARB path, SA bond yields/curve, credit/growth expectations, USD/ZAR.
Test bull/bear asymmetry: rate hikes can support margins but harm credit/growth; sector response is conditional.

## Gold miners
Technical candidates:
- breakout/trend + ATR;
- relative strength vs J200;
- MACD/ADX;
- volume confirmation.
Cross-asset features:
- USD gold; rand gold (`gold_usd * USDZAR` conceptually);
- real-yield/DXY proxies;
- VIX/risk aversion;
- company SENS.

## PGM / diversified mining
Technical candidates:
- trend/breakout + ADX/ATR;
- relative volume;
- relative strength vs resources index/J200.
Context:
- platinum/palladium/rhodium or relevant commodity basket;
- China/industrial-cycle proxies;
- USD/ZAR;
- energy/logistics/operational SENS.

## Energy / Sasol
Technical candidates:
- trend/ADX/MACD;
- ATR due volatility;
- breakout with volume;
- relative strength.
Context:
- Brent and oil volatility;
- USD/ZAR;
- chemical/refining margin proxies if obtainable;
- company operational/hedging SENS.

## Retail / consumer
Technical candidates:
- trend/relative strength;
- RSI/Bollinger in ranges;
- earnings/SENS gap filters.
Context:
- rates, inflation, fuel, consumer confidence, employment/real income and USD/ZAR/import costs.

## Agriculture/agri-linked
Technical candidates:
- slower trend/breakout and ATR due liquidity;
- relative volume filter essential;
- longer horizons may outperform intraday approaches.
Context:
- crop/soft commodity prices, rainfall/drought, fertilizer/fuel, USD/ZAR, logistics.

## USD/ZAR / FX CFDs or futures where available
Priority candidates:
- trend/ADX/EMA;
- ATR and session volatility;
- support/resistance and breakout;
- RSI only regime-aware;
- DXY, UST/SA yield differential proxies, risk sentiment, commodity basket.
Explicitly separate London/NY/liquidity sessions when intraday data supports it.
