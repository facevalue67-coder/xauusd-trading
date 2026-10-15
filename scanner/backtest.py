"""Replay scan.py's rules over recent 5m history and score each signal.

Usage: python3 scanner/backtest.py [candles=5000] [sweep_min=1.0] [target=10|5]
Scoring (conservative): a candle touching both SL and target counts as SL.
Net points subtract SPREAD once per trade (long fills at ask; short SL already includes it).
"""
import os, sys
from collections import defaultdict
from datetime import timedelta

sys.path.insert(0, os.path.dirname(__file__))
import scan

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
if len(sys.argv) > 2:
    scan.SWEEP_MIN = float(sys.argv[2])
TARGET = int(sys.argv[3]) if len(sys.argv) > 3 else 10   # 5 = TP1 exit, 10 = TP2 with breakeven at +3

m5 = scan.candles("5min", N, os.environ["TWELVE_DATA_API_KEY"])


def h1_upto(i):
    buckets = defaultdict(list)
    for c in m5[max(0, i - 12 * 45):i + 1]:
        buckets[c["t"].replace(minute=0)].append(c)
    return [{"c": v[-1]["c"]} for _, v in sorted(buckets.items())][:-1]  # closed hours only


def atr(cs, n=14):
    trs = [max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"])) for p, c in zip(cs, cs[1:])]
    return sum(trs[-n:]) / n


def outcome(s, future):
    long = s["side"] == "LONG"
    be, hit_be = False, False
    for c in future[:48]:                         # 4h max hold
        adverse = c["l"] if long else c["h"]
        fav = c["h"] if long else c["l"]
        if (adverse <= s["sl"]) if long else (adverse >= s["sl"]):
            return ("BE", 0.0) if hit_be else ("SL", -s["risk"])
        if hit_be and ((adverse <= s["entry"]) if long else (adverse >= s["entry"] + scan.SPREAD)):
            return "BE", 0.0
        tp = s["tp1"] if TARGET == 5 else s["tp2"]
        if (fav >= tp) if long else (fav <= tp):
            return "TP", float(TARGET)
        if TARGET == 10 and not hit_be and ((fav >= s["entry"] + 3) if long else (fav <= s["entry"] - 3)):
            hit_be = True
            s["sl"] = s["entry"] if long else s["entry"] + scan.SPREAD
    return "OPEN", 0.0


res = []
last_t = None
for i in range(200, len(m5) - 1):
    c = m5[i]
    mins = c["t"].hour * 60 + c["t"].minute
    if 20 * 60 + 45 <= mins < 22 * 60 or not (7 * 60 <= mins < 20 * 60 + 45):
        continue                                   # same window as the workflow
    if atr(m5[i - 15:i + 1]) > scan.ATR5_MAX:
        continue
    h1 = h1_upto(i)
    if len(h1) < 25:
        continue
    trend = scan.trend_1h(h1)
    for s in scan.scan(m5[max(0, i - 59):i + 1], trend, c["t"]):
        if s["risk"] > scan.MAX_RISK or s["time"] == last_t:
            continue
        last_t = s["time"]
        o, pts = outcome(s, m5[i + 1:])
        s["out"], s["pts"] = o, pts - (0 if s["side"] == "SHORT" and o == "SL" else scan.SPREAD) if o != "OPEN" else 0
        res.append(s)

print(f"{len(m5)} candles {m5[0]['t']:%m-%d} -> {m5[-1]['t']:%m-%d %H:%M} UTC, sweep_min={scan.SWEEP_MIN}, target=+{TARGET}")
groups = defaultdict(list)
for s in res:
    groups[(s["setup"], "with" if s["with_trend"] else "counter")].append(s)
groups[("ALL", "")] = res
for k, v in sorted(groups.items()):
    if not v:
        continue
    w = sum(1 for s in v if s["out"] == "TP")
    l = sum(1 for s in v if s["out"] == "SL")
    b = sum(1 for s in v if s["out"] == "BE")
    net = sum(s["pts"] for s in v)
    print(f"{k[0]:<7}{k[1]:<8} n={len(v):<4} TP={w:<3} BE={b:<3} SL={l:<3} "
          f"win%={100*w/max(1,w+l):5.1f}  net={net:+7.1f} pts  per-trade={net/len(v):+5.2f}")
