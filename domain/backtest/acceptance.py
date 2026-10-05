"""Offline real-source diagnostics. Observed data never proves its own admission."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json

from domain.backtest.data import number

VERSION = 'local-real-source-audit-v1'
FIELDS = ('Open', 'High', 'Low', 'Close', 'Volume')


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _rows(source):
    """Validate the whole frozen source without sorting away ordering defects."""
    rows = source.get('bars', [])
    defects = []
    previous = None
    seen = set()
    for index, row in enumerate(rows):
        try:
            at = datetime.fromisoformat(row['timestamp'])
            if at.tzinfo is None or at.utcoffset() is None:
                raise ValueError('offset required')
            if at in seen:
                defects.append({'row': index, 'reason': 'DUPLICATE_TIMESTAMP'})
            if previous is not None and at <= previous:
                defects.append({'row': index, 'reason': 'NONCHRONOLOGICAL_TIMESTAMP'})
            seen.add(at)
            previous = at
            o, h, l, c, v = (number(row[k]) for k in FIELDS)
            if min(o, h, l, c) <= 0 or l > min(o, c) or h < max(o, c) or v < 0:
                raise ValueError('invalid bar')
        except (KeyError, TypeError, ValueError, ArithmeticError):
            defects.append({'row': index, 'reason': 'INVALID_BAR'})
    return rows, defects


def compare_sources(daily, intraday):
    """Raw-provider-unit reconciliation, with no invented session/calendar/fills."""
    drows, ddefects = _rows(daily)
    irows, idefects = _rows(intraday)
    identity_fields = ('symbol', 'provider')
    identity_match = all(daily.get(k) and daily.get(k) == intraday.get(k) for k in identity_fields)
    # Price scale/timezone metadata must be explicit on both frozen inputs.
    metadata = ('provider_currency', 'timezone')
    metadata_match = all(daily.get(k) and daily.get(k) == intraday.get(k) for k in metadata)
    result = {'version': VERSION, 'daily_fingerprint': fingerprint(daily),
              'intraday_fingerprint': fingerprint(intraday), 'identity_match': identity_match,
              'metadata_match': metadata_match, 'daily_rows': len(drows), 'intraday_rows': len(irows),
              'daily_defects': ddefects, 'intraday_defects': idefects,
              'sessions': [], 'extra_intraday_dates': [], 'real_data_accepted': False,
              'real_trade_audit': None, 'availability_basis': 'RETRIEVAL_ONLY_NOT_POINT_IN_TIME',
              'calendar_basis': 'OBSERVED_DATES_NOT_VERIFIED_EXCHANGE_CALENDAR'}
    if ddefects or idefects or not identity_match:
        result['comparison_state'] = 'BLOCKED_INVALID_OR_MISMATCHED_SOURCES'
        return result
    groups = defaultdict(list)
    for row in irows:
        groups[row['timestamp'][:10]].append(row)
    dates = {row['timestamp'][:10] for row in drows}
    result['extra_intraday_dates'] = sorted(set(groups) - dates)
    for row in drows:
        key = row['timestamp'][:10]
        bars = groups.get(key, [])
        entry = {'date': key, 'intraday_rows': len(bars)}
        if not bars:
            entry['state'] = 'NO_INTRADAY_OBSERVATIONS'
        else:
            values = [tuple(number(b[k]) for k in FIELDS) for b in bars]
            aggregate = (values[0][0], max(v[1] for v in values), min(v[2] for v in values),
                         values[-1][3], sum(v[4] for v in values))
            differences = {k: str(a - number(row[k])) for k, a in zip(FIELDS, aggregate)}
            entry.update(first_at=bars[0]['timestamp'], last_at=bars[-1]['timestamp'],
                         differences_in_provider_units=differences,
                         state='OBSERVED_AGGREGATE_MATCH' if all(number(v) == 0 for v in differences.values())
                         else 'OBSERVED_AGGREGATE_MISMATCH')
        result['sessions'].append(entry)
    matched = sum(s['state'] == 'OBSERVED_AGGREGATE_MATCH' for s in result['sessions'])
    result['matched_sessions'] = matched
    result['comparison_state'] = ('OBSERVED_AGGREGATES_MATCH_CALENDAR_STILL_UNVERIFIED'
                                  if matched == len(drows) and drows and not result['extra_intraday_dates']
                                  else 'BLOCKED_INCOMPLETE_OR_DIFFERENT_INTRADAY_AGGREGATES')
    result['metadata_state'] = 'EXPLICIT_MATCH' if metadata_match else 'INTRADAY_UNITS_OR_TIMEZONE_UNVERIFIED'
    # Even exact aggregates cannot establish continuous coverage, fill capacity,
    # corporate-action completeness or historical publication availability.
    return result


def published_share_fee(notional, direction, *, brokerage_rate='.005', brokerage_minimum='110',
                        strate_rate='.00006018', strate_minimum='6.29', strate_maximum='142.20',
                        levy_rate='.0000033', purchase_tax_rate='.0025', vat_rate='.15'):
    """Illustrative current OST cash-share schedule; not a historical broker receipt.

    Round each taxable component and its VAT to cents. VAT on the levy is an
    explicit conservative assumption; actual broker invoice rounding is unverified.
    This diagnostic deliberately stays outside replay's generic fee contract.
    """
    if direction not in (-1, 1) or isinstance(direction, bool):
        raise ValueError('buy/sell direction required')
    value = number(notional)
    if value <= 0:
        raise ValueError('positive cash-share notional required')
    rates = [number(x) for x in (brokerage_rate, brokerage_minimum, strate_rate, strate_minimum,
                                strate_maximum, levy_rate, purchase_tax_rate, vat_rate)]
    if min(rates) < 0 or rates[4] < rates[3]:
        raise ValueError('nonnegative ordered schedule required')
    def cents(x):
        return x.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    br, bm, sr, sm, sx, lr, tr, vr = rates
    components = {'brokerage': cents(max(bm, value * br)),
                  'strate': cents(min(sx, max(sm, value * sr))),
                  'levy': cents(value * lr),
                  'purchase_tax': cents(value * tr) if direction == 1 else Decimal('0.00')}
    components['vat'] = sum(cents(components[k] * vr) for k in ('brokerage', 'strate', 'levy'))
    total = sum(components.values())
    return {'components': {k: str(v) for k, v in components.items()}, 'total': str(total),
            'basis': 'CURRENT_PUBLISHED_OST_SCHEDULE_ASSUMED_VAT_AND_COMPONENT_ROUNDING',
            'historical_invoice_verified': False}
