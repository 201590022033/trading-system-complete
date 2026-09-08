"""OI2 operational dashboard; analysis-only, with no live execution path."""
import os

from flask import Flask, g, jsonify, render_template, request
from flask_socketio import SocketIO
from instrument_registry import instrument_list, resolve_instrument
from operational_intelligence import service
from dashboard_feeds import feeds
from market_intelligence.source_registry import SourceRegistry
from market_intelligence.store import MarketIntelligenceStore

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

@app.teardown_appcontext
def close_market_store(error=None):
    store = g.pop("market_store", None)
    if store is not None:
        store.close()

@app.get("/")
def index(): return render_template("dashboard.html")
@app.get("/health")
def health(): return jsonify(status="ok", service="oi2", live_execution=False)
@app.get("/api/system/status")
def status(): return jsonify(service.status())
@app.get("/api/market-intelligence/sources")
def intelligence_sources():
    return jsonify(sources=[s.__dict__ for s in request_source_registry().list_policies()])
@app.post("/api/market-intelligence/sources/<source_id>")
def intelligence_source_toggle(source_id):
    body = request.get_json(silent=True) or {}
    return jsonify(source=request_source_registry().enable(source_id, bool(body.get("enabled"))).__dict__)
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
