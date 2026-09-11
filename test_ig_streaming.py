import unittest
from datetime import datetime, timedelta, timezone

from domain.broker.ig import IGConfig, IGMapping, IGReadOnlyAdapter, IGSession
from domain.broker.ig_streaming import IGMarketStream, MID_RULE
from domain.market_data.streaming import OrderingState, RawMarketUpdate, StreamStatus

UTC=timezone.utc
NOW=datetime(2026,9,11,10,tzinfo=UTC)

class Transport:
    def __init__(self, fail=False): self.calls=[]; self.fail=fail
    def connect(self,*args):
        self.calls.append(("connect",)+args)
        if self.fail: raise RuntimeError("token=secret")
    def subscribe(self,*args): self.calls.append(("subscribe",)+args[:2])
    def unsubscribe(self,*args): self.calls.append(("unsubscribe",)+args)
    def disconnect(self): self.calls.append(("disconnect",))

def adapter(environment="DEMO"):
    value=IGReadOnlyAdapter(IGConfig("API_SECRET","user","PASSWORD",environment=environment),lambda *a:None)
    value._session=IGSession("CST_SECRET","XST_SECRET","ACC","https://demo-apd.marketdatasystems.com")
    return value

def mapping(cid="BRENT",epic="CC.D.LCO.BMU.IP",environment="DEMO"):
    return IGMapping(cid,"IG",epic,environment,"COMMODITY","Brent")

class IGStreamingTests(unittest.TestCase):
    def setUp(self):
        self.transport=Transport(); self.stream=IGMarketStream(adapter(),[mapping()],transport=self.transport,stale_after_seconds=30)
        self.sub=self.stream.subscriptions[0]
    def raw(self, values=None, at=NOW, sequence=None):
        return RawMarketUpdate(self.sub.subscription_id,self.sub.epic,values or {"BID":"75","OFFER":"76","MARKET_STATE":"TRADEABLE","UTM":str(int(at.timestamp()*1000))},at,sequence)

    def test_capability_is_streaming_but_never_execution(self):
        caps=adapter().capabilities(); self.assertTrue(caps["streaming"]); self.assertFalse(caps["order_submission"])
    def test_demo_only_and_mapping_required(self):
        with self.assertRaises(RuntimeError): IGMarketStream(adapter("LIVE"),[])
        with self.assertRaises(ValueError): self.stream.subscribe(object())
        with self.assertRaises(ValueError): self.stream.subscribe(mapping(environment="LIVE"))
    def test_subscription_uses_official_price_item_and_fields(self):
        self.stream.connect(); call=self.transport.calls[1]
        self.assertEqual(call[1],"PRICE:ACC:CC.D.LCO.BMU.IP"); self.assertIn("BID",call[2]); self.assertIn("OFFER",call[2])
    def test_source_prices_mid_spread_status_and_provenance(self):
        obs=self.stream.receive(self.raw(sequence="7")); self.assertEqual((obs.bid,obs.ask,obs.mid,obs.spread),(75,76,75.5,1)); self.assertEqual(obs.market_status,"TRADEABLE"); self.assertIn(MID_RULE,obs.provenance); self.assertEqual(obs.data_grade,"RESEARCH_DATA")
    def test_utc_and_receipt_time_are_distinct(self):
        source=NOW-timedelta(seconds=2); obs=self.stream.receive(self.raw({"BID":1,"OFFER":2,"UTM":source.timestamp()*1000},NOW)); self.assertEqual(obs.source_timestamp,source); self.assertEqual(obs.received_at,NOW)
        no_source=self.stream.receive(self.raw({"BID":1,"OFFER":2},NOW)); self.assertIsNone(no_source.source_timestamp); self.assertEqual(no_source.timestamp_basis,"RECEIPT_TIME_ONLY")
    def test_duplicate_out_of_order_and_repeated_are_explicit(self):
        first=self.raw(sequence="1"); self.assertEqual(self.stream.receive(first).ordering_state,OrderingState.FIRST); self.assertEqual(self.stream.receive(first).ordering_state,OrderingState.DUPLICATE)
        repeated=self.raw({"BID":75,"OFFER":76,"MARKET_STATE":"TRADEABLE","UTM":(NOW+timedelta(seconds=1)).timestamp()*1000},NOW+timedelta(seconds=1),"2"); self.assertEqual(self.stream.receive(repeated).ordering_state,OrderingState.REPEATED)
        old=self.raw({"BID":74,"OFFER":75,"UTM":(NOW-timedelta(seconds=1)).timestamp()*1000},NOW+timedelta(seconds=2),"0"); self.assertEqual(self.stream.receive(old).ordering_state,OrderingState.OUT_OF_ORDER)
    def test_stale_quote_and_health_states(self):
        obs=self.stream.receive(self.raw({"BID":1,"OFFER":2,"UTM":(NOW-timedelta(seconds=31)).timestamp()*1000},NOW)); self.assertTrue(obs.stale)
        self.assertEqual(self.stream.health(NOW).status,StreamStatus.DISCONNECTED); self.stream.connect(); self.assertEqual(self.stream.health(NOW).status,StreamStatus.LIVE); self.assertEqual(self.stream.health(NOW+timedelta(seconds=31)).status,StreamStatus.STALE)
    def test_disconnect_reconnect_restore_and_bounded_attempts(self):
        self.stream.connect(); self.stream.connection_lost(); self.assertEqual(self.stream.health().status,StreamStatus.RECONNECTING); self.assertTrue(self.stream.reconnect()); self.assertGreaterEqual(len([c for c in self.transport.calls if c[0]=="subscribe"]),2)
        failing=IGMarketStream(adapter(),[mapping()],transport=Transport(True),max_reconnect_attempts=1); self.assertFalse(failing.reconnect()); self.assertFalse(failing.reconnect()); self.assertEqual(failing.health().status,StreamStatus.DISCONNECTED)
    def test_unsubscribe_and_multiple_subscriptions_are_isolated(self):
        other=self.stream.subscribe(mapping("GOLD","CS.D.GOLD.CFD.IP")); self.assertEqual(len(self.stream.subscriptions),2); self.stream.unsubscribe(other.subscription_id); self.assertEqual(len(self.stream.subscriptions),1)
    def test_malformed_partial_crossed_and_bad_timestamp_rejected(self):
        for values in ({"BID":1},{"BID":2,"OFFER":1},{"BID":1,"OFFER":2,"UTM":"bad"},{"BID":"secret","OFFER":2}):
            with self.subTest(values=values),self.assertRaises(ValueError): self.stream.receive(self.raw(values))
    def test_secrets_absent_from_health_and_observation(self):
        self.stream.connection_lost("CST=CST_SECRET password=PASSWORD API_SECRET"); rendered=repr(self.stream.health())
        for secret in ("CST_SECRET","XST_SECRET","PASSWORD","API_SECRET"): self.assertNotIn(secret,rendered)
    def test_no_trading_or_domain_side_effects(self):
        obs=self.stream.receive(self.raw()); self.assertFalse(hasattr(obs,"order")); self.assertFalse(hasattr(self.stream,"place_order")); self.assertEqual(self.transport.calls,[])
    def test_auth_response_retains_stream_metadata_only_in_session(self):
        body=b'{"currentAccountId":"ACC","lightstreamerEndpoint":"https://ls.example"}'
        a=IGReadOnlyAdapter(IGConfig("key","user","pass"),lambda *x:(200,{"cst":"c","x-security-token":"x"},body)); result=a.authenticate(); self.assertEqual(result,{"authenticated":True,"environment":"DEMO"}); self.assertEqual(a._session.lightstreamer_endpoint,"https://ls.example")

if __name__=="__main__": unittest.main()
