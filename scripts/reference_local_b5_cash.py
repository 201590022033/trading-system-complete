"""Independent observed-price cash oracle; does not admit data or call replay."""
import argparse
from decimal import Decimal as D, ROUND_FLOOR, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from pathlib import Path
import sys


def cents(value):
    return value.quantize(D('.01'), rounding=ROUND_HALF_UP)


def reference_fee(value, buy):
    # Independent arithmetic from the disclosed published schedule, not the
    # production fee helper. Invoice applicability/rounding remains assumed.
    brokerage = cents(max(D(110), value / 200))
    settlement = cents(min(D('142.20'), max(D('6.29'), value * D('.00006018'))))
    levy = cents(value * D('.0000033'))
    vat = sum(cents(x * D('.15')) for x in (brokerage, settlement, levy))
    return brokerage + settlement + levy + vat + (cents(value / 400) if buy else D(0))


def reference(comparison, calendar):
    with localcontext() as ctx:
        ctx.prec = 28
        ctx.rounding = ROUND_HALF_UP
        days = comparison['daily']
        dates = [d['date'] for d in days]
        if dates != calendar['expected_dates'] or len(set(dates)) != len(dates):
            raise ValueError('exact chronological calendar coverage required')
        for day in days:
            bar = day['iress_daily']
            o, h, l, c, v = (D(str(bar[k])) for k in ('Open', 'High', 'Low', 'Close', 'Volume'))
            if not all(x.is_finite() for x in (o, h, l, c, v)) or min(o, h, l, c) <= 0 or v <= 0:
                raise ValueError('finite positive observed prices/activity required')
            if l > min(o, c) or h < max(o, c):
                raise ValueError('invalid observed OHLC')
        cases = []
        # Fixed accounting probes, not indicator-selected opportunities. Each
        # case starts independently with 20,000 ZAR and a 5,000 ZAR cash cap.
        for signal_date in ('2026-09-01', '2026-09-09', '2026-09-17'):
            signal_idx = dates.index(signal_date)
            entry_idx = signal_idx + 1
            stop = D(str(days[signal_idx]['iress_daily']['Close'])) / 200
            for horizon in (3, 4, 5):
                exit_idx = entry_idx + horizon
                if exit_idx >= len(days):
                    raise ValueError('complete horizon required')
                for spread, slip in ((0, 0), (10, 10), (25, 10), (50, 25)):
                    entry_mid = D(str(days[entry_idx]['iress_daily']['Close'])) / 100
                    entry = entry_mid * (1 + (D(spread)/2 + slip)/10000)
                    if D(str(days[entry_idx]['iress_daily']['Low'])) / 100 <= stop:
                        raise ValueError('pre-entry stop invalidation; this probe is not applicable')
                    quantity = min(D(5000)/entry, D(1000)/(entry-stop)).to_integral_value(rounding=ROUND_FLOOR)
                    while quantity > 0 and quantity*entry + reference_fee(quantity*entry, True) > 5000:
                        quantity -= 1
                    if quantity <= 0:
                        raise ValueError('unfundable probe')
                    for day in days[entry_idx+1:exit_idx+1]:
                        if D(str(day['iress_daily']['Low'])) / 100 <= stop:
                            raise ValueError('stop touched; horizon-only reference is not applicable')
                    exit_mid = D(str(days[exit_idx]['iress_daily']['Close'])) / 100
                    exit_price = exit_mid * (1 - (D(spread)/2 + slip)/10000)
                    buy_fee = reference_fee(quantity*entry, True)
                    sell_fee = reference_fee(quantity*exit_price, False)
                    cash_after_entry = cents(D(20000) - cents(quantity*entry) - buy_fee)
                    final_cash = cents(cash_after_entry + cents(quantity*exit_price) - sell_fee)
                    marks = [dict(date=days[i]['date'], equity=str(cents(cash_after_entry + quantity*D(str(days[i]['iress_daily']['Close']))/100)))
                             for i in range(entry_idx, exit_idx)]
                    marks.append(dict(date=dates[exit_idx], equity=str(final_cash)))
                    cases.append(dict(signal_date=signal_date, entry_date=dates[entry_idx], exit_date=dates[exit_idx],
                        horizon=horizon, entry_session_counts=False, full_spread_bps=spread, per_side_slippage_bps=slip,
                        stop=str(stop), quantity=str(quantity), entry=str(entry), exit=str(exit_price),
                        entry_fee=str(buy_fee), exit_fee=str(sell_fee), cash_after_entry=str(cash_after_entry),
                        final_cash=str(final_cash), net_cash_change=str(final_cash-20000), equity=marks,
                        entry_notional=str(quantity*entry), exit_notional=str(quantity*exit_price)))
        return cases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--comparison', type=Path, required=True)
    p.add_argument('--calendar', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--verify-fees', action='store_true')
    args = p.parse_args()
    cases = reference(json.loads(args.comparison.read_text()), json.loads(args.calendar.read_text()))
    verified = 0
    if args.verify_fees:
        # Expected answers above never import the implementation being checked.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from domain.backtest.costs import OSTCashShareCosts
        costs = OSTCashShareCosts()
        for case in cases:
            for field, side in (('entry', 1), ('exit', -1)):
                actual = costs.fee(D(case[field+'_notional']), side)
                if actual != D(case[field+'_fee']):
                    raise AssertionError('published fee adapter/reference mismatch')
                verified += 1
    result = dict(scope='INDEPENDENT_CONDITIONAL_OBSERVED_PRICE_ACCOUNTING_REFERENCE',
        real_data_admitted=False, replay_executed=False, admitted_real_trades=0,
        input_sha256=sha256(args.comparison.read_bytes()).hexdigest(),
        calendar_sha256=sha256(args.calendar.read_bytes()).hexdigest(),
        reference_code_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        scenario_count=len(cases), fee_component_checks=verified, cases=cases,
        assumptions=['Independent 20,000 ZAR starting cash per case; fixed dated probes, no strategy selection',
            'Full fills at later-close proxies with declared spread/slippage; no execution-ready claim',
            'Broad predeclared half-signal-close stop, 1,000 ZAR price risk, 5,000 ZAR cash cap, no target or trailing',
            'Current public fees and component VAT rounding; historical invoice applicability unverified',
            'No shareholder-wide action in each probe is CONDITIONAL, not an admission certification',
            'Daily activity is post-hoc evidence and is not used to size entry'],
        remaining=['Verified RAW price/action contract before manifested replay',
            'Compare independently expected cash/equity with engine replay only after admission',
            'Unresolved intraday volume/bar-label semantics are not accepted as reconciled'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','assumptions','remaining')}))


if __name__ == '__main__':
    main()
