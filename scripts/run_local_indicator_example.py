"""Run bounded synthetic indicator trials without providers, models or secrets."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from domain.backtest.selection import Journal,run_study
from domain.backtest.engine import Costs
from research.fixtures.selection_oracle import study_fixture


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    m,c,f,fs,fe,registry=study_fixture(commit)
    journal=Journal(args.output/'trial-journal.sqlite')
    try:
        report=run_study('synthetic-indicators-v1',(m,),c,(f,),final_start=fs,final_end=fe,journal=journal,registry=registry,code_commit=commit,costs=Costs(minimum_fee=2))
        (args.output/'indicator-study.json').write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        definitions=[asdict(d) for d in registry.list_experiments()]
        (args.output/'experiment-definitions.json').write_text(json.dumps(definitions,sort_keys=True,indent=2,default=str)+'\n',encoding='utf-8')
        print(json.dumps({'semantic_hash':report['semantic_hash'],'final_state':report['final_period_state'],'promotion':'NONE'}))
    finally: journal.close()

if __name__=='__main__': main()
