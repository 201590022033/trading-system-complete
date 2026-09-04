# UI Human Review Checklist

## Start locally

From the repository root:

```bash
.venv/bin/python app.py
```

Open `http://127.0.0.1:5000/`. This page is a simulated ticker prototype. It
does not display HR9/HR10 recommendations and does not use live market data.

## Current routes and data flow

- `/`: single inline Flask template containing the ticker table.
- `/api/snapshot`: simulated snapshot with explicit `SIMULATED`, `RESEARCH`,
  and `live: false` metadata.
- `/health`: process health and simulated-state metadata.
- Socket.IO `ticker_update`: one-second in-memory random-walk prices from
  `INSTRUMENTS` in `app.py`; no broker, research artifact or credential access.

## Review questions

- Can I immediately tell this is simulated research data, not live data?
- Can I tell immediately which instrument I am looking at?
- Can I find a suggested BUY / SELL / NO TRADE direction? (Currently absent.)
- Can I see the intended horizon? (Currently absent.)
- Can I tell how strong or weak the evidence is, and why? (Currently absent.)
- Can I distinguish model confidence from historical return? (Currently absent.)
- Can I see downside, stop, target, position sizing and maximum risk? (Absent.)
- Can I see data source, age and timestamp? (Simulation state/time only.)
- Is anything visually prominent that does not help a decision?
- What is needed immediately before placing a manual trade?

## Feedback → future task

| Screen/element | Clear/confusing/redundant | Desired change | Priority | Safety/data dependency |
|---|---|---|---|---|
| | | | | |

Future decision screen priority: instrument; BUY/SELL/NO TRADE; horizon; price
and timestamp; entry/stop/target; risk and size; evidence; rationale; execution
availability. Diagnostics should be secondary. This is a concept, not a live UI.
