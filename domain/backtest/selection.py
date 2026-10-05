"""Local chronological research runner; selection never reads outer/final outcomes."""
from dataclasses import dataclass, asdict, replace
from datetime import datetime, timedelta
from decimal import Decimal as D
import json
import math
import random
import sqlite3
from statistics import mean, pstdev
from domain.backtest.indicators import feature, CATALOGUE
from domain.backtest.engine import replay, Signal, Costs, atr
from domain.evaluation.experiment import configuration_hash, utc, ExperimentRun, ExperimentResult, ExperimentStage
from domain.evaluation.metrics import expectancy
from domain.contracts.trade import MetricContext
from domain.strategy.attribution import fields

VERSION='local-indicator-selection-v1'


@dataclass(frozen=True)
class Candidate:
    id: str
    experiment_id: str
    experiment_version: str
    change: str
    indicators: tuple[str,...]
    threshold_z: float = 0.0

    def __post_init__(self):
        if self.change not in ('BASELINE','ADD','REPLACE','REMOVE','CONTROL') or not self.id or not self.experiment_id:
            raise ValueError('registered bounded candidate required')
        if not isinstance(self.indicators,tuple) or len(set(self.indicators))!=len(self.indicators) or not math.isfinite(self.threshold_z):
            raise ValueError('immutable unique indicators and finite threshold required')
        if any(i not in {p.id for p in CATALOGUE} for i in self.indicators): raise ValueError('unknown indicator')

    @property
    def sha256(self): return configuration_hash(asdict(self))


@dataclass(frozen=True)
class Fold:
    id: str
    train_start: datetime
    train_end: datetime
    validation_start: datetime
    validation_end: datetime
    outer_start: datetime
    outer_end: datetime
    embargo_days: int = 1

    def __post_init__(self):
        for name in ('train_start','train_end','validation_start','validation_end','outer_start','outer_end'):
            object.__setattr__(self,name,utc(getattr(self,name),name))
        if not self.id or self.embargo_days<0 or not self.train_start<self.train_end<self.validation_start<self.validation_end<self.outer_start<self.outer_end:
            raise ValueError('strict chronological disjoint fold required')


class Journal:
    """Local durable append-only attempts and final lock. No production DB use."""
    def __init__(self,path):
        self.db=sqlite3.connect(str(path))
        self.db.execute('CREATE TABLE IF NOT EXISTS studies(id TEXT PRIMARY KEY, hash TEXT NOT NULL, budget INTEGER NOT NULL, final_used INTEGER NOT NULL DEFAULT 0, report TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS trials(study TEXT, trial TEXT, config TEXT NOT NULL, state TEXT NOT NULL, PRIMARY KEY(study,trial))')
        self.db.commit()

    def freeze(self,id,hash,budget):
        with self.db:
            row=self.db.execute('SELECT hash,budget,report FROM studies WHERE id=?',(id,)).fetchone()
            if row:
                if row[:2]!=(hash,budget): raise ValueError('study frozen: changed inputs require a new study and fresh final period')
                return json.loads(row[2]) if row[2] else None
            self.db.execute('INSERT INTO studies(id,hash,budget) VALUES(?,?,?)',(id,hash,budget))

    def reserve(self,study,trial,config):
        with self.db:
            row=self.db.execute('SELECT config FROM trials WHERE study=? AND trial=?',(study,trial)).fetchone()
            if row:
                if row[0]!=config: raise ValueError('trial immutable')
                return
            budget=self.db.execute('SELECT budget FROM studies WHERE id=?',(study,)).fetchone()[0]
            count=self.db.execute('SELECT count(*) FROM trials WHERE study=?',(study,)).fetchone()[0]
            if count>=budget: raise ValueError('trial budget exhausted')
            self.db.execute('INSERT INTO trials VALUES(?,?,?,?)',(study,trial,config,'RESERVED'))

    def complete_trial(self,study,trial):
        with self.db: self.db.execute("UPDATE trials SET state='COMPLETE' WHERE study=? AND trial=?",(study,trial))

    def unlock_final(self,study,period):
        # A period may be inspected by one frozen study only, across restarts.
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS final_periods(hash TEXT PRIMARY KEY, study TEXT NOT NULL, period TEXT NOT NULL)')
            for owner,text in self.db.execute('SELECT study,period FROM final_periods'):
                old=json.loads(text)
                if owner!=study and set(old['instruments']) & set(period['instruments']) and old['start']<period['end'] and period['start']<old['end']:
                    raise ValueError('final period contaminated by earlier study')
            self.db.execute('INSERT OR IGNORE INTO final_periods VALUES(?,?,?)',(configuration_hash(period),study,json.dumps(period,sort_keys=True)))
            self.db.execute('UPDATE studies SET final_used=1 WHERE id=?',(study,))

    def save(self,study,report):
        text=json.dumps(report,sort_keys=True,separators=(',',':'),allow_nan=False)
        with self.db:
            old=self.db.execute('SELECT report FROM studies WHERE id=?',(study,)).fetchone()[0]
            if old and old!=text: raise ValueError('frozen report cannot be rewritten')
            self.db.execute('UPDATE studies SET report=? WHERE id=?',(text,study))

    def trials(self,study): return self.db.execute('SELECT trial,config,state FROM trials WHERE study=? ORDER BY trial',(study,)).fetchall()
    def close(self): self.db.close()


def fit(candidate,manifests,fold):
    """Fit pooled feature location/scale ONLY from training timestamps."""
    normal={}
    for id in candidate.indicators:
        values=[]
        for m in manifests:
            rows=m.admit(m.sessions[0].key,m.sessions[-1].key,fold.train_end)
            for i,b in enumerate(rows):
                if fold.train_start<=b.available_at<fold.train_end:
                    v=feature(id,rows[:i+1],m.product)
                    if v is not None: values.append(float(v))
        normal[id]=dict(mean=mean(values) if values else None,scale=pstdev(values) if len(values)>1 else 0,
                        count=len(values),fit_end=fold.train_end.isoformat())
    return normal


def observations(candidate,normal,manifests,start,end,*,costs,embargo_days=1,adapters=None):
    """All eligible denominators, setup rejects and matched price-only controls.

    Purge by the full maximum label interval (signal -> next-close entry -> five
    sessions). Use the same boundary across instruments. Feature prefixes are
    backward-only; delayed bars cannot become earlier inputs. Returns diagnostic
    event studies, explicitly separate from a cash portfolio.
    """
    records=[]
    cutoff=end-timedelta(days=embargo_days)
    for m in manifests:
        rows=m.admit(m.sessions[0].key,m.sessions[-1].key,end)
        for i,b in enumerate(rows):
            if not start<=b.available_at<end: continue
            row=dict(instrument=m.instrument,session=b.session,decision_at=b.available_at.isoformat(),state='NO_SETUP',radar=None,outcomes={})
            if i+6>=len(rows) or rows[i+6].available_at>=cutoff:
                row['state']='PURGED_FULL_LABEL_INTERVAL'; records.append(row); continue
            row['label_end']=rows[i+6].available_at.isoformat()
            prefix=rows[:i+1]; a=atr(prefix,3)
            if i<3 or a is None:
                row['state']='WARMUP'; records.append(row); continue
            rv=feature('VOLUME20',prefix,m.product) if m.product=='EQUITY' else None
            row['radar']=None if rv is None else rv>=D('1.5')
            row['price_setup']=D(b.close)>max(D(x.high) for x in rows[i-3:i])
            observed={id:feature(id,prefix,m.product) for id in candidate.indicators}
            row['features']={id:None if v is None else str(v) for id,v in observed.items()}
            usable=all(v is not None and normal[id]['mean'] is not None for id,v in observed.items())
            selected=usable and all((float(v)-normal[id]['mean'])/(normal[id]['scale'] or 1)>=candidate.threshold_z for id,v in observed.items())
            row['state']='SELECTED' if row['price_setup'] and selected else ('FEATURE_UNAVAILABLE' if not usable else 'CONTROL_REJECTED')
            # Matched controls keep the same price setup even if an indicator rejects it.
            if row['price_setup']:
                stop=D(b.close)-a
                if stop<=0: row['state']='INVALID_GEOMETRY'
                else:
                    for h in (3,4,5):
                        s=Signal(configuration_hash(dict(candidate=candidate.id,instrument=m.instrument,session=b.session,horizon=h)),m.instrument,b.session,b.available_at,
                                 stop,D(10000),D(100),horizon=h)
                        r=replay((m,),(s,),as_of=rows[i+1+h].available_at,initial_cash=20000,account_currency=(adapters[m.instrument].account_currency if adapters else m.currency),costs=costs,adapters=adapters)
                        if r['trades']:
                            t=r['trades'][0]; capital=-sum(D(x['amount']) for x in r['ledger'] if x['kind']=='ENTRY')
                            row['outcomes'][str(h)]={'net_return':float(D(t['net_pnl'])/capital),'net_pnl':t['net_pnl'],
                                'reason':t['reason'],'ambiguous':t['ambiguous'],'exit_session':t['exit_session']}
                        else: row['outcomes'][str(h)]={'net_return':None,'state':'UNRESOLVED_OR_INVALIDATED'}
            records.append(row)
    return sorted(records,key=lambda r:(r['decision_at'],r['instrument']))


def summarize(records):
    result={'denominator':len(records),'selected':sum(r['state']=='SELECTED' for r in records),'horizons':{},
            'states':{state:sum(r['state']==state for r in records) for state in sorted({r['state'] for r in records})},
            'portfolio_drawdown':None,'uncertainty':'UNAVAILABLE_INSUFFICIENT_INDEPENDENT_EPISODES','annualization':None}
    # Across assets, transitive overlapping full label intervals are one episode.
    groups=[]
    for r in records:
        if r['state']!='SELECTED' or 'label_end' not in r: continue
        start=datetime.fromisoformat(r['decision_at']); end=datetime.fromisoformat(r['label_end'])
        if not groups or start>groups[-1][1]: groups.append([start,end,[r]])
        else: groups[-1][1]=max(end,groups[-1][1]); groups[-1][2].append(r)
    result['independent_episodes']=len(groups)
    for h in ('3','4','5'):
        def values(cohort): return [r['outcomes'][h]['net_return'] for r in records if cohort(r) and h in r['outcomes'] and r['outcomes'][h]['net_return'] is not None]
        selected=values(lambda r:r['state']=='SELECTED')
        matched=values(lambda r:bool(r.get('price_setup')))
        cohorts={'selected':selected,'matched_price_only':matched,
                 'radar':values(lambda r:r['state']=='SELECTED' and r['radar'] is True),
                 'non_radar':values(lambda r:r['state']=='SELECTED' and r['radar'] is False)}
        result['horizons'][h]={k:dict(count=len(v),net_expectancy=mean(v) if v else None,hit_rate=sum(x>0 for x in v)/len(v) if v else None) for k,v in cohorts.items()}
        if len(groups)>=3:
            means=[mean([r['outcomes'][h]['net_return'] for r in g[2] if h in r['outcomes'] and r['outcomes'][h]['net_return'] is not None]) for g in groups if any(h in r['outcomes'] and r['outcomes'][h]['net_return'] is not None for r in g[2])]
            if len(means)>=3:
                rng=random.Random(7); samples=sorted(mean(rng.choices(means,k=len(means))) for _ in range(500))
                result['horizons'][h]['episode_mean_bootstrap_95']=[samples[12],samples[487]]
                result['uncertainty']='EXPLORATORY_CLUSTER_BOOTSTRAP_NO_PROMOTION'
    return result


def select(validation):
    # Fixed preregistered 3-session net expectancy, never highest win rate/horizon.
    eligible=[(v['horizons']['3']['selected']['net_expectancy'],id) for id,v in validation.items() if v['horizons']['3']['selected']['net_expectancy'] is not None]
    return sorted(eligible,key=lambda x:(-x[0],x[1]))[0][1] if eligible else None


def run_study(study_id,manifests,candidates,folds,*,final_start,final_end,journal,registry,code_commit,
              costs=Costs(),trial_budget=4,adapters=None):
    manifests=tuple(manifests); candidates=tuple(candidates); folds=tuple(folds)
    final_start=utc(final_start,'final_start'); final_end=utc(final_end,'final_end')
    if not candidates or len(candidates)>trial_budget or not 1<=trial_budget<=8 or not folds or final_start>=final_end:
        raise ValueError('bounded registered design required')
    if len({c.id for c in candidates})!=len(candidates) or len({f.id for f in folds})!=len(folds): raise ValueError('unique IDs required')
    baselines=[c for c in candidates if c.change=='BASELINE']
    if len(baselines)!=1 or not any(not c.indicators for c in candidates):
        raise ValueError('one baseline and price-only control required')
    base=set(baselines[0].indicators)
    for c in candidates:
        ids=set(c.indicators)
        valid=(c.change=='BASELINE' or
               c.change=='CONTROL' and not ids or
               c.change=='ADD' and base<ids and len(ids-base)==1 or
               c.change=='REMOVE' and ids<base and len(base-ids)==1 or
               c.change=='REPLACE' and len(ids-base)==len(base-ids)==1)
        if not valid: raise ValueError('single bounded indicator treatment required')
    if any(a.outer_end>=b.outer_start for a,b in zip(folds,folds[1:])) or max(f.outer_end for f in folds)>=final_start:
        raise ValueError('outer/final chronological periods overlap')
    definitions={c.id:registry.get_experiment(c.experiment_id,c.experiment_version)['definition'] for c in candidates}
    if len({m.product for m in manifests})!=1 or len({d.strategy_family for d in definitions.values()})!=1:
        raise ValueError('independent hypothesis/product studies required')
    for c in candidates:
        if definitions[c.id].treatment_config_hash!=c.sha256: raise ValueError('candidate differs from registered definition')
        if set(m.instrument for m in manifests)-set(definitions[c.id].instrument_scope): raise ValueError('instrument scope outside registry')
        # Registry carries exact lineage; runner enforces training/validation/OOS boundaries additionally.
        for m in manifests:
            bounds=[b for b in definitions[c.id].data_boundaries if b.dataset_id==m.instrument and b.dataset_version==m.sha256]
            for f in folds:
                if not any(b.train_start==f.train_start and b.train_end==f.train_end and b.validation_start==f.validation_start and b.validation_end==f.validation_end and b.oos_start==f.outer_start and b.oos_end==f.outer_end for b in bounds):
                    raise ValueError('every dataset/fold must match registered boundaries')
            if not any(b.oos_start==final_start and b.oos_end==final_end for b in bounds):
                raise ValueError('registered locked final boundary required')
    config=configuration_hash(dict(version=VERSION,datasets={m.instrument:m.sha256 for m in manifests},candidates=[asdict(c) for c in candidates],folds=[asdict(f) for f in folds],final_start=final_start,final_end=final_end,costs=asdict(costs),code_commit=code_commit,adapters={k:a.configuration() for k,a in (adapters or {}).items()}))
    cached=journal.freeze(study_id,config,trial_budget*len(folds))
    if cached: return cached
    report={'version':VERSION,'study_id':study_id,'config_hash':config,'code_commit':code_commit,'folds':[],
            'diagnostic_event_study':True,'execution_enabled':False,'promotion':'NONE',
            'multiplicity':'BOUNDED_EXPLORATORY_ALL_TRIALS_RETAINED_NO_SIGNIFICANCE_CLAIM','dataset_hashes':{m.instrument:m.sha256 for m in manifests}}
    for fold in folds:
        normals={}; validation={}; records={}
        for c in candidates:
            trial=fold.id+':'+c.id; journal.reserve(study_id,trial,c.sha256)
            normal=fit(c,manifests,fold); normals[c.id]=normal
            rows=observations(c,normal,manifests,fold.validation_start,fold.validation_end,costs=costs,embargo_days=fold.embargo_days,adapters=adapters)
            validation[c.id]=summarize(rows); records[c.id]=rows
            journal.complete_trial(study_id,trial)
        winner=select(validation)
        # The control and baseline are evaluated, but cannot affect selection afterward.
        tested=[c for c in candidates if c.id==winner or c.change in ('BASELINE','CONTROL')]
        outer={c.id:observations(c,normals[c.id],manifests,fold.outer_start,fold.outer_end,costs=costs,embargo_days=fold.embargo_days,adapters=adapters) for c in tested}
        report['folds'].append(dict(id=fold.id,normalizers=normals,validation=validation,validation_records=records,selected=winner,
                                    outer={id:summarize(rows) for id,rows in outer.items()},outer_records=outer))
    chosen=report['folds'][-1]['selected']; last=folds[-1]
    report['final_choice']=chosen
    report['final_period_state']='UNAVAILABLE_NO_VALIDATION_SELECTION' if chosen is None else 'VIEWED_LOCKED'
    if chosen:
        journal.unlock_final(study_id,dict(instruments=sorted(m.instrument for m in manifests),start=final_start.isoformat(),end=final_end.isoformat()))
        c=next(c for c in candidates if c.id==chosen)
        rows=observations(c,report['folds'][-1]['normalizers'][chosen],manifests,final_start,final_end,costs=costs,embargo_days=last.embargo_days,adapters=adapters)
        report['final']=summarize(rows); report['final_records']=rows
    # Export provenance into established registry records, rather than a new vocabulary.
    for c in candidates:
        definition=definitions[c.id]; run_id=configuration_hash(dict(study=study_id,candidate=c.id,config=config)); attribution=fields(definition)
        existing=registry.get_experiment(c.experiment_id,c.experiment_version)
        if any(r.run_id==run_id for r in existing['runs']): continue
        run=ExperimentRun(run_id,c.experiment_id,c.experiment_version,final_end,final_end,code_commit,VERSION,'OFFLINE_LOCAL',
            {m.instrument:m.sha256 for m in manifests},tuple(p.version for p in CATALOGUE if p.id in c.indicators),None,'explicit-cost-v1',7,c.sha256,final_end,ExperimentStage.WALK_FORWARD,**attribution)
        registry.record_run(run)
        rows=[r for fold in report['folds'] for r in fold['validation_records'][c.id] if r['state']=='SELECTED' and '3' in r['outcomes'] and r['outcomes']['3']['net_return'] is not None]
        context=MetricContext('TRADE_BY_TRADE','3_SESSIONS','MANIFEST_CALENDARS',None,'DECIMAL_RETURN','NET','MODELED_BASE','3','STRATEGY',True,None,**attribution)
        metric=expectancy([r['outcomes']['3']['net_return'] for r in rows],context,minimum_sample=50)
        result=ExperimentResult(run_id+':result',run_id,final_end,{'net_expectancy':metric.value},{'net_expectancy':context},
            definition.strategy_target_id,definition.strategy_target_version,None,{'events':len(rows)},
            {'status':'INSUFFICIENT_INDEPENDENT_EPISODES'},{},{},ExperimentStage.VALIDATION,(),(),
            ('OVERLAPPING_EVENT_STUDY_NOT_PORTFOLIO','BOUNDED_EXPLORATORY_NOT_PROMOTABLE'),('HYPOTHETICAL_COSTS',),canonical_metrics=(metric,),**attribution)
        registry.record_result(result)
    report['trials']=[list(r) for r in journal.trials(study_id)]
    report['semantic_hash']=configuration_hash(report); journal.save(study_id,report)
    return report
