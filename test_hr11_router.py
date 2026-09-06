import unittest
from dataclasses import replace
from datetime import timedelta
from intraday_router import preview,submit_order,cancel_order
from intraday_instruments import InstrumentRegistry
from intraday_signals import EnsembleDecision
from intraday_gates import GateResult
from provider_interfaces import LiveExecutionDisabled
from test_hr11_costs import INSTRUMENT,SCHEDULE
from test_hr11_data import bar
from test_hr11_sessions import SESSION
class RouterTests(unittest.TestCase):
    def args(self):
        b=bar(0)
        return dict(registry=InstrumentRegistry([INSTRUMENT]),instrument_id=INSTRUMENT.instrument_id,
            decision=EnsembleDecision(b.event_time,('SOL_CASH',),1,{'macd':1},{}),bar=b,session=SESSION,
            gates=GateResult({'freshness':'PASS'},(),True,False,.001),schedule=SCHEDULE,
            admission='ADMIT_FOR_CONTINUED_SHADOW',now=b.event_time,units=10)
    def test_paper_preview(self):
        result=preview(**self.args());self.assertTrue(result.accepted);self.assertEqual(result.preview.mode,'PAPER_ONLY')
        self.assertEqual(result.preview.underlying_id,'SASOL')
    def test_refusal_matrix(self):
        for change in (dict(instrument_id='UNKNOWN'),dict(admission='REJECT'),dict(schedule=None),dict(session=None),
            dict(now=bar(0).event_time+timedelta(hours=1)),dict(registry=InstrumentRegistry([replace(INSTRUMENT,enabled=False)])),
            dict(gates=GateResult({'liquidity':'FAIL'},('thin',),False,False,None))):
            args=self.args();args.update(change);self.assertFalse(preview(**args).accepted,change)
    def test_no_live_path(self):
        for function in (submit_order,cancel_order):
            with self.assertRaises(LiveExecutionDisabled):function()
