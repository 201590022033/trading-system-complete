# OI2 Operational Dashboard

OI2 is a thin Flask interface over `OperationalIntelligence`. The browser never
manufactures evidence: it invokes separate market, technical, news, full-analysis,
and universe-scan endpoints. An `AnalysisRun` records independently timestamped
component results, the characterized legacy decision, all 30 gates, and the
overall completeness state.

The reliable offline path is the frozen HR7 point-in-time feature dataset and is
always labelled `HISTORICAL`. Yahoo and public SENS/Moneyweb retrieval are
explicit, on-demand paths labelled `CURRENT_PUBLIC`; failures return
`UNAVAILABLE`. Mixed or missing components produce `PARTIAL` runs.

Instrument identity is centralized in `instrument_registry.py`. UI symbols,
research identifiers, Yahoo symbols, and Finnhub identifiers must not be joined
outside that registry.

There is no order-submission implementation. OI2 legacy output remains
`RESEARCH`, is non-actionable, and the manual broker controls stay disabled.
