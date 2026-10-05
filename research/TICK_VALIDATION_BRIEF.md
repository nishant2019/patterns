# Brief for a coding agent: validate our order-flow findings on 30 days of tick data (500 NSE stocks)

## Context
We studied 7 days of 30-minute bars with CVD OHLC (`Time, open_price, high_price, low_price, close_price, open_cvd, high_cvd, low_cvd, close_cvd, volume`).
Every edge found was small and some shrank as days were added. 7 days is too few to trust them. Your job is to **confirm or kill** them on 30 days of ticks, **using the definitions below exactly as written. Do not tune any threshold.**
Reference code is in this repo (paths given below). Read it before you start.

## Step 0: build the data and check it against the vendor
1. From ticks, build 30-minute bars starting at 09:15 (09:15, 09:45, …, 15:15) with price OHLC, volume and CVD OHLC.
   - Delta per trade: +size if the trade was buyer-initiated, −size if seller-initiated.
   - If quotes are available, use the quote rule: at or above the ask = buy, at or below the bid = sell.
   - Otherwise use the tick rule: an uptick = buy, a downtick = sell, and an unchanged price keeps the previous side.
   - CVD runs from the day's first trade. open/high/low/close_cvd are the CVD path within each bar.
2. Compare your bars with the vendor CSVs for the overlapping days (`data/CVD_Scanner_*`). Report the correlation of bar delta, the sign agreement, and any systematic offset.
   - If agreement is poor (sign agreement below about 85%), stop and report.
   - Every finding below depends on how the CVD is built.
3. Save one file per stock-day in the same CSV format, so the existing scripts run unchanged.

## Step 1: validation protocol (apply to every hypothesis)
- **Outcome:** forward return from the signal bar's close (next 1 bar, next 2 bars, and to the 14:45 close), minus the **cross-sectional mean** of all stocks for the same day and bar.
  - Do not subtract the median. That made every pattern look positive (+0.04%) in our study.
- **t-statistics:** cluster them by (day, bar). Stocks move together, so naive per-row t-stats are badly inflated (we saw t = 8 on noise).
- **Split by date:** first 15 days = discovery, last 15 = test. Also report each day's mean and the number of days that came out positive.
- **Costs:** report results net of 0.06% round trip and 0.10% round trip.
- **Multiple testing:** report how many variants you ran and how many would pass by chance.
- **Pass gate for building a scanner:**
  - test-period clustered t ≥ 2,
  - same sign as discovery,
  - positive on at least 60% of test days,
  - mean return after 0.06% costs above 0,
  - and at least 100 signals in the test period.

## Step 2: hypotheses, in priority order

### H1. SIZE-driven selling outlier at the lower third, inside the master range (best lead, least proven)
- **Definition:** all four must hold:
  - bar index ≥ 3 (10:45 or later);
  - net delta below −10% of the bar's volume;
  - a Mahalanobis joint outlier on (|D|, Pd, ln volume spike) with d² > 9.35, where the largest marginal z is |D| (driver = SIZE);
  - the close sits in the lower third of the day's range so far and inside the master (09:15) candle's range.
- **Code:** `research/regime/regime_summary.py::size_outliers` and `research/absorption/efficiency_chart.py::peer_tables/fit_maha/maha_state`.
- **Seven-day result:** 72 bars, +0.55% to the close versus the median stock (6 of 7 days positive). It was found after about 25 splits, so expect it to shrink.
- **Expectation:** long bias to the close.

### H2. Regime A and regime E (regime classifier at 11:15 and 12:45)
- **Code:** `research/regime/regime_scanner.py` (`analyse`, `TIMES`).
- Regime A = selling absorbed inside the middle or upper third of the master range.
  - Seven days: +0.17% versus +0.06% baseline, 6 of 7 days.
- Regime E = +0.12%, 7 of 7 days.
- Regime C (extended breakout) about 0. Confirm it is still flat, which would mean chasing breakouts adds nothing.

### H3. Opening Absorption Breakout (OAB)
- **Spec:** `scanners/oab/OAB_SPEC.md`. **Code:** `scanners/oab/oab_scanner.py` (use the `PARAMS` as frozen).
- **Seven days:** 83 setups. Breakout rate 55% versus a 32% baseline. Return from window end to the close +0.13%.

### H4. "CVD makes a new low but price doesn't" at VWAP or master-low support
- **Code:** `research/cvd_patterns/cvd_levels_study.py` (TOL = 0.2%).
- **Seven days:** +0.05 to +0.06% over 2 bars and +0.07 to +0.09% to the close (t 2.1 to 2.6). It weakened in the test days.

### H5. Flow persistence (CVD only)
- **Code:** `research/cvd_patterns/flow_flags.py`, `candle_cvd_only.py`, `cvd_only_control.py`.
- **Claim:** if |bar delta| ≥ 30% of volume, the next bar has the same delta sign about 65% of the time (selling) and about 56% (buying).
- After controlling for the bar's own delta, only three white soldiers and bullish marubozu added information.
- **Check:** does persistence survive with tick-built delta, and is it just a 30-minute artefact? Repeat the check on 5-minute and 15-minute bars.

## Step 3: nulls to confirm (results that should come out near zero)
- Classic candlestick patterns on CVD candles predicting **price**: 27 patterns, none replicated.
  - Script: `research/cvd_patterns/candle_catalog_study.py`.
- Reversal CVD patterns (hammer, stars, piercing, tweezers) predicting a CVD reversal: no effect.
- Single-bar delta-efficiency labels (robust z ABSORBED / STRONG) predicting price: no effect.

If any of these turns significant on 30 days, report it, but treat it as new discovery, not as confirmation.

## Step 4: tick-only extensions (exploratory; label them as such)
- Block trades:
  - Does the H1 outlier bar contain one or a few large prints (top 1% trade size for that stock), or many small ones?
  - Split H1 by that.
- Absorption at the level:
  - Within the bar, how much volume printed at the bar low against seller aggression, and did price hold?
  - This is a direct tick measure of "absorbed".
- Do not let these change H1 to H5. Report them separately, with their own discovery/test split.

## Deliverables
1. `validation_report.md` with these sections:
   - the data check;
   - a table per hypothesis (n, mean, clustered t, days positive, discovery versus test, net of costs, PASS or FAIL);
   - the nulls;
   - the exploratory section.
2. For every hypothesis that PASSES: a scanner script that runs at a given time of day on a folder of stock-day CSVs and prints symbol, signal bar, key levels (master high/low, invalidation) and the signal stats, with no look-ahead.
3. Do not build scanners for hypotheses that FAIL. State plainly that they failed.
