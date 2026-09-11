"""M25 data-source-only bridge from IG v3 history to frozen HR11 research."""
from datetime import datetime, timezone

from domain.broker.ig_history import IGHistoricalSeries
from domain.evaluation.experiment import (DataBoundary, ExperimentDefinition,
    ExperimentMode, configuration_hash)
from intraday_data import IntradayBar, SourcePolicy, canonical_bars
from intraday_instruments import DataGrade

VERSION="m25-hr11-real-data-v1"
EXPERIMENT_ID="M25-HR11-IG-DATA-SOURCE-ONLY"
BASELINE_COMMIT="b080f2f0f8f7077f6861426eb4582d4c3033a149"
FROZEN_COMPONENTS=("features","signal thresholds","gates","profiles","horizons","costs","regimes","evaluation","robustness")

MODULE_CLASSIFICATION={
    "PRESERVE":("intraday_data","intraday_sessions","intraday_horizons","intraday_cross_asset","intraday_costs","intraday_evaluation","intraday_robustness","intraday_features","intraday_gates","intraday_signals","intraday_profiles","intraday_router","hr11_research"),
    "REFRACTORABLE":("m25_hr11_validation",),
    "EXPERIMENTAL":("IG REST v3 input dataset","M25 artifacts"),
}

def experiment_definition(start, end):
    config={"source":"IG REST /prices/{epic} v3","epic":"CC.D.LCO.BMU.IP","timeframe":"5m","treatment":"DATA_SOURCE_ONLY"}
    return ExperimentDefinition(EXPERIMENT_ID,VERSION,datetime(2026,9,11,tzinfo=timezone.utc),"M25 mandate",
        ExperimentMode.RETROSPECTIVE,"HR11",("BRENT_IG_CFD_USD1",),
        ("intraday_5m","intraday_15m","intraday_30m","intraday_60m","session_close"),
        "HR11_FROZEN","hr11-research-v1",BASELINE_COMMIT,(),("docs/reports/HR11_REPORT.md",),
        "No validated real intraday input was available to HR11.",
        ("HR11 default report: zero input records and 180 INSUFFICIENT_EVIDENCE cells",),
        "Frozen HR11 can produce attributable, interpretable evidence from broker-backed real data.",
        "Only data availability/source changes; research logic remains fixed.",
        "Accepted real bars yield auditable decisions/trades or explicit insufficiency without logic changes.",
        "Replace absent input with validated IG historical input.",("data_source_input_availability",),VERSION,
        configuration_hash(config),FROZEN_COMPONENTS,"HR11 report at protected baseline",
        "M16_UNCONFIGURED_TARGET","strategy-target-v1",
        ("GROSS_EXPECTANCY","NET_EXPECTANCY","HIT_RATE","AVERAGE_WIN","AVERAGE_LOSS","PAYOFF_RATIO","MAX_DRAWDOWN","CANONICAL_ANNUALIZED_SHARPE","LEGACY_TSTAT_LIKE_V1","POSITION_STATE_TURNOVER"),
        (DataBoundary("IG_CC.D.LCO.BMU.IP_5M_BOUNDED",VERSION,"RESEARCH_DATA",end,
                      validation_start=start,validation_end=end,
                      provenance="IG REST /prices/{epic} v3; no fallback"),))

def adapt_ig_series(series, instrument_id, currency, session_for_timestamp):
    """Convert accepted M12B bars only; caller must supply factual sessions."""
    if not isinstance(series,IGHistoricalSeries) or series.environment!="DEMO" or series.canonical_timeframe!="5m":
        raise ValueError("validated IG Demo 5-minute series required")
    source=SourcePolicy("IG_REST_HISTORICAL",1,"licensed",DataGrade.RESEARCH,300,"historical_publication")
    output=[]
    for value in series.bars:
        bar=value.canonical; session=session_for_timestamp(bar.interval_start)
        if session is None: raise ValueError("factual session calendar required; gaps cannot be inferred")
        output.append(IntradayBar(instrument_id,bar.interval_start,bar.event_time,bar.available_time,
            bar.available_time,series.retrieved_at,session.session_id,session.session_date,"5m",source,
            bar.close,bar.open,bar.high,bar.low,value.last_traded_volume,bar.bid,bar.ask,
            source_timestamp=bar.interval_start,currency=currency,market_state="OPEN",
            input_record_ids=bar.input_record_ids))
    return canonical_bars(output)

def classify_evidence(*, valid_context, outcome_ready_samples, net_expectancy):
    if not valid_context: return "INVALID_CONTEXT"
    if outcome_ready_samples == 0: return "INSUFFICIENT_EVIDENCE"
    return "NEGATIVE_EVIDENCE" if net_expectancy is not None and net_expectancy <= 0 else "SUPPORTED_EVIDENCE"

def unavailable_result():
    return {"experiment_id":EXPERIMENT_ID,"version":VERSION,"external_validation":"NOT RUN — CREDENTIALS UNAVAILABLE",
            "evidence_classification":"INSUFFICIENT_EVIDENCE","bars_requested":None,"bars_received":0,"bars_accepted":0,
            "metrics":{},"warnings":["No IG credentials in coding workspace","Prior HR11 missing-data interpretation unchanged","No strategy conclusion without real input"],
            "execution":"NONE","optimization":"NONE"}

__all__=["BASELINE_COMMIT","EXPERIMENT_ID","FROZEN_COMPONENTS","MODULE_CLASSIFICATION","VERSION","adapt_ig_series","classify_evidence","experiment_definition","unavailable_result"]
