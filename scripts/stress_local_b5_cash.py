"""Offline post-hoc cost/capacity diagnostic; not fills, sizing or admission."""
import argparse
from decimal import Decimal as D, ROUND_FLOOR
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from domain.backtest.costs import OSTCashShareCosts

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--comparison',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); source=json.loads(args.comparison.read_text())
    cases=[]
    for day in source['daily']:
        mid=D(str(day['iress_daily']['Close']))/100
        daily_volume=D(str(day['iress_daily']['Volume']))
        if mid<=0 or daily_volume<=0: raise ValueError('positive raw daily close/volume required')
        for budget in (1000,10000,50000,100000):
            for spread,slip in ((0,0),(10,10),(25,10),(50,25)):
                costs=OSTCashShareCosts(spread_bps=spread,slippage_bps=slip)
                buy=costs.fill(mid,1); sell=costs.fill(mid,-1)
                qty=(D(budget)/buy).to_integral_value(rounding=ROUND_FLOOR)
                while qty>0 and qty*buy+costs.fee(qty*buy,1)>budget: qty-=1
                if qty<=0: raise ValueError('budget cannot fund one share with modeled fees')
                buy_fee=costs.fee(qty*buy,1); sell_fee=costs.fee(qty*sell,-1)
                drag=(qty*(buy-sell)+buy_fee+sell_fee).quantize(D('.01'))
                cases.append(dict(date=day['date'],budget_zar=budget,full_spread_bps=spread,
                    per_side_slippage_bps=slip,quantity=str(qty),buy_fee=str(buy_fee),sell_fee=str(sell_fee),
                    flat_mid_round_trip_drag_zar=str(drag),drag_pct_budget=str(100*drag/D(budget)),
                    pct_observed_daily_volume=str(100*qty/daily_volume)))
    result={'scope':'POST_HOC_FLAT_MID_COST_AND_DAILY_CAPACITY_DIAGNOSTIC',
        'input_sha256':sha256(args.comparison.read_bytes()).hexdigest(),'days':len(source['daily']),
        'cases':cases,'case_count':len(cases),'max_pct_daily_volume':max(D(c['pct_observed_daily_volume']) for c in cases),
        'liquidity_verified':False,'real_data_admitted':False,
        'limitations':['Daily volume observed after the day is not causal sizing input or available closing-auction liquidity',
                       'No dated bid/ask, order queue, spread, impact or full-fill evidence',
                       'Current published schedule; account tier, historical applicability and invoice rounding unverified',
                       'Monthly account/data charges excluded; no performance inference']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,default=str)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},default=str))

if __name__=='__main__': main()
