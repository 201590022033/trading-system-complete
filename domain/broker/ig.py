"""Read-only IG REST discovery and canonical EPIC mapping boundary."""

from dataclasses import dataclass
import json
import os
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

VERSION = "ig-discovery-v1"
BASE_URLS = {"DEMO": "https://demo-api.ig.com/gateway/deal", "LIVE": "https://api.ig.com/gateway/deal"}


@dataclass(frozen=True)
class IGConfig:
    api_key: str
    username: str
    password: str
    account_id: str | None = None
    environment: str = "DEMO"
    timeout_seconds: float = 20.0

    def __post_init__(self):
        if self.environment not in BASE_URLS:
            raise ValueError("IG_ENVIRONMENT must be DEMO or LIVE")
        if not all((self.api_key, self.username, self.password)):
            raise ValueError("IG credentials are required")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout must be positive")

    @classmethod
    def from_env(cls, environ=None):
        environ = os.environ if environ is None else environ
        environment = environ.get("IG_ENVIRONMENT", "DEMO").strip().upper()
        if environment not in BASE_URLS:
            raise ValueError("IG_ENVIRONMENT must be DEMO or LIVE")
        values = {"api_key": environ.get("IG_API_KEY", "").strip(),
                  "username": environ.get("IG_USERNAME", "").strip(),
                  "password": environ.get("IG_PASSWORD", "").strip()}
        return cls(**values, account_id=environ.get("IG_ACCOUNT_ID") or None, environment=environment)

    @property
    def base_url(self):
        return BASE_URLS[self.environment]


@dataclass(frozen=True)
class IGSession:
    cst: str
    security_token: str
    account_id: str | None = None


@dataclass(frozen=True)
class IGAccount:
    broker: str
    environment: str
    account_id: str
    account_name: str | None
    account_type: str | None
    currency: str | None
    preferred: bool
    status: str | None


@dataclass(frozen=True)
class IGMarket:
    epic: str
    name: str
    instrument_type: str
    currency: str | None
    market_status: str
    expiry: str | None
    minimum_deal_size: float | None
    contract_size: float | None
    lot_size: float | None
    tick_size: float | None
    margin_factor: float | None
    trading_hours: tuple[str, ...]
    bid: float | None
    offer: float | None
    metadata_status: str
    environment: str
    raw_identity: str


@dataclass(frozen=True)
class IGMapping:
    canonical_instrument_id: str
    broker: str
    epic: str
    environment: str
    product_variant: str
    market_name: str
    mapping_status: str = "CANDIDATE / RESEARCH"
    version: str = VERSION


def _number(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class IGReadOnlyAdapter:
    """IG discovery adapter. No dealing endpoints or state-changing methods exist."""

    broker = "IG"

    def __init__(self, config: IGConfig, transport: Callable | None = None):
        self.config = config
        self._transport = transport or self._default_transport
        self._session: IGSession | None = None

    @staticmethod
    def _default_transport(method, url, headers, body, timeout):
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.status, dict(response.headers), response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"IG request failed: {type(exc).__name__}") from None

    def _request(self, method, path, *, version, payload=None, auth=True):
        headers = {"X-IG-API-KEY": self.config.api_key, "Accept-Version": str(version),
                   "Content-Type": "application/json", "Accept": "application/json"}
        if auth:
            if self._session is None:
                raise RuntimeError("IG authentication required")
            headers.update({"CST": self._session.cst, "X-SECURITY-TOKEN": self._session.security_token})
        body = json.dumps(payload).encode() if payload is not None else None
        try:
            status, _, raw = self._transport(method, self.config.base_url + path, headers, body, self.config.timeout_seconds)
            if status >= 400:
                raise RuntimeError(f"IG request rejected with HTTP {status}")
            return json.loads(raw.decode() or "{}")
        except (ValueError, UnicodeDecodeError):
            raise RuntimeError("IG returned invalid JSON") from None

    def authenticate(self):
        payload = self._request("POST", "/session", version=2,
                                payload={"identifier": self.config.username, "password": self.config.password,
                                         "encryptedPassword": False}, auth=False)
        cst = payload.get("cst")
        security = payload.get("x-security-token") or payload.get("securityToken")
        if not cst or not security:
            raise RuntimeError("IG authentication response missing session credentials")
        self._session = IGSession(str(cst), str(security), self.config.account_id)
        return {"authenticated": True, "environment": self.config.environment, "account_id": self.config.account_id}

    def session_status(self):
        return {"authenticated": self._session is not None, "environment": self.config.environment}

    def get_accounts(self):
        values = self._request("GET", "/accounts", version=1).get("accounts", [])
        return tuple(IGAccount("IG", self.config.environment, str(item.get("accountId", "UNKNOWN")),
                              item.get("accountName"), item.get("accountType"),
                              (item.get("currency") or {}).get("code") if isinstance(item.get("currency"), dict) else item.get("currency"),
                              bool(item.get("preferred")), item.get("status")) for item in values)

    def search_markets(self, query):
        values = self._request("GET", "/markets?" + urlencode({"searchTerm": query}), version=1).get("markets", [])
        return tuple(self._normalize_market(item) for item in values)

    def get_market(self, epic):
        return self._normalize_market(self._request("GET", "/markets/" + quote(epic, safe=""), version=3))

    def _normalize_market(self, item: Mapping):
        dealing = item.get("dealingRules") or {}
        instrument = item.get("instrument") or {}
        snapshot = item.get("snapshot") or {}
        hours = instrument.get("openingHours") or {}
        raw_hours = hours.get("marketTimes") if isinstance(hours, dict) else None
        currency = instrument.get("currency")
        currency = currency.get("code") if isinstance(currency, dict) else currency
        epic = str(item.get("epic") or instrument.get("epic") or "UNKNOWN")
        known = all(value is not None for value in (epic, item.get("instrumentName") or instrument.get("name")))
        return IGMarket(
            epic, str(item.get("instrumentName") or instrument.get("name") or "UNKNOWN"),
            str(instrument.get("type") or "UNKNOWN"), currency,
            str(snapshot.get("marketStatus") or "UNKNOWN"), instrument.get("expiry"),
            _number((dealing.get("minDealSize") or {}).get("value") if isinstance(dealing.get("minDealSize"), dict) else dealing.get("minDealSize")),
            _number(instrument.get("contractSize")), _number(instrument.get("lotSize")),
            _number(instrument.get("valueOfOnePip")), _number(instrument.get("marginFactor")),
            tuple(str(value) for value in (raw_hours or ())),
            _number(snapshot.get("bid")), _number(snapshot.get("offer")),
            "AVAILABLE" if known else "UNKNOWN", self.config.environment, "IG REST market metadata",
        )

    def discover_instrument(self, canonical_instrument_id, market: IGMarket):
        return IGMapping(canonical_instrument_id, self.broker, market.epic, market.environment,
                         market.instrument_type, market.name)

    def capabilities(self):
        return {"broker": self.broker, "environment": self.config.environment, "read_only": True,
                "authentication": True, "accounts": True, "market_search": True, "market_detail": True,
                "order_submission": False, "position_modification": False, "version": VERSION}

    def place_order(self, *args, **kwargs):
        raise RuntimeError("IG execution disabled in M12A")

    def close_position(self, *args, **kwargs):
        raise RuntimeError("IG execution disabled in M12A")

    def amend_order(self, *args, **kwargs):
        raise RuntimeError("IG execution disabled in M12A")


__all__ = ["BASE_URLS", "IGAccount", "IGConfig", "IGMapping", "IGMarket", "IGReadOnlyAdapter", "IGSession", "VERSION"]
