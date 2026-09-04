"""
JSE Trading Prototype - app.py
--------------------------------
A self-contained Flask + Flask-SocketIO server that simulates a live
JSE (Johannesburg Stock Exchange) ticker feed and streams JSON price
updates to a browser UI in real time.

Requirements:
    pip install flask flask-socketio

Run:
    python app.py
Then open http://localhost:5000 in a browser.
"""

import random
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, render_template_string
from flask_socketio import SocketIO, emit

from provider_interfaces import SuggestionState, TradeSuggestion

# --------------------------------------------------------------------------
# App setup
# --------------------------------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = "jse-prototype-secret"
socketio = SocketIO(app, cors_allowed_origins="*")

TICK_INTERVAL = 1.0  # seconds between broadcast ticks

# --------------------------------------------------------------------------
# Simulated market state (prices quoted in ZAR)
# --------------------------------------------------------------------------

INSTRUMENTS = {
    "AGL": {"name": "Anglo American",          "price": 628.40,  "volatility": 0.0018},
    "ANG": {"name": "AngloGold Ashanti",       "price": 486.75,  "volatility": 0.0025},
    "BVT": {"name": "Bidvest Group",           "price": 264.10,  "volatility": 0.0012},
    "CPI": {"name": "Capitec Bank Holdings",   "price": 2415.00, "volatility": 0.0016},
    "FSR": {"name": "FirstRand",               "price": 71.85,   "volatility": 0.0011},
    "GFI": {"name": "Gold Fields",             "price": 289.30,  "volatility": 0.0024},
    "MTN": {"name": "MTN Group",               "price": 138.60,  "volatility": 0.0017},
    "NPN": {"name": "Naspers",                 "price": 3542.00, "volatility": 0.0019},
    "PRX": {"name": "Prosus",                  "price": 765.40,  "volatility": 0.0018},
    "SBK": {"name": "Standard Bank Group",     "price": 214.75,  "volatility": 0.0012},
    "SHP": {"name": "Shoprite Holdings",       "price": 271.90,  "volatility": 0.0010},
    "SOL": {"name": "Sasol",                   "price": 148.25,  "volatility": 0.0026},
    "VOD": {"name": "Vodacom Group",           "price": 117.30,  "volatility": 0.0009},
}

# Initialise session reference data
for _inst in INSTRUMENTS.values():
    _inst["open"] = _inst["price"]
    _inst["volume"] = random.randint(100_000, 5_000_000)


# --------------------------------------------------------------------------
# Simulation engine
# --------------------------------------------------------------------------

def build_quote(symbol, inst, prev_price=None):
    """Build a JSON-serialisable quote dict for one instrument."""
    price = inst["price"]
    spread = price * random.uniform(0.0004, 0.0012)
    day_change = price - inst["open"]

    if prev_price is None or price == prev_price:
        direction = "flat"
    else:
        direction = "up" if price > prev_price else "down"

    return {
        "symbol": symbol,
        "name": inst["name"],
        "price": round(price, 2),
        "direction": direction,
        "bid": round(price - spread / 2, 2),
        "ask": round(price + spread / 2, 2),
        "change": round(day_change, 2),
        "change_pct": round(day_change / inst["open"] * 100, 2),
        "volume": inst["volume"],
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }


def simulate_tick():
    """Advance every instrument by one random-walk step and return quotes."""
    quotes = []
    for symbol, inst in INSTRUMENTS.items():
        prev_price = inst["price"]
        drift = random.gauss(0.0, inst["volatility"])
        inst["price"] = max(0.01, prev_price * (1 + drift))
        inst["volume"] += random.randint(500, 25_000)
        quotes.append(build_quote(symbol, inst, prev_price))
    return quotes


def current_state():
    """Return quotes for all instruments without mutating prices."""
    return [build_quote(sym, inst) for sym, inst in INSTRUMENTS.items()]


def demo_suggestion():
    """Fabricated rejected ticket for UI review; never an HR9 recommendation."""
    now = datetime.now(timezone.utc)
    price = round(INSTRUMENTS["SOL"]["price"], 2)
    return TradeSuggestion(
        suggestion_id="demo-sol-review-only", instrument="SOL · Sasol",
        timestamp=now, data_timestamp=now, data_source="simulated random walk",
        direction="buy", horizon="DEMO: 3 sessions", entry=price,
        stop=round(price * .97, 2), target=round(price * 1.06, 2),
        position_size=10, defined_risk=round(price * .03 * 10, 2),
        confidence=.42, evidence="Fabricated UI example; not validated evidence",
        rationale=("Demonstrates the future decision-card layout.",
                   "HR10 rejected every HR9 instrument × horizon cell."),
        strategy_version="ui-demo-v1", state=SuggestionState.REJECTED,
        stale_after=now + timedelta(minutes=5),
    )


def ticker_worker():
    """Background worker: continuously simulates and broadcasts ticker data."""
    app.logger.info("Ticker worker started - streaming every %.1fs", TICK_INTERVAL)
    while True:
        quotes = simulate_tick()
        socketio.emit("ticker_update", quotes)
        socketio.sleep(TICK_INTERVAL)


# --------------------------------------------------------------------------
# Socket.IO event handlers
# --------------------------------------------------------------------------

@socketio.on("connect")
def handle_connect():
    app.logger.info("Client connected")
    # Send an immediate snapshot so the UI populates without waiting for a tick
    emit("ticker_update", current_state())


@socketio.on("disconnect")
def handle_disconnect():
    app.logger.info("Client disconnected")


# --------------------------------------------------------------------------
# HTTP routes
# --------------------------------------------------------------------------

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>JSE Trading Prototype</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<style>
  * { box-sizing: border-box; }
  body { background:#0d1117; color:#e6edf3; font-family:'Segoe UI',Arial,sans-serif;
         margin:0; padding:24px; }
  main { max-width:1180px; margin:auto; }
  header { display:flex; align-items:center; justify-content:space-between;
           border-bottom:1px solid #21262d; padding-bottom:12px; }
  h1 { font-size:20px; margin:0; }
  h1 span { color:#8b949e; font-weight:400; font-size:13px; margin-left:8px; }
  .data-state { background:#9e6a03; color:#fff; border-radius:4px; padding:5px 8px;
                font-size:11px; font-weight:700; letter-spacing:.08em; }
  #status { font-size:13px; font-weight:600; }
  #status.connected { color:#3fb950; }
  #status.disconnected { color:#f85149; }
  .card { margin-top:22px; background:#161b22; border:1px solid #30363d;
          border-radius:12px; padding:22px; }
  .warning { color:#ffdf8b; background:#332701; padding:10px; border-radius:6px;
             font-weight:700; }
  .decision-head { display:flex; justify-content:space-between; gap:16px; align-items:start; }
  .instrument { color:#8b949e; font-size:13px; text-transform:uppercase; letter-spacing:.08em; }
  .action { font-size:42px; font-weight:800; color:#3fb950; line-height:1; margin:8px 0; }
  .price { font-size:30px; font-family:Consolas,monospace; }
  .state-rejected { color:#f85149; border:1px solid #f85149; padding:6px 9px;
                    border-radius:5px; font-weight:700; }
  .grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:18px 0; }
  .metric { background:#0d1117; border-radius:7px; padding:12px; }
  .label { display:block; color:#8b949e; font-size:11px; text-transform:uppercase; margin-bottom:5px; }
  .value { font-weight:700; font-size:17px; }
  .why { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
  details { border-top:1px solid #30363d; margin-top:16px; padding-top:12px; }
  summary { cursor:pointer; color:#58a6ff; }
  .flow { color:#8b949e; margin:18px 0 10px; }
  button, .button { border:1px solid #58a6ff; color:#58a6ff; background:transparent;
                    border-radius:6px; padding:9px 12px; margin:4px 4px 4px 0;
                    text-decoration:none; display:inline-block; font:inherit; cursor:pointer; }
  button:disabled { border-color:#484f58; color:#8b949e; cursor:not-allowed; }
  textarea { width:100%; min-height:70px; background:#0d1117; color:#e6edf3;
             border:1px solid #30363d; border-radius:6px; padding:9px; }
  table { border-collapse:collapse; width:100%; margin-top:16px; font-size:14px; }
  th, td { padding:8px 12px; border-bottom:1px solid #21262d; text-align:left; }
  th { color:#8b949e; text-transform:uppercase; font-size:11px; letter-spacing:.06em; }
  .num { text-align:right; font-variant-numeric:tabular-nums;
         font-family:Consolas,'Courier New',monospace; }
  .sym { font-weight:700; color:#58a6ff; }
  .up { color:#3fb950; }
  .down { color:#f85149; }
  .flat { color:#8b949e; }
  tr.flash-up { animation:flashUp .6s ease-out; }
  tr.flash-down { animation:flashDown .6s ease-out; }
  @keyframes flashUp { from { background:rgba(63,185,80,.22); } to { background:transparent; } }
  @keyframes flashDown { from { background:rgba(248,81,73,.22); } to { background:transparent; } }
  footer { margin-top:16px; color:#8b949e; font-size:12px; }
  @media (max-width:760px) {
    body { padding:12px; } header,.decision-head { align-items:flex-start; flex-direction:column; }
    .grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
    .why { grid-template-columns:1fr; } .table-wrap { overflow-x:auto; }
    .action { font-size:36px; }
  }
</style>
</head>
<body>
<main>
<header>
  <h1>JSE Ticker <span>HUMAN REVIEW MODE</span></h1>
  <div class="data-state">SIMULATED · RESEARCH · NOT LIVE</div>
  <div id="status" class="disconnected">Connecting&hellip;</div>
</header>
<section class="card" id="decision-card">
  <div class="warning">FABRICATED DEMO · HR9/HR10 REJECTED · NOT AN EXECUTABLE TRADE</div>
  <div class="decision-head">
    <div><div class="instrument">SOL · Sasol</div><div class="action">BUY</div>
      <span class="label">Current price</span><div class="price">R <span id="idea-price">148.25</span></div>
      <small>Simulated random walk · <span id="idea-time">awaiting timestamp</span></small></div>
    <div class="state-rejected">REJECTED RESEARCH</div>
  </div>
  <div class="grid">
    <div class="metric"><span class="label">Horizon</span><span class="value">DEMO: 3 sessions</span></div>
    <div class="metric"><span class="label">Suggested entry</span><span class="value">R <span id="entry">148.25</span></span></div>
    <div class="metric"><span class="label">Stop</span><span class="value">R 143.80</span></div>
    <div class="metric"><span class="label">Target</span><span class="value">R 157.15</span></div>
    <div class="metric"><span class="label">Maximum defined risk</span><span class="value">R 44.48 demo</span></div>
    <div class="metric"><span class="label">Position size</span><span class="value">10 demo units</span></div>
    <div class="metric"><span class="label">Confidence</span><span class="value">42% · weak</span></div>
    <div class="metric"><span class="label">Execution</span><span class="value">Manual only</span></div>
  </div>
  <div class="why"><div><h3>Why this trade?</h3><p>This is fabricated to test visual hierarchy. It is not a validated signal.</p></div>
    <div><h3>Safety status</h3><p>Rejected by design. Copying is for UI review only; broker submission is unavailable.</p></div></div>
  <details><summary>Research details and diagnostics</summary>
    <p>Strategy: ui-demo-v1 · Evidence: fabricated · Regime/indicators: not applicable.</p>
    <p>HR10 outcome: 0 admitted, 40 rejected. No HR9 result is connected to this screen.</p>
  </details>
  <div class="flow">TRADE IDEA → REVIEW → OPEN / COPY TO BROKER → CONFIRM IN BROKER</div>
  <button id="copy-details">COPY DEMO DETAILS</button>
  <a class="button" href="https://www.shyft.co.za/en-ZA/Trading" target="_blank" rel="noopener">OPEN PUBLIC SHYFT PAGE</a>
  <button disabled>MARK AS EXECUTED MANUALLY — DISABLED</button>
  <button id="dismiss">DISMISS CARD</button>
</section>
<section class="card"><h2>Simulated market context</h2><div class="table-wrap">
<table>
  <thead>
    <tr>
      <th>Symbol</th><th>Instrument</th><th class="num">Last (ZAR)</th>
      <th class="num">Chg</th><th class="num">Chg %</th>
      <th class="num">Bid</th><th class="num">Ask</th>
      <th class="num">Volume</th><th>Time</th>
    </tr>
  </thead>
  <tbody id="ticker-body"></tbody>
</table>
</div></section>
<section class="card"><h2>Development feedback</h2>
  <p>Stored only in this browser. Nothing is sent to the server or committed.</p>
  <textarea id="feedback" placeholder="Confusing, unnecessary, missing, should be larger, needs explanation…"></textarea>
  <button id="save-feedback">SAVE IN THIS BROWSER</button><span id="feedback-status"></span>
</section>
<footer>Prototype only &mdash; prices are randomly simulated and do not reflect real market data.</footer>
<script>
  const socket = io();
  const tbody = document.getElementById('ticker-body');
  const statusEl = document.getElementById('status');

  document.getElementById('feedback').value = localStorage.getItem('oi1-ui-feedback') || '';
  document.getElementById('save-feedback').onclick = () => {
    localStorage.setItem('oi1-ui-feedback', document.getElementById('feedback').value);
    document.getElementById('feedback-status').textContent = ' Saved locally.';
  };
  document.getElementById('dismiss').onclick = () => document.getElementById('decision-card').hidden = true;
  document.getElementById('copy-details').onclick = () => navigator.clipboard.writeText(
    'DEMO ONLY — REJECTED RESEARCH — SOL BUY — 3 sessions — no broker submission'
  );

  socket.on('connect', () => {
    statusEl.textContent = 'CONNECTED';
    statusEl.className = 'connected';
  });

  socket.on('disconnect', () => {
    statusEl.textContent = 'DISCONNECTED';
    statusEl.className = 'disconnected';
  });

  socket.on('ticker_update', (quotes) => {
    quotes.forEach((q) => {
      if (q.symbol === 'SOL') {
        document.getElementById('idea-price').textContent = q.price.toFixed(2);
        document.getElementById('entry').textContent = q.price.toFixed(2);
        document.getElementById('idea-time').textContent = q.timestamp + ' · simulated';
      }
      let row = document.getElementById('row-' + q.symbol);
      if (!row) {
        row = document.createElement('tr');
        row.id = 'row-' + q.symbol;
        tbody.appendChild(row);
      }
      const dayCls = q.change >= 0 ? 'up' : 'down';
      row.innerHTML =
        '<td class="sym">' + q.symbol + '</td>' +
        '<td>' + q.name + '</td>' +
        '<td class="num ' + q.direction + '">' + q.price.toFixed(2) + '</td>' +
        '<td class="num ' + dayCls + '">' + q.change.toFixed(2) + '</td>' +
        '<td class="num ' + dayCls + '">' + q.change_pct.toFixed(2) + '%</td>' +
        '<td class="num">' + q.bid.toFixed(2) + '</td>' +
        '<td class="num">' + q.ask.toFixed(2) + '</td>' +
        '<td class="num">' + q.volume.toLocaleString() + '</td>' +
        '<td>' + q.timestamp + '</td>';
      row.classList.remove('flash-up', 'flash-down');
      if (q.direction !== 'flat') {
        void row.offsetWidth;  // restart CSS animation
        row.classList.add(q.direction === 'up' ? 'flash-up' : 'flash-down');
      }
    });
  });
</script>
</main>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/api/snapshot")
def snapshot():
    """REST fallback: current market state as JSON."""
    return jsonify({"data_state": "SIMULATED", "purpose": "RESEARCH",
                    "live": False, "quotes": current_state()})


@app.route("/api/demo-suggestion")
def suggestion_snapshot():
    return jsonify(demo_suggestion().to_dict())


@app.route("/health")
def health():
    return jsonify({"status": "ok", "instruments": len(INSTRUMENTS),
                    "data_state": "SIMULATED", "live": False})


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

if __name__ == "__main__":
    # Launch the simulated streaming feed as a background worker thread
    socketio.start_background_task(ticker_worker)
    socketio.run(app, host="0.0.0.0", port=5000)
