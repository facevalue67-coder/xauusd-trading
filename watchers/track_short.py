"""Track an open XAUUSD short. Args: entry sl tp1 tp2. Exits on SL or TP2."""
import json, sys, time, urllib.request
from datetime import datetime, timezone

ENTRY, SL, TP1, TP2 = (float(x) for x in sys.argv[1:5])
BE = ENTRY - 4.0  # shorts: wait for +4, then SL to entry + 2.5 (spread)
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

fired, fails, last_beat, first = set(), 0, 0, True
hi, lo = -1e9, 1e9
hi_after_be = -1e9
say(f"TRADE OPEN short entry {ENTRY:.2f} | SL {SL} | BE at {BE:.2f} | TP1 {TP1} | TP2 {TP2}")
while True:
    try:
        price, h5, l5 = fetch(); fails = 0
    except Exception as e:
        fails += 1
        if fails >= 3:
            say(f"ERROR data fetch failed 3x ({e}) - watch your platform manually"); sys.exit(1)
        time.sleep(POLL); continue
    if True:  # use live price only; candle H/L can predate entry or the breakeven move
        h5 = l5 = price; first = False
    hi, lo = max(hi, price, h5), min(lo, price, l5)
    if "be" in fired:
        hi_after_be = max(hi_after_be, price, h5)
    if lo <= BE and "be" not in fired:
        fired.add("be"); hi_after_be = price
        say(f"BREAKEVEN price reached {lo:.2f} (+{ENTRY-lo:.1f}) - move SL to {ENTRY+2.5:.2f} (entry + spread)")
    if lo <= TP1 and "tp1" not in fired:
        fired.add("tp1"); say(f"TP1 HIT {TP1} (price {price:.2f}) - take profit or trail SL to {ENTRY-2:.2f}")
    if lo <= TP2:
        say(f"TP2 HIT {TP2} (price {price:.2f}) - trade complete"); sys.exit(0)
    if hi >= SL and "be" not in fired:
        say(f"STOP LOSS HIT {SL} (high {hi:.2f}) - trade closed"); sys.exit(0)
    if "be" in fired and hi_after_be >= ENTRY:
        say(f"BREAKEVEN STOP hit: price back to {hi_after_be:.2f} - stopped near entry (~0) if SL was at entry + 2.5"); sys.exit(0)
    if hi >= SL - 1.5 and "be" not in fired and "nearsl" not in fired:
        fired.add("nearsl"); say(f"WARNING price {price:.2f} within 1.5 pts of SL {SL}")
    if time.time() - last_beat >= HEARTBEAT:
        last_beat = time.time()
        say(f"HEARTBEAT price {price:.2f} P&L {ENTRY-price:+.1f} pts | high {hi:.2f} low {lo:.2f}")
    time.sleep(POLL)
