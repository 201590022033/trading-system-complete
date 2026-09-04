import unittest
from app import app
from confidence_gates import GATES
from instrument_registry import resolve_instrument
from operational_intelligence import service

class OI2OperationalTests(unittest.TestCase):
    def setUp(self): self.client=app.test_client()
    def test_aliases_have_one_identity(self):
        self.assertEqual(resolve_instrument("SOL"),resolve_instrument("SASOL"))
        self.assertEqual(resolve_instrument("SHP.JO").research_symbol,"SHPJ")
    def test_all_thirty_gates_are_returned(self):
        run=service.analyze("SOL")
        self.assertEqual(sum(map(len,GATES.values())),30)
        self.assertEqual(len(run["gates"]["results"]),30)
        self.assertEqual(run["overall_state"],"PARTIAL")
    def test_legacy_path_uses_historical_data_and_is_not_actionable(self):
        run=service.analyze("NPN")
        self.assertEqual(run["components"]["technical"]["state"],"HISTORICAL")
        self.assertEqual(run["decision"]["strategy"],"characterized-legacy-v1")
        self.assertFalse(run["decision"]["actionable"])
    def test_missing_news_is_visible_not_fake(self):
        result=self.client.post('/api/analysis/SOL/news',json={}).get_json()
        self.assertFalse(result['success']); self.assertEqual(result['state'],'UNAVAILABLE')
    def test_no_order_route_accepts_handoff(self):
        result=self.client.post('/api/trade/anything/manual')
        self.assertEqual(result.status_code,409); self.assertFalse(result.get_json()['accepted'])
    def test_unknown_instrument_is_404(self):
        self.assertEqual(self.client.post('/api/analysis/NOPE').status_code,404)

if __name__ == '__main__': unittest.main()
