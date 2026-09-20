"""Display-only connected cash; no funding, execution or simulated defaults."""
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from math import isfinite
from threading import Lock
from time import monotonic


def instant(value):
    result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timezone-aware timestamp required')
    return result.astimezone(timezone.utc)


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError('Finite numeric value required')
    if abs(value) > 1e12:
        raise ValueError('Numeric value exceeds supported range')
    return float(value)


def account_key(account):
    identity = '|'.join(str(account[k]) for k in ('broker', 'environment', 'account_id'))
    return sha256(identity.encode()).hexdigest()[:24]


def aggregate(accounts, rates, *, now):
    """Adapters supply factual snapshots. Duplicate identities fail, never double count."""
    groups = {}
    rows = []
    seen = set()
    for original in accounts:
        a = dict(original)
        key = account_key(a)
        if key in seen:
            raise ValueError('Duplicate connected account')
        seen.add(key)
        environment = a['environment']
        if environment not in ('DEMO', 'LIVE'):
            raise ValueError('Unsupported account environment')
        group = groups.setdefault(environment, {'by_currency': {}, 'zar_total': 0.0, 'complete': True, 'excluded': []})
        a.update(key=key, cash_zar=None, conversion=None, state='UNAVAILABLE')
        try:
            age = now - instant(a['retrieved_at'])
            if not timedelta(0) <= age <= timedelta(seconds=300) or a.get('freshness') != 'FRESH':
                raise ValueError('Account balance is stale')
            cash = number(a['available_funds'])
            currency = a['account_currency']
            if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha():
                raise ValueError('Account currency unavailable')
            group['by_currency'][currency] = group['by_currency'].get(currency, 0) + cash
            a['state'] = 'AVAILABLE'
            if currency == 'ZAR':
                a['cash_zar'] = cash
            else:
                rate = rates.get(currency)
                if not rate or not timedelta(0) <= now-instant(rate['as_of']) <= timedelta(days=4):
                    raise ValueError('Dated FX rate unavailable or older than four days')
                multiplier = number(rate['zar_per_unit'])
                if multiplier <= 0:
                    raise ValueError('Invalid FX rate')
                a['cash_zar'] = number(cash * multiplier)
                a['conversion'] = rate
            group['zar_total'] += a['cash_zar']
        except (ValueError, KeyError, TypeError) as exc:
            group['complete'] = False
            group['excluded'].append(key)
            a['reason'] = str(exc)
        rows.append(a)
    for group in groups.values():
        group['known_zar_subtotal'] = group['zar_total']
        if not group['complete']:
            group['zar_total'] = None
    return {'accounts': rows, 'groups': groups, 'as_of': now.isoformat(),
            'live_execution': False, 'display_only': True,
            'cash_basis': 'Broker-reported available funds, not equity or transferable pooled capital'}


_lock = Lock()
_cached = None
_cached_at = 0.0


def cached_ig_status():
    global _cached, _cached_at
    with _lock:
        if _cached is None or monotonic()-_cached_at >= 60:
            from account_dashboard import safe_status
            _cached = safe_status()
            _cached_at = monotonic()
        return _cached


def connected_snapshot():
    status = cached_ig_status()
    accounts = []
    if status.get('state') == 'AVAILABLE' and status.get('account'):
        accounts.extend(status.get('accounts') or [status['account']])
    rates = {}
    if any(a.get('account_currency') == 'USD' for a in accounts):
        try:
            rates['USD'] = usd_rate()
        except Exception:
            pass  # Cash stays in USD; no invented FX fallback.
    result = aggregate(accounts, rates, now=datetime.now(timezone.utc))
    result['connections'] = [
        {'broker': 'IG', 'state': status.get('state', 'UNAVAILABLE'), 'environment': 'DEMO'},
        {'broker': 'Standard Bank', 'state': 'NOT_CONNECTED', 'environment': 'LIVE'},
    ]
    return result


_fx_lock = Lock()
_fx = None
_fx_at = 0.0


def usd_rate():
    global _fx, _fx_at
    with _fx_lock:
        if _fx is None or monotonic()-_fx_at >= 300:
            from jse_adapter import YahooFinanceFetcher
            chart = YahooFinanceFetcher().get_chart('ZAR=X', '1mo')
            if chart['currency'] != 'ZAR':
                raise ValueError('Unverified USD/ZAR units')
            _fx = {'zar_per_unit': chart['price'], 'as_of': chart['source_timestamp'],
                   'source': 'Yahoo ZAR=X', 'timestamp_kind': chart['timestamp_kind'],
                   'purpose': 'Indicative display conversion only'}
            _fx_at = monotonic()
        return _fx
