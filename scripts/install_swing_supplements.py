"""Install explicit captured sources for prospective shadow research only."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.check_swing_data_readiness import recover_sasol, recover_benchmark
from scripts.collect_swing_data import attach_supplements
from application.opportunities.swing_research import validate_dataset


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iress-sasol',type=Path,required=True)
    parser.add_argument('--ost-stx40',type=Path,required=True)
    parser.add_argument('--sasol-acquired-at',required=True)
    parser.add_argument('--stx40-acquired-at',required=True)
    args=parser.parse_args()
    folder=ROOT/'runtime/local-swing-data'
    latest=folder/'latest.json'
    data=json.loads(latest.read_text(encoding='utf-8'))
    now=datetime.now(timezone.utc)
    sasol=recover_sasol(args.iress_sasol.read_bytes(),data['charts']['SASOL'],now)
    benchmark=recover_benchmark(args.ost_stx40.read_bytes(),now)
    charts={}
    for key,source,provider,origin,purpose,acquired in (
        ('SASOL',sasol,'IRESS','SOL.JSE','OHLCV',args.sasol_acquired_at),
        ('ETF_STX40',benchmark,'OST','STX40','HLCV_CLOSE_BENCHMARK',args.stx40_acquired_at)):
        charts[key]={k:source[k] for k in ('symbol','currency','interval','bars')}
        charts[key]['provenance']={'provider':provider,'origin_symbol':origin,'purpose':purpose,
            'source_sha256':source['source_sha256'],'acquired_at':acquired,
            'price_basis':'UNVERIFIED','volume_basis':'UNVERIFIED','historical_availability':'UNVERIFIED'}
    supplement={'research_charts':charts}
    combined=attach_supplements(data,supplement,now)
    if set(combined.get('research_charts',{}))!={'SASOL','ETF_STX40'}:
        raise ValueError('both current acquisition receipts required')
    # Preserve the exact pre-installation file. Future installs retain dated copies.
    backup=folder/('before-supplement-'+now.strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    backup.write_bytes(latest.read_bytes())
    normalized=validate_dataset(combined,now)
    supplement={'research_charts':normalized['research_charts']}
    for path,payload in ((folder/'supplemental.json',supplement),(latest,combined)):
        staged=path.with_suffix('.tmp')
        staged.write_text(json.dumps(payload,allow_nan=False),encoding='utf-8')
        os.replace(staged,path)
    print(json.dumps({'state':'SUPPLEMENTAL_RESEARCH_INSTALLED','canonical_charts':len(combined['charts']),
        'research_charts':list(charts),'schema':combined['schema'],'live_execution':False,'real_data_admitted':False}))


if __name__=='__main__':main()
