"""OI2 operational dashboard; analysis-only, with no live execution path."""
import os

from flask import Flask, g, jsonify, render_template, request
from flask_socketio import SocketIO
from instrument_registry import instrument_list, resolve_instrument
from operational_intelligence import service
from dashboard_feeds import feeds
from market_intelligence.source_registry import SourceRegistry
from market_intelligence.store import MarketIntelligenceStore
from market_intelligence import TickerSelection
from datetime import datetime, timezone
from uuid import uuid4
from application.opportunities import OpportunityService
from application.opportunities.api import create_blueprint

market_store = MarketIntelligenceStore()
source_registry = SourceRegistry(market_store)
source_registry.seed_defaults()
market_store.close()

def request_source_registry():
    if "market_store" not in g:
        g.market_store = MarketIntelligenceStore()
    return SourceRegistry(g.market_store)
portfolio_rows = []

app = Flask(__name__); app.config["SECRET_KEY"] = "local-oi2-session"
socketio = SocketIO(app, cors_allowed_origins="*")
canonical_opportunity_service = OpportunityService()
app.register_blueprint(create_blueprint(canonical_opportunity_service))

@app.teardown_appcontext
def close_market_store(error=None):
    store = g.pop("market_store", None)
    if store is not None:
        store.close()

@app.get("/")
def index(): return render_template("dashboard.html")
@app.get("/health")
def health():
    mode = os.environ.get("APP_MODE", "DEVELOPMENT").upper()
    database_url = os.environ.get("DATABASE_URL", "").strip()
    production = mode not in {"DEVELOPMENT", "RESEARCH"}
    database = "CONFIGURED_POSTGRES" if database_url.lower().startswith(("postgresql://", "postgres://")) else (
        "MISSING_POSTGRES" if production else "LOCAL_SQLITE")
    healthy = database != "MISSING_POSTGRES"
    return jsonify(status="ok" if healthy else "degraded", application="trading-system",
                   service="oi2", database=database, mode=mode, live_execution=False), (200 if healthy else 503)
@app.get("/api/system/status")
def status(): return jsonify(service.status())
@app.get("/api/market-intelligence/sources")
def intelligence_sources():
    return jsonify(sources=[s.__dict__ for s in request_source_registry().list_policies()])
@app.post("/api/market-intelligence/sources/<source_id>")
def intelligence_source_toggle(source_id):
    body = request.get_json(silent=True) or {}
    return jsonify(source=request_source_registry().enable(source_id, bool(body.get("enabled"))).__dict__)
@app.get("/api/market-intelligence")
def market_intelligence():
    store = request_source_registry().store
    narrative = store.latest_narrative()
    return jsonify(narrative=narrative.to_dict() if narrative else None,
                   sources=[s.__dict__ for s in request_source_registry().list_policies()],
                   selections=[s.__dict__ for s in store.active_ticker_selections()],
                   state="AVAILABLE" if narrative else "UNAVAILABLE",
                   live_execution=False)
@app.post("/api/market-intelligence/pin")
def pin_intelligence():
    body = request.get_json(silent=True) or {}
    symbol, instrument_id = str(body.get("display_symbol", "")).strip(), str(body.get("instrument_id", "")).strip()
    if not symbol or not instrument_id or len(symbol) > 32 or len(instrument_id) > 64:
        return jsonify(error="instrument_id and display_symbol are required"), 400
    store = request_source_registry().store
    selection = TickerSelection(instrument_id, symbol, True, "User-pinned instrument", None, None,
                                [], datetime.now(timezone.utc).isoformat())
    store.save_ticker_selection(selection)
    return jsonify(selection=selection.__dict__, live_execution=False)
@app.get("/api/market-intelligence/provenance/<entity_type>/<entity_id>")
def intelligence_provenance(entity_type, entity_id):
    if entity_type not in {"document", "theme", "instrument_candidate", "watchlist"}:
        return jsonify(error="unsupported provenance entity"), 400
    return jsonify(edges=request_source_registry().store.provenance_for(entity_type, entity_id), live_execution=False)
@app.get("/api/market-intelligence/ticker")
def intelligence_ticker():
    selections = request_source_registry().store.active_ticker_selections()
    return jsonify(items=[s.__dict__ for s in selections], state="AVAILABLE" if selections else "UNAVAILABLE",
                   message="No pinned or AI-selected instruments are currently available." if not selections else None,
                   live_execution=False)
@app.post("/api/portfolio/csv")
def portfolio_csv():
    import csv, io
    global portfolio_rows
    body = request.get_json(silent=True) or {}
    text = body.get("csv", "")
    if not text.strip(): return jsonify(error="CSV content is required"), 400
    rows = list(csv.DictReader(io.StringIO(text)))
    required = {"instrument", "quantity"}
    if not rows or not required.issubset(rows[0]):
        return jsonify(error="CSV must include instrument and quantity columns"), 400
    portfolio_rows = rows
    return jsonify(rows=portfolio_rows, count=len(rows), state="IMPORTED_CSV", live_execution=False)
@app.get("/api/portfolio")
def portfolio(): return jsonify(rows=portfolio_rows, state="IMPORTED_CSV" if portfolio_rows else "NOT_LOADED", live_execution=False)
@app.get("/api/instruments")
def instruments(): return jsonify(instruments=instrument_list())
@app.get("/api/feed/market/<instrument>")
def market_feed(instrument):
    return respond(lambda: feeds.chart(instrument, request.args.get("period", "3mo")))
@app.get("/api/feed/news")
def news_feed(): return jsonify(feeds.news())
@app.get("/api/opportunities")
def opportunities(): return jsonify(feeds.opportunities())
@app.get("/api/market/<instrument>")
def market(instrument): return respond(lambda: service.market(instrument, request.args.get("provider", "historical")))
@app.post("/api/analysis/<instrument>")
def analysis(instrument):
    body=request.get_json(silent=True) or {}
    return respond(lambda: service.analyze(instrument, body.get("horizon","swing"), body.get("provider","historical"), bool(body.get("allow_network",False))))
@app.post("/api/analysis/<instrument>/technical")
def technical(instrument): return respond(lambda: service.technical(instrument))
@app.get("/api/technical-intelligence/<instrument>")
def technical_intelligence(instrument):
    result = service.technical(instrument)
    indicators = result.get("data", {}).get("metrics", {}) if result.get("success") else {}
    names = ("rsi", "sma", "breakout", "stochastic", "macd", "bollinger_mean_reversion", "adx_dmi", "ichimoku")
    rows = [{"name": name, "state": "CURRENTLY_CONTRIBUTING" if name in indicators or name in {"sma", "breakout", "stochastic"} else "RESEARCH_ONLY",
             "value": indicators.get(name), "signal": indicators.get(name + "_signal"),
             "reason": None if name in indicators or name in {"sma", "breakout", "stochastic"} else "Implemented in research path; not admitted to production UI scoring"}
            for name in names]
    return jsonify(instrument=resolve_instrument(instrument).to_dict(), technical=result,
                   indicators=rows, flow=[{"id":"instrument","label":"Instrument","state":"ACTIVE"},
                                          {"id":"technical","label":"Technical indicators","state":result.get("state")},
                                          {"id":"assessment","label":"Current assessment","state":"LEGACY BENCHMARK"}],
                   boundary="RESEARCH_ONLY; NO TRADE", live_execution=False)
@app.post("/api/analysis/<instrument>/news")
def news(instrument):
    body=request.get_json(silent=True) or {}
    return respond(lambda: service.news(instrument, bool(body.get("allow_network",False))))
@app.post("/api/scan/market")
def scan():
    body=request.get_json(silent=True) or {}
    return jsonify(runs=service.scan(body.get("horizon","swing")), live_execution=False)
@app.get("/api/analysis/run/<run_id>")
def run_detail(run_id):
    run=service.runs.get(run_id)
    return (jsonify(run.to_dict()),200) if run else (jsonify(error="run not found"),404)
@app.get("/api/research/<instrument>")
def research(instrument): return respond(lambda:{"instrument":resolve_instrument(instrument).to_dict(),"state":"RESEARCH","hr10":"validated no-trade boundary","promotion":"not authorized","message":"Historical diagnostics; not a current recommendation."})
@app.post("/api/trade/<suggestion_id>/manual")
def manual(suggestion_id): return jsonify(accepted=False,suggestion_id=suggestion_id,live_execution=False,reason="No OI2 strategy is admitted; broker handoff remains disabled."),409
@app.get("/api/snapshot")
def snapshot(): return jsonify(live=False,data_state="HISTORICAL",quotes=[])
@app.get("/api/demo-suggestion")
def demo(): return jsonify(state="rejected",direction="no_trade",safety={"actionable":False,"live_execution_available":False,"reasons":["demo_removed","no_admitted_strategy"]})
def respond(operation):
    try: return jsonify(operation())
    except KeyError as exc: return jsonify(error=str(exc)),404
    except ValueError as exc: return jsonify(error=str(exc)),400
if __name__ == "__main__":
    socketio.run(
        app,
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
        allow_unsafe_werkzeug=True,
    )
