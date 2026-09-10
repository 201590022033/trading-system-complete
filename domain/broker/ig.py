"""Read-only IG REST discovery and canonical EPIC mapping boundary."""

from dataclasses import dataclass
import json
import os
import re
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

VERSION = "ig-discovery-v1"
BASE_URLS = {"DEMO": "https://demo-api.ig.com/gateway/deal", "LIVE": "https://api.ig.com/gateway/deal"}
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,30}$")

ERROR_CATEGORIES = {
    "AUTHENTICATION_FAILED", "INVALID_API_KEY", "ENVIRONMENT_MISMATCH",
    "TWO_FACTOR_REQUIRED", "PERMISSION_DENIED", "RATE_LIMITED",
    "NETWORK_ERROR", "MALFORMED_REQUEST", "MALFORMED_RESPONSE", "UNKNOWN_IG_ERROR",
}

_KNOWN_ERROR_CATEGORIES = {
    "error.security.invalid-details": "AUTHENTICATION_FAILED",
    "error.security.invalid-api-key": "INVALID_API_KEY",
    "error.security.account-not-enabled-for-api": "PERMISSION_DENIED",
    "error.security.two-factor-authentication-required": "TWO_FACTOR_REQUIRED",
    "error.public-api.exceeded-api-key-allowance": "RATE_LIMITED",
    "error.public-api.exceeded-account-allowance": "RATE_LIMITED",
    "error.public-api.exceeded-account-historical-data-allowance": "RATE_LIMITED",
}


def sanitize_text(value, secrets=()):
    """Return operator-safe text without credentials, tokens, headers or cookies."""
    text = str(value or "")
    for secret in secrets:
        if secret:
            text = text.replace(str(secret), "[REDACTED]")
    patterns = (
        r'(?i)(password|api[_-]?key|identifier|username|account[_-]?id)\s*[:=]\s*[^\s,;}]+',
        r'(?i)(CST|X-SECURITY-TOKEN|authorization|cookie)\s*[:=]\s*[^\s,;}]+',
        r'(?i)bearer\s+[A-Za-z0-9._~+/=-]+',
    )
    for pattern in patterns:
        text = re.sub(pattern, lambda match: match.group(0).split(":", 1)[0].split("=", 1)[0] + ":[REDACTED]", text)
    return text


def _error_category(status, error_code):
    code = str(error_code or "").strip().lower()
    if code in _KNOWN_ERROR_CATEGORIES:
        return _KNOWN_ERROR_CATEGORIES[code]
    if "two-factor" in code or "2fa" in code or "security-code" in code:
        return "TWO_FACTOR_REQUIRED"
    if "invalid-api-key" in code:
        return "INVALID_API_KEY"
    if "environment" in code and any(word in code for word in ("invalid", "mismatch", "wrong")):
        return "ENVIRONMENT_MISMATCH"
    if status == 401:
        return "AUTHENTICATION_FAILED"
    if status == 403:
        return "PERMISSION_DENIED"
    if status == 429:
        return "RATE_LIMITED"
    if status == 400:
        return "MALFORMED_REQUEST"
    return "UNKNOWN_IG_ERROR"


class IGRequestError(RuntimeError):
    """Structured error whose string representation is safe for operator output."""

    def __init__(self, http_status, ig_error_code, error_category, message):
        self.http_status = http_status
        self.ig_error_code = ig_error_code
        self.error_category = error_category
        self.safe_message = message
        super().__init__(message)

    def diagnostic(self, environment):
        return {"authenticated": False, "environment": environment,
                "http_status": self.http_status, "ig_error_code": self.ig_error_code,
                "error_category": self.error_category, "message": self.safe_message}


@dataclass(frozen=True)
class IGConfig:
    api_key: str
    username: str
    password: str
    account_id: str | None = None
    environment: str = "DEMO"
    timeout_seconds: float = 20.0
    identifier: str | None = None

    def __post_init__(self):
        if self.environment not in BASE_URLS:
            raise ValueError("IG_ENVIRONMENT must be DEMO or LIVE")
        if not all((self.api_key, self.auth_identifier, self.password)):
            raise ValueError("IG credentials are required")
        if not IDENTIFIER_PATTERN.fullmatch(self.auth_identifier):
            raise ValueError("IG_IDENTIFIER must be 1-30 letters, digits, hyphens or underscores")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout must be positive")

    @property
    def auth_identifier(self):
        """Explicit API login identifier, with IG_USERNAME as a legacy alias."""
        return (self.identifier or self.username).strip()

    @classmethod
    def from_env(cls, environ=None):
        environ = os.environ if environ is None else environ
        environment = environ.get("IG_ENVIRONMENT", "DEMO").strip().upper()
        if environment not in BASE_URLS:
            raise ValueError("IG_ENVIRONMENT must be DEMO or LIVE")
        values = {"api_key": environ.get("IG_API_KEY", "").strip(),
                  "username": environ.get("IG_USERNAME", "").strip(),
                  "password": environ.get("IG_PASSWORD", "").strip(),
                  "identifier": environ.get("IG_IDENTIFIER", "").strip() or None}
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


def _header_value(headers, name):
    """Read an HTTP response header using RFC case-insensitive semantics."""
    wanted = name.casefold()
    for key, value in headers.items():
        if str(key).casefold() == wanted:
            return value
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
        except HTTPError as exc:
            return exc.code, dict(exc.headers or {}), exc.read()
        except (URLError, TimeoutError, OSError):
            raise IGRequestError(None, None, "NETWORK_ERROR", "IG could not be reached") from None

    def _secrets(self):
        session_values = () if self._session is None else (self._session.cst, self._session.security_token)
        return (self.config.api_key, self.config.username, self.config.identifier,
                self.config.password,
                self.config.account_id, *session_values)

    def _rejection(self, status, raw):
        error_code = None
        server_message = None
        malformed = False
        try:
            payload = json.loads(raw.decode() or "{}")
            if not isinstance(payload, Mapping):
                malformed = True
            else:
                error_code = payload.get("errorCode") or payload.get("error_code") or payload.get("code")
                server_message = payload.get("errorMessage") or payload.get("message")
        except (ValueError, UnicodeDecodeError):
            malformed = True
        category = _error_category(status, error_code)
        if malformed and status not in (400, 401, 403, 429):
            category = "MALFORMED_RESPONSE"
        default_messages = {
            "AUTHENTICATION_FAILED": "IG rejected the supplied credentials",
            "INVALID_API_KEY": "IG rejected the supplied API key",
            "ENVIRONMENT_MISMATCH": "IG reported an environment mismatch",
            "TWO_FACTOR_REQUIRED": "IG requires a two-factor security code",
            "PERMISSION_DENIED": "IG denied access for this account or API permission",
            "RATE_LIMITED": "IG rate-limited the request",
            "MALFORMED_REQUEST": "IG rejected the authentication request",
            "MALFORMED_RESPONSE": "IG returned an unreadable error response",
            "UNKNOWN_IG_ERROR": "IG rejected the request",
        }
        message = sanitize_text(server_message, self._secrets()) if server_message else default_messages[category]
        return IGRequestError(status, sanitize_text(error_code, self._secrets()) or None, category, message)

    def _request(self, method, path, *, version, payload=None, auth=True, return_headers=False):
        headers = {"X-IG-API-KEY": self.config.api_key, "Accept-Version": str(version),
                   "Content-Type": "application/json", "Accept": "application/json"}
        if auth:
            if self._session is None:
                raise RuntimeError("IG authentication required")
            headers.update({"CST": self._session.cst, "X-SECURITY-TOKEN": self._session.security_token})
        body = json.dumps(payload).encode() if payload is not None else None
        try:
            status, response_headers, raw = self._transport(
                method, self.config.base_url + path, headers, body, self.config.timeout_seconds,
            )
        except IGRequestError:
            raise
        except HTTPError as exc:
            raise self._rejection(exc.code, exc.read()) from None
        except (URLError, TimeoutError, OSError):
            raise IGRequestError(None, None, "NETWORK_ERROR", "IG could not be reached") from None
        except Exception:
            raise IGRequestError(None, None, "UNKNOWN_IG_ERROR", "Unexpected IG transport failure") from None
        if status >= 400:
            raise self._rejection(status, raw)
        try:
            payload = json.loads(raw.decode() or "{}")
        except (ValueError, UnicodeDecodeError):
            raise IGRequestError(status, None, "MALFORMED_RESPONSE", "IG returned invalid JSON") from None
        if not isinstance(payload, Mapping):
            raise IGRequestError(status, None, "MALFORMED_RESPONSE", "IG returned an unexpected response")
        return (payload, response_headers) if return_headers else payload

    @staticmethod
    def malformed_response(message):
        return IGRequestError(200, None, "MALFORMED_RESPONSE", message)

    def authenticate(self):
        _, response_headers = self._request(
            "POST", "/session", version=2,
            payload={"identifier": self.config.auth_identifier, "password": self.config.password,
                     "encryptedPassword": False},
            auth=False, return_headers=True,
        )
        cst = _header_value(response_headers, "CST")
        security = _header_value(response_headers, "X-SECURITY-TOKEN")
        if not cst or not security:
            raise IGRequestError(200, None, "MALFORMED_RESPONSE",
                                 "IG authentication response omitted session credentials")
        self._session = IGSession(str(cst), str(security), self.config.account_id)
        return {"authenticated": True, "environment": self.config.environment}

    def authentication_status(self):
        """Attempt authentication and return only a structured, redacted diagnostic."""
        try:
            return self.authenticate()
        except IGRequestError as exc:
            return exc.diagnostic(self.config.environment)
        except Exception:
            return IGRequestError(None, None, "UNKNOWN_IG_ERROR",
                                  "Unexpected IG authentication failure").diagnostic(self.config.environment)

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

    def get_historical_prices(self, epic, resolution, start, end, **limits):
        from domain.broker.ig_history import fetch_historical_prices
        return fetch_historical_prices(self, epic, resolution, start, end, **limits)

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
                "historical_prices": True,
                "order_submission": False, "position_modification": False, "version": VERSION}

    def place_order(self, *args, **kwargs):
        raise RuntimeError("IG execution disabled")

    def close_position(self, *args, **kwargs):
        raise RuntimeError("IG execution disabled")

    def amend_order(self, *args, **kwargs):
        raise RuntimeError("IG execution disabled")


__all__ = ["BASE_URLS", "ERROR_CATEGORIES", "IDENTIFIER_PATTERN", "IGAccount", "IGConfig", "IGMapping", "IGMarket",
           "IGReadOnlyAdapter", "IGRequestError", "IGSession", "VERSION", "sanitize_text"]
