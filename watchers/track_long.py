"""Track an open XAUUSD long. Emits level-crossing events; exits on SL or TP2."""
import json, sys, time, urllib.request
from datetime import datetime, timezone

ENTRY = float(sys.argv[1]) if len(sys.argv) > 1 else 4187.3
SL, TP1, TP2 = (float(x) for x in sys.argv[2:5])
BE = ENTRY + 3.0
NEAR_SL = SL + 1.5
POLL, HEARTBEAT = 15, 300
BODY = json.dumps({"symbols": {"tickers": ["TVC:GOLD"], "query": {"types": []}},
                   "columns": ["close", "high|5", "low|5"]}).encode()

def fetch():
    req = urllib.request.Request("https://scanner.tradingview.com/cfd/scan", data=BODY,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)["data"][0]["d"]

def say(msg):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {msg}", flush=True)

fired, fails, last_beat, hi, lo = set(), 0, 0, -1e9, 1e9
say(f"TRADE OPEN long entry {ENTRY:.2f} | SL {SL} | BE at {BE:.2f} | TP1 {TP1} | TP2 {TP2}")
while True:
    try:
        price, h5, l5 = fetch(); fails = 0
    except Exception as e:
        fails += 1
        if fails >= 3:
            say(f"ERROR data fetch failed 3x ({e}) - watch your platform manually"); sys.exit(1)
        time.sleep(POLL); continue
    if True:  # live price only
        h5 = l5 = price
    hi, lo = max(hi, price, h5 or price), min(lo, price, l5 or price)
    pnl = price - ENTRY
    def once(key, cond, msg):
        if cond and key not in fired:
            fired.add(key); say(msg)
    once("be", hi >= BE, f"BREAKEVEN price reached {hi:.2f} (+{hi-ENTRY:.1f}) - move SL to {ENTRY:.2f}")
    once("tp1", hi >= TP1, f"TP1 HIT {TP1} (price {price:.2f}) - close part / trail SL to {ENTRY+2:.2f}")
    if hi >= TP2:
        say(f"TP2 HIT {TP2} (price {price:.2f}) - trade complete"); sys.exit(0)
    if lo <= SL:
        if "be" in fired:
            say(f"BACK TO ENTRY price {price:.2f} - if SL was moved to breakeven you are out at 0")
        else:
            say(f"STOP LOSS HIT {SL} (low {lo:.2f}) - trade closed")
        sys.exit(0)
    if "be" in fired and lo <= ENTRY and "beout" not in fired:
        fired.add("beout"); say(f"BREAKEVEN STOP likely hit: price back to {lo:.2f} after reaching +3")
    once("nearsl", lo <= NEAR_SL and "be" not in fired, f"WARNING price {price:.2f} within 1.5 pts of SL {SL}")
    if time.time() - last_beat >= HEARTBEAT:
        last_beat = time.time()
        say(f"HEARTBEAT price {price:.2f} P&L {pnl:+.1f} pts | high {hi:.2f} low {lo:.2f}")
    time.sleep(POLL)
