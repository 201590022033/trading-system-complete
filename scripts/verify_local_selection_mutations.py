"""Disposable leakage and final-lock defects, narrow independent assertions."""
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
import test_local_backtest_selection as checks


def main():
    source=(ROOT/'domain/backtest/selection.py').read_text()
    mutants=[('training_leak','v=feature(id,rows[:i+1],m.product)','v=feature(id,m.bars,m.product)','test_normalizer_fits_training_only_future_attack'),
             ('removed_purge',"if i+6>=len(rows) or rows[i+6].available_at>=cutoff:","if i+6>=len(rows):",'test_full_label_purge_is_shared_across_instruments'),
             ('final_reuse',"if owner!=study and set(old['instruments'])", "if False and owner!=study and set(old['instruments'])",'test_journal_budget_immutability_and_overlapping_final_period')]
    results=[]
    for name,old,new,test in mutants:
        if old not in source: raise RuntimeError('missing anchor '+name)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'selection_mutant.py'; path.write_text(source.replace(old,new))
            spec=importlib.util.spec_from_file_location('selection_mutant',path); module=importlib.util.module_from_spec(spec)
            sys.modules[spec.name]=module; spec.loader.exec_module(module)
            names=('fit','observations','Journal','run_study'); original={n:getattr(checks,n) for n in names}
            for n in names: setattr(checks,n,getattr(module,n))
            try:
                result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite([checks.LocalSelectionTests(test)]))
            finally:
                for n,v in original.items(): setattr(checks,n,v)
                sys.modules.pop(spec.name,None)
            if result.wasSuccessful(): raise RuntimeError('SURVIVED '+name)
            if result.errors: raise RuntimeError('mutation must fail an assertion, not infrastructure: '+name)
            results.append({'mutation':name,'failures':len(result.failures)})
    import json
    print(json.dumps({'killed':results,'total':len(results)},sort_keys=True))

if __name__=='__main__': main()
