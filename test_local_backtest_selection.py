"""Locked folds, seeded fixtures and leakage attacks; no market claims."""
from dataclasses import replace
from contextlib import closing
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from pathlib import Path
import tempfile
import unittest
from domain.backtest.data import Manifest,Bar,Session
from domain.backtest.selection import Candidate,Fold,Journal,fit,observations,run_study,select
from domain.backtest.indicators import feature
from domain.backtest.engine import Costs
from domain.evaluation.experiment import InMemoryExperimentRepository,DataBoundary
import test_experiment_registry as registry_fixtures


from research.fixtures.selection_oracle import study_fixture as setup

class LocalSelectionTests(unittest.TestCase):
    def test_fixed_indicator_values_and_missing_volume(self):
        m,*_=setup()
        self.assertEqual(feature('ROC3',m.bars[:4],'EQUITY'),D(103)/100-1)
        self.assertEqual(feature('RSI14',m.bars[:15],'EQUITY'),D(100))
        self.assertEqual(feature('VOLUME20',tuple(replace(b,activity=D(1000)) for b in m.bars[:21]),'EQUITY'),1)
        self.assertIsNone(feature('VOLUME20',tuple(replace(b,activity=None) for b in m.bars[:21]),'EQUITY'))
        with self.assertRaises(ValueError): feature('VOLUME20',m.bars[:21],'FX')
        self.assertIsNone(feature('ROC3',m.bars[:3],'EQUITY'))

    def test_normalizer_fits_training_only_future_attack(self):
        m,c,f,*_=setup(); before=fit(c[0],(m,),f)
        changed=replace(m,bars=m.bars[:30]+tuple(replace(b,close=D(999999)) for b in m.bars[30:]))
        self.assertEqual(before,fit(c[0],(changed,),f))
        self.assertEqual(before['ROC3']['count'],27)

    def test_full_label_purge_is_shared_across_instruments(self):
        m,c,f,*_=setup(); normal=fit(c[-1],(m,),f)
        other=replace(m,instrument='OTHER')
        rows=observations(c[-1],normal,(m,other),f.validation_start,f.validation_end,costs=Costs())
        for r in rows:
            if r['state']!='PURGED_FULL_LABEL_INTERVAL':
                self.assertLess(datetime.fromisoformat(r['label_end']),f.validation_end-timedelta(days=1))
        by_asset={key:[r['session'] for r in rows if r['instrument']==key and r['state']=='PURGED_FULL_LABEL_INTERVAL'] for key in ('TOY','OTHER')}
        self.assertEqual(by_asset['TOY'],by_asset['OTHER']); self.assertEqual(len(by_asset['TOY']),7)

    def test_journal_budget_immutability_and_overlapping_final_period(self):
        with tempfile.TemporaryDirectory() as temp, closing(Journal(Path(temp)/'journal.db')) as j:
            j.freeze('x','hash',1); j.reserve('x','a','ca'); j.reserve('x','a','ca')
            with self.assertRaises(ValueError): j.reserve('x','b','cb')
            with self.assertRaises(ValueError): j.freeze('x','changed',1)
            j.unlock_final('x',{'instruments':['TOY'],'start':'2020-01-01','end':'2020-02-01'})
            j.freeze('y','other',1)
            with self.assertRaises(ValueError): j.unlock_final('y',{'instruments':['TOY'],'start':'2020-01-15','end':'2020-03-01'})
            j.close()

    def test_registered_run_controls_provenance_resume_and_final_lock(self):
        m,c,f,fs,fe,registry=setup()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'journal.db'; j=Journal(path)
            kwargs=dict(final_start=fs,final_end=fe,journal=j,registry=registry,code_commit='fixture-commit')
            r=run_study('study',(m,),c,(f,),**kwargs)
            self.assertEqual(len(r['trials']),4); self.assertEqual(r['promotion'],'NONE')
            self.assertEqual(r['final_period_state'],'VIEWED_LOCKED')
            self.assertEqual(len(registry.get_experiment('base','1')['runs']),1)
            for trial in r['trials']: self.assertEqual(trial[2],'COMPLETE')
            chosen=r['final_choice']; self.assertIsNone(r['final']['portfolio_drawdown'])
            self.assertIn('matched_price_only',r['final']['horizons']['3'])
            j.close(); j=Journal(path); kwargs['journal']=j
            self.assertEqual(r,run_study('study',(m,),c,(f,),**kwargs))
            with self.assertRaises(ValueError): run_study('study',(replace(m,revision='2'),),c,(f,),**kwargs)
            with self.assertRaises(ValueError): run_study('other-study',(m,),c,(f,),**kwargs)
            with self.assertRaises(ValueError): run_study('bad',(m,),c,(replace(f,train_end=f.outer_end),),**kwargs)
            j.close()

    def test_outer_changes_do_not_select_and_mismatched_registered_candidate_refused(self):
        m,c,f,fs,fe,registry=setup()
        with tempfile.TemporaryDirectory() as temp:
            j=Journal(Path(temp)/'j.db')
            normal={x.id:fit(x,(m,),f) for x in c}
            validation={x.id:__import__('domain.backtest.selection',fromlist=['summarize']).summarize(observations(x,normal[x.id],(m,),f.validation_start,f.validation_end,costs=Costs())) for x in c}
            selected=select(validation)
            # Selection only receives validation summaries; poisoned outer outcomes have no route into it.
            poisoned=replace(m,bars=m.bars[:62]+tuple(replace(b,open=D(1000),high=D(1001),low=D(999),close=D(1000)) for b in m.bars[62:]))
            normal2={x.id:fit(x,(poisoned,),f) for x in c}
            validation2={x.id:__import__('domain.backtest.selection',fromlist=['summarize']).summarize(observations(x,normal2[x.id],(poisoned,),f.validation_start,f.validation_end,costs=Costs())) for x in c}
            self.assertEqual(selected,select(validation2)); self.assertEqual(validation,validation2)
            with self.assertRaises(ValueError): run_study('changed',(m,),(replace(c[0],threshold_z=10),)+c[1:],(f,),final_start=fs,final_end=fe,journal=j,registry=registry,code_commit='x')
            j.close()

if __name__=='__main__': unittest.main()
