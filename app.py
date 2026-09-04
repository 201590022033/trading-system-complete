"""OI2 operational dashboard; analysis-only, with no live execution path."""
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO
from instrument_registry import instrument_list, resolve_instrument
from operational_intelligence import service

app = Flask(__name__); app.config["SECRET_KEY"] = "local-oi2-session"
socketio = SocketIO(app, cors_allowed_origins="*")

@app.get("/")
def index(): return render_template("dashboard.html")
@app.get("/health")
def health(): return jsonify(status="ok", service="oi2", live_execution=False)
@app.get("/api/system/status")
def status(): return jsonify(service.status())
@app.get("/api/instruments")
def instruments(): return jsonify(instruments=instrument_list())
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
if __name__ == "__main__": socketio.run(app,host="0.0.0.0",port=5000,debug=False)
