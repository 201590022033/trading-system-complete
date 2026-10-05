"""Opt-in published OST cash-share cost sensitivity, never an account invoice."""
from dataclasses import dataclass
from decimal import Decimal

from domain.backtest.acceptance import published_share_fee
from domain.backtest.data import number
from domain.backtest.engine import Costs


@dataclass(frozen=True)
class OSTCashShareCosts(Costs):
    basis: str = 'CURRENT_PUBLISHED_OST_CASH_ASSUMED_VAT_ROUNDING_NOT_HISTORICAL_INVOICE'
    schedule_version: str = 'ost-public-cash-2026-10-05-v1'
    brokerage_rate: Decimal = Decimal('.005')
    brokerage_minimum: Decimal = Decimal('110')
    strate_rate: Decimal = Decimal('.00006018')
    strate_minimum: Decimal = Decimal('6.29')
    strate_maximum: Decimal = Decimal('142.20')
    levy_rate: Decimal = Decimal('.0000033')
    purchase_tax_rate: Decimal = Decimal('.0025')
    vat_rate: Decimal = Decimal('.15')

    def __post_init__(self):
        super().__post_init__()
        if self.fee_bps or self.minimum_fee:
            raise ValueError('generic fees must not be stacked on the OST schedule')
        if not self.schedule_version:
            raise ValueError('dated schedule identity required')
        for name in ('brokerage_rate','brokerage_minimum','strate_rate','strate_minimum',
                     'strate_maximum','levy_rate','purchase_tax_rate','vat_rate'):
            object.__setattr__(self,name,number(getattr(self,name)))
        self.fee(Decimal(1),1)  # Validate rates and bounds using the shared diagnostic.

    def validate(self, manifests):
        if any(m.product!='EQUITY' or m.currency!='ZAR' for m in manifests):
            raise ValueError('OST cash-share costs require ZAR cash-equity manifests')

    def breakdown(self, notional, direction):
        return published_share_fee(notional,direction,**{name:getattr(self,name) for name in
            ('brokerage_rate','brokerage_minimum','strate_rate','strate_minimum',
             'strate_maximum','levy_rate','purchase_tax_rate','vat_rate')})

    def fee(self, notional, direction=1):
        return number(self.breakdown(notional,direction)['total'])
