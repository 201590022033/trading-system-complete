"""Offline HR11 research CLI. Real inputs are explicit; no synthetic default data."""
from dataclasses import asdict,replace
from datetime import datetime,timezone
from pathlib import Path
import argparse
import hashlib
import json
from intraday_instruments import DEFAULT_REGISTRY,InstrumentRegistry,InstrumentDefinition,DataGrade,VERSION as INSTRUMENT_VERSION
from intraday_data import load_jsonl,canonical_bars,VERSION as DATA_VERSION,utc
from intraday_sessions import SessionWindow,aggregate,VERSION as SESSION_VERSION
from intraday_features import compute_features,VERSION as FEATURE_VERSION
from intraday_horizons import HORIZONS,primary_horizon,VERSION as HORIZON_VERSION
from intraday_profiles import get_profile,VERSION as PROFILE_VERSION
from intraday_costs import CostSchedule,missing_cost_metadata,VERSION as COST_VERSION
from intraday_cross_asset import factor_return,join_factors,VERSION as CROSS_VERSION
from intraday_signals import ensemble,regimes,cell_key,VERSION as SIGNAL_VERSION
from intraday_gates import evaluate_gates,VERSION as GATE_VERSION
from intraday_evaluation import evaluate,EvaluationPolicy,metrics,VERSION as EVALUATION_VERSION
from intraday_robustness import prepare_cell,admit_cells,VERSION as ROBUSTNESS_VERSION
from intraday_router import VERSION as ROUTER_VERSION
from technical_feature_registry import REGISTRY_VERSION
from technical_signals import SIGNAL_DEFINITION_VERSION
VERSION='hr11-research-v1'
DEFAULT_FRAMES=('5m','15m','30m','60m')


def run_research(bars=(),sessions=None,schedules=None,registry=DEFAULT_REGISTRY,cutoff=None,timeframes=DEFAULT_FRAMES,
                 horizon_ids=None,policy=EvaluationPolicy(),primary='intraday_30m'):
    bars=canonical_bars(bars);sessions=sessions or {};schedules=schedules or {}
    cutoff=utc(cutoff or (max(b.decision_time for b in bars) if bars else datetime.now(timezone.utc)))
    primary_horizon(primary)
    horizons=tuple(h for h in HORIZONS if horizon_ids is None or h.horizon_id in horizon_ids)
    if not horizons or (horizon_ids is not None and len(horizons)!=len(set(horizon_ids))):raise ValueError('Unknown horizon selection')
    if not timeframes or any(f not in DEFAULT_FRAMES for f in timeframes):raise ValueError('Unsupported decision timeframe')
    if any(b.instrument_id not in {i.instrument_id for i in registry.instruments()} for b in bars):raise ValueError('Input contains unknown instrument')
    raw={i.instrument_id:tuple(b for b in bars if b.instrument_id==i.instrument_id and b.timeframe=='5m') for i in registry.instruments(True)}
    factors={i.signal_target_id:raw[i.instrument_id] for i in registry.instruments(True)}
    for source_id in {b.source.source_id for b in bars}:
        if len({b.source for b in bars if b.source.source_id==source_id})>1:raise ValueError('Conflicting policy for source ID')
    reports=[];regime_reports=[];trades_output=[];decisions_output=[];source_policies={b.source.source_id:asdict(b.source) for b in bars}
    for instrument in registry.instruments(True):
        iid=instrument.instrument_id;observations=raw[iid];windows=sessions.get(iid,());schedule=schedules.get(iid);profile=get_profile(instrument)
        warnings=[]
        if not observations:warnings.append('NO_REAL_5M_HISTORY')
        if not windows:warnings.append('NO_VERSIONED_SESSION_CALENDAR')
        warnings.extend(missing_cost_metadata(instrument,schedule))
        if observations and any(b.currency!=instrument.currency for b in observations):raise ValueError('Input price currency does not match instrument: '+iid)
        if any(b.delayed for b in observations):warnings.append('DELAYED_RESEARCH_DATA')
        if any(b.stale for b in observations):warnings.append('STALE_RECORDS')
        if any(b.volume is None for b in observations):warnings.append('MISSING_VOLUME_CAPABILITY')
        if any(b.bid is None for b in observations):warnings.append('NO_OBSERVED_BID_ASK')
        for frame in timeframes:
            aggregation=aggregate(observations,windows,frame,cutoff) if observations and windows else None
            decision_bars=aggregation.bars if aggregation else ()
            frame_warnings=warnings+list(aggregation.warnings if aggregation else ())
            cache={}
            benchmark_bars=()
            benchmark=next((i for i in registry.instruments(True) if instrument.benchmark_symbol and i.data_symbol==instrument.benchmark_symbol),None)
            if benchmark and raw[benchmark.instrument_id] and sessions.get(benchmark.instrument_id):
                benchmark_bars=aggregate(raw[benchmark.instrument_id],sessions[benchmark.instrument_id],frame,cutoff).bars
            def build(current,prefix,evidence,horizon_id,static=False):
                key=current.decision_time
                if key not in cache:
                    snapshot=compute_features(prefix,key,windows,benchmark_bars)
                    observations_=[]
                    for factor in profile.factors:
                        observation=factor_return(factors.get(factor,()),factor,key)
                        if observation is not None:observations_.append(observation)
                    cross=join_factors(observations_,key,profile.factors)
                    cache[key]=(snapshot,cross)
                snapshot,cross=cache[key]
                decision=ensemble(snapshot,current.close,cell_key(instrument,frame,horizon_id,regimes(snapshot)),() if static else evidence)
                session=next((s for s in windows if s.session_id==current.session_id),None)
                gates=evaluate_gates(instrument,current,session,profile,snapshot,decision,cross,schedule,policy.units)
                return decision,gates
            for horizon in horizons:
                base_key=(iid,instrument.instrument_type,frame,horizon.horizon_id,instrument.profile_id)
                if decision_bars:
                    result=evaluate(instrument,decision_bars,observations,windows,horizon,schedule,
                        lambda c,p,e:build(c,p,e,horizon.horizon_id),cutoff,policy)
                    baseline=evaluate(instrument,decision_bars,observations,windows,horizon,schedule,
                        lambda c,p,e:build(c,p,e,horizon.horizon_id,True),cutoff,policy)
                    sensitivity=[]
                    for threshold in (.15,.25):
                        variant=evaluate(instrument,decision_bars,observations,windows,horizon,schedule,
                            lambda c,p,e:build(c,p,e,horizon.horizon_id),cutoff,replace(policy,score_threshold=threshold))
                        sensitivity.append(variant.trades)
                    prepared=prepare_cell(base_key,result.trades,len(result.decisions),baseline.trades,sensitivity,frame_warnings+list(result.warnings))
                    prepared['metrics']=result.metrics
                    prepared['static_baseline_metrics']=baseline.metrics
                    for trade in result.trades:trades_output.append(trade.to_dict())
                    for record in result.decisions:
                        snapshot,cross=cache[datetime.fromisoformat(record['decision_time'])]
                        decisions_output.append(dict(record,feature_version=snapshot.version,features=snapshot.values,
                            unavailable_features=snapshot.unavailable,feature_record_ids=snapshot.input_record_ids,benchmark_record_ids=snapshot.benchmark_record_ids,
                            cross_asset_values=cross.values,unavailable_cross_asset=cross.unavailable,cross_asset_lineage=cross.lineage))
                    for regime in sorted({tuple(t.cell[5:]) for t in result.trades}):
                        match=lambda ts:tuple(t for t in ts if tuple(t.cell[5:])==regime)
                        regime_reports.append(prepare_cell((*base_key,*regime),match(result.trades),
                            sum(tuple(d['cell'][5:])==regime for d in result.decisions),match(baseline.trades),
                            tuple(match(v) for v in sensitivity),frame_warnings))
                    prepared['unavailable_cross_asset']=sorted({factor for _,cross in cache.values() for factor in cross.unavailable})
                else:
                    prepared=prepare_cell(base_key,(),warnings=frame_warnings)
                    prepared['unavailable_cross_asset']=list(profile.factors)
                prepared['data_quality']=dict(input_bars=len(observations),decision_bars=len(decision_bars),
                    delayed_bars=sum(b.delayed for b in observations),stale_bars=sum(b.stale for b in observations),
                    data_grades=sorted({b.data_grade.value for b in observations}),
                    missing_capabilities=[name for name in ('open','high','low','volume','bid','ask') if not observations or any(getattr(b,name) is None for b in observations)])
                reports.append(prepared)
    admitted=admit_cells(reports+regime_reports)
    return dict(version=VERSION,mode='RESEARCH_SHADOW_ONLY',live_execution_allowed=False,cutoff=cutoff.isoformat(),
        primary_horizon=primary,versions=dict(instruments=INSTRUMENT_VERSION,data=DATA_VERSION,sessions=SESSION_VERSION,
            technical_registry=REGISTRY_VERSION,features=FEATURE_VERSION,horizons=HORIZON_VERSION,profiles=PROFILE_VERSION,
            costs=COST_VERSION,cross_asset=CROSS_VERSION,signals=SIGNAL_VERSION,authoritative_signals=SIGNAL_DEFINITION_VERSION,
            gates=GATE_VERSION,evaluation=EVALUATION_VERSION,robustness=ROBUSTNESS_VERSION,router=ROUTER_VERSION),
        evaluation_policy=asdict(policy),instruments=[i.to_dict() for i in registry.instruments()],source_policies=source_policies,
        cost_schedules={k:asdict(v) for k,v in schedules.items()},sessions={k:[dict(session_id=s.session_id,session_date=s.session_date,
            open_time=s.open_time.isoformat(),close_time=s.close_time.isoformat(),calendar_version=s.calendar_version,
            breaks=[(a.isoformat(),b.isoformat()) for a,b in s.breaks]) for s in v] for k,v in sessions.items()},
        cells=admitted[:len(reports)],regime_cells=admitted[len(reports):],trades=trades_output,decisions=decisions_output,
        input_record_count=len(bars),input_digest=hashlib.sha256(''.join(b.record_id for b in bars).encode()).hexdigest(),
        limitations=['No live execution or accuracy claim.','Public proxy prices do not establish tradable contract specifications.',
            'Unknown costs and missing real intraday history block admission.','Zero-latency next-interval-open fills are hypothetical paper assumptions.',
            'RSI/SMA reuse existing causal bar mathematics; thresholds/windows are not calibrated for intraday profitability.',
            'Learning is conditioned on independently entered research trades; selection effects remain.',
            'Bootstrap uncertainty and block-mean normal p-values are approximate; FDR covers all reported cells and observed regimes.',
            'Cross-asset factors provide required context, not invented directional predictive weights.'])


def write_report(report,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    summary={k:v for k,v in report.items() if k not in ('trades','decisions')}
    (output/'report.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    for name in ('trades','decisions'):
        (output/(name+'.jsonl')).write_text(''.join(json.dumps(row,allow_nan=False)+'\n' for row in report[name]))
    states={state:sum(c['admission_state']==state for c in report['cells']) for state in ('REJECT','INSUFFICIENT_EVIDENCE','ADMIT_FOR_CONTINUED_SHADOW')}
    lines=['# HR11 short-term research report','',f"Mode: {report['mode']}. Input records: {report['input_record_count']}. Primary horizon: {report['primary_horizon']}.",'',
        'Admission counts: '+json.dumps(states)+'.','',
        '| Instrument | Timeframe | Horizon | Trades | Mean net | State | Reasons |','|---|---|---|---:|---:|---|---|']
    for cell in report['cells']:
        key=cell['cell'];value=cell['metrics']['mean_net_return']
        lines.append(f"| {key[0]} | {key[2]} | {key[3]} | {cell['metrics']['trade_count']} | {value if value is not None else 'unavailable'} | {cell['admission_state']} | {', '.join(cell['failure_reasons']+cell['data_quality_warnings'])} |")
    lines+=['','## Limitations','']+['- '+line for line in report['limitations']]
    (output/'report.md').write_text('\n'.join(lines)+'\n')
    return states


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,help='Canonical real-data JSONL; omitted means an honest empty-universe audit')
    parser.add_argument('--sessions',type=Path,help='JSON mapping instrument IDs to explicit session windows')
    parser.add_argument('--costs',type=Path,help='JSON list of explicit instrument cost schedules')
    parser.add_argument('--instruments',type=Path,help='JSON list of complete instrument definitions; no implicit overrides')
    parser.add_argument('--cutoff',help='Timezone-aware ISO timestamp')
    parser.add_argument('--output',type=Path,default=Path('analysis/results/hr11'))
    parser.add_argument('--primary-horizon',default='intraday_30m')
    parser.add_argument('--units',type=float,default=1)
    args=parser.parse_args();registry=DEFAULT_REGISTRY
    if args.instruments:
        definitions=[]
        for value in json.loads(args.instruments.read_text()):
            value['data_grade']=DataGrade(value['data_grade']);value['trading_hours']=tuple(value.get('trading_hours',()))
            definitions.append(InstrumentDefinition(**value))
        registry=InstrumentRegistry(definitions)
    sessions={}
    if args.sessions:
        for iid,windows in json.loads(args.sessions.read_text()).items():
            sessions[iid]=tuple(SessionWindow(w['session_id'],w['session_date'],datetime.fromisoformat(w['open_time']),datetime.fromisoformat(w['close_time']),w['calendar_version'],
                tuple((datetime.fromisoformat(a),datetime.fromisoformat(b)) for a,b in w.get('breaks',()))) for w in windows)
    schedules={}
    if args.costs:
        for value in json.loads(args.costs.read_text()):
            value['assumptions']=tuple(value['assumptions']);schedule=CostSchedule(**value)
            if schedule.instrument_id in schedules:raise ValueError('Duplicate instrument cost schedule')
            schedules[schedule.instrument_id]=schedule
    report=run_research(load_jsonl(args.input) if args.input else (),sessions,schedules,registry,
        datetime.fromisoformat(args.cutoff) if args.cutoff else None,policy=EvaluationPolicy(units=args.units),primary=args.primary_horizon)
    print(json.dumps(write_report(report,args.output),sort_keys=True))

if __name__=='__main__':main()
