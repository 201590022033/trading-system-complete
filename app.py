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
from datetime import datetime

from flask import Flask, jsonify, render_template_string
from flask_socketio import SocketIO, emit

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
  header { display:flex; align-items:center; justify-content:space-between;
           border-bottom:1px solid #21262d; padding-bottom:12px; }
  h1 { font-size:20px; margin:0; }
  h1 span { color:#8b949e; font-weight:400; font-size:13px; margin-left:8px; }
  #status { font-size:13px; font-weight:600; }
  #status.connected { color:#3fb950; }
  #status.disconnected { color:#f85149; }
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
</style>
</head>
<body>
<header>
  <h1>JSE Live Ticker <span>SIMULATED PROTOTYPE FEED</span></h1>
  <div id="status" class="disconnected">Connecting&hellip;</div>
</header>
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
<footer>Prototype only &mdash; prices are randomly simulated and do not reflect real market data.</footer>
<script>
  const socket = io();
  const tbody = document.getElementById('ticker-body');
  const statusEl = document.getElementById('status');

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
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


@app.route("/api/snapshot")
def snapshot():
    """REST fallback: current market state as JSON."""
    return jsonify(current_state())


@app.route("/health")
def health():
    return jsonify({"status": "ok", "instruments": len(INSTRUMENTS)})


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

if __name__ == "__main__":
    # Launch the simulated streaming feed as a background worker thread
    socketio.start_background_task(ticker_worker)
    socketio.run(app, host="0.0.0.0", port=5000)