import json,unittest
from datetime import datetime,timedelta,timezone

from domain.broker.ig import IGConfig,IGMapping,IGReadOnlyAdapter,IGRequestError,IGSession
from domain.broker.ig_state import BrokerStateService
from domain.broker.paper import PaperAccount
from domain.broker.state import Freshness

UTC=timezone.utc;NOW=datetime(2026,9,11,12,tzinfo=UTC)

class IGStateTests(unittest.TestCase):
    def setUp(self):
        self.calls=[]
        self.accounts={"accounts":[{"accountId":"ACC-SECRET","accountName":"Demo","accountType":"CFD","preferred":True,"currency":"USD","status":"ENABLED","balance":{"balance":1000,"available":700,"deposit":250,"profitLoss":-50}}]}
        self.positions={"positions":[
          {"position":{"dealId":"D1","direction":"BUY","size":2,"level":75,"stopLevel":70,"limitLevel":85,"currency":"USD","contractSize":1,"createdDateUTC":"2026-09-11T08:00:00Z"},"market":{"epic":"CC.D.LCO.BMU.IP","bid":76,"offer":77,"marketStatus":"TRADEABLE"}},
          {"position":{"dealId":"D2","direction":"SELL","size":1,"level":2000,"currency":"USD","upl":-4},"market":{"epic":"CS.D.GOLD.CFD.IP","bid":1998,"offer":2001,"marketStatus":"TRADEABLE"}}]}
        def transport(method,url,headers,body,timeout):
            self.calls.append((method,url,headers))
            return (200,{},json.dumps(self.positions if url.endswith('/positions') else self.accounts).encode())
        self.adapter=IGReadOnlyAdapter(IGConfig("API_SECRET","user","PASSWORD",environment="DEMO"),transport)
        self.adapter._session=IGSession("CST_SECRET","XST_SECRET","ACC-SECRET")
        mapping=IGMapping("BRENT_IG_CFD_USD1","IG","CC.D.LCO.BMU.IP","DEMO","COMMODITY","Brent")
        self.service=BrokerStateService(self.adapter,[mapping],stale_after_seconds=60,clock=lambda:NOW)

    def test_account_normalization_preserves_currency_and_distinctions(self):
        a=self.service.get_accounts()[0];self.assertEqual(a.account_currency,"USD");self.assertEqual(a.balance,1000);self.assertEqual(a.available_funds,700);self.assertEqual(a.deposit,250);self.assertEqual(a.profit_loss,-50)
        self.assertIsNone(a.equity);self.assertIsNone(a.margin_used);self.assertIsNone(a.margin_available);self.assertIsNone(a.unrealized_pnl);self.assertTrue(a.enabled)
    def test_long_short_position_and_epic_identity(self):
        long,short=self.service.get_positions("ACC-SECRET");self.assertEqual((long.direction,long.current_level),("LONG",76));self.assertEqual((short.direction,short.current_level),("SHORT",2001));self.assertNotEqual(long.epic,short.epic);self.assertEqual(short.unrealized_pnl,-4)
    def test_resolved_and_unresolved_mapping_are_both_retained(self):
        values=self.service.get_positions("ACC-SECRET");self.assertEqual(values[0].instrument_id,"BRENT_IG_CFD_USD1");self.assertEqual(values[0].mapping_status,"RESOLVED");self.assertIsNone(values[1].instrument_id);self.assertEqual(values[1].mapping_status,"UNRESOLVED_INSTRUMENT_MAPPING")
    def test_zero_positions_is_available_not_failure(self):
        self.positions={"positions":[]};snapshot=self.service.get_broker_snapshot("ACC-SECRET");self.assertTrue(snapshot.positions_available);self.assertEqual(snapshot.position_count,0)
    def test_endpoint_failure_is_not_zero_positions(self):
        self.adapter._transport=lambda *a:(500,{},b'{"errorCode":"error.system"}')
        with self.assertRaises(IGRequestError):self.service.get_positions("ACC-SECRET")
    def test_malformed_account_and_position_responses(self):
        self.accounts={};
        with self.assertRaisesRegex(ValueError,"accounts response"):self.service.get_accounts()
        self.accounts={"accounts":[]};self.positions={}
        with self.assertRaisesRegex(ValueError,"positions response"):self.service.get_positions("ACC")
    def test_snapshot_timestamp_and_staleness(self):
        snap=self.service.get_broker_snapshot("ACC-SECRET");self.assertEqual(snap.retrieved_at,NOW);self.assertEqual(snap.freshness,Freshness.FRESH)
        self.assertEqual(self.service.get_broker_snapshot("ACC-SECRET",NOW+timedelta(seconds=61)).freshness,Freshness.STALE)
    def test_only_get_endpoints_and_versions_are_used(self):
        self.service.get_broker_snapshot("ACC-SECRET");self.assertEqual([x[0] for x in self.calls],["GET","GET"]);self.assertEqual([x[2]["Version"] for x in self.calls],["1","2"])
    def test_execution_capabilities_remain_false(self):
        caps=self.adapter.capabilities();self.assertTrue(caps["account_state"] and caps["positions"])
        for key in ("order_submission","amend","cancel","close","position_modification"):self.assertFalse(caps[key])
        for method in (self.adapter.place_order,self.adapter.amend_order,self.adapter.close_position):
            with self.assertRaises(RuntimeError):method({})
    def test_paper_state_is_distinct_and_no_risk_side_effect(self):
        account=self.service.get_accounts()[0];self.assertNotIsInstance(account,PaperAccount);self.assertEqual(account.broker,"IG");self.assertFalse(hasattr(self.service,"risk_engine"))
    def test_provenance_and_secrets(self):
        position=self.service.get_positions("ACC-SECRET")[0];self.assertEqual(position.source_endpoint,"GET /positions");self.assertEqual(position.source_version,"2")
        rendered=repr(position)
        for secret in ("API_SECRET","PASSWORD","CST_SECRET","XST_SECRET"):self.assertNotIn(secret,rendered)
    def test_live_environment_rejected(self):
        a=IGReadOnlyAdapter(IGConfig("k","u","p",environment="LIVE"),lambda *x:None)
        with self.assertRaises(RuntimeError):BrokerStateService(a,stale_after_seconds=60)

if __name__=="__main__":unittest.main()
