"""Kill deliberate defects in disposable source copies; never modify the checkout."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import test_local_backtest_engine as checks


def main():
    source=(ROOT/'domain/backtest/engine.py').read_text()
    mutations={
        'future_access':("for b in rows[m.instrument])", "for b in m.bars)"),
        'stop_order':("elif hit_stop:", "elif hit_stop and not hit_target:"),
        'duplicate_fill':("post(at,sid,'ENTRY',-capital,price=str(fill),quantity=str(qty));", "post(at,sid,'ENTRY',-capital,price=str(fill),quantity=str(qty)); post(at,sid,'ENTRY',-capital);"),
        'removed_fee':("post(at,sid,'FEE',-fee)", "post(at,sid,'FEE',ZERO)"),
    }
    killed=[]
    for name,(old,new) in mutations.items():
        if old not in source: raise RuntimeError('mutation anchor missing: '+name)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'mutant.py'; path.write_text(source.replace(old,new))
            spec=importlib.util.spec_from_file_location('disposable_mutant',path)
            module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module
            spec.loader.exec_module(module)
            original=checks.replay; checks.replay=module.replay
            try:
                result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(checks.LocalReplayTests))
            finally: checks.replay=original; sys.modules.pop(spec.name,None)
            if result.wasSuccessful(): raise RuntimeError('SURVIVED: '+name)
            killed.append({'mutation':name,'failures':len(result.failures),'errors':len(result.errors)})
    import json
    print(json.dumps({'killed':killed,'total':len(mutations)},sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
