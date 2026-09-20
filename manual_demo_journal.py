"""Durable self-reported demo trades, isolated from canonical strategy learning."""
from datetime import datetime, timezone
from uuid import UUID
from connected_accounts import instant, number

PREFIX = 'manual-demo-journal:'


def identity(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise ValueError('A valid trade UUID is required') from None


def text(value, name, limit=2000, required=False):
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError(f'Invalid {name}')
    return value.strip()


def positive(value):
    value = number(value)
    if value <= 0:
        raise ValueError('Quantity, prices and planned risk must be positive')
    return value


class ManualDemoJournal:
    def __init__(self, repo, *, clock=None):
        self.repo = repo
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def open(self, account, body):
        if not isinstance(body, dict) or set(body)-{'trade_id', 'instrument', 'direction', 'quantity', 'entry_price', 'opened_at', 'stop_price', 'target_price', 'planned_risk', 'idea_source', 'notes', 'broker_reference'}:
            raise ValueError('Unsupported entry fields')
        if account.get('environment') != 'DEMO' or account.get('state') != 'AVAILABLE':
            raise ValueError('A currently available DEMO account is required')
        trade_id = identity(body.get('trade_id'))
        key = account['key']
        ledger = PREFIX+key
        record_id = f'{ledger}:entry:{trade_id}'
        now = self.clock()
        opened = instant(body.get('opened_at'))
        if opened > now:
            raise ValueError('Entry time cannot be in the future')
        direction = body.get('direction')
        source = body.get('idea_source')
        if direction not in ('LONG', 'SHORT') or source not in ('MY_IDEA', 'APP_INSPIRED'):
            raise ValueError('Select direction and idea source')
        entry = dict(trade_id=trade_id, account_key=key,
                     instrument=text(body.get('instrument'), 'instrument', 100, True),
                     direction=direction, idea_source=source, quantity=positive(body.get('quantity')),
                     entry_price=positive(body.get('entry_price')), opened_at=opened.isoformat(),
                     notes=text(body.get('notes', ''), 'notes'),
                     broker_reference=text(body.get('broker_reference', ''), 'broker reference', 100))
        for field in ('stop_price', 'target_price', 'planned_risk'):
            entry[field] = positive(body[field]) if body.get(field) is not None else None
        self.repo.create_paper_account(ledger, {'mode': 'PAPER', 'purpose': 'MANUAL_DEMO_JOURNAL', 'account': account})
        with self.repo.paper_account_transaction(ledger) as state:
            if state.get('purpose') != 'MANUAL_DEMO_JOURNAL':
                raise ValueError('Journal namespace conflict')
            existing = self.repo.paper_record(record_id)
            if existing:
                if any(existing[k] != v for k, v in entry.items()):
                    raise ValueError('Trade ID already used with different entry details')
                return existing
            entry.update(recorded_at=now.isoformat(), account_currency=account['account_currency'],
                         account_snapshot=account, source='USER_REPORTED_NOT_BROKER_VERIFIED',
                         retrospective=opened < now, canonical_learning_eligible=False)
            self.repo.save_paper_record(record_id, ledger, 'manual_demo_entry', now.isoformat(), entry)
            return entry

    def close(self, key, trade_id, body):
        if not isinstance(body, dict) or set(body)-{'closed_at', 'exit_price', 'net_pnl', 'notes'}:
            raise ValueError('Unsupported closure fields')
        trade_id = identity(trade_id)
        ledger = PREFIX+key
        now = self.clock()
        with self.repo.paper_account_transaction(ledger):
            entry = self.repo.paper_record(f'{ledger}:entry:{trade_id}')
            if not entry:
                raise ValueError('Trade does not belong to this account')
            closed = instant(body.get('closed_at'))
            if not instant(entry['opened_at']) <= closed <= now:
                raise ValueError('Close time must follow entry and cannot be in the future')
            record = dict(trade_id=trade_id, account_key=key, closed_at=closed.isoformat(),
                          exit_price=positive(body.get('exit_price')), net_pnl=number(body.get('net_pnl')),
                          notes=text(body.get('notes', ''), 'notes'))
            record_id = f'{ledger}:close:{trade_id}'
            existing = self.repo.paper_record(record_id)
            if existing:
                if any(existing[k] != v for k, v in record.items()):
                    raise ValueError('Trade already closed with different details')
                return existing
            record.update(recorded_at=now.isoformat(), account_currency=entry['account_currency'],
                          source='USER_REPORTED_NET_OF_ALL_COSTS', canonical_learning_eligible=False)
            self.repo.save_paper_record(record_id, ledger, 'manual_demo_close', now.isoformat(), record)
            return record

    def review(self, key, *, as_of=None):
        at = as_of or self.clock()
        ledger = PREFIX+key
        entries = self.repo.paper_records(ledger, 'manual_demo_entry', as_of=at.isoformat(), limit=1000)
        trades = []
        for entry in entries:
            closure = self.repo.paper_record(f"{ledger}:close:{entry['trade_id']}")
            if closure and instant(closure['recorded_at']) > at:
                closure = None
            net = closure['net_pnl'] if closure else None
            assessment = []
            risk = entry.get('planned_risk')
            stop = entry.get('stop_price')
            sign = 1 if entry['direction'] == 'LONG' else -1
            if not risk or not stop:
                assessment.append('Risk plan incomplete: record both initial stop and planned monetary loss to review risk discipline.')
            if stop and sign*(entry['entry_price']-stop) <= 0:
                assessment.append('Recorded initial stop is not on the loss-limiting side of entry; check the reported plan.')
            if net is not None and risk and net < -risk:
                assessment.append('Reported net loss exceeded the stated planned loss, including costs.')
            if entry['retrospective']:
                assessment.append('Plan entered retrospectively: cannot establish what was known before the trade.')
            assessment.append('Outcome alone does not establish decision quality or predictive skill.')
            trades.append({'entry': entry, 'closure': closure,
                           'outcome': 'OPEN' if net is None else 'PROFIT' if net > 0 else 'LOSS' if net < 0 else 'FLAT',
                           'assessment': assessment,
                           'r_multiple': net/risk if net is not None and risk else None})
        closed = [t for t in trades if t['closure']]
        net = sum(t['closure']['net_pnl'] for t in closed)
        patterns = {}
        for trade in closed:
            entry = trade['entry']
            cohort = (entry['instrument'], entry['idea_source'])
            group = patterns.setdefault(cohort, dict(instrument=cohort[0], idea_source=cohort[1], closed_count=0, wins=0, net_pnl=0))
            group['closed_count'] += 1
            group['wins'] += trade['outcome'] == 'PROFIT'
            group['net_pnl'] += trade['closure']['net_pnl']
        return dict(trades=trades, closed_count=len(closed), net_pnl=net,
                    patterns=list(patterns.values()),
                    wins=sum(t['outcome'] == 'PROFIT' for t in closed), as_of=at.isoformat(),
                    scope='Latest 1000 entries for this account; self-reported, not strategy validation',
                    canonical_learning_eligible=False, live_execution=False)
