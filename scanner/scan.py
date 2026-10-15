"""Automated XAUUSD setup scanner for unattended runs (GitHub Actions, cron, VPS).

Finds the two setups the trade log supports, on closed 5m candles:
  SWEEP  - wick takes out a 5m swing high/low by >= SWEEP_MIN pts, candle closes back
           inside (stop hunt reversal; alerted only AGAINST the 1h trend - with-trend
           sweeps were the worst group in backtest.py)
  RETEST - with the 1h trend only: candle wicks into a broken swing level and closes
           back on the trend side
Hard gates: weekend/stale data, 20:45-22:00 UTC rollover, 5m ATR > 8, 15m ATR > 20,
stop wider than MAX_RISK. Short stops include spread (they trigger on the ask).

Usage: python3 scanner/scan.py [--lookback-min 20] [--dry-run]       one scan
       python3 scanner/scan.py --loop-min 350 [--poll 1]               live loop: wakes every
                                                                       second, scans each 5m close
Env:   TWELVE_DATA_API_KEY (required); GITHUB_TOKEN + GITHUB_REPOSITORY to open an issue
       per alert. SPREAD (default 2.5).
Out:   appends new signals to signals/log.csv. Exit 2 = gate/no data, 1 = fetch failure.
"""
import argparse, csv, json, os, sys, time, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "signals" / "log.csv"
SWING_N = 2          # bars each side for a fractal swing point
SWEEP_MIN = 3.0      # pts beyond the level to count as a sweep (1-2 = mostly noise)
SPREAD = float(os.environ.get("SPREAD", 2.5))  # your broker's spread in $; added to short stops
MAX_RISK = 8.0       # skip if stop distance (incl. spread) is wider
MAX_DRIFT = 2.5      # skip if live price already moved this far from the signal close
ATR5_MAX, ATR15_MAX = 8.0, 20.0
TV_COLS = ["close", "ATR|5", "ATR|15", "Stoch.K|5", "CCI20|5", "RSI|5"]


def http_json(url, body=None):
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def candles(interval, n, key):
    d = http_json(f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={interval}"
                  f"&outputsize={n}&timezone=UTC&apikey={key}")
    if "values" not in d:
        raise RuntimeError(f"Twelve Data {interval}: {d.get('message', d)}")
    out = [{"t": datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc),
            "o": float(v["open"]), "h": float(v["high"]), "l": float(v["low"]), "c": float(v["close"])}
           for v in d["values"]]
    return out[::-1]  # oldest first


def tradingview():
    body = json.dumps({"symbols": {"tickers": ["TVC:GOLD"], "query": {"types": []}},
                       "columns": TV_COLS}).encode()
    d = http_json("https://scanner.tradingview.com/cfd/scan", body)
    return dict(zip(TV_COLS, d["data"][0]["d"]))


def ema(vals, n):
    k, e = 2 / (n + 1), vals[0]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
    return e


def swings(cs):
    """Fractal swing highs/lows as (index, price)."""
    hi, lo = [], []
    for i in range(SWING_N, len(cs) - SWING_N):
        win = cs[i - SWING_N:i + SWING_N + 1]
        if cs[i]["h"] == max(c["h"] for c in win):
            hi.append((i, cs[i]["h"]))
        if cs[i]["l"] == min(c["l"] for c in win):
            lo.append((i, cs[i]["l"]))
    return hi, lo


def trend_1h(h1):
    closes = [c["c"] for c in h1]
    e20_now, e20_prev = ema(closes, 20), ema(closes[:-3], 20)
    if closes[-1] > e20_now and e20_now > e20_prev:
        return "UP"
    if closes[-1] < e20_now and e20_now < e20_prev:
        return "DOWN"
    return "FLAT"


def make(side, setup, c, level, trend, note):
    if side == "LONG":
        sl = round(min(c["l"] - 1.0, c["c"] - 5.0), 2)
        risk = c["c"] - sl
        d = 1
    else:
        sl = round(max(c["h"] + 1.0 + SPREAD, c["c"] + 5.0), 2)
        risk = sl - c["c"]
        d = -1
    return {"time": c["t"].strftime("%Y-%m-%d %H:%M"), "side": side, "setup": setup,
            "level": round(level, 2), "entry": round(c["c"], 2), "sl": sl, "risk": round(risk, 1),
            "tp1": round(c["c"] + 5 * d, 2), "tp2": round(c["c"] + 10 * d, 2),
            "trend": trend, "with_trend": (trend == "UP") == (side == "LONG") and trend != "FLAT",
            "note": note}


def scan(m5, trend, since):
    sigs = []
    for i in range(len(m5) - 1, SWING_N * 2, -1):
        c = m5[i]
        if c["t"] < since:
            break
        hi, lo = swings(m5[:i])              # levels known before this candle
        hi = [p for j, p in hi if j < i - 1][-4:]
        lo = [p for j, p in lo if j < i - 1][-4:]
        for lvl in sorted(lo, reverse=True):
            if c["l"] <= lvl - SWEEP_MIN and c["c"] > lvl:
                sigs.append(make("LONG", "SWEEP", c, lvl, trend, f"swept swing low {lvl:.2f} to {c['l']:.2f}, closed back above"))
                break
        for lvl in sorted(hi):
            if c["h"] >= lvl + SWEEP_MIN and c["c"] < lvl:
                sigs.append(make("SHORT", "SWEEP", c, lvl, trend, f"swept swing high {lvl:.2f} to {c['h']:.2f}, closed back below"))
                break
        prev = m5[max(0, i - 12):i]
        if trend == "UP":   # broken swing high retested as support
            for lvl in hi:
                if any(p["c"] > lvl + 1 for p in prev) and c["l"] <= lvl + 0.5 and c["c"] > lvl + 1 and c["c"] > c["o"]:
                    sigs.append(make("LONG", "RETEST", c, lvl, trend, f"broken high {lvl:.2f} retested as support"))
                    break
        if trend == "DOWN":
            for lvl in lo:
                if any(p["c"] < lvl - 1 for p in prev) and c["h"] >= lvl - 0.5 and c["c"] < lvl - 1 and c["c"] < c["o"]:
                    sigs.append(make("SHORT", "RETEST", c, lvl, trend, f"broken low {lvl:.2f} retested as resistance"))
                    break
    return sigs


def already_logged(sig):
    if not LOG.exists():
        return False
    with LOG.open() as f:
        return any(r["time"] == sig["time"] and r["side"] == sig["side"] for r in csv.DictReader(f))


def log(sigs):
    LOG.parent.mkdir(exist_ok=True)
    new = not LOG.exists()
    with LOG.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sigs[0].keys()) + ["live", "status"])
        if new:
            w.writeheader()
        w.writerows(sigs)


def fmt(s):
    arrow = "🟢 BUY" if s["side"] == "LONG" else "🔴 SELL"
    trend = "with 1h trend" if s["with_trend"] else f"COUNTER 1h trend ({s['trend']})"
    return (f"{arrow} XAUUSD {s['setup']} @ {s['entry']} ({s['time']} UTC 5m close)\n"
            f"SL {s['sl']} ({s['risk']} pts incl. spread) | TP1 {s['tp1']} | TP2 {s['tp2']}\n"
            f"{s['note']}; {trend}. Live {s['live']}. Market order only if price still within "
            f"{MAX_DRIFT} pts of entry. Breakeven at +3 (shorts: SL to entry+2.5).")


def notify(alerts):
    """Open a GitHub issue per alert (assigned to the owner -> GitHub mobile push)."""
    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return
    for s in alerts:
        body = fmt(s) + "\n\n_Rule-based scanner, not financial advice. Check news/calendar._"
        data = json.dumps({"title": body.split("\n")[0], "body": body,
                           "assignees": [repo.split("/")[0]]}).encode()
        req = urllib.request.Request(f"https://api.github.com/repos/{repo}/issues", data=data, headers={
            "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        try:
            urllib.request.urlopen(req, timeout=20).close()
        except Exception as e:
            print(f"ERROR could not open issue: {e}")


_H1 = {"hour": None, "data": None}


def h1_cached(key, now):
    """1h candles change once an hour; refetch only then (saves Twelve Data credits)."""
    hour = now.replace(minute=0, second=0, microsecond=0)
    if _H1["hour"] != hour:
        _H1["data"], _H1["hour"] = candles("1h", 40, key), hour
    return _H1["data"]


def run_once(key, lookback_min, dry_run=False):
    """Scan recently closed 5m candles. Returns (exit_code, last_closed_candle_time)."""
    now = datetime.now(timezone.utc)
    mins = now.hour * 60 + now.minute
    if 20 * 60 + 45 <= mins < 22 * 60:
        print("GATE rollover window 20:45-22:00 UTC"); return 2, None
    try:
        m5, h1, tv = candles("5min", 60, key), h1_cached(key, now), tradingview()
    except Exception as e:
        print(f"ERROR fetch failed: {e}"); return 1, None
    m5 = [c for c in m5 if c["t"] + timedelta(minutes=5) <= now]   # closed candles only
    if not m5 or now - m5[-1]["t"] > timedelta(minutes=20):
        print(f"GATE data stale (last candle {m5[-1]['t'] if m5 else 'none'}) - market closed?"); return 2, None
    trend = trend_1h(h1)
    live = tv["close"]
    print(f"{now:%Y-%m-%d %H:%M:%S}Z price {live:.2f} | 1h trend {trend} | 5m ATR {tv['ATR|5']:.2f} "
          f"15m ATR {tv['ATR|15']:.2f} | StochK {tv['Stoch.K|5']:.1f} CCI {tv['CCI20|5']:.0f} RSI {tv['RSI|5']:.1f}",
          flush=True)
    if tv["ATR|5"] > ATR5_MAX or tv["ATR|15"] > ATR15_MAX:
        print("GATE volatility too high for 5-pt scalps"); return 2, m5[-1]["t"]

    fresh = []
    for s in scan(m5, trend, now - timedelta(minutes=lookback_min)):
        s["live"] = round(live, 2)
        if s["setup"] == "SWEEP" and s["with_trend"]:
            s["status"] = "skip: with-trend sweep (worst in backtest)"
        elif s["risk"] > MAX_RISK:
            s["status"] = f"skip: stop {s['risk']} > {MAX_RISK}"
        elif abs(live - s["entry"]) > MAX_DRIFT:
            s["status"] = f"skip: price moved {live - s['entry']:+.1f} since signal"
        else:
            s["status"] = "ALERT"
        print(f"  {s['status']:<34} {s['side']} {s['setup']} {s['time']} entry {s['entry']} sl {s['sl']}", flush=True)
        if not already_logged(s):
            fresh.append(s)
    if fresh and not dry_run:
        log(fresh)
        notify([s for s in fresh if s["status"] == "ALERT"])
    return 0, m5[-1]["t"]


def loop(key, poll, minutes, dry_run):
    """Wake every `poll` s; scan as soon as each 5m candle has closed.
    Retries a not-yet-updated candle feed every RETRY s (Twelve Data free tier: 8 req/min)."""
    RETRY = 10
    end = time.time() + minutes * 60
    scanned, fails, next_try = None, 0, 0.0
    while time.time() < end:
        now = datetime.now(timezone.utc)
        if 20 * 60 + 45 <= now.hour * 60 + now.minute < 22 * 60:
            print("STOP rollover window"); return 0
        closed = now.replace(second=0, microsecond=0) - timedelta(minutes=now.minute % 5 + 5)
        if closed != scanned and time.time() >= next_try:
            code, last = run_once(key, 15 if scanned is None else 10, dry_run)
            next_try = time.time() + RETRY
            if code == 1:
                fails += 1
                if fails >= 5:
                    return 1
                next_try = time.time() + 30 * fails
            else:
                fails = 0
            if code == 2 and last is None:
                return 0                       # market closed / stale
            if last is not None and last >= closed:
                scanned = closed               # else feed not updated yet: retry in RETRY s
        time.sleep(poll)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookback-min", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--loop-min", type=int, default=0, help="keep polling for N minutes")
    ap.add_argument("--poll", type=int, default=30, help="seconds between live checks in loop mode")
    a = ap.parse_args()
    key = os.environ.get("TWELVE_DATA_API_KEY")
    if not key:
        print("ERROR TWELVE_DATA_API_KEY not set"); return 1
    if a.loop_min:
        return loop(key, a.poll, a.loop_min, a.dry_run)
    return run_once(key, a.lookback_min, a.dry_run)[0]


if __name__ == "__main__":
    sys.exit(main())
