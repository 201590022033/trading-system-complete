"""One transactional, restartable canonical PAPER cycle. No real broker imports."""
from dataclasses import asdict, replace
from datetime import datetime, timezone
from math import isfinite
from domain.broker.paper import PaperBroker, PaperExecutionConfig, CanonicalOrderIntent, MarketObservation, OrderState
from domain.evaluation.effectiveness import FeatureOutcome
from domain.evaluation.opportunity import ResearchOpportunity, FeatureEvidenceSummary
from domain.policy.paper_geometry import resolve_paper_policy
from domain.risk import RiskEvaluation, RiskStatus, ApprovedRiskIntent
from domain.risk.paper_sizing import size_paper_policy
from shadow_learning import stable_id, timestamp
from .public_research import public_share_catalog, _identities, _available_at, refresh_public_research

VERSION = "canonical-paper-loop-v1"


def opportunity_from_dict(data):
    values = dict(data)
    values["evaluated_at"] = timestamp(values["evaluated_at"])
    values["feature_evidence_summary"] = FeatureEvidenceSummary(**values["feature_evidence_summary"])
    for name in ("uncertainty", "reasons", "blockers", "input_feature_versions"):
        values[name] = tuple(values[name])
    return ResearchOpportunity(**values)


def risk_from_dict(data):
    values = dict(data)
    values["evaluated_at"] = timestamp(values["evaluated_at"])
    values["status"] = RiskStatus(values["status"])
    values["approved_intent"] = (ApprovedRiskIntent(**values["approved_intent"])
                                  if values["approved_intent"] else None)
    return RiskEvaluation(**values)


def paper_feature_outcomes(repository, account_id, now):
    outcomes = []
    for row in repository.paper_records(account_id, "outcome", as_of=now.isoformat()):
        # Explicitly recorded strategy outcomes: no indicator attribution.
        if row["version"] != VERSION or row["mode"] != "PAPER" or row["horizon_id"] != "1d":
            continue
        if timestamp(row["recorded_at"]) > now:
            continue
        outcomes.append(FeatureOutcome(
            "paper_strategy", VERSION, "strategy", row["instrument_id"], "1d",
            row["regime_version"], row["regime_state"], 1,
            timestamp(row["decision_at"]), timestamp(row["decision_at"]),
            timestamp(row["recorded_at"]), row["gross_return"], row["net_return"],
            row["outcome_id"]))
    return tuple(outcomes)


class FrozenCharts:
    def __init__(self, charts):
        self.charts = charts

    def get_chart(self, symbol, period):
        for key, chart in self.charts.items():
            if public_share_catalog().get(key, {}).get("yahoo_symbol") == symbol:
                return chart
        raise ValueError("frozen public chart unavailable")


def causal_series(key, chart, now):
    catalog = public_share_catalog()[key]
    if chart.get("symbol") != catalog["yahoo_symbol"] or chart.get("interval") != "1d" or chart.get("currency") != "ZAR":
        raise ValueError("public chart identity/currency/cadence unavailable")
    series = []
    for row in chart.get("bars", ()):
        at = _available_at(row["timestamp"])
        if at > now:
            continue
        close = float(row["close"])
        if not isfinite(close) or close <= 0:
            raise ValueError("invalid close")
        if at <= now:
            series.append((at, close, row.get("volume")))
    if not series or any(a[0] >= b[0] for a, b in zip(series, series[1:])):
        raise ValueError("ordered complete sessions unavailable")
    return series[-400:]


class PaperLoop:
    def __init__(self, repository, config):
        self.repository, self.config = repository, config

    def initialize(self):
        broker = PaperBroker(self.config.starting_cash, PaperExecutionConfig(
            VERSION, self.config.slippage_per_unit, self.config.commission_per_fill, self.config.currency))
        initial = {"mode": "PAPER", "version": VERSION, "config": self.config.to_dict(),
                   "broker": broker.snapshot(), "book": {}, "pending": [], "last_evaluated_at": None,
                   "peak_equity": self.config.starting_cash, "daily_loss": 0., "loss_day": None,
                   "ranking_record_id": None, "status": "INITIALIZED"}
        self.repository.create_paper_account(self.config.account_id, initial)
        if self.repository.paper_account(self.config.account_id)["config"] != self.config.to_dict():
            raise ValueError("paper account configuration changed; use a new account identity")

    def cycle(self, job_key, frozen, *, paused=False):
        now = timestamp(frozen["evaluated_at"])
        if frozen["job_key"] != job_key:
            raise ValueError("frozen input identity mismatch")
        rid = stable_id("paper-result", self.config.account_id, job_key)
        with self.repository.paper_account_transaction(self.config.account_id) as state:
            prior = self.repository.paper_record(rid)
            if prior is not None:
                return prior
            if state["last_evaluated_at"] and timestamp(state["last_evaluated_at"]) >= now:
                raise ValueError("paper cycles must advance causally")
            charts = frozen["input"].get("charts", {})
            series, unavailable = {}, []
            for key in self.config.universe:
                try:
                    values = causal_series(key, charts[key], now)
                    if (now-values[-1][0]).total_seconds() > self.config.max_price_age_seconds:
                        raise ValueError("stale public close")
                    series[key] = values
                except (ValueError, KeyError, TypeError, OverflowError):
                    unavailable.append(key)
            broker = PaperBroker.restore(state["broker"])
            initial_fill_count = len(broker.fills())
            book = state["book"]
            if state["loss_day"] != now.date().isoformat():
                state["daily_loss"], state["loss_day"] = 0., now.date().isoformat()
            for key, values in series.items():
                instrument = _identities(key, public_share_catalog()[key])[0].instrument_id
                broker.mark(MarketObservation(instrument, values[-1][1], now, "Yahoo complete daily close; paper observation"))
            # Close first. Closing consumes an existing approval and cannot increase exposure.
            closed = []
            for instrument, trade in list(book.items()):
                values = series.get(trade["symbol"])
                if not values:
                    continue
                bar_at, price, _ = values[-1]
                if bar_at <= timestamp(trade["entry_bar_at"]):
                    continue
                reason = ("STOP" if price <= trade["stop_price"] else
                          "TARGET" if price >= trade["target_price"] else
                          "TIME_EXPIRY" if now >= timestamp(trade["time_exit_at"]) else "SESSION_EXIT")
                observation = MarketObservation(instrument, price, now, "Yahoo complete daily close; paper exit")
                order = broker.close_position("paper-position:"+instrument,
                                              observation=observation, risk=risk_from_dict(trade["risk"]))
                if order.state is not OrderState.FILLED:
                    raise ValueError("paper exit failed")
                fill = broker.fills()[-1]
                net_pnl = trade["entry_cash_effect"] + fill.net_cash_effect
                outcome_id = stable_id("paper-outcome", self.config.account_id, trade["intent_id"])
                observed_sessions = sum(at > timestamp(trade["entry_bar_at"]) for at, _, _ in values)
                outcome = {"outcome_id": outcome_id, "version": VERSION, "mode": "PAPER",
                           "instrument_id": instrument,
                           "horizon_id": "1d" if observed_sessions == 1 else "DELAYED_EXIT",
                           "observed_sessions": observed_sessions, "reason": reason,
                           "decision_at": trade["decision_at"], "entry_at": trade["entry_at"],
                           "exit_at": now.isoformat(), "recorded_at": now.isoformat(),
                           "gross_return": price/trade["entry_observed_price"]-1,
                           "net_return": net_pnl/(trade["quantity"]*trade["entry_observed_price"]),
                           "net_pnl": net_pnl, "entry_fill_id": trade["entry_fill_id"],
                           "entry_fill_record_id": stable_id("paper-fill", self.config.account_id, trade["entry_fill_id"]),
                           "exit_fill_record_id": stable_id("paper-fill", self.config.account_id, fill.fill_id),
                           "exit_fill_id": fill.fill_id, "regime_version": trade["regime_version"],
                           "regime_state": trade["regime_state"], "opportunity_id": trade["opportunity_id"]}
                self.repository.save_paper_record(outcome_id, self.config.account_id, "outcome",
                                                   now.isoformat(), outcome)
                state["daily_loss"] += max(0., -net_pnl)
                closed.append(instrument)
                del book[instrument]
            outcomes = paper_feature_outcomes(self.repository, self.config.account_id, now)
            ranking = refresh_public_research(
                fetcher=FrozenCharts({key: charts[key] for key in series}), evaluated_at=now, universe=self.config.universe,
                max_workers=1, news_report=frozen["input"].get("news"), paper_outcomes=outcomes)
            current = {o.instrument_id: o for o in ranking.opportunities}
            opened, blocked = [], []
            # Pending proposals were ranked in an earlier cycle. Recheck current eligibility.
            for pending in state["pending"]:
                key = pending["symbol"]
                original = opportunity_from_dict(pending["opportunity"])
                instrument = original.instrument_id
                if instrument in book or instrument in closed:
                    continue
                values = series.get(key)
                if not values:
                    blocked.append({"instrument_id": instrument, "reason": "CURRENT_PRICE_UNAVAILABLE"})
                    continue
                bar_at, price, volume = values[-1]
                if bar_at <= original.evaluated_at:
                    continue
                latest = current.get(instrument)
                if not latest or latest.eligibility_status != "ELIGIBLE" or latest.direction != original.direction:
                    blocked.append({"instrument_id": instrument, "reason": "OPPORTUNITY_INVALIDATED"})
                    continue
                if original.direction != "LONG":
                    blocked.append({"instrument_id": instrument, "reason": "CASH_EQUITY_SHORT_BORROW_UNAVAILABLE"})
                    continue
                if any(trade["symbol"] not in series for trade in book.values()):
                    blocked.append({"instrument_id": instrument, "reason": "PORTFOLIO_MARK_UNAVAILABLE"})
                    continue
                prior_closes = [(timestamp(at), p) for at, p in pending["structure"]]
                try:
                    policy = resolve_paper_policy(
                        original, now=now, observed_at=bar_at, observed_price=price,
                        prior_closes=prior_closes, slippage=self.config.slippage_per_unit,
                        reward_multiple=self.config.reward_multiple,
                        max_holding_seconds=self.config.max_holding_seconds)
                    policy = replace(policy, policy_id=stable_id("paper-policy", self.config.account_id, policy.policy_id))
                    sector = public_share_catalog()[key].get("sector", "UNCLASSIFIED")
                    policy, risk = size_paper_policy(
                        policy, now=now, broker=broker, book=book, config=self.config,
                        peak_equity=state["peak_equity"], daily_loss=state["daily_loss"],
                        volume=float(volume) if volume is not None else None, sector=sector, paused=paused)
                except (ValueError, TypeError):
                    blocked.append({"instrument_id": instrument, "reason": "GEOMETRY_OR_RISK_INPUT_UNAVAILABLE"})
                    continue
                self.repository.save_paper_record(policy.policy_id, self.config.account_id, "policy",
                                                   now.isoformat(), policy.to_dict())
                self.repository.save_paper_record(risk.evaluation_id, self.config.account_id, "risk",
                                                   now.isoformat(), risk.to_dict())
                if risk.status not in {RiskStatus.APPROVED, RiskStatus.REDUCED}:
                    blocked.append({"instrument_id": instrument, "reason": risk.status.value,
                                    "blockers": list(risk.blockers+tuple(risk.rejection_reasons))})
                    continue
                intent_id = stable_id("paper-intent", self.config.account_id, original.opportunity_id)
                intent = CanonicalOrderIntent(
                    intent_id, now, "PAPER", instrument, public_share_catalog()[key]["yahoo_symbol"],
                    "LONG", risk.approved_position_size, "MARKET", policy.entry_price,
                    policy.stop_price, policy.target_levels[0], "IOC", risk.evaluation_id, False,
                    {"policy_id": policy.policy_id, "opportunity_id": original.opportunity_id, "version": VERSION})
                order = broker.place_order(intent, risk=risk,
                                   observation=MarketObservation(instrument, price, now, "Yahoo complete daily close; paper entry"))
                if order.state is not OrderState.FILLED:
                    raise ValueError("paper entry failed")
                broker.mark(MarketObservation(instrument, price, now, "Yahoo complete daily close"))
                fill = broker.fills()[-1]
                book[instrument] = {
                    "symbol": key, "sector": sector, "intent_id": intent_id,
                    "opportunity_id": original.opportunity_id, "decision_at": original.evaluated_at.isoformat(),
                    "entry_at": now.isoformat(), "entry_bar_at": bar_at.isoformat(),
                    "entry_observed_price": price, "entry_cash_effect": fill.net_cash_effect,
                    "entry_fill_id": fill.fill_id, "quantity": fill.quantity,
                    "stop_price": policy.stop_price, "target_price": policy.target_levels[0],
                    "time_exit_at": policy.time_exit_at.isoformat(), "risk": risk.to_dict(),
                    "regime_version": original.regime_version, "regime_state": original.regime_context.get("trend")}
                self.repository.save_paper_record(intent_id, self.config.account_id, "intent", now.isoformat(),
                    {**dict(intent.__dict__), "created_at": now.isoformat(), "provenance": dict(intent.provenance)})
                opened.append(instrument)
            state["peak_equity"] = max(state["peak_equity"], broker.get_account().equity)
            ranked = [o for o in ranking.opportunities if o.rank is not None][:5]
            state["pending"] = []
            for o in ranked:
                key = next((key for key in series if _identities(key, public_share_catalog()[key])[0].instrument_id == o.instrument_id), None)
                if key and o.eligibility_status == "ELIGIBLE":
                    state["pending"].append({"symbol": key, "opportunity": o.to_dict(),
                                             "structure": [(at.isoformat(), price) for at, price, _ in series[key][-20:]]})
            ranking_id = stable_id("paper-ranking", self.config.account_id, job_key)
            snapshot = {"version": VERSION, "evaluated_at": now.isoformat(), "mode": "PAPER",
                        "opportunities": [o.to_dict() for o in ranking.opportunities],
                        "unavailable": list(ranking.unavailable)}
            self.repository.save_paper_record(ranking_id, self.config.account_id, "ranking", now.isoformat(), snapshot)
            if not broker.reconcile(now).clean:
                raise ValueError("paper ledger failed reconciliation")
            for fill in broker.fills()[initial_fill_count:]:
                self.repository.save_paper_record(stable_id("paper-fill", self.config.account_id, fill.fill_id),
                    self.config.account_id, "fill", now.isoformat(),
                    {**asdict(fill), "filled_at": fill.filled_at.isoformat()})
            state.update(broker=broker.snapshot(), ranking_record_id=ranking_id,
                         last_evaluated_at=now.isoformat(), status="PAUSED" if paused else "AVAILABLE")
            result = {"mode": "PAPER", "live_execution": False, "evaluated_at": now.isoformat(),
                      "opened": opened, "closed": closed, "blocked": blocked, "unavailable": unavailable,
                      "outcome_count": len(outcomes), "account": asdict(broker.get_account()),
                      "ranking_record_id": ranking_id}
            self.repository.save_paper_record(rid, self.config.account_id, "cycle", now.isoformat(), result)
            return result
