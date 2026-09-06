"""Local, metadata-only correlation for human ViewPoint discovery trials."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
from collections import Counter, defaultdict
from urllib.parse import urlsplit

class ActionType(str, Enum):
    PAGE_RELOAD="PAGE_RELOAD"; OPEN_ORDER_PAD="OPEN_ORDER_PAD"; CLOSE_ORDER_PAD="CLOSE_ORDER_PAD"
    SEARCH_INSTRUMENT="SEARCH_INSTRUMENT"; SELECT_INSTRUMENT="SELECT_INSTRUMENT"
    CHANGE_ORDER_TYPE="CHANGE_ORDER_TYPE"; CHANGE_QUANTITY="CHANGE_QUANTITY"; CHANGE_LIMIT_PRICE="CHANGE_LIMIT_PRICE"
    OPEN_ACCOUNT_SELECTOR="OPEN_ACCOUNT_SELECTOR"; SELECT_ACCOUNT_PROFILE="SELECT_ACCOUNT_PROFILE"
    OPEN_PORTFOLIO="OPEN_PORTFOLIO"; OPEN_TRADES="OPEN_TRADES"; OPEN_ORDER_HISTORY="OPEN_ORDER_HISTORY"
    OPEN_QUOTE="OPEN_QUOTE"; CLEAR_TICKET="CLEAR_TICKET"; OTHER_NON_SUBMITTING="OTHER_NON_SUBMITTING"

class ProductCategory(str, Enum):
    EQUITY="EQUITY"; ETF="ETF"; WARRANT="WARRANT"; FUTURE="FUTURE"; INDEX="INDEX"; CFD="CFD"
    FX="FX"; COMMODITY="COMMODITY"; DEPOSIT="DEPOSIT"; OPTION_OR_CALL="OPTION_OR_CALL"; OTHER="OTHER"; UNKNOWN="UNKNOWN"

@dataclass(frozen=True)
class DiscoveryAction:
    action_id: str; timestamp: datetime; action_type: ActionType; action_label: str
    instrument_alias: str|None=None; product_category: ProductCategory=ProductCategory.UNKNOWN; notes: str|None=None
    def __post_init__(self):
        if self.action_type.value in {"PLACE_ORDER","SUBMIT_ORDER","CONFIRM_ORDER","CANCEL_LIVE_ORDER"}:
            raise ValueError("submitting/live-order actions are prohibited")

@dataclass(frozen=True)
class WebSocketFrameObservation:
    observation_id: str; timestamp: datetime; socket_host: str; direction: str="UNKNOWN"
    frame_type: str="UNKNOWN"; byte_length: int=0; content_hash: str=""; socket_path: str|None=None
    sequence_number: int|None=None; correlation_action_id: str|None=None; relative_time_ms: int|None=None
    repeated_hash_count: int|None=None
    @classmethod
    def from_bytes(cls, observation_id, timestamp, socket_url, payload, *, direction="UNKNOWN", frame_type="BINARY", action_id=None, sequence_number=None, relative_time_ms=None):
        u=urlsplit(socket_url)
        if frame_type not in {"TEXT","BINARY","CONTROL","UNKNOWN"} or direction not in {"SENT","RECEIVED","UNKNOWN"}: raise ValueError("invalid frame metadata")
        return cls(observation_id,timestamp,u.netloc,direction,frame_type,len(payload),hashlib.sha256(payload).hexdigest(),u.path or None,sequence_number,action_id,relative_time_ms)

def classify_endpoint(url: str) -> str:
    host=urlsplit(url).netloc.lower(); path=urlsplit(url).path.lower()
    if host=="services.iress.co.za" and path=="/mdnl/web-logger/api": return "TELEMETRY_LOGGER"
    if host=="services.iress.co.za" and path=="/md/settings-user/api": return "USER_SETTINGS"
    if host=="heapanalytics.com" or host.endswith(".heapanalytics.com"): return "THIRD_PARTY_ANALYTICS"
    return "CANDIDATE_UNCLASSIFIED"

def correlate(actions, frames, window_ms=30000):
    grouped=defaultdict(list)
    for f in frames:
        if f.correlation_action_id in {a.action_id for a in actions}: grouped[f.correlation_action_id].append(f)
    result=[]
    for a in actions:
        fs=grouped[a.action_id]; hashes=Counter(f.content_hash for f in fs)
        result.append({"action_id":a.action_id,"frames":len(fs),"hosts":sorted({f.socket_host for f in fs}),"directions":dict(Counter(f.direction for f in fs)),"lengths":sorted(f.byte_length for f in fs),"unique_hashes":len(hashes),"repeated_hashes":sum(v>1 for v in hashes.values()),"classification":"CORRELATED" if fs else "NOT_OBSERVED"})
    return result
