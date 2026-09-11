"""Final-veto planning engine. It has no broker or order dependency."""

from hashlib import sha256
from math import floor, isclose
from datetime import timezone

from domain.contracts.policy import StopPolicyType
from domain.policy.engine import TradePolicy
from .constitution import (ApprovedRiskIntent, FXConversion, InstrumentRiskMetadata,
                           PortfolioRiskState, RiskEvaluation, RiskLimits, RiskStatus, VERSION)


def _cap(current: float, candidate: float, reason: str, reductions: list[str]) -> float:
    if candidate < current and not isclose(candidate, current, rel_tol=1e-12, abs_tol=1e-12):
        reductions.append(reason)
        return max(0.0, candidate)
    return current


class RiskEngine:
    """Evaluate a policy against immutable point-in-time facts; never executes."""

    def evaluate(self, policy: TradePolicy, *, evaluated_at, limits: RiskLimits,
                 portfolio: PortfolioRiskState, metadata: InstrumentRiskMetadata,
                 fx: FXConversion | None = None) -> RiskEvaluation:
        if not isinstance(policy, TradePolicy):
            raise TypeError("canonical TradePolicy required")
        if evaluated_at.tzinfo is None or evaluated_at.utcoffset() is None:
            raise ValueError("evaluated_at must be timezone-aware")
        evaluated_at = evaluated_at.astimezone(timezone.utc)
        common = dict(policy=policy, evaluated_at=evaluated_at, limits=limits,
                      portfolio=portfolio, metadata=metadata)
        if any(value > evaluated_at for value in (policy.created_at, limits.effective_at,
                                                   portfolio.as_of, metadata.as_of)) or (fx and fx.as_of > evaluated_at):
            return self._empty(RiskStatus.BLOCKED, blockers=("FUTURE_INPUT",), **common)
        if metadata.instrument_id != policy.instrument_id:
            return self._empty(RiskStatus.BLOCKED, blockers=("INSTRUMENT_METADATA_MISMATCH",), **common)
        if policy.status == "BLOCKED" or portfolio.kill_switch_active or limits.emergency_trading_pause is True:
            reasons = ("POLICY_BLOCKED",) if policy.status == "BLOCKED" else ("KILL_SWITCH_ACTIVE",)
            return self._empty(RiskStatus.BLOCKED, rejection_reasons=reasons, **common)
        if policy.status != "READY_FOR_RISK_REVIEW":
            unresolved = ("STOP_GEOMETRY_UNRESOLVED",) if (policy.stop_type is StopPolicyType.UNRESOLVED or
                          policy.stop_price is None or policy.entry_price is None) else ("POLICY_NOT_READY_FOR_RISK_REVIEW",)
            return self._empty(RiskStatus.UNRESOLVED, blockers=unresolved, **common)
        if policy.stop_price is None or policy.entry_price is None:
            return self._empty(RiskStatus.UNRESOLVED, blockers=("STOP_GEOMETRY_UNRESOLVED",), **common)
        if limits.missing:
            return self._empty(RiskStatus.NOT_CONFIGURED,
                               blockers=tuple(f"NOT_CONFIGURED:{name}" for name in limits.missing), **common)
        required_state = ("equity", "margin_available", "margin_used", "current_open_risk",
                          "daily_realised_loss", "daily_unrealised_loss", "current_drawdown_fraction", "gross_notional")
        missing_state = tuple(name for name in required_state if getattr(portfolio, name) is None)
        if missing_state:
            return self._empty(RiskStatus.UNRESOLVED,
                               blockers=tuple(f"PORTFOLIO_STATE_UNAVAILABLE:{name}" for name in missing_state), **common)
        if portfolio.equity <= 0:
            return self._empty(RiskStatus.REJECTED, rejection_reasons=("ACCOUNT_EQUITY_NOT_POSITIVE",), **common)
        if any(getattr(metadata, name) is None for name in ("contract_multiplier", "lot_size", "minimum_deal_size")):
            return self._empty(RiskStatus.UNRESOLVED, blockers=("CONTRACT_METADATA_UNAVAILABLE",), **common)
        if metadata.margin_factor is None:
            return self._empty(RiskStatus.UNRESOLVED, blockers=("MARGIN_EVALUATION_UNAVAILABLE",), **common)
        conversion = 1.0
        if metadata.price_currency is None:
            return self._empty(RiskStatus.UNRESOLVED, blockers=("PRICE_CURRENCY_UNAVAILABLE",), **common)
        if metadata.price_currency != portfolio.account_currency:
            if fx is None:
                return self._empty(RiskStatus.UNRESOLVED, blockers=("FX_CONVERSION_UNAVAILABLE",), **common)
            if (fx.base_currency, fx.quote_currency) != (metadata.price_currency, portfolio.account_currency):
                return self._empty(RiskStatus.UNRESOLVED, blockers=("FX_PAIR_MISMATCH",), **common)
            conversion = fx.rate
        equity = portfolio.equity
        requested = policy.requested_loss_budget
        fraction_budget = (policy.requested_risk_fraction * equity
                           if policy.requested_risk_fraction is not None else None)
        if requested is None:
            requested = fraction_budget
        if requested is None or requested <= 0:
            return self._empty(RiskStatus.NOT_CONFIGURED, blockers=("REQUESTED_LOSS_BUDGET_NOT_CONFIGURED",), **common)
        checks: dict[str, str] = {}
        total_daily_loss = portfolio.daily_realised_loss + portfolio.daily_unrealised_loss
        rejection = []
        for name, breached in (
            ("daily_loss", total_daily_loss >= limits.max_daily_loss_monetary),
            ("drawdown", portfolio.current_drawdown_fraction >= limits.max_drawdown_fraction),
            ("portfolio_open_risk", portfolio.current_open_risk >= equity * limits.max_portfolio_open_risk_fraction),
            ("margin", portfolio.margin_used >= equity * limits.max_margin_utilization_fraction),
        ):
            checks[name] = "BREACHED" if breached else "PASS"
            if breached:
                rejection.append(f"{name.upper()}_LIMIT_BREACHED")
        if rejection:
            return self._empty(RiskStatus.REJECTED, rejection_reasons=tuple(rejection), checks=checks, **common)

        reductions: list[str] = []
        if fraction_budget is not None:
            requested = _cap(requested, fraction_budget, "REQUESTED_RISK_FRACTION_CAP", reductions)
        budget = _cap(requested, equity * limits.max_risk_per_trade_fraction,
                      "MAX_RISK_PER_TRADE_CAP", reductions)
        budget = _cap(budget, equity * limits.max_portfolio_open_risk_fraction - portfolio.current_open_risk,
                      "MAX_PORTFOLIO_OPEN_RISK_CAP", reductions)
        stop_distance = abs(policy.entry_price - policy.stop_price)
        if stop_distance <= 0:
            return self._empty(RiskStatus.UNRESOLVED, blockers=("STOP_DISTANCE_INVALID",), **common)
        loss_per_unit = stop_distance * metadata.contract_multiplier * conversion
        units = budget / loss_per_unit
        notional_per_unit = policy.entry_price * metadata.contract_multiplier * conversion
        exposure_caps = (
            (equity * limits.max_notional_exposure_fraction - portfolio.gross_notional, "MAX_NOTIONAL_EXPOSURE_CAP"),
            (equity * limits.max_instrument_exposure_fraction - portfolio.instrument_exposure.get(policy.instrument_id, 0.0), "MAX_INSTRUMENT_EXPOSURE_CAP"),
            (equity * limits.max_sector_exposure_fraction - portfolio.sector_exposure.get(metadata.sector or "UNCLASSIFIED", 0.0), "MAX_SECTOR_EXPOSURE_CAP"),
        )
        for room, reason in exposure_caps:
            units = _cap(units, room / notional_per_unit, reason, reductions)
        for bucket in metadata.correlation_buckets:
            room = equity * limits.max_correlated_exposure_fraction - portfolio.correlated_exposure.get(bucket, 0.0)
            units = _cap(units, room / notional_per_unit, f"MAX_CORRELATED_EXPOSURE_CAP:{bucket}", reductions)
        gearing_cap = limits.max_gearing
        if policy.requested_gearing is not None:
            gearing_cap = min(gearing_cap, policy.requested_gearing)
        units = _cap(units, (equity * gearing_cap - portfolio.gross_notional) / notional_per_unit,
                     "MAX_GEARING_CAP", reductions)
        margin_room = min(portfolio.margin_available,
                          equity * limits.max_margin_utilization_fraction - portfolio.margin_used)
        if metadata.margin_factor > 0:
            units = _cap(units, margin_room / (notional_per_unit * metadata.margin_factor),
                         "MAX_MARGIN_UTILIZATION_CAP", reductions)
        rounded = floor(max(0.0, units) / metadata.lot_size + 1e-12) * metadata.lot_size
        if rounded < units and not isclose(rounded, units, rel_tol=1e-12, abs_tol=1e-12):
            reductions.append("LOT_SIZE_ROUND_DOWN")
        if rounded < metadata.minimum_deal_size or rounded <= 0:
            return self._empty(RiskStatus.REJECTED, rejection_reasons=("BELOW_MINIMUM_DEAL_SIZE",),
                               checks=checks, **common)
        notional = rounded * notional_per_unit
        loss = rounded * loss_per_unit
        margin = notional * metadata.margin_factor
        gearing = (portfolio.gross_notional + notional) / equity
        approved_budget = min(budget, loss)
        status = RiskStatus.REDUCED if reductions or loss < requested else RiskStatus.APPROVED
        intent = ApprovedRiskIntent(policy.policy_id, policy.instrument_id, rounded, notional,
                                    gearing, margin, loss, portfolio.account_currency)
        checks.update({"per_trade_risk": "PASS", "instrument_exposure": "PASS",
                       "sector_exposure": "PASS", "correlated_exposure": "PASS", "gearing": "PASS"})
        return self._result(status, policy, evaluated_at, limits, portfolio, metadata,
                            approved_loss_budget=approved_budget, approved_position_size=rounded,
                            approved_notional=notional, approved_gearing=gearing,
                            estimated_margin=margin, estimated_loss_at_stop=loss,
                            reduction_reasons=tuple(dict.fromkeys(reductions)), checks=checks,
                            approved_intent=intent, fx=fx)

    def _empty(self, status, *, policy, evaluated_at, limits, portfolio, metadata,
               rejection_reasons=(), blockers=(), checks=None):
        return self._result(status, policy, evaluated_at, limits, portfolio, metadata,
                            rejection_reasons=rejection_reasons, blockers=blockers,
                            checks=checks or {})

    def _result(self, status, policy, evaluated_at, limits, portfolio, metadata, *,
                approved_loss_budget=None, approved_position_size=None, approved_notional=None,
                approved_gearing=None, estimated_margin=None, estimated_loss_at_stop=None,
                reduction_reasons=(), rejection_reasons=(), blockers=(), checks=None,
                approved_intent=None, fx=None):
        identity = f"{policy.policy_id}|{evaluated_at.isoformat()}|{limits.limits_id}|{portfolio.state_id}|{VERSION}"
        return RiskEvaluation(
            "risk:" + sha256(identity.encode()).hexdigest(), VERSION, evaluated_at,
            policy.policy_id, policy.instrument_id, status, policy.requested_loss_budget,
            policy.requested_risk_fraction, policy.requested_gearing, policy.stop_distance,
            policy.stop_price, policy.entry_reference, approved_loss_budget,
            approved_position_size, approved_notional, approved_gearing, estimated_margin,
            estimated_loss_at_stop, reduction_reasons, rejection_reasons, blockers,
            checks or {}, {"limits_id": limits.limits_id, "portfolio_state_id": portfolio.state_id,
                           "metadata_source": metadata.source,
                           "fx_source": fx.source if fx else "SAME_CURRENCY_OR_UNAVAILABLE"}, approved_intent)


__all__ = ["RiskEngine"]
