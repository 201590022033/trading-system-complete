"""Read-only IG Demo Lightstreamer normalization and lifecycle boundary."""
from datetime import datetime, timedelta, timezone
import math

from domain.broker.ig import IGMapping, sanitize_text
from domain.market_data.streaming import (CanonicalMarketObservation, MarketStreamSubscription,
    OrderingState, RawMarketUpdate, StreamHealth, StreamStatus)

IG_STREAM_VERSION="ig-lightstreamer-price-v1"
MID_RULE="ig-bid-ask-mid-v1"

def _number(value):
    if value in (None,""): return None
    try: result=float(value)
    except (TypeError,ValueError): raise ValueError("invalid numeric market field") from None
    if not math.isfinite(result) or result < 0: raise ValueError("invalid numeric market field")
    return result

class IGMarketStream:
    """Transport-neutral core; a Lightstreamer client delivers raw field maps."""
    def __init__(self, adapter, mappings, *, stale_after_seconds=30, max_reconnect_attempts=3, clock=None, transport=None):
        if adapter.config.environment != "DEMO": raise RuntimeError("IG streaming is restricted to DEMO")
        if stale_after_seconds <= 0 or max_reconnect_attempts < 0: raise ValueError("invalid stream policy")
        self.adapter=adapter; self.stale_after=timedelta(seconds=stale_after_seconds)
        self.max_reconnect_attempts=max_reconnect_attempts; self.clock=clock or (lambda: datetime.now(timezone.utc)); self.transport=transport
        self._subscriptions={}; self._last={}; self._connected=False; self._reconnecting=False; self._attempts=0
        self._last_message=None; self._last_valid=None; self._error=None
        for mapping in mappings: self.subscribe(mapping)

    def subscribe(self, mapping):
        if not isinstance(mapping,IGMapping) or mapping.environment!="DEMO" or not mapping.canonical_instrument_id or not mapping.epic:
            raise ValueError("resolved IG Demo instrument mapping required")
        sid=f"ig:{mapping.canonical_instrument_id}:{mapping.epic}"
        sub=MarketStreamSubscription(sid,mapping.canonical_instrument_id,mapping.epic,"IG",mapping.epic)
        if sid not in self._subscriptions:
            self._subscriptions[sid]=sub
            if self._connected and self.transport: self.transport.subscribe(self.item_name(sub),sub.fields,self.receive)
        return sub

    @property
    def subscriptions(self): return tuple(self._subscriptions.values())

    def item_name(self, sub):
        account=self.adapter._session.account_id if self.adapter._session else None
        if not account: raise RuntimeError("active IG account identifier unavailable")
        return f"PRICE:{account}:{sub.epic}"

    def connect(self):
        session=self.adapter._session
        if not session or not session.lightstreamer_endpoint or not session.account_id:
            raise RuntimeError("IG session omitted Lightstreamer connection metadata")
        if self.transport:
            self.transport.connect(session.lightstreamer_endpoint,session.account_id,f"CST-{session.cst}|XST-{session.security_token}")
            for sub in self._subscriptions.values(): self.transport.subscribe(self.item_name(sub),sub.fields,self.receive)
        self._connected=True; self._reconnecting=False; self._error=None

    def unsubscribe(self, subscription_id):
        sub=self._subscriptions.pop(subscription_id)
        if self.transport: self.transport.unsubscribe(self.item_name(sub))
        return sub

    def disconnect(self):
        if self.transport: self.transport.disconnect()
        self._connected=False; self._reconnecting=False

    def connection_lost(self, message="connection lost"):
        self._connected=False; self._error=sanitize_text(message,self.adapter._secrets()); self._reconnecting=self._attempts < self.max_reconnect_attempts

    def reconnect(self):
        if self._attempts >= self.max_reconnect_attempts:
            self._reconnecting=False; return False
        self._attempts += 1
        try: self.connect(); return True
        except Exception:
            self._connected=False; self._reconnecting=self._attempts < self.max_reconnect_attempts; self._error="IG stream reconnect failed"; return False

    def receive(self, raw):
        if not isinstance(raw,RawMarketUpdate): raise ValueError("typed raw update required")
        sub=self._subscriptions.get(raw.subscription_id)
        if not sub or sub.epic != raw.epic: raise ValueError("update does not match an active subscription")
        self._last_message=raw.received_at
        bid=_number(raw.values.get("BID") if "BID" in raw.values else raw.values.get("BIDPRICE1")); ask=_number(raw.values.get("OFFER") if "OFFER" in raw.values else raw.values.get("ASKPRICE1"))
        if (bid is None)!=(ask is None) or bid is None: raise ValueError("complete bid/ask quote required")
        if bid>ask: raise ValueError("crossed quote")
        source_time=raw.values.get("UTM")
        if source_time not in (None,""):
            try: source_time=datetime.fromtimestamp(float(source_time)/1000,tz=timezone.utc)
            except (ValueError,TypeError,OverflowError): raise ValueError("invalid source timestamp") from None
            basis="IG_UTM_EPOCH_MS"
        else: source_time=None; basis="RECEIPT_TIME_ONLY"
        previous=self._last.get(sub.subscription_id); fingerprint=(source_time,bid,ask,raw.values.get("LTP"),raw.values.get("MARKET_STATE"),raw.source_sequence)
        if previous and previous[0]==fingerprint: ordering=OrderingState.DUPLICATE
        elif previous and source_time and previous[1] and source_time<previous[1]: ordering=OrderingState.OUT_OF_ORDER
        elif previous and fingerprint[1:5]==previous[0][1:5]: ordering=OrderingState.REPEATED
        elif previous: ordering=OrderingState.IN_ORDER
        else: ordering=OrderingState.FIRST if raw.source_sequence else OrderingState.SOURCE_SEQUENCE_UNAVAILABLE
        stale=(raw.received_at-(source_time or raw.received_at))>self.stale_after
        obs=CanonicalMarketObservation(sub.instrument_id,sub.execution_symbol,"IG",sub.epic,sub.subscription_id,source_time,raw.received_at,basis,bid,ask,(bid+ask)/2,_number(raw.values.get("LTP")),ask-bid,raw.values.get("MARKET_STATE"),"RESEARCH_DATA",stale,ordering,raw.source_sequence,f"IG Demo Lightstreamer Pricing; mid={MID_RULE}",IG_STREAM_VERSION)
        if ordering not in {OrderingState.DUPLICATE,OrderingState.OUT_OF_ORDER}: self._last[sub.subscription_id]=(fingerprint,source_time)
        self._last_valid=raw.received_at
        return obs

    def health(self, now=None):
        now=now or self.clock(); stale=bool(self._last_valid and now-self._last_valid>self.stale_after)
        status=(StreamStatus.RECONNECTING if self._reconnecting else StreamStatus.DISCONNECTED if not self._connected else StreamStatus.STALE if stale else StreamStatus.LIVE)
        return StreamHealth(status,self._connected,self._last_message,self._last_valid,len(self._subscriptions),self._error,self._attempts)

__all__=["IGMarketStream","IG_STREAM_VERSION","MID_RULE"]
