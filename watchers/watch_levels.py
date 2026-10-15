"""Watch XAUUSD at the day low (~4150) during a strong downtrend.

  SWEEP LONG     - wick <=4148.5 then 5m close back >=4151.5 (stop hunt of day low; counter-trend)
  RETEST SHORT   - after a 5m close <=4147.5, a later candle tags >=4149.5 and closes <4149 (with trend)
  PULLBACK SHORT - wick >=4158 (5m EMA20 area) then close <=4156 (with trend)
SL 6-8 pts, skip if wider. Stops at 20:45 UTC (rollover).
"""
import json, time, sys, urllib.request
from datetime import datetime, timezone

POLL, HEARTBEAT = 30, 600
COLS = ["close|5", "open|5", "high|5", "low|5", "ATR|5", "Stoch.K|5", "CCI20|5"]
BODY = json.dumps({"symbols": {"tickers": ["TVC:GOLD"], "query": {"types": []}}, "columns": COLS}).encode()

def fetch():
    req = urllib.request.Request("https://scanner.tradingview.com/cfd/scan", data=BODY,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return dict(zip(COLS, json.load(r)["data"][0]["d"]))

def say(msg):
    print(f"{datetime.now(timezone.utc):%H:%M:%S}Z {msg}", flush=True)

def signal(side, entry, sl, note):
    risk = abs(entry - sl)
    if risk > 8:
        say(f"SKIP {side} trigger at {entry:.2f} but stop needs {risk:.1f} pts (>8)"); return
    d = 1 if side == "LONG" else -1
    say(f"SIGNAL {side} entry {entry:.2f} | SL {sl:.2f} ({risk:.1f} pts) | TP1 {entry+5*d:.2f} | TP2 {entry+10*d:.2f} | {note}")
    sys.exit(0)

bucket, last, broke, fails, same, last_beat = None, None, False, 0, 0, 0
say("START Oct15: pullback long 4130.5/4133.5 | short 4145/4142.5")
while True:
    now = datetime.now(timezone.utc)
    if now.hour >= 21 or (now.hour == 20 and now.minute >= 45):
        say("STOP rollover window (21:00 UTC) - no new trades today"); sys.exit(0)
    try:
        s = fetch(); fails = 0
    except Exception as e:
        fails += 1
        if fails >= 3:
            say(f"ERROR data fetch failed 3x ({e}) - stopping"); sys.exit(1)
        time.sleep(POLL); continue

    b = (now.hour * 60 + now.minute) // 5
    if bucket is not None and b != bucket and last:
        o, h, l, c = last["open|5"], last["high|5"], last["low|5"], last["close|5"]
        if last["ATR|5"] and last["ATR|5"] > 8:
            say(f"GATE 5m ATR {last['ATR|5']:.2f} > 8 - no trade")
        elif l <= 4130.5 and c >= 4133.5:
            signal("LONG", c, min(l - 1.0, c - 6.0), "pullback to 4130-4132 support (1h EMA20 + session low), WITH 1h uptrend")
        elif h >= 4145.0 and c <= 4142.5:
            signal("SHORT", c, max(h + 1.0, c + 6.0), "rejection at 4145 (old support turned resistance), AGAINST 1h uptrend - lower confidence")
        elif c >= 4148.0:
            say(f"RECOVERY 5m closed {c:.2f} above 4148 - rally extending, reassess"); sys.exit(0)
        elif c <= 4127.0:
            say(f"BREAKDOWN 5m closed {c:.2f} below 4127 (1h EMA20 lost) - bounce failed, reassess"); sys.exit(0)
    bucket = b

    same = same + 1 if last and s["close|5"] == last["close|5"] else 0
    if same >= 10:
        say("ERROR price unchanged 5 min - data stale/market closed"); sys.exit(1)
    last = s
    if time.time() - last_beat >= HEARTBEAT:
        last_beat = time.time()
        say(f"HEARTBEAT [{'PULLBACK 4131-4145'}] price {s['close|5']:.2f} 5m H/L "
            f"{s['high|5']:.2f}/{s['low|5']:.2f} StochK {s['Stoch.K|5']:.1f} CCI {s['CCI20|5']:.0f}")
    time.sleep(POLL)
