# Opening Absorption Breakout (OAB)

A 30-minute intraday CVD pattern: **aggressive selling is absorbed above the
opening master candle's low, price coils near the top of a tight window, then
breaks the window high.**

Reference example: **COALINDIA, 01-10-2026**.

```
Master candle (09:15 or 09:45)
        ↓
Window of 3+ bars starts right after it
        ↓
Price holds above the master low, near it (≤ 0.8%)
        ↓
Net CVD is strongly negative (≥ 10% of window volume)
        ↓
Heaviest-selling bar barely moves price (effort without result)
        ↓
Last close sits in the upper part of the window
        ↓
Signal at window end → watch for a close above the window high
```

It combines three order-flow ideas: **absorption** (passive buyers take the
aggressive selling), **bullish CVD divergence** (CVD falls while price holds)
and Wyckoff **effort vs. result**.

## Input

One CSV per stock per day, named `<SYMBOL>_<DD-MM-YYYY>.csv`, 30-minute bars,
`Time` = candle start (IST):

`Time, open_price, high_price, low_price, close_price, open_cvd, high_cvd, low_cvd, close_cvd, volume`

Files with missing columns, unsorted timestamps, negative volume or fewer than
5 candles are rejected (not silently fixed).

## Definitions

| Term | Formula |
|---|---|
| Bar delta | `close_cvd − open_cvd` |
| HL% | `(high − low) / open × 100` |
| Window CVD selling % | `−(close_cvd[end] − open_cvd[start]) / Σ volume[start..end] × 100` |
| Window price change % | `(close[end] − open[start]) / open[start] × 100` |
| Post-master change % | `(close[end] − master_close) / master_close × 100` |
| Hold % | `(window_low − master_low) / master_low × 100` |
| Heaviest-selling bar | window bar with the most negative bar delta |
| Heavy bar return % | `(close − open) / open × 100` of that bar |
| Heavy bar delta % | `−delta / volume × 100` of that bar |
| Close in window | `(close[end] − window_low) / (window_high − window_low)` |

## Rules (all must pass)

| # | Rule | Default |
|---|---|---|
| 1 | Master candle is the 09:15 or 09:45 bar | `master_candidates=(0,1)` |
| 2 | Window starts at most 1 bar after the master | `max_gap=1` |
| 3 | Window length | `min_bars=3` |
| 4 | No window low at or below the master low | — |
| 5 | Post-master change | `≥ −0.5%` |
| 6 | Window price change | `−0.3% … +0.3%` |
| 7 | Window CVD selling | `≥ 10%` |
| 8 | Hold above master low | `≤ 0.8%` |
| 9 | Last bar HL% < first bar HL% | `require_compression=True` |
| 10 | Heavy bar return | `−0.25% … +0.2%` |
| 11 | Heavy bar delta | `≤ 45%` of its volume |
| 12 | Close in window | `≥ 0.45` |

The scanner keeps the **earliest-ending** valid window per stock and uses only
data up to the window end. Outcome fields (breakout, returns) use later bars
and exist only for validation.

**Trigger (not part of the signal):** a later 30m close above the window high.

### Why each bar-level rule exists

- **Heavy bar delta ≤ 45%:** bars where CVD was 50–85% of volume (FDC, KITEX,
  CEIGALL, SANDUMA) were one-sided dumping, and those stocks fell.
- **Heavy bar return −0.25% … +0.2%:** absorption means price does not move on
  the selling. A bar that rallies on negative delta (ASTERDM 10:45, +0.57%) or
  drops on it is not absorption.
- **Close in window ≥ 0.45:** across 26 tested features this separated
  breakouts from failures best (AUC 0.74).
- **Window starts right after the master:** removes setups that form hours
  later and are unrelated to the opening (MANKIND 12:45).

## Results on 01-10-2026 (506 stocks)

| Version | Setups | Breakouts | Rate |
|---|---|---|---|
| Spec scanner (original rules) | 181 | — | — |
| Master-low hold + breakout | 96 | 20 | 21% |
| + clean-window rules | 69 | 11 | 15% |
| **OAB (current)** | **8** | **6** | **75%** |

Out-of-sample check (parameters chosen on a random half of stocks, measured on
the other half, 20 times): **~37–42%** breakout rate vs ~15% baseline. Each
test half has only ~4–6 setups, so this is noisy.

| Symbol | Window | Heavy bar (ret, delta%) | Close in win | Breakout | Window → close | Breakout → close |
|---|---|---|---|---|---|---|
| BAJAJHFL | 10:15–11:15 | 10:15 (0.00%, 38) | 0.72 | 14:15 | +1.43% | +0.96% |
| COALINDIA | 10:15–11:15 | 10:45 (−0.05%, 23) | 0.79 | 11:45 | +0.46% | −0.35% |
| FINPIPE | 10:45–12:15 | 12:15 (0.00%, 44) | 0.58 | 14:45 | +0.47% | +0.05% |
| HINDCOPPER | 09:45–11:15 | 10:45 (0.00%, 21) | 0.62 | 15:15 | +0.24% | 0.00% |
| JYOTICNC | 10:15–11:15 | 10:15 (−0.17%, 38) | 0.48 | 14:45 | +1.42% | +0.64% |
| PETRONET | 09:45–11:15 | 09:45 (−0.21%, 34) | 0.51 | 14:45 | +0.74% | 0.00% |
| JSWSTEEL | 10:15–11:15 | 10:45 (+0.01%, 19) | 0.84 | — | −1.75% | — |
| ZEEL | 09:45–10:45 | 10:45 (+0.01%, 14) | 0.52 | — | −2.00% | — |

## Known limitations

- **One trading day.** All thresholds were tuned on 01-10-2026. Treat them as
  hypotheses until confirmed on more dates.
- **Breakout entry earned little.** From the breakout close, breakouts
  averaged about +0.2% to the day's close; most broke out after 14:15.
  COALINDIA fell back through the window low after breaking out.
- **Weak heavy bars.** Both failures (JSWSTEEL, ZEEL) had heavy-bar delta of
  only 14–19%. A minimum of ~20% would remove them but is untested.
- **Related but separate pattern:** APOLLOTYRE-type *Breakout-Retest
  Absorption* (heavy selling right after a breakout) is not covered.

## Next validation steps

1. Run `validate.py` on more `data/CVD_Scanner_<date>` folders.
2. Compare entries: window end vs breakout close, with stops at window low or
   master low.
3. Check whether a minimum heavy-bar delta (~20%) holds up out of sample.
