---
name: xauusd-trading
description: Fetch XAUUSD (Gold) price data and analyze it using LLM reasoning to generate scalping signals. Optimized for small accounts with tight stop losses (5 points). Use 5m/15m timeframes for precise entry timing.
---

# XAUUSD LLM Scalping Analysis

Skill for **small account scalping** with tight stop losses (~5 points / $5).

## Philosophy

You ARE the analyst. Your PRIMARY decision tool is **price structure** — where price is relative to support, resistance, swing points, and key levels.

Indicators (RSI, MACD, Stoch, etc.) are **context only** — they confirm or deny what structure is telling you. Never take a trade purely because an indicator says so. Structure first, indicators second, TradingView rating last.

**Your priority stack**:
1. Price structure (where is price relative to levels?)
2. Candle patterns (rejection wicks, engulfing, momentum)
3. Indicator confluence (do RSI/MACD/Stoch agree with structure?)
4. TradingView signal rating (treat as a secondary opinion, not gospel)

## Quick Start - Fetch Data

### 1. Real-time price + indicators (TradingView - NO DELAY)

```bash
bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_price.sh
```

Returns live price, current candle OHLC, RSI, MACD, Stoch, ADX, CCI, EMA, BB, ATR on 5m/15m/1h timeframes. **Use for current snapshot and indicator context.**

### 2. Real-time candle history (Twelve Data - NO DELAY)

```bash
# Requires: export TWELVE_DATA_API_KEY="your_key"
# Get free key: https://twelvedata.com (800 requests/day, free forever)

# 5-minute candles (primary for scalping)
bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_candles.sh 5min 30

# 15-minute candles (for trend/structure)
bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_candles.sh 15min 20

# 1-minute candles (for micro entries)
bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_candles.sh 1min 40
```

Returns last N candles with OHLC — **real-time, no delay**. Use for structure analysis: swing highs/lows, support/resistance, patterns.

**Intervals**: 1min, 5min, 15min, 30min, 1h, 4h, 1day

### 3. Fallback candle history (Yahoo Finance - ~15-20min delay, NO key needed)

```bash
bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_gold.sh 5m 1d 50
```

Only use if Twelve Data key is not set. Data is delayed ~15-20 minutes.

## Analysis Workflow

1. **Run `fetch_price.sh`** → get live price + indicators snapshot
2. **Run `fetch_candles.sh 5min 30`** → get real-time candle structure (swing points, patterns)
3. **Optionally run `fetch_candles.sh 15min 20`** → for higher timeframe trend
4. **Analyze** → structure first, indicators as context
5. **Output signal** → with checklist, levels, and probabilities

## Scalping Analysis Framework (5-Point Stop Loss)

### 1. IDENTIFY MICRO STRUCTURE
With only 5 points of risk, you need PRECISE entries:
- Find the **immediate swing high/low** (last 5-10 candles)
- Identify **micro support/resistance** levels
- Look for **tight consolidation** ranges (< 10 points)

### 2. ENTRY TIMING CRITERIA
Only signal when:
- Price is AT a clear level (not in the middle of a range)
- Recent candle shows **rejection wick** or **engulfing pattern**
- Stop loss placement is LOGICAL (behind structure, not arbitrary)

### 3. CALCULATE EXACT LEVELS
For every signal, specify:
```
Entry: [exact price]
Stop Loss: [entry ± 5 points]
Take Profit: [minimum 1:1.5 R:R = 7.5 points]
```

### 4. MOMENTUM CHECK
On 5m chart, confirm:
- Last 3-5 candles show directional bias
- No major wick rejections against your direction
- Volume/candle size increasing in your direction

### 5. EXTREME INDICATOR READINGS (High-Probability Triggers)
These extreme readings often precede reversals — use them as entry confirmations:

| Indicator | Extreme LONG Zone | Extreme SHORT Zone |
|-----------|-------------------|-------------------|
| Stochastic K | **< 10** | **> 90** |
| CCI | **< -100** | **> +100** |
| RSI | **< 30** | **> 70** |

**When multiple indicators are extreme simultaneously**, bounce probability increases significantly.

Example from real session: Stoch K hit 7.2 with CCI at -92 → price bounced 12+ points.

## Hard "NO TRADE" Gates

Before generating any signal, check these. Gates marked **HARD** = must skip. Gates marked **SOFT** = warn but can still trade.

### HARD Gate 1: Volatility Filter
- If 5m ATR > 8 points → **SKIP** (your 5-point SL is noise in this volatility)
- If 15m ATR > 20 points → **SKIP** (market too wild for scalping)

### HARD Gate 2: News Event Filter
Do NOT trade during or 15 minutes before/after these events:
- **US**: CPI, NFP (Non-Farm Payrolls), FOMC rate decisions, PCE, PPI
- **Global**: ECB/BOE/BOJ rate decisions, geopolitical shocks
- Gold can move 30-50+ points in seconds during these events. A 5-point SL is meaningless.

If you're unsure whether a news event is happening, add a warning: "Check economic calendar before entering."

### HARD Gate 3: Script Failure
- If `fetch_price.sh` returns an error or "Market may be closed" → **NO TRADE**
- If data looks stale (price hasn't changed in multiple fetches) → **NO TRADE**

### SOFT Gate 4: Spread/Slippage Cost Awareness
Gold spread is typically 2-3 points, plus ~1 point slippage on entries.

**Your REAL risk per trade**:
```
Effective SL = 5 (your SL) + 2-3 (spread) + 1 (slippage) = 8-9 points total cost
Effective TP1 = 5 (your TP) - 2-3 (spread) = 2-3 points net gain
Effective TP2 = 10 (your TP) - 2-3 (spread) = 7-8 points net gain
```

Always mention this in your analysis, but still suggest the trade if structure looks good.

### HARD Gate 5: Rollover Period (21:00-22:00 UTC)
- **DO NOT TRADE** during 21:00-22:00 UTC (daily rollover/swap time)
- Stop hunts are extremely common during this window — market makers sweep liquidity before the new session
- If you must trade during rollover, use **minimum 8-point SL** (not 5) to survive the wicks
- This gate was upgraded from SOFT to HARD based on real session experience where two consecutive 5-pt SLs were hunted during rollover

### SOFT Gate 6: Session Timing
- **Best**: London-NY overlap (13:00-17:00 UTC) — tightest spreads, best liquidity
- **OK**: London session (08:00-12:00 UTC), NY session (13:00-21:00 UTC)
- **Warn but allow**: Asian session (wider spreads, note it)

## Signal Output Format

```
## XAUUSD SCALP SIGNAL

**Action**: 🟢 BUY (Long) / 🔴 SELL (Short) / ⚪ NO TRADE
**Confidence**: [High / Medium / Low]

### Levels
- Current Price: $XXXX.XX
- Entry Zone: $XXXX.XX - $XXXX.XX
- Stop Loss: $XXXX.XX (5 points risk)
- Take Profit 1: $XXXX.XX (+5 points)
- Take Profit 2: $XXXX.XX (+10 points)

### Win Probability & Scenarios

**IMPORTANT**: These probabilities are HEURISTIC — educated guesses based on structure, not statistical models. Be honest but not paralyzed.

**Probability guidelines**:
- Use ranges: "35-45%", not "42%"
- Cap at 70% max for any single outcome
- If SL probability > TP1 probability by a wide margin → SKIP
- If everything is 33/33/33 → lean toward the direction momentum supports

Estimate how likely each outcome is based on the current structure:

| Scenario | Target | Gross Pts | Net After Spread (~3pts) | Est. Probability |
|----------|--------|-----------|--------------------------|-----------------|
| SL Hit | $XXXX | -5 | -8 (SL + spread + slip) | XX-XX% |
| TP1 Hit | $XXXX | +5 | +2 to +3 | XX-XX% |
| TP2 Hit | $XXXX | +10 | +7 to +8 | XX-XX% |

**Expected Value (cost-adjusted)**:
- TP1 play: (TP1% x net_TP1) - (SL% x net_SL) = $X.XX
- TP2 play: (TP2% x net_TP2) - (SL% x net_SL) = $X.XX

**Verdict**: [WORTH TAKING / MARGINAL / SKIP]

The goal is to help the user DECIDE, not to block all trades. If a setup has any structural edge at all, present it with honest probabilities and let the user judge.

### Pre-Signal Checklist

Answer these. Flag any "No" items as risks, but still suggest the trade if the overall picture has an edge.

| # | Check | Answer |
|---|-------|--------|
| 1 | Is price near a clear level? | Yes/No |
| 2 | Is 5m ATR reasonable (≤ 8)? | Yes/No |
| 3 | Is there a candle pattern or momentum confirming? | Yes/No |
| 4 | Does higher timeframe direction agree? | Yes/No |
| 5 | Is SL behind some structure? | Yes/No |
| 6 | No major news event right now? | Yes/No |

**Trade if**: Majority are "Yes" and #2 + #6 pass. Flag any "No" as a risk factor.

### Structure Analysis
[What micro structure you see - support/resistance, swing points]

### Entry Trigger
[Specific condition to enter - e.g., "break above 5032", "rejection candle at 5025"]

### Reasoning
[2-3 sentences on why this setup works]

### Risk Warning
This is LLM-based analysis for testing only. Not financial advice.
```

## What to Look For (5m Chart)

### 🟢 BUY (Long) Setups
1. **Support Bounce**: Price touches recent low, forms rejection wick up
2. **Breakout Pullback**: Breaks resistance, pulls back to retest, holds
3. **Higher Low**: Creates higher low after swing up, momentum continuing
4. **Stop Hunt Reversal** (High Probability): Price makes a sharp wick that sweeps previous lows by 3-5+ pts, then V-recovers. Enter LONG after candle closes back above the swept level. SL below wick (6-8 pts). Key signal: Stochastic K < 10 during wick = extreme oversold, high bounce probability.

### 🔴 SELL (Short) Setups  
1. **Resistance Rejection**: Price hits recent high, rejection wick down
2. **Breakdown Retest**: Breaks support, pulls back to retest, rejected
3. **Lower High**: Creates lower high after swing down, momentum continuing
4. **Stop Hunt Reversal** (High Probability): Price makes a sharp wick that sweeps previous highs by 3-5+ pts, then V-reverses down. Enter SHORT after candle closes back below the swept level. SL above wick (6-8 pts). Key signal: Stochastic K > 90 during wick = extreme overbought.

### ⚪ NO TRADE Conditions
- Price in middle of range (no clear level nearby)
- Choppy/whipsaw action (alternating direction candles)
- Wide spread candles (volatility too high)
- Near session open/close (unpredictable)
- **Counter-trend plain rejections** — against the 1h trend, only take a Stop Hunt Reversal (wick sweeps the level, then closes back). A plain rejection against the 1h trend lost (Trade #5).

### Execution Rules (from the trade log)
- **Short SL = wick high + 1 + spread (~2.5)**. A short's stop triggers on the ASK, so a stop placed 1-2 pts above the chart wick is effectively AT the wick. Long SL = wick low - 1 (bid = chart price). Skip if total risk > 8 pts.
- **Never widen a stop mid-trade.** Accept the planned loss.
- **Enter with a market order** on the signal (within the skip limit). Pending limits at the exact signal price missed twice — they need the chart to move a full spread past the level.

## Example Analysis Process

1. **Fetch real-time indicators**:
```bash
bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_price.sh
```

2. **Fetch real-time candle history** (for structure):
```bash
bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_candles.sh 5min 30
```

3. **Analyze**: Use candles to find swing points, support/resistance. Use indicators to confirm direction. Apply the Analysis Framework.

4. **Generate signal with exact levels** based on live price

## Multi-Timeframe (Optional)

For higher confidence, fetch multiple timeframes:

```bash
bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_price.sh
bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_candles.sh 15min 20
bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_candles.sh 5min 30
```

Rule: Only take 5m signals that ALIGN with 15m direction.

## Important Notes

1. **LLM is NOT predictive** - You are doing opinionated pattern reading, not forecasting. Scalping with tight SLs has high failure rates even among experienced human traders.
2. **Small account = strict risk** - Never risk more than 1-2% of account per trade
3. **5 points is TIGHT** - After spread+slippage, your real risk is ~8 points. Be extremely selective — most of the time the correct signal is NO TRADE.
4. **Spread eats your edge** - With ~3pt spread, your TP1 of +5pts nets only +2-3pts. You need high win rates or bigger TP2 plays.
5. **Session timing** - Best: London-NY overlap (13:00-17:00 UTC). Avoid Asian session and rollover.
6. **News kills scalpers** - A single CPI print can move gold 40 points in 1 second. Check calendar.
7. **This is experimental** - For paper trading and learning ONLY until you have evidence it works.

## Trade Management (Once in a Position)

### Breakeven Rule
- When trade reaches **+2.5 to +3 pts** profit, move SL to **breakeven** (entry price)
- This creates a "risk-free" trade — worst case you exit at 0, not -5
- Especially important after experiencing stop hunts earlier in the session
- **SHORTS — account for spread**: a short's SL triggers on the ASK (chart price + ~2-3 pt spread). Put the breakeven SL at **entry + 2.5** (not entry), or wait until **+4 to +5** before moving it. A SL exactly at entry gets hit while the chart still shows ~2-3 pts profit (Trade #4).
- **LONGS**: SL at entry is fine (long SL triggers on the bid, which is the chart price).

### Trailing Stop Option
- After hitting +5 pts, consider trailing SL to **+2 pts** (lock in some profit)
- Or hold for TP2 with breakeven SL if momentum is strong

### Session Loss Limit
- After **2 consecutive losses** (-10 pts total), STOP trading for the session
- Emotional state after losses leads to revenge trading and poor decisions
- Exception: If you identify a clear stop hunt reversal pattern, one more attempt is acceptable with WIDER SL (6-8 pts instead of 5)

### Recovery After Losses
- If you continue after losses, **widen your SL** to 6-8 pts
- Stop hunts often come in clusters during low-liquidity periods
- Accept that you're trading with worse R:R but better survival odds

## Trading Experience Log

Use this section as a running journal. Each time the user asks, append a new entry based on the actual trade outcome.

### How to log each trade

For every completed trade, add one block using this template:

```markdown
### Trade #N - YYYY-MM-DD HH:MM UTC
- Session: [London / NY / Overlap / Asian]
- Direction: [BUY / SELL]
- Setup Type: [Support Bounce / Resistance Rejection / Breakout Pullback / Stop Hunt Reversal / Other]
- Entry: [price]
- Stop Loss: [price] (5 points)
- TP1 / TP2: [price] / [price]
- Outcome: [TP1 / TP2 / SL / Manual Exit]
- Net Result (points): [+X / -X]
- Key Context: [ATR, spread estimate, news status, market condition]
- What Worked: [1-2 bullets]
- What Failed: [1-2 bullets]
- Lesson: [single sentence]
```

### Weekly review (every 10-20 trades)

After enough entries, add a summary block:

```markdown
### Weekly Review - YYYY-MM-DD
- Total Trades: X
- Wins: X | Losses: X | Win Rate: XX%
- Avg Win (pts): X.X | Avg Loss (pts): X.X
- Best Setup Type: [name + stats]
- Worst Setup Type: [name + stats]
- Most Common Mistake: [one line]
- Rule Adjustment: [one concrete rule to keep/change]
```

Rule: Experience log is for factual outcomes and lessons only. Do not rewrite past entries.

### Trade #1 - 2026-10-13 09:56 UTC
- Session: London
- Direction: BUY
- Setup Type: Support Bounce (double bottom ~4182, trigger candle wicked to 4182.10 and closed 4187.28)
- Entry: ~4187.3
- Stop Loss: 4181.8 (5.5 points, placed just under the trigger wick)
- TP1 / TP2: 4192.3 / 4197.0
- Outcome: SL (5m low 4181.60 at ~10:15-10:20 UTC)
- Net Result (points): about -5.5 plus spread (~-8 effective)
- Key Context: 5m ATR ~3.6, 15m ATR ~6, no news check done, 5m trend down (lower highs all morning) vs 1h up, $12 account on 0.01 lot = ~70% account risk
- What Worked: Level was real - price bounced ~3 pts off 4182 support; ATR gate and trigger rules were followed
- What Failed: SL sat 0.3 pts under an obvious double-bottom wick and got swept; 5m downtrend never broke (trade fought the 5m lower-high structure); active-trade monitoring started ~23 min late, so the near-breakeven high (~4190 vs BE 4190.3) went unwatched
- Lesson: Don't put the stop right under an obvious, already-tested low - require the 5m lower-high structure to break first or give the stop room beyond the sweep zone (and size so that room is affordable).

### Trade #2 - 2026-10-13 11:05 UTC
- Session: London
- Direction: BUY
- Setup Type: Stop Hunt Reversal (swept 4180-4182 support to 4178.90, 5m closed back at 4183.26)
- Entry: ~4183.3
- Stop Loss: 4177.3 (6 points, post-loss widened SL, 1+ pt under sweep wick)
- TP1 / TP2: 4188.3 / 4193.3
- Outcome: TP1 (user took profit; spot high in the next hour ~4189.75, TP2 not reached)
- Net Result (points): about +5 gross (~+2 to +3 net of spread)
- Key Context: 5m ATR ~3.6, Stoch K ~12 at the sweep, 1h uptrend intact, 4th test of the same support
- What Worked: Waited for the stop hunt to actually happen instead of placing the stop where it would be hunted; SL behind the sweep wick with 6 pts of room
- What Failed: Nothing on the trade; stop size (~9 pts with spread) was still too large for the account balance
- Lesson: The same level that stopped Trade #1 paid out once the sweep was confirmed first - let the hunt happen, then enter.

### Trade #3 - 2026-10-14 07:35 UTC
- Session: London open
- Direction: BUY
- Setup Type: Stop Hunt Reversal (day-low double bottom ~4144.5 swept, 5m closed back at 4147.56) - counter-trend vs 1h downtrend
- Entry: ~4147.6
- Stop Loss: 4141.6 (6 points), moved to breakeven 4147.56 at 08:02 after +3.4
- TP1 / TP2: 4152.5 / 4157.5
- Outcome: TP2 (TP1 hit 08:08, user held with breakeven SL, TP2 hit 08:18)
- Net Result (points): +10 gross (~+7 to +8 net of spread)
- Key Context: 5m ATR ~4.4, 15m ATR ~7.3, Stoch K ~12 at the sweep, London open volatility, tracking started immediately on entry
- What Worked: Sweep-then-close confirmation again; breakeven move at +3 protected through dips to 4148; price punched through the 4152-4155 resistance
- What Failed: Tracker falsely flagged a breakeven stop-out (compared against a pre-breakeven low) - fixed by restarting with SL at entry
- Lesson: Stop-hunt reversals at a twice-tested low worked even counter-trend at London open - 2/2 for this setup type so far.

### Trade #4 - 2026-10-14 10:25 UTC (filled ~10:37)
- Session: London
- Direction: SELL
- Setup Type: Breakdown Retest (day low 4143 broke at 10:05, retest rejected, 5m closed 4141.89)
- Entry: 4141.9 (sell limit, filled when price bounced back to ~4142.8)
- Stop Loss: 4147.9 (6 points), moved to breakeven 4141.9 at 10:56 after +3.2
- TP1 / TP2: 4136.9 / 4131.9
- Outcome: Breakeven stop (closed ~0 within 1-3 min of the move; chart bid only reached ~4141.2)
- Net Result (points): ~0 (minus any commission)
- Key Context: 5m ATR ~3.2, 1h downtrend, price chopped 4140-4145 for 2+ hours before and after the break
- What Worked: Breakeven move turned a trade that came within 2.5 pts of SL into a scratch, not a loss
- What Failed: A short's stop triggers on the ASK (chart bid + ~2-3 pt spread) - a breakeven stop at entry gets hit when the chart is still ~2-3 pts in profit; the retest was weak (price reclaimed the broken level for 15 min) inside a choppy range
- Lesson: On shorts, place the breakeven stop at entry + spread (or wait until +4 to move it), and skip breakdown retests while price is still chopping inside the old range.

### Trade #5 - 2026-10-15 07:50 UTC
- Session: London open
- Direction: SELL
- Setup Type: Resistance Rejection at 4145 (old support turned resistance) - COUNTER-TREND vs 1h uptrend
- Entry: ~4141.7 (market)
- Stop Loss: 4147.7 (6 points), widened by user to 4148.5 while losing
- TP1 / TP2: 4136.7 / 4131.7
- Outcome: SL (chart high 4146.03 at 08:01 = ask ~4148.5)
- Net Result (points): about -7 plus spread (~-9.5 effective)
- Key Context: 1h trend up (EMAs stacked bullish, MACD hist positive), London-open push, watcher was offline 07:13-07:44 from a network drop, Stoch K 86 at entry
- What Worked: Signal rules fired as designed; tracker alerted before the stop
- What Failed: Plain rejection (no sweep) taken against the 1h trend at London open; short SL was only ~2.4 chart-pts above the wick high, i.e. ~0 after spread; SL widened mid-trade (bigger loss, same outcome)
- Lesson: Counter-trend trades only on a confirmed stop-hunt sweep, never a plain rejection; short stops need wick high + 1 + spread; never widen a stop.

### Trade #6 - 2026-10-15 13:35 UTC
- Session: London-NY overlap
- Direction: BUY
- Setup Type: Breakout Pullback / retest WITH 1h uptrend (dip into 4150-4151 EMA cluster, 5m closed 4153.46)
- Entry: ~4153.5 (market, immediately)
- Stop Loss: 4147.5 (6 points)
- TP1 / TP2: 4158.5 / 4163.5
- Outcome: TP1 (closed by user at ~4158.5 within ~2 min)
- Net Result (points): +5 gross (~+2 to +3 net of spread)
- Key Context: post-US-data (12:30 jobless claims) whipsaw 4130-4168; 5m ATR gate (>8) paused signals 13:20-13:30, signal fired once ATR dipped to ~7.9; 1h trend up
- What Worked: Waited out the news chop and the ATR gate; with-trend retest (the backtest's best group); market entry filled at the signal price
- What Failed: Nothing on the trade; ATR was still near the 8 limit, so the move was fast in both directions
- Lesson: With-trend pullbacks to the 5m EMA cluster after a news spike settles are clean - and TP1 hits fast in high ATR, so take it.

### Running Review - 2026-10-15 (6 trades)
- Wins: 3 (#2 TP1, #3 TP2, #6 TP1) | Losses: 2 (#1, #5) | Breakeven: 1 (#4) | Missed fills: 2 (pending limit orders)
- Gross points: about -5.5 +5 +10 0 -7 +5 = +7.5 (net of ~2.5 spread x 6 trades: about -7.5)
- Backtest warning (scanner/backtest.py, 173 trades, 2026-09-28 to 10-15): -1.85 pts/trade at 2.5 spread; best group = with-trend retests; edge depends on real spread
- Best setup: Stop Hunt Reversal (sweep + close back) - 2/2 wins
- Worst setup: entering at an obvious level without a sweep (#1) or against the 1h trend without a sweep (#5) - 0/2
- Rule adjustments: (1) counter-trend = sweeps only; (2) short SL = wick high + 1 + spread; (3) never widen SL; (4) market orders on signal, no pending limits; (5) shorts: breakeven at +4 to entry + 2.5

## Setup

1. Get a free Twelve Data API key: https://twelvedata.com/pricing (10 seconds, free forever, 800 req/day)
2. Set it: `export TWELVE_DATA_API_KEY="your_key"`
3. Test: `bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_candles.sh 5min 10`

## File Structure

```
xauusd-trading/
├── SKILL.md              # This file
└── scripts/
    ├── fetch_price.sh    # REAL-TIME price + indicators (TradingView, no key)
    ├── fetch_candles.sh  # REAL-TIME candle history (Twelve Data, free key)
    └── fetch_gold.sh     # Fallback candles (Yahoo Finance, delayed, no key)
```

## Continuous Monitoring Mode

When asked to monitor XAUUSD for scalping opportunities, use this workflow:

### Monitor Loop Execution Rules (CRITICAL)

**This is an INFINITE loop.** You MUST continue until user explicitly says "stop", "exit", or "pause".

| State          | Action After Analysis                          |
| -------------- | ---------------------------------------------- |
| `NEUTRAL`      | `sleep 120` → fetch again → **DO NOT STOP**    |
| `WATCHING`     | `sleep 60` → fetch again → **DO NOT STOP**     |
| `CONSOLIDATING`| `sleep 90` → fetch again → **DO NOT STOP**     |
| `SIGNAL`       | Output signal → **STOP and wait for user**     |

**HARD RULES:**
- After `NEUTRAL`, `WATCHING`, or `CONSOLIDATING` → execute sleep → immediately fetch new data
- Do NOT say "let me know if you want me to continue" — just continue
- Do NOT rationalize stopping ("market seems quiet", "no setup forming") — keep monitoring
- Only stop on: `SIGNAL` state, user command, or HARD gate failure (market closed, script error)

After user responds to `SIGNAL`:
- User enters → switch to 30-second active trade monitoring
- User skips → resume normal monitoring loop with sleep

### Monitor Loop

1. **Load this skill** for all analysis
2. **Fetch data** — you MUST run BOTH scripts every cycle:
   ```bash
   # REQUIRED: Run these in parallel every monitoring cycle
   bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_price.sh
   bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_candles.sh 5min 15
   ```
   - `fetch_price.sh` → indicators (RSI, MACD, Stoch, ATR, etc.)
   - `fetch_candles.sh` → **structure** (swing highs/lows, support/resistance, patterns)
   - **DO NOT skip candles** — indicators alone cannot identify structure levels
   - Every 3-5 cycles, also fetch 15m candles for trend context:
     ```bash
     bash /home/hazeruno/.config/opencode/skill/xauusd-trading/scripts/fetch_candles.sh 15min 10
     ```
3. **Analyze** and determine state (structure first, indicators as confirmation)
4. **Wait** based on state, then repeat

### Wait Discipline (Important)

When monitoring continuously, you MUST actually pause between cycles using `sleep`.

- `WATCHING` (1 minute):
  ```bash
  sleep 60
  ```
- `NEUTRAL` (2 minutes):
  ```bash
  sleep 120
  ```
- `CONSOLIDATING` (3 minutes):
  ```bash
  # Some tool environments time out at 120s.
  # If so, split into two waits:
  sleep 90
  # run fetch scripts
  sleep 90
  ```

Rule: Do not run back-to-back fetches without waiting unless the user explicitly says "check now" or "new candle now".

### Adaptive Intervals

| State          | Description                                                    | Wait Time     |
| -------------- | -------------------------------------------------------------- | ------------- |
| `NEUTRAL`      | Price mid-range, no clear level nearby                         | **2 minutes** |
| `WATCHING`     | Price near key level, overbought/oversold, rejection forming   | **1 minute**  |
| `CONSOLIDATING`| Price stuck in tight range (<5 pts), low momentum, no breakout | **3 minutes** |
| `SIGNAL`       | Entry opportunity confirmed per skill criteria                 | **Ask user**  |

### Detecting CONSOLIDATING State

Switch to `CONSOLIDATING` when ALL of these are true:
1. **Tight range**: Last 3-5 candles have total range < 5 points (highs and lows compressed)
2. **Flat MACD**: Histogram near zero (between -0.10 and +0.10)
3. **No breakout**: Price not testing key support/resistance (stuck in middle)
4. **Low momentum**: CCI between -30 and +30, or Mom indicator flat

**Why this matters**: Checking every minute during consolidation wastes API calls and adds no value. Wait for the range to break, then switch back to WATCHING.

**Exit CONSOLIDATING**: When price breaks out of the range OR volatility expands (ATR increases, MACD histogram expands)

### State Transitions

- `NEUTRAL` → `WATCHING`: Price approaches support/resistance, or indicators reach extreme zones
- `NEUTRAL` → `CONSOLIDATING`: Price enters tight range with no momentum
- `WATCHING` → `SIGNAL`: Entry trigger confirmed (rejection wick, breakout, stop hunt reversal)
- `WATCHING` → `NEUTRAL`: Price moves away from level without triggering
- `WATCHING` → `CONSOLIDATING`: Price stalls at level, forms tight range instead of breaking
- `CONSOLIDATING` → `WATCHING`: Range breaks, price moves toward key level
- `CONSOLIDATING` → `SIGNAL`: Breakout with momentum confirms entry
- `SIGNAL` → User decides to enter or skip

### On SIGNAL

Output the full signal format (see Signal Output Format above) and ask user whether to enter.

### On Active Trade

When user enters a position:
- Switch to **30-second** monitoring intervals
- Track P&L, distance to SL/TP
- Alert on key levels (+2.5 pts for breakeven move, approaching TP, approaching SL)
- Continue until trade closes
