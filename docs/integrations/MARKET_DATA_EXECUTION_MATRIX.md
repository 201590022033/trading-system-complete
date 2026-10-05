# Market-data and execution capability matrix

Snapshot reviewed 5 October 2026; observations are from project probes, not universal vendor guarantees. See [current state](../CURRENT_STATE.md). Preserve source/instrument, currency, timeframe, availability and price/volume basis on every import.

| Source / component | Working capability | Blocked or unverified | Execution boundary |
| --- | --- | --- | --- |
| Yahoo public charts | Daily real OHLCV archive, quotes/charts, 17 active cash shares plus four chart ETFs | Invalid individual OHLC; no licensed deep 30-minute archive or certified liquidity | Research/paper only |
| IG Demo API | Authentication, account/cash reads, tested JSE epic search | Tested equity details/DAY history returned 403 entitlement; cash-share volume semantics unverified | Read-only in current workflow; existing separate Demo gates; Live disabled |
| Alpha Vantage | Private key setup, bounded client/cache and conditional repair code | Bounded discovery did not verify JSE coverage; free compact is not 20-year history | Scheduled calls off; no execution |
| Moneyweb/SENS and configured news feed | Current policy-enabled article retrieval and persisted context | Historic dated SENS archive, completeness and pre-entry availability | Context only |
| Monday market brief | Manual derived-research import and source-linked local Ollama cases | Unverified claims/time; future automatic ChatGPT delivery not connected | Up to +0.05 research attention only after corroboration |
| Standard Bank OST / ViewPoint IRESS | Integration questions and discovery boundaries documented | Supported API, OHLCV/export rights and automated access not verified here | No automated trading connection |
| Shyft | Research notes only | Entitled historical data/export/API not verified | No connected execution |
| MT5 / EA bots | Owner option under consideration | IG account linkage, datasets and strategy validation not configured/verified here | No trained or deployed EA strategy |
| HR11 / intraday core | Horizon/session/aggregation/cost/evaluation infrastructure | Real-data admission and validated intraday strategy | Placeholder/research; cannot activate from card |
| Paper broker | Durable funded cash simulation, conservative risk and attributed outcomes | Real costs, borrow, derivative geometry and portfolio evidence | Simulator only |

Cash traded-share volume, CFD contract volume, FX tick volume and spot gold volume are different data contracts. Do not substitute one for another without an explicit proxy label and evaluation. Daily chart display or API login is not proof of intraday entitlement.

Display averaging never becomes data repair for tests/trading: estimates are flagged, volume is never invented, and strict OHLC policy admission remains closed. Sector-relative 30-minute radar and six-family local backtests remain proposed follow-up work.
