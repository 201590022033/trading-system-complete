"""Offline fixture replay, decision/trade/cost/accounting exports and provenance."""
import argparse
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from domain.backtest.engine import replay,Signal,Costs
from domain.backtest.products import Forex,Gold,Conversion
from domain.evaluation.experiment import configuration_hash
from domain.evaluation.metrics import drawdown
from domain.contracts.trade import MetricContext
from research.fixtures.daily_oracle import fixture,ORACLE


def dump(path,value): path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')


def examples(output):
    output.mkdir(parents=True,exist_ok=True)
    m=fixture(); s=Signal('equity-oracle','TOY','0',m.sessions[0].close_at,D(90),D(1100),D(120))
    equity=replay((m,),(s,),as_of=m.sessions[4].close_at,initial_cash=2000,costs=Costs(minimum_fee=2))
    assert D(equity['cash'])==ORACLE['final_cash']
    dump(output/'equity-replay.json',equity)
    stress=[]
    for bps in (0,25,100):
        r=replay((m,),(replace(s,risk_budget=D(10000)),),as_of=m.sessions[4].close_at,initial_cash=2000,
                 costs=Costs(fee_bps=bps,spread_bps=bps,slippage_bps=bps))
        context=MetricContext('PERIODIC_CALENDAR','MANIFEST_SESSION','TOY',None,'FRACTION','NET','MODELED_STRESS','3','PORTFOLIO',False,None)
        metric=drawdown([2000]+[float(x['equity']) for x in r['equity']],context)
        stress.append({'fee_spread_slippage_bps_each':bps,'quantity':r['trades'][0]['quantity'],'net_pnl':r['trades'][0]['net_pnl'],
                       'cash':r['cash'],'max_drawdown':metric.to_dict(),'config_hash':r['config_hash']})
    dump(output/'cost-stress.json',stress)
    prices=[(18,18.1,17.9,18),(18,18.2,17.9,18)]+[(18,18.8,17.2,18.5)]*3
    fx=fixture(prices,'FX'); fx=replace(fx,bars=tuple(replace(b,activity=None) for b in fx.bars))
    adapter=Forex('ZAR','ZAR',fx.calendar_id,fx.sessions,(),D(1),D(2),D(1),D(1),D('.1'))
    sfx=Signal('fx-oracle','TOY','0',fx.sessions[0].close_at,D(17),D(1000),D(100))
    result=replay((fx,),(sfx,),as_of=fx.sessions[4].close_at,initial_cash=2000,costs=Costs(minimum_fee=2),adapters={'TOY':adapter})
    assert D(result['cash'])==D('2045.28'); dump(output/'fx-replay.json',result)
    gold=replace(fixture(product='GOLD',currency='USD'),instrument='XAU/USD')
    conversions=tuple(Conversion(session.key,session.open_at,D(18) if session.key!='4' else D(19)) for session in gold.sessions)
    adapter=Gold('ZAR','USD',gold.calendar_id,gold.sessions,conversions,D(0),D(0),D(10),D(1),D('.1'))
    sgold=Signal('gold-oracle','XAU/USD','0',gold.sessions[0].close_at,D(90),D(20000),D(21600))
    result=replay((gold,),(sgold,),as_of=gold.sessions[4].close_at,initial_cash=20000,costs=Costs(minimum_fee=2),adapters={'XAU/USD':adapter})
    assert D(result['cash'])==27596; dump(output/'gold-replay.json',result)
    files=sorted((ROOT/'domain/backtest').glob('*.py'))+[ROOT/'research/fixtures/daily_oracle.py']
    code_hashes={p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in files}
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    provenance={'engine':'local-daily-replay-v1','source_commit':commit,'code_file_hashes':code_hashes,
                'aggregate_code_hash':configuration_hash(code_hashes),'fixture_class':'SYNTHETIC_HAND_CALCULATED',
                'oracle':ORACLE,'real_market_fill_validation':'BLOCKED','profitability':'NOT_ESTABLISHED'}
    dump(output/'provenance.json',provenance)
    return provenance


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); info=examples(args.output)
    print(json.dumps({'output':str(args.output.resolve()),'code_hash':info['aggregate_code_hash'],'oracle_passed':True}))

if __name__=='__main__': main()
