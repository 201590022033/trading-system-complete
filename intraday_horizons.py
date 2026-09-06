"""Separate minute/session horizon identities; daily HR7–10 labels are untouched."""
from dataclasses import dataclass
from datetime import timedelta
from intraday_data import utc
VERSION='intraday-horizons-v1'

@dataclass(frozen=True)
class IntradayHorizon:
    horizon_id: str
    minutes: int | None
    version: str=VERSION
    def target(self,decision_time,session):
        decision=utc(decision_time)
        if not session.open_time<=decision<session.close_time:return None
        target=session.close_time if self.minutes is None else decision+timedelta(minutes=self.minutes)
        if target>session.close_time or any(decision<b and target>a for a,b in session.breaks):return None
        return target

HORIZONS=tuple(IntradayHorizon('intraday_'+str(m)+'m',m) for m in (5,15,30,60))+(IntradayHorizon('intraday_eod',None),)

def get_horizon(horizon_id):
    return {h.horizon_id:h for h in HORIZONS}[horizon_id]

def primary_horizon(horizon_id='intraday_30m'):
    return get_horizon(horizon_id)
