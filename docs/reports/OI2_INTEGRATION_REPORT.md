# OI2 Integration Report

## Outcome

The simulated inline prototype has been replaced by an operational analysis
surface backed by existing historical data and the characterized legacy scoring
function. It supports full analysis, isolated technical/news actions, a universe
scan, research context, and system status.

## Truthfulness and safety

The offline default is `HISTORICAL`; public network adapters are on demand.
Component failures remain `UNAVAILABLE`, make the combined result `PARTIAL`, and
do not erase successful technical/market evidence. Gate counts are evidence
support, not predictive accuracy. HR10 remains the no-trade boundary. Decisions
are `RESEARCH` and non-actionable, broker buttons are disabled, and the server
has no submit/cancel route.

## Verification

The safe offline suite passed 104 tests. Unfiltered discovery additionally found
two known environment-dependent import failures: the optional Ollama package is
absent and the LLM availability script exits when its service is unavailable.
These were excluded alongside credential/network/browser probes. Python compile
and `git diff --check` passed. A real local server returned HTTP 200 for `/health`
and `POST /api/analysis/SOL`; the response contained 30 gates, `PARTIAL` state,
and `actionable: false`.

## Deliberate omissions

No local trade journal is created because there is no actionable suggestion to
hand off. No credentials were read, no live broker connection was attempted, and
no claim of accuracy or strategy promotion is made.
