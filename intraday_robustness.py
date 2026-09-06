"""Conservative HR10-derived admission, separated by instrument/timeframe/horizon cell."""
from dataclasses import dataclass,asdict
import math
import numpy as np
from hr10_robustness import block_bootstrap_ci,benjamini_hochberg,_p_positive,admission_state
from intraday_evaluation import metrics
VERSION='intraday-robustness-v1'

@dataclass(frozen=True)
class RobustnessPolicy:
    minimum_trades: int=30
    minimum_folds: int=3
    minimum_regime_trades: int=5
    seed: int=20260906
    bootstrap_samples: int=1000
    version: str='intraday-robustness-policy-v1'
    def __post_init__(self):
        if self.minimum_trades<30 or self.minimum_folds<3 or self.minimum_regime_trades<1 or self.bootstrap_samples<100:raise ValueError('Conservative minimum evidence required')


def prepare_cell(key,trades,sample_count=0,baseline=(),sensitivity=(),warnings=(),policy=RobustnessPolicy()):
    trades=tuple(sorted(trades,key=lambda t:t.entry_time))
    if any(tuple(t.cell[:len(key)])!=tuple(key) for t in trades):raise ValueError('Mixed robustness cells')
    if any(a.exit_time>b.entry_time for a,b in zip(trades,trades[1:])):raise ValueError('Overlapping evidence')
    values=np.array([t.net_return for t in trades]);m=metrics(trades,sample_count)
    ci=block_bootstrap_ci(values,policy.seed,policy.bootstrap_samples) if len(values)>=2 else (None,None)
    block=max(1,int(round(math.sqrt(len(values)))))
    # Reuse HR10's one-sided normal approximation on non-overlapping block means.
    # This is approximate inference, not an exact finite-sample p-value.
    block_means=np.array([np.mean(values[i:i+block]) for i in range(0,len(values)-block+1,block)])
    p=_p_positive(block_means) if len(block_means)>=2 else 1.
    folds={f:[t.net_return for t in trades if t.fold_id==f] for f in sorted({t.fold_id for t in trades})}
    regimes={}
    for t in trades:regimes.setdefault(tuple(t.cell[5:]),[]).append(t.net_return)
    insuff=[]
    if len(trades)<policy.minimum_trades:insuff.append('MINIMUM_TRADES')
    if len(folds)<policy.minimum_folds:insuff.append('MINIMUM_FOLDS')
    if not baseline:insuff.append('MISSING_STATIC_BASELINE')
    if len(sensitivity)<2 or any(not variant for variant in sensitivity):insuff.append('MISSING_PARAMETER_SENSITIVITY')
    if not regimes or any('unknown' in key[:2] or len(v)<policy.minimum_regime_trades for key,v in regimes.items()):insuff.append('REGIME_EVIDENCE')
    return dict(cell=key,metrics=m,ci_low=ci[0],ci_high=ci[1],raw_p_value=p,adjusted_p_value=None,
        fold_means=[float(np.mean(v)) for v in folds.values()],fold_ids=list(folds),
        regime_means={ '|'.join(k):float(np.mean(v)) for k,v in regimes.items()},
        cost_stress_mean=float(np.mean([t.net_return-t.cost_fraction for t in trades])) if trades else None,
        sensitivity_means=[float(np.mean([t.net_return for t in variant])) if variant else None for variant in sensitivity],
        baseline_mean=float(np.mean([t.net_return for t in baseline])) if baseline else None,
        insufficient_reasons=insuff,data_quality_warnings=list(warnings),robustness_policy=asdict(policy),version=VERSION)


def admit_cells(cells):
    adjusted=benjamini_hochberg([cell['raw_p_value'] for cell in cells]);result=[]
    for source,q in zip(cells,adjusted):
        cell=dict(source);cell['adjusted_p_value']=q
        if cell['insufficient_reasons']:
            state='INSUFFICIENT_EVIDENCE';reasons=cell['insufficient_reasons']
        else:
            m=cell['metrics']
            state,reasons=admission_state(dict(trades=m['trade_count'],mean_net_return=m['mean_net_return'],ci_low=cell['ci_low'],maximum_drawdown=m['max_drawdown']),
                cell['fold_means'],cell['cost_stress_mean'],cell['sensitivity_means'],q,cell['baseline_mean'])
            if any(v<=0 for v in cell['regime_means'].values()):state='REJECT';reasons=list(reasons)+['regime_stability']
        cell['admission_state']=state;cell['failure_reasons']=list(reasons);cell['live_execution_allowed']=False;result.append(cell)
    return result
