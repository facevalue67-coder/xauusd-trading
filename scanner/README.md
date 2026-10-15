# Unattended scanner

`scan.py --loop-min 350` runs in GitHub Actions (`.github/workflows/scanner.yml`)
Mon–Fri 07:00–20:45 UTC. It wakes every second and scans each 5m candle within seconds
of its close. When it finds a setup it opens a GitHub issue assigned to the repo
owner, which the GitHub mobile app sends to your phone as a push notification.
That uses ~14 h of runner time a day: free if the repo is **public**, about
18,000 billed minutes a month (~$130) if it stays private.
Every signal, alerted or skipped, is appended to `signals/log.csv`.

## Setup (one time)
1. Repo **Settings → Secrets and variables → Actions → New repository secret**:
   `TWELVE_DATA_API_KEY`.
2. Optional **Variables** tab: `SPREAD` = your broker's XAUUSD spread in $ (default 2.5).
3. Merge to `main`. GitHub only runs schedules from the default branch.
4. Phone: install the GitHub app → enable push notifications for **Assigned** issues.
5. Test: **Actions → XAUUSD scanner → Run workflow**.

## Backtest (`backtest.py`, 5000 × 5m candles, 2026‑09‑28 → 10‑15)
| Spread | Target | Trades | Win % | Net per trade |
|---|---|---|---|---|
| 2.5 | +10 with breakeven at +3 | 173 | 42 % | **−1.85** |
| 2.5 | +5 | 173 | 57 % | **−1.84** |
| 0.5 | +10 with breakeven at +3 | 205 | 38 % | −0.34 (with-trend retest +0.11) |
| 0.0 | +10 with breakeven at +3 | 211 | 39 % | +0.20 (with-trend retest +0.46) |

At a $2–3 spread, 5‑point scalps lose money even when the win rate is above 50%.
Whether this strategy has any edge depends mostly on your real spread. Sweeps in the
trend's direction were the worst group, so the scanner skips them. Only ~2.5 weeks of
data were tested, so treat these numbers as rough.
