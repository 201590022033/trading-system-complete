"""Immutable daily research inputs and fail-closed window admission."""
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal
from domain.evaluation.experiment import configuration_hash, utc


def number(value):
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError('finite number required')
    return result


@dataclass(frozen=True)
class Session:
    key: str
    open_at: datetime
    close_at: datetime

    def __post_init__(self):
        for name in ('open_at', 'close_at'):
            object.__setattr__(self, name, utc(getattr(self, name), name))
        if not self.key or self.open_at >= self.close_at:
            raise ValueError('session identity and ordered times required')


@dataclass(frozen=True)
class Bar:
    session: str
    available_at: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    activity: Decimal | None = None
    estimated: bool = False

    def __post_init__(self):
        object.__setattr__(self, 'available_at', utc(self.available_at, 'available_at'))
        # Numeric validation belongs to admission so unseen bad data is irrelevant.


@dataclass(frozen=True)
class Manifest:
    instrument: str
    product: str
    currency: str
    provider: str
    retrieved_at: datetime
    price_basis: str
    activity_basis: str
    calendar_id: str
    calendar_verified: bool
    grade: str
    universe_basis: str
    action_basis: str
    revision: str
    sessions: tuple[Session, ...]
    bars: tuple[Bar, ...]

    def __post_init__(self):
        object.__setattr__(self, 'retrieved_at', utc(self.retrieved_at, 'retrieved_at'))
        if not isinstance(self.sessions, tuple) or not isinstance(self.bars, tuple):
            raise ValueError('immutable tuples required')
        if not all((self.instrument, self.product, self.currency, self.provider,
                    self.calendar_id, self.universe_basis, self.revision)):
            raise ValueError('complete provenance required')
        if self.price_basis != 'RAW' or self.action_basis not in {'NONE_VERIFIED', 'EXPLICIT'}:
            raise ValueError('raw prices with explicit or verified absent actions required')
        if self.grade not in {'SYNTHETIC', 'RECONSTRUCTED', 'POINT_IN_TIME'}:
            raise ValueError('explicit data grade required')
        keys = [s.key for s in self.sessions]
        if len(set(keys)) != len(keys) or any(a.close_at >= b.open_at for a, b in zip(self.sessions, self.sessions[1:])):
            raise ValueError('unique chronological nonoverlapping sessions required')

    @property
    def sha256(self):
        return configuration_hash(asdict(self))

    def admit(self, start: str, end: str, as_of: datetime, *, activity_required=False):
        """Admit a requested completed window; never compress missing sessions."""
        now = utc(as_of, 'as_of')
        if not self.calendar_verified:
            raise ValueError('verified calendar required (synthetic fixtures may explicitly verify their toy calendar)')
        keys = [s.key for s in self.sessions]
        if start not in keys or end not in keys or keys.index(start) > keys.index(end):
            raise ValueError('window outside calendar')
        sessions = self.sessions[keys.index(start):keys.index(end)+1]
        eligible = [s for s in sessions if s.close_at <= now]
        visible = [b.session for b in self.bars if b.session in {s.key for s in eligible} and b.available_at <= now]
        if visible != [s.key for s in eligible]:
            raise ValueError('ordered complete unique session bars required')
        rows = []
        for session in eligible:
            matches = [b for b in self.bars if b.session == session.key and b.available_at <= now]
            if len(matches) != 1:
                raise ValueError('missing or duplicate expected session')
            b = matches[0]
            if b.estimated or b.available_at < session.close_at:
                raise ValueError('real completed bar required')
            o, h, l, c = (number(getattr(b, k)) for k in ('open', 'high', 'low', 'close'))
            if min(o, h, l, c) <= 0 or l > min(o, c) or h < max(o, c):
                raise ValueError('invalid OHLC')
            if b.activity is not None and number(b.activity) < 0:
                raise ValueError('negative activity')
            if activity_required and (b.activity is None or self.activity_basis != 'TRADED_SHARES'):
                raise ValueError('verified traded-share activity required')
            rows.append(b)
        return tuple(rows)
