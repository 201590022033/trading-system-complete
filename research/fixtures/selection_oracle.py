"""Entirely synthetic reproducible study, explicit research lineage and registry."""
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from domain.backtest.data import Manifest,Bar,Session
from domain.backtest.selection import Candidate,Fold
from domain.evaluation.experiment import InMemoryExperimentRepository,DataBoundary,ExperimentDefinition,ExperimentMode


def study_fixture(code_commit='synthetic-fixture'):
    start=datetime(2020,1,1,tzinfo=timezone.utc)
    sessions=tuple(Session(str(i),start+timedelta(days=i,hours=7),start+timedelta(days=i,hours=15)) for i in range(130))
    bars=tuple(Bar(s.key,s.close_at,D(100+i),D('100.2')+i,D('99.8')+i,D(100+i),D(1000 if i%3 else 2000)) for i,s in enumerate(sessions))
    m=Manifest('TOY','EQUITY','ZAR','SYNTHETIC',sessions[-1].close_at,'RAW','TRADED_SHARES','TOY_DAILY',True,'SYNTHETIC','FIXED','NONE_VERIFIED','1',sessions,bars)
    candidates=(Candidate('base','base','1','BASELINE',('ROC3',)),Candidate('add','add','1','ADD',('ROC3','VOLUME20')),
                Candidate('replace','replace','1','REPLACE',('RSI14',)),Candidate('remove','remove','1','REMOVE',()))
    fold=Fold('f1',start,start+timedelta(days=30),start+timedelta(days=32),start+timedelta(days=60),
              start+timedelta(days=62),start+timedelta(days=90))
    fs=start+timedelta(days=92); fe=start+timedelta(days=125)
    boundaries=(DataBoundary('TOY',m.sha256,'SYNTHETIC',fe,fold.train_start,fold.train_end,fold.validation_start,fold.validation_end,fold.outer_start,fold.outer_end,provenance='HAND_AUTHORED_TOY'),
                DataBoundary('TOY',m.sha256,'SYNTHETIC',fe,oos_start=fs,oos_end=fe,provenance='LOCKED_SYNTHETIC_FINAL'))
    registry=InMemoryExperimentRepository()
    for c in candidates:
        definition=ExperimentDefinition(c.experiment_id,c.experiment_version,start-timedelta(days=1),'offline-fixture',ExperimentMode.RETROSPECTIVE,
            'H1_SYNTHETIC',('TOY',),('3','4','5'),'simple-price','1',code_commit,(),('synthetic-oracle',),
            'Need causal runner correctness',('hand-authored fixture',),'One bounded indicator change affects net event expectancy',
            'Causal momentum/activity filter','Later held-out net expectancy differs',c.change,('indicator_selection',),'1',c.sha256,
            ('replay','costs','folds'),'remove','research-target','1',('NET_EXPECTANCY',),boundaries,
            strategy_profile_id='local_swing_research',strategy_profile_version='0.1.0')
        registry.register_definition(definition)
    return m,candidates,fold,fs,fe,registry
