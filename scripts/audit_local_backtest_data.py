"""Read-only admissibility audit of known local market archives; never repair data."""
import argparse
import csv
from decimal import Decimal,InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from application.opportunities.swing_data_quality import diagnostics


def audit():
    result={'scope':'LOCAL_EXISTING_ARCHIVES_ONLY','real_data_accepted':False,'real_trade_audit':None,
            'blocked_gates':['VERIFIED_SESSION_CALENDARS','CORPORATE_ACTION_AND_RAW_PRICE_CONSISTENCY',
                'HISTORICAL_IDENTITY_UNIVERSE_AND_PRICE_UNITS','POINT_IN_TIME_AVAILABILITY',
                'REAL_PRODUCT_COSTS_LIQUIDITY_AND_FULL_FILL_ENVELOPE','REAL_INTRADAY_PATH_COMPARISON',
                'FX_GOLD_PRODUCT_CONVERSION_FINANCING_AND_MARGIN_VALIDATION'],
            'sources':[],'provider_requests':0}
    path=ROOT/'runtime/local-swing-data/2026-10-04.json'
    if path.exists():
        value=json.loads(path.read_text(encoding='utf-8'))
        source={'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest(),
                'schema':value.get('schema'),'observed_at':value.get('observed_at'),'instruments':[]}
        for key,chart in sorted(value.get('charts',{}).items()):
            rows=chart.get('bars',[]); quality=diagnostics(rows)
            invalid=[]
            for row in rows:
                try:
                    o,h,l,c=(Decimal(str(row.get(k))) for k in ('open','high','low','close'))
                    good=all(x.is_finite() and x>0 for x in (o,h,l,c)) and l<=min(o,c) and h>=max(o,c)
                except (InvalidOperation,ValueError,TypeError): good=False
                if not good: invalid.append(row.get('timestamp'))
            source['instruments'].append({'id':key,'symbol':chart.get('symbol'),'currency':chart.get('currency'),
                'bars':len(rows),'first_session':rows[0].get('timestamp') if rows else None,
                'last_session':rows[-1].get('timestamp') if rows else None,
                'invalid_ohlc_count':len(invalid),'first_invalid_sessions':invalid[:5],
                'missing_activity_count':sum(r.get('volume') is None for r in rows),
                'zero_activity_count':sum(r.get('volume')==0 for r in rows),
                'existing_quality_diagnostics':quality,'admission':'BLOCKED_UNVERIFIED_MANIFEST_CONTRACTS'})
        source['total_bars']=sum(x['bars'] for x in source['instruments'])
        source['invalid_ohlc_count']=sum(x['invalid_ohlc_count'] for x in source['instruments'])
        result['sources'].append(source)
    for name in ('abspj','npn','usdzar','gold'):
        path=ROOT/f'analysis/data/hr2/{name}.csv'
        if not path.exists(): continue
        with path.open(encoding='utf-8',newline='') as stream: rows=list(csv.DictReader(stream))
        result['sources'].append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest(),
            'rows':len(rows),'columns':list(rows[0]) if rows else [],
            'first_event_time':rows[0].get('event_time') if rows else None,'last_event_time':rows[-1].get('event_time') if rows else None,
            'availability_basis':'RECONSTRUCTED_HISTORICAL_NOT_POINT_IN_TIME',
            'admission':'BLOCKED_NO_VERIFIED_CALENDAR_ACTION_PRODUCT_COST_MANIFEST'})
    path=ROOT/'artifacts/research/m25_hr11_real_data/run_manifest.json'
    if path.exists():
        value=json.loads(path.read_text(encoding='utf-8'))
        result['sources'].append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest(),
            'bars_accepted':value.get('bars_accepted'),'outcome_ready_samples':value.get('outcome_ready_samples'),
            'admission':'NO_ADMITTED_INTRADAY_SLICE'})
    result['resolution']='Acquire versioned source-verified calendars, raw/action/identity/unit manifests, historical availability assumptions, dated costs/liquidity and actual intraday/product evidence; then audit immutable admitted windows. Do not repair mismatched OHLC with estimates or admit display averages.'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); report=audit(); args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'sources':len(report['sources']),'real_data_accepted':False,'blocked_gates':report['blocked_gates']}))

if __name__=='__main__': main()
