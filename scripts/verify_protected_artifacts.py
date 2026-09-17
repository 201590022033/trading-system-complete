"""Read-only checksum verification; never regenerates research outputs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASELINE='ea3f3a7ef229f333832d2b68ebd7b3370d117379'

def verify():
    manifest=json.loads((ROOT/'docs/handoffs/2026-09-06-ARTIFACT-CHECKSUMS.json').read_text(encoding='utf-8'))
    failures=[]; normalized=0
    for name,expected in manifest['files'].items():
        baseline=subprocess.check_output(['git','show',f'{BASELINE}:{name}'],cwd=ROOT)
        current=subprocess.check_output(['git','show',f'HEAD:{name}'],cwd=ROOT)
        index=subprocess.check_output(['git','show',f':{name}'],cwd=ROOT)
        raw=(ROOT/name).read_bytes()
        work=raw.replace(b'\r\n',b'\n') if Path(name).suffix in {'.csv','.json','.md','.py','.txt'} else raw
        normalized+=raw!=work
        if hashlib.sha256(baseline).hexdigest()!=expected['sha256'] or not baseline==current==index==work:
            failures.append(name)
    return {'checked':len(manifest['files']),'line_ending_normalized':normalized,'failures':failures}

def main():
    result=verify()
    print(json.dumps(result,sort_keys=True))
    return 1 if result['failures'] else 0

if __name__=='__main__': raise SystemExit(main())
