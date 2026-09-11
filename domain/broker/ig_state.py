"""IG Demo GET-only account and open-position normalization."""
from datetime import datetime, timezone
from math import isfinite
from typing import Mapping
from .state import BrokerAccountState,BrokerPositionState,BrokerStateSnapshot,Freshness

def _num(value):
    if value is None:return None
    try:value=float(value)
    except (TypeError,ValueError):raise ValueError("malformed IG numeric field") from None
    if not isfinite(value):raise ValueError("malformed IG numeric field")
    return value
def _time(value):
    if not value:return None
    try:result=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    except ValueError:raise ValueError("malformed IG position timestamp") from None
    if result.tzinfo is None:result=result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)

class BrokerStateService:
    def __init__(self,adapter,mappings=(),*,stale_after_seconds,clock=None):
        if adapter.config.environment!="DEMO":raise RuntimeError("broker state restricted to IG DEMO")
        if stale_after_seconds<=0:raise ValueError("explicit positive freshness threshold required")
        self.adapter=adapter;self.clock=clock or (lambda:datetime.now(timezone.utc));self.stale_after_seconds=stale_after_seconds
        self.mapping_by_epic={m.epic:m.canonical_instrument_id for m in mappings if m.broker=="IG" and m.environment=="DEMO"}
    def _freshness(self,retrieved,now=None):return Freshness.STALE if ((now or self.clock())-retrieved).total_seconds()>self.stale_after_seconds else Freshness.FRESH
    def get_accounts(self):
        retrieved=self.clock();payload=self.adapter._request("GET","/accounts",version=1);values=payload.get("accounts")
        if not isinstance(values,list):raise ValueError("malformed IG accounts response")
        output=[]
        for item in values:
            if not isinstance(item,Mapping) or not item.get("accountId"):raise ValueError("malformed IG account record")
            balance=item.get("balance") or {}
            if not isinstance(balance,Mapping):raise ValueError("malformed IG account balance")
            currency=item.get("currency");currency=currency.get("code") if isinstance(currency,Mapping) else currency
            output.append(BrokerAccountState("IG","DEMO",str(item["accountId"]),item.get("accountName"),item.get("accountType"),item.get("preferred"),currency,_num(balance.get("balance")),None,_num(balance.get("available")),_num(balance.get("deposit")),_num(balance.get("profitLoss")),None,None,None,None,item.get("status"),item.get("status")=="ENABLED" if item.get("status") is not None else None,retrieved,self._freshness(retrieved)))
        return tuple(output)
    def get_account(self,account_id):
        values=[a for a in self.get_accounts() if a.account_id==account_id]
        if not values:raise LookupError("IG account unavailable")
        return values[0]
    def get_positions(self,account_id):
        retrieved=self.clock();payload=self.adapter._request("GET","/positions",version=2);values=payload.get("positions")
        if not isinstance(values,list):raise ValueError("malformed IG positions response")
        output=[]
        for item in values:
            if not isinstance(item,Mapping) or not isinstance(item.get("position"),Mapping) or not isinstance(item.get("market"),Mapping):raise ValueError("malformed IG position record")
            position=item["position"];market=item["market"];direction={"BUY":"LONG","SELL":"SHORT"}.get(position.get("direction"))
            if direction is None:raise ValueError("malformed IG position direction")
            epic=market.get("epic") or position.get("epic");deal=position.get("dealId")
            if not epic or not deal:raise ValueError("malformed IG position identity")
            current=market.get("bid") if direction=="LONG" else market.get("offer");iid=self.mapping_by_epic.get(str(epic));currency=position.get("currency")
            output.append(BrokerPositionState("IG","DEMO",account_id,str(deal),iid,"RESOLVED" if iid else "UNRESOLVED_INSTRUMENT_MAPPING",str(epic),str(epic),direction,_num(position.get("size")),_num(position.get("level")),_num(current),_num(position.get("stopLevel")),_num(position.get("limitLevel")),_num(position.get("profitLoss") if "profitLoss" in position else position.get("upl")),currency,_time(position.get("createdDateUTC")),retrieved,_num(position.get("contractSize")),currency,market.get("marketStatus")))
        return tuple(output)
    def get_broker_snapshot(self,account_id,now=None):
        account=self.get_account(account_id);positions=self.get_positions(account_id);retrieved=max([account.retrieved_at]+[p.retrieved_at for p in positions]);freshness=self._freshness(retrieved,now)
        return BrokerStateSnapshot("IG","DEMO",account,positions,True,len(positions),retrieved,freshness)

__all__=["BrokerStateService"]
