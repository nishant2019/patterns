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

## Out-of-sample day: 15-09-2026 (507 stocks)

Parameters were **not** changed after seeing this day.

| Day | Market (median stock, 09:15 close → EOD) | Stocks up | Baseline setups → breakouts | OAB setups → breakouts | OAB window → close |
|---|---|---|---|---|---|
| 01-10-2026 (tuning day) | −0.75% | 28% | 86 → 13 (15%) | 8 → 6 (75%) | +0.13% |
| 15-09-2026 (unseen) | −2.23% | 6% | 37 → 5 (14%) | 5 → 1 (20%) | −0.72% |

15-09 setups: CAMS, CANBK, LLOYDSME (breakout 15:15), MCX, PNB.

- The 75% breakout rate did **not** carry over; on the unseen day OAB was
  barely above baseline (20% vs 14%, n=5).
- 15-09 was a broad selloff (94% of stocks down). The OAB picks lost less
  than the median stock (−0.72% vs about −1.6% from 10:15), a possible
  relative-strength effect, but n=5.
- Combined (2 days): 13 setups, 7 breakouts (54%); split-half out-of-sample
  31% vs 14% baseline. The combined number is inflated by the tuning day.

## Out-of-sample day: 16-09-2026 (507 stocks, up day)

Parameters unchanged. Market: median stock +1.41% from the 09:15 close, 89%
of stocks up.

Setups: APOLLOTYRE (breakout 14:45), IGL (14:45), SJVN (15:15), BANKBARODA,
CASTROLIND, GRASIM, INDUSINDBK.

### All days, OAB vs baseline (return vs market median over the same bars)

| Day | Type | OAB setups → breakouts | Baseline setups → breakouts | OAB vs market | Baseline vs market | OAB beat market |
|---|---|---|---|---|---|---|
| 01-10-2026 | Tuning, down | 8 → 6 (75%) | 86 → 13 (15%) | +0.69% | −0.04% | 6/8 |
| 15-09-2026 | Unseen, selloff | 5 → 1 (20%) | 37 → 5 (14%) | +0.70% | +0.32% | 4/5 |
| 16-09-2026 | Unseen, rally | 7 → 3 (43%) | 95 → 16 (17%) | −0.24% | −0.30% | 2/7 |

- Breakout rate beat baseline on both unseen days (20% vs 14%, 43% vs 17%).
- Return vs market: ahead on the down days, behind on the up day. On 16-09,
  OAB lagged the market by about as much as the baseline, so the filters
  added nothing there. Possibly a defensive pattern: it holds up in selloffs
  but doesn't lead rallies. Too few days to tell.

## Five-day summary (window end → close, long, vs market median)

| Day | Market | OAB setups | OAB breakout | Baseline breakout | OAB vs market | Baseline vs market | OAB beat market |
|---|---|---|---|---|---|---|---|
| 01-10 (tuning) | Down | 8 | 75% | 15% | +0.69% | −0.04% | 6/8 |
| 15-09 | Selloff | 5 | 20% | 14% | +0.70% | +0.32% | 4/5 |
| 16-09 | Rally | 7 | 43% | 17% | −0.24% | −0.30% | 2/7 |
| 17-09 | Flat | 27 | 70% | 48% | +0.55% | +0.36% | 24/27 |
| 18-09 | Mild up | 20 | 55% | 52% | −0.19% | −0.05% | 8/20 |
| **All** | | **67** | **60%** | **33%** | **+0.27%** | **+0.05%** | **66%** |

Excluding the tuning day: 59 setups, breakout rate above baseline on all four
days, and OAB beat the market on 2 of 4 days (strongly on 17-09).

## Update: 28-09-2026 added (6 days)

28-09: mild down day (median stock −0.37%). 11 setups, 3 breakouts (27%),
−0.26% window end → close (absolute), +0.11% vs market. Parameters unchanged.

| | 5 days | 6 days |
|---|---|---|
| OAB setups | 67 | 78 |
| OAB breakout rate | 60% | 55% (baseline 32%) |
| OAB vs market (window end → close) | +0.21% | +0.19% (beat market 59%, 5/6 days) |
| Long-only, hold to close | +0.16% / trade, 58% win | **+0.07%**, 53% win |
| Long-only, 2R target | +0.22% / trade | +0.15% / trade |
| Stop (master low) hit | 18 of 67 | 25 of 78 |

28-09 long-only trades: 11 trades, average −0.47%, 18% win. The edge versus
the market holds up (+0.11%), but the absolute long-only return is thin
(+0.07%/trade before costs) and is not distinguishable from zero.

The market-regime idea (skip when the market is down > 0.5%) is **not
supported by the new day**: on 28-09 the market was only about −0.2% to 0%
at the window ends, so the filter would not have skipped it, yet the
trades lost. The 6-day split is unchanged (6 setups below −0.5%: −0.52%;
72 above: +0.22%) because 28-09 contributed no setups below −0.5%.

Net: OAB still shows a relative edge over the average stock and a higher
breakout rate than the baseline, but as a standalone long-only trade it is
roughly breakeven before costs.

## Two-sided trade backtest (`two_sided.py`)

After the signal, trade whichever side of the window closes outside first:
long above the window high (stop at window low), short below the window low
(stop at window high). Exit at the stop or the last bar's close. No costs.

Five days (01-10, 15-09, 16-09, 17-09, 18-09): 67 signals, 55 trades,
12 never triggered.

| Setup | Stop | Side | Trades | Win | Avg / trade | Avg R |
|---|---|---|---|---|---|---|
| OAB | Opposite side | Long | 36 | 50% | −0.04% | +0.01 |
| OAB | Opposite side | Short | 19 | 37% | −0.26% | −0.26 |
| OAB | Opposite side | All | 55 | 45% | −0.11% | −0.08 |
| OAB | Range mid | All | 55 | 35% | −0.13% | −0.18 |
| Baseline | Opposite side | All | 336 | 46% | +0.01% | +0.02 |

Baseline per day: 01-10 −0.04%, 15-09 +0.55% (shorts on a selloff), 16-09
−0.07%, 17-09 −0.04%, 18-09 −0.08% per trade.

- **No edge as a two-sided trade.** Every version is about breakeven or
  negative before costs. The only positive day for the baseline is the 15-09
  selloff, i.e. market direction.
- **The short side is the weak side** (−0.26%/trade, 37% win). Shorting below
  the window fights the absorption the pattern is built on; several OAB
  stocks broke the window low, stopped the short, then broke out.
- **Longs are about breakeven** (50% win). OAB may only work long, and needs a
  better entry or exit than "close above window high, hold to close".

## Improvement study (5 days; scripts in `research/absorption/`)

Question: can the absorption research improve OAB? Tested features at the
window end against return to close vs the average stock, on OAB (67 setups)
and on the loose "base" set (448 setups) for more data.

**Long-only trade** (`oab_long_test.py`): enter at the window-end close, stop
at the master low, no costs.

| Exit | Trades | Win | Avg / trade | Avg R | Stopped |
|---|---|---|---|---|---|
| Hold to close | 67 | 58% | +0.16% | +0.19 | 18 |
| Target 1R | 67 | 61% | +0.16% | +0.18 | 17 |
| Target 2R | 67 | 60% | +0.22% | +0.29 | 17 |
| Target 3R | 67 | 58% | +0.16% | +0.19 | 18 |

Median risk is 0.87% of entry. The window-end long (+0.16%) is better than the
breakout entry (+0.04%) and the two-sided version (−0.11%). Target choice
makes no meaningful difference. Per day: 17-09 +0.38% (74% win), 18-09
+0.19%, 16-09 +0.18%, 01-10 −0.10%, **15-09 −0.77% (0 of 5 won)**.

**Refinements tested (none clearly improves OAB):**

| Idea (from the research) | OAB result | Base set (n=448) |
|---|---|---|
| Near the day's low (SA was stronger there) | No effect (AUC 0.37) | No effect |
| CVD selling ≤ 25% (very heavy selling is not absorbed) | +0.18% vs +0.41% for >25% (n=10) | **+0.08% vs −0.11%** |
| Longer windows (≥ 4 bars) | +0.16% vs +0.25% for 3 bars | **+0.15% vs −0.10%** (5/5 days) |
| Later windows (end ≥ 11:15) | No effect | No effect |
| Volume ratios, last-bar delta, relative strength | AUC 0.43–0.60, noise | AUC 0.50–0.53 |

The CVD-selling cap and minimum 4 bars help the loose set, but OAB's filters
already capture that effect, so nothing is gained on OAB itself.

**Market regime matters more than any feature.** Window end → close:

| Market so far (avg stock since 09:15 close) | Setups | Absolute return | Win | vs market |
|---|---|---|---|---|
| Down more than 0.5% | 6 | **−0.52%** | 33% | +0.52% |
| Otherwise | 61 | **+0.31%** | 70% | +0.19% |

OAB holds up relative to a falling market but still loses in absolute terms.
A long-only version should be skipped (or sized down) when the market is down
more than ~0.5%. Only 6 setups on 2 days, so treat as a hypothesis.

**Conclusion:** the current OAB parameters are already near what this data
supports. The practical improvements are about how it is traded (long-only,
enter at window end, stop at master low, skip falling markets), not extra
entry filters. SAB cannot be added as a filter (see `REPORT.md`).

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
