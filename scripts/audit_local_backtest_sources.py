"""Offline B5 audit of frozen Yahoo observations; never uses provider credentials."""
import argparse
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from domain.backtest.acceptance import compare_sources, published_share_fee


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def audit(daily, intraday, receipts, alpha):
    if daily.get('symbol') != 'SOL.JO' or intraday.get('symbol') != 'SOL.JO':
        raise ValueError('this dated evidence assessment is specific to SOL.JO')
    if daily.get('provider') != 'YAHOO' or intraday.get('provider') != 'YAHOO':
        raise ValueError('frozen Yahoo source required')
    if not daily.get('bars') or not intraday.get('bars'):
        raise ValueError('nonempty frozen observations required')
    result = compare_sources(daily, intraday)
    result['scope'] = 'SASOL_JSE_OBSERVATIONS_2026_09_01_TO_2026_10_02_NOT_ADMITTED'
    result['source_receipts'] = receipts
    result['provider_requests_during_audit'] = 0
    result['provider_findings'] = {
        'yahoo': 'FRESH_DAILY_AND_30M_OBSERVATIONS_FROZEN_SEPARATELY',
        'alpha_vantage': {'search_state': alpha.get('state'), 'matches': alpha.get('matches', []),
                          'admission': 'NO_VERIFIED_JSE_SASOL_MAPPING',
                          'local_rolling_five_call_budget': 'EXHAUSTED_AT_PROBE',
                          'fx_gold_probe': 'NOT_CALLED_AFTER_BUDGET_EXHAUSTION'},
        'ig': 'CREDENTIALS_UNAVAILABLE_IN_THIS_CHECKOUT_NO_AUTH_OR_HISTORY_CALL'}
    result['unit_evidence'] = {
        'daily_currency': daily.get('provider_currency'), 'daily_timezone': daily.get('timezone'),
        'daily_ZAR_price_multiplier': '0.01' if daily.get('provider_currency') == 'ZAc' else None,
        'intraday_currency': intraday.get('provider_currency'),
        'intraday_currency_status': 'NOT_CAPTURED_IN_RAW_RECEIPT_NO_SCALE_GUESSED'}
    result['corporate_actions'] = {
        'provider_action_rows': sum(bool(r.get('Dividends') or r.get('Stock Splits')) for r in daily['bars']),
        'issuer_evidence': '2026_09_01_RESULTS_IDENTIFY_SOL_ISIN_ZAE000006896_AND_NO_FINAL_DIVIDEND',
        'status': 'COMPLETE_HISTORICAL_ACTION_COVERAGE_NOT_VERIFIED'}
    result['gates'] = {
        'source_identity': 'PARTIAL_ISSUER_CASH_SOL_IDENTIFIED_SEPARATE_FROM_US_ADR',
        'daily_OHLC_consistency': 'PASS_OBSERVED_SLICE' if not result['daily_defects'] else 'FAIL',
        'session_calendar': 'BLOCKED_OFFICIAL_JSE_CALENDAR_AND_SESSION_LIBRARY_HTTP_403',
        'raw_actions_historical_universe': 'BLOCKED_COMPLETE_ACTION_AND_DATED_UNIVERSE_EVIDENCE_MISSING',
        'historical_availability': 'PARTIAL_RECONSTRUCTED_ONLY_CONSERVATIVE_AVAILABILITY_CONTRACT_REQUIRED',
        'cost_liquidity_full_fills': 'PARTIAL_CURRENT_FEES_STRESSED_ACTUAL_QUOTES_AUCTION_AND_CAPACITY_MISSING',
        'daily_intraday_comparison': result['comparison_state'],
        'independent_admitted_real_trades': 'BLOCKED_NO_FULLY_ADMITTED_WINDOW_ZERO_TRADES_AUDITED',
        'fx_gold_products': 'BLOCKED_BROKER_CONTRACT_MARGIN_CARRY_CONVERSION_AND_EXECUTABLE_PRICES_UNVERIFIED'}
    scenarios = []
    for notional in (1000, 10000, 50000, 100000):
        buy, sell = published_share_fee(notional, 1), published_share_fee(notional, -1)
        fees = Decimal(buy['total']) + Decimal(sell['total'])
        for spread, slip in ((0, 0), (10, 10), (25, 10), (50, 25)):
            # Same-notional, same-midpoint diagnostic only: a round trip crosses one
            # full spread and pays two slips. No trade path or invoice is inferred.
            drag = (Decimal(notional) * Decimal(spread + 2 * slip) / 10000).quantize(
                Decimal('.01'), rounding=ROUND_HALF_UP)
            scenarios.append(dict(notional_ZAR=notional, buy=buy, sell=sell,
                                  full_spread_bps=spread, per_side_slippage_bps=slip,
                                  roundtrip_fee_ZAR=str(fees), price_drag_ZAR=str(drag),
                                  flat_price_total_cost_ZAR=str(fees + drag),
                                  basis='SENSITIVITY_ONLY_NOT_REPLAYED_OR_VERIFIED_FILLS'))
    result['cash_share_cost_sensitivity'] = scenarios
    result['cost_exclusions'] = ['Monthly account charge', 'Market-data subscriptions',
                                 'Actual historical tariff/tier', 'Verified invoice VAT and rounding',
                                 'Partial fills/market impact/settlement availability']
    result['next_evidence_required'] = [
        'Official JSE calendar/session document for the explicit window, plus SOL trading segment.',
        'Complete action ledger and dated identity/universe evidence for that window.',
        'An explicit conservative historical availability contract; label reconstructed research honestly.',
        'Complete intraday observations including closing sessions, with own currency/timezone metadata.',
        'Dated cash-share tariff/quotes and capacity envelope; independent replay cash/trade reconciliation.',
        'Own executable FX/gold product, conversion, margin and carry sources; no ADR or continuous-futures substitution.']
    result['resolution'] = 'B5_REAL_MARKET_ACCEPTANCE_BLOCKED_NO_FOLLOWING_MILESTONE_STARTED'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('daily', 'intraday', 'source-receipts', 'alpha-search', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = audit(read(args.daily), read(args.intraday), read(args.source_receipts), read(args.alpha_search))
    result['input_files'] = {name: {'filename': path.name, 'sha256': sha256(path.read_bytes()).hexdigest()}
                             for name, path in (('daily', args.daily), ('intraday', args.intraday),
                                                ('receipts', args.source_receipts), ('alpha_search', args.alpha_search))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('daily_rows', 'intraday_rows', 'matched_sessions',
                                          'comparison_state', 'real_data_accepted', 'resolution')}, sort_keys=True))


if __name__ == '__main__': main()
