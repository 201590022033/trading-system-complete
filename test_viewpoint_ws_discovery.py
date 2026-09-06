import unittest
from datetime import datetime, timezone
from viewpoint_ws_discovery import *

class ViewPointWSDiscoveryTests(unittest.TestCase):
    def test_hash_and_length_are_metadata_only(self):
        t=datetime(2026,9,6,tzinfo=timezone.utc)
        a=DiscoveryAction("a",t,ActionType.SELECT_INSTRUMENT,"EQUITY_A",ProductCategory.EQUITY)
        x=WebSocketFrameObservation.from_bytes("x",t,"wss://data.iress.co.za/ws",b"secret",action_id="a")
        y=WebSocketFrameObservation.from_bytes("y",t,"wss://data.iress.co.za/ws",b"other",action_id="a")
        self.assertEqual(x.byte_length,6); self.assertNotEqual(x.content_hash,y.content_hash)
        self.assertEqual(correlate([a],[x,y])[0]["classification"],"CORRELATED")
        self.assertNotIn("secret",repr(x))
    def test_idle_frames_not_attributed_and_unknowns_preserved(self):
        t=datetime(2026,9,6,tzinfo=timezone.utc); a=DiscoveryAction("a",t,ActionType.OPEN_QUOTE,"QUOTE_A")
        x=WebSocketFrameObservation.from_bytes("x",t,"wss://data.iress.co.za/ws",b"x")
        self.assertEqual(correlate([a],[x])[0]["classification"],"NOT_OBSERVED"); self.assertEqual(x.direction,"UNKNOWN")
    def test_endpoint_and_policy_boundaries(self):
        self.assertEqual(classify_endpoint("https://services.iress.co.za/mdnl/web-logger/api"),"TELEMETRY_LOGGER")
        self.assertEqual(classify_endpoint("https://services.iress.co.za/md/settings-user/api"),"USER_SETTINGS")
        self.assertEqual(classify_endpoint("https://heapanalytics.com/x"),"THIRD_PARTY_ANALYTICS")
        self.assertEqual(ProductCategory.UNKNOWN.value,"UNKNOWN")
        with self.assertRaises(ValueError): DiscoveryAction("x",datetime.now(timezone.utc),ActionType("SUBMIT_ORDER"),"bad")
