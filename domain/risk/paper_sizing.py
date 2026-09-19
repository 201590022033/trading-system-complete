"""PAPER cash-equity portfolio adapter; M15 remains final veto."""
from dataclasses import replace
from math import floor, isfinite
from domain.risk import RiskEngine, RiskStatus, PortfolioRiskState, InstrumentRiskMetadata
from shadow_learning import stable_id


def size_paper_policy(policy, *, now, broker, book, config, peak_equity,
                      daily_loss, volume, sector, paused=False):
    account = broker.get_account()
    exposures, sectors, gross, open_risk = {}, {}, 0., 0.
    for position in broker.get_positions():
        row = book.get(position.instrument_id)
        if row is None or row.get("stop_price") is None or position.last_mark is None:
            raise ValueError("paper portfolio ancestry/mark unavailable")
        notional = position.quantity * position.last_mark
        exposures[position.instrument_id] = notional
        sectors[row["sector"]] = sectors.get(row["sector"], 0) + notional
        gross += notional
        open_risk += position.quantity * (max(0., position.last_mark-row["stop_price"])
                                         + config.slippage_per_unit) + config.commission_per_fill
    if account.equity <= 0 or account.available_cash < 0:
        raise ValueError("paper equity/cash exhausted")
    # Round-trip costs reduce risk allowance; all JSE shares share a conservative
    # exposure bucket. It is a constraint assumption, not estimated correlation.
    unreal_loss = sum(max(0., -p.unrealized_pnl) for p in broker.get_positions()) + config.commission_per_fill*len(book)
    portfolio = PortfolioRiskState(
        stable_id("paper-portfolio", config.account_id, now.isoformat(), account.available_cash, gross),
        now, config.currency, account.equity, account.available_cash,
        max(0., account.available_cash-config.commission_per_fill), gross, open_risk,
        daily_loss, unreal_loss, max(0., 1-account.equity/max(peak_equity, account.equity)),
        gross, exposures, sectors, {"JSE_CASH": gross}, paused)
    metadata = InstrumentRiskMetadata(policy.instrument_id, now, "ZAR", 1., 1., 1., 1.,
                                      sector, ("JSE_CASH",), "PAPER_FULLY_FUNDED_WHOLE_SHARE_MODEL")
    factor = {"conservative": .5, "balanced": .75, "aggressive": 1.}[config.aggression]
    policy = replace(policy, requested_risk_fraction=config.risk_fraction*factor,
                     requested_gearing=1., provenance={**policy.provenance, "aggression": config.aggression})
    risk = RiskEngine().evaluate(policy, evaluated_at=now, limits=config.risk_limits(),
                                 portfolio=portfolio, metadata=metadata)
    if risk.status not in {RiskStatus.APPROVED, RiskStatus.REDUCED}:
        return policy, risk
    if volume is None or isinstance(volume, bool) or not isfinite(volume) or volume <= 0:
        return policy, replace(risk, status=RiskStatus.UNRESOLVED,
                               approved_loss_budget=None, approved_position_size=None,
                               approved_notional=None, approved_gearing=None, estimated_margin=None,
                               estimated_loss_at_stop=None, approved_intent=None,
                               blockers=("OBSERVED_VOLUME_UNAVAILABLE",))
    commission = config.commission_per_fill
    # An opening also reserves one closing fee per held position.
    cash_room = max(0., account.available_cash - commission * (len(book) + 2))
    day_room = max(0., config.risk_limits().max_daily_loss_monetary-daily_loss-unreal_loss)
    budget = min(risk.approved_loss_budget, day_room)
    loss_per_unit = policy.stop_distance + config.slippage_per_unit
    quantity = floor(max(0., min(risk.approved_position_size, cash_room / policy.entry_price,
                                volume*config.max_volume_fraction,
                                (budget-2*commission) / loss_per_unit)))
    if quantity < 1:
        return policy, replace(risk, status=RiskStatus.REJECTED,
                               approved_loss_budget=None, approved_position_size=None,
                               approved_notional=None, approved_gearing=None, estimated_margin=None,
                               estimated_loss_at_stop=None, approved_intent=None,
                               rejection_reasons=("PAPER_CASH_VOLUME_OR_COST_LIMIT",))
    notional = quantity * policy.entry_price
    loss = quantity * loss_per_unit + 2*commission
    intent = replace(risk.approved_intent, position_size=quantity, notional=notional,
                     gearing=(gross+notional)/account.equity, estimated_margin=notional,
                     estimated_loss_at_stop=loss)
    risk = replace(risk, status=RiskStatus.REDUCED, approved_position_size=quantity,
                   approved_loss_budget=loss, approved_notional=notional,
                   approved_gearing=intent.gearing, estimated_margin=notional,
                   estimated_loss_at_stop=loss, approved_intent=intent,
                   reduction_reasons=risk.reduction_reasons+("PAPER_CASH_VOLUME_ROUNDTRIP_COST_CAP",))
    return policy, risk
