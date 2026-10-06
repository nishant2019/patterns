# Final handoff: develop and test the 30-minute scanners against stored tick data

For a coding agent. Self-contained; reference code is in this repo (paths given). Supersedes `research/TICK_VALIDATION_BRIEF.md`.
Scope rule: **only full 30-minute bars are traded** (enter at a bar open, exit at a bar close). The 15:15 bar is only 15 minutes long: it is never a trade window.
Data to be used: stored ticks, 30 days, ~500 NSE stocks. Existing evidence comes from 23 days of 30-minute OHLCV (`data/ohlc/`) and 7 days of 30-minute bars with CVD (`data/CVD_Scanner_*`).

## 0. Honest starting point (read first)
- **No profitable directional edge has been proven.** Everything below is either a *volatility/time-of-day fact* (robust, but not directional) or a *directional lead* from only 7 days (small, unconfirmed). The job is to confirm or kill, not to tune.
- Every positive result so far shrank when more days were added, and one finding ("midday coil -> late expansion") turned out to be a look-ahead artefact. Keep the protocol in section 3 exactly.

## 1. What is established (use as regression benchmarks for your bar build)
Bars: 09:15, 09:45, ... 14:45 (full 30-minute bars), 15:15 (15-minute). Range index = bar range% / the stock-day mean bar range%.

| Slot | Range index | Volume index | % of day volume | Bars moving >0.5% |
|---|---|---|---|---|
| 09:15 | 2.45 | 2.10 | 16.5 | 63% |
| 09:45 | 1.23 | 1.12 | 8.9 | 34% |
| 10:15 | 1.01 | 0.86 | 6.8 | 27% |
| 12:45 (quietest) | 0.72 | 0.68 | 5.4 | 13% |
| 14:45 | 1.05 | 1.88 | 14.9 | 22% |

Facts (23 days, 506 stocks, `research/golden_hours/REPORT.md`):
1. Movement and volume cluster at 09:15-10:15 and 14:45; 11:45-14:15 is the coil zone (23-27% compressed bars at 12:15-13:45).
2. **Activity persists (robust, 17-18 of 18 days, both halves):** stocks with a wide or loud midday (relative to their own prior days) move 1.44-1.53x their usual in the afternoon; quiet midday -> 17-20% *less* than usual afternoon movement. Daily rank correlation of the scanner score with afternoon movement +0.105 (t 11.4). (`scanners/afternoon_volatility/`)
3. Direction is **not** predicted by: bar-to-bar momentum, any of 27 classic candlestick patterns on CVD or price candles, 8 direction filters (trend, VWAP, range position, gap, relative strength, last bars, midday drift, signed volume), breakouts of the day or midday range (net -0.08 to -0.16% per trade), new day highs/lows at any slot on 30-minute bars (all four rule sets negative net), coil width, volume dry-up, tight coils.
4. CVD-only (7 days, `research/cvd_patterns/REPORT.md`): flow persists - after a bar with |delta| >= 30% of volume the next bar has the same delta sign 64.7% (selling) / 55.6% (buying) - but it does not move price enough to trade.
5. Single-bar efficiency labels and Mahalanobis outlier labels carry essentially no forward information on their own.

## 2. Directional leads from 7 days of CVD bars (small, unconfirmed - the things to test)
All outcomes below are vs the cross-sectional mean stock for the same day/bar, measured to the close of the 14:45 bar (a full 30-minute bar), 7 days only.
| ID | Lead | 7-day result | Code |
|---|---|---|---|
| L1 | SIZE-driven selling outlier in the lower third of the day range and inside the 09:15 master candle, bar >= 10:45 | 72 bars, +0.55% (found after ~25 splits; the broader SIZE-selling-outlier set: 320 bars, +0.21%, 6/7 days) | `research/regime/regime_summary.py::size_outliers`, `research/absorption/efficiency_chart.py` |
| L2 | Regime A (selling absorbed inside the middle/upper third of the master range) at 11:15 and 12:45 | +0.17% vs +0.06% baseline, 6/7 days; Regime E (buying absorbed inside the range) +0.12%, 7/7; Regime C (extended breakout, buying confirmed) ~0 (+0.005%) | `research/regime/regime_scanner.py` |
| L3 | Opening Absorption Breakout (OAB) | 83 setups, breakout 55% vs 32% baseline, window-end -> close +0.13% | `scanners/oab/OAB_SPEC.md`, `oab_scanner.py` (PARAMS frozen) |
| L4 | CVD makes a new low but price does not, at VWAP or the master low | +0.05 to +0.06% over 2 bars, +0.07 to +0.09% to the close (t 2.1-2.6; weak in the test days) | `research/cvd_patterns/cvd_levels_study.py` |
| L5 | CVD persistence (use for sizing/holding only) | 65% / 56% continuation | `research/cvd_patterns/flow_flags.py`, `candle_cvd_only.py`, `cvd_only_control.py` |

## 3. Validation protocol (apply to every item; do not deviate)
1. **Point-in-time only.** Features at decision time use bars that have closed. Never use full-day medians/means (this created the coil-expansion artefact). Baselines for a stock use prior days only.
2. **Outcome:** forward return from the *next bar open* to a stated full-bar close (1 bar, 2 bars, to the 14:45 bar close), minus the **cross-sectional MEAN** of all stocks over the same window; also report raw.
3. **Statistics:** per-day mean first, then t across days (t clustered by day). Report days positive. Stocks move together, naive t-stats are inflated (we saw t = 8 on noise).
4. **Split by date:** first 15 days discovery, last 15 days test. Also run walk-forward (train 10 days, test next 5, roll). Parameters are frozen before the test half is looked at.
5. **Costs:** report net of 0.06% and 0.10% round trip; with ticks, replace by realised half-spread + impact of your simulated fill (entry at the bar's first-5-minute VWAP vs the open).
6. **Robustness:** leave-one-day-out; within-day permutation test (random same-day stocks, same count per day); placebos (same entry, random or opposite events).
7. **Multiple testing:** log every variant run; report how many would pass by chance.
8. **PASS gate (to build a scanner):** test t >= 2, same sign in discovery and test, positive on >= 60% of test days, net > 0 after 0.06% (and still >= 0 at 0.10%), >= 100 signals in the test half, survives leave-one-day-out.

## 4. Step 0 - data foundation (must be done first)
1. Build 30-minute bars from ticks, aligned to 09:15: price OHLC, volume, **CVD OHLC** (open/high/low/close of the cumulative delta path inside the bar). Delta per trade: quote rule (at/above ask = buy, at/below bid = sell) if quotes exist, else tick rule. Mark the 15:15 bar as partial.
2. **Reconcile with the vendor files** on overlapping days (`data/CVD_Scanner_*`, `data/ohlc/`): price OHLC must match exactly; bar delta sign agreement >= 85% (stop and report otherwise); report correlation of delta and CVD range.
3. Handle: zero-volume bars, corporate actions/splits, circuit days, stocks with < 25 days, symbol changes. Drop stocks with price <= 0 bars.
4. **Regression test of the build:** reproduce the section 1 table (tolerance +/-0.03 on indices, +/-0.5 pt on percentages) and the volatility scanner statistics (HOT 1.54x, WARM 1.35x, rest 1.18x; Spearman +0.105) on the overlapping days.
5. Write one parquet/CSV per stock-day in the vendor CSV format so existing scripts run unchanged.

## 5. Priority list (do in this order)
| # | Item | Why / expected value | Effort | Pass-gate target |
|---|---|---|---|---|
| P1 | **Step 0 data foundation + regression benchmarks** | Everything depends on it; fixes the CVD definition question | 1-2 days | reconciliation + benchmark reproduction |
| P2 | **Time-of-day map and volatility-ranked watchlist on 30 days** (`scanners/afternoon_volatility/`) | The only robust finding. Not directional, but gives expected-move forecasts for stops, targets and sizing, and a universe filter for everything else | 1 day | Spearman >= +0.08, t >= 5, positive on >= 80% of days, calibration within 15% |
| P3 | **Extend P2 to every decision time (10:45, 11:45, 12:45, 13:45)** and add tick features (trades/minute, realised intrabar vol, large-trade share) | Gives a "how far will it move in the next 1-4 bars" forecast for any bar; tradeable use = vol-scaled stops/size; improves every other idea | 2 days | rank correlation higher than the 2-feature baseline in both halves |
| P4 | **L1: SIZE-driven selling outlier (lower third, inside master)** and its parent set | Best 7-day lead (+0.55%) but post-hoc; the test is whether it is real | 2 days | section 3 gate; also test the broader parent set without the lower-third/inside conditions |
| P5 | **L2: Regime A (selling absorbed, middle/upper third) and E (buying absorbed)** at 11:15 and 12:45 (and confirm Regime C ~ 0) | Largest pooled sample (6/7 and 7/7 days); cleanest definitions | 2 days | section 3 gate |
| P6 | **Intrabar tick features at 30-minute bar close (new, tick-only)**: delta in the first vs second 15 minutes of the bar, aggressor imbalance, sequence of delta inside the bar (sold first then bought), large-trade (top 1% size per stock) share, close vs bar VWAP, trades/minute. Target: next 1-2 full bars | Information the 30-minute CSVs cannot show; bar-level delta alone had no edge, so intrabar *shape* is the credible next place for one | 3-4 days | section 3 gate with a pre-written list of <= 10 features and a fixed model (e.g. one gradient-boosted model or a rank-IC test per feature); report rank-IC per day |
| P7 | **L3: OAB** with costs on 30 days, frozen PARAMS; also the master-candle (09:15) direction + gap + first-bar delta -> rest of day | OAB was the most specific, validated-on-7-days pattern; cheap to rerun | 1 day | section 3 gate; breakout rate vs 32% baseline and net return |
| P8 | **L4: CVD new low / price not, at VWAP or master low**; flow persistence (L5) as a hold/size filter on P4-P7 | Small effect; mainly useful as a confirmation filter | 1 day | section 3 gate |
| P9 | **Market overlay:** breadth (% of stocks above VWAP, % making new day lows) and index-relative strength; test it as a conditioner for P4-P7 and as a way to build market-neutral long/short baskets | Past results depend on market-wide days; need index data (NIFTY 50/500 bars) | 2 days | improvement of P4-P7 stability across market-up/down days |
| P10 | **Overnight / multi-day on 30-minute bars:** day-close flow and location vs next-day open gap and first bar (untested) | Different horizon; may carry more edge per trade vs costs | 2 days | section 3 gate with overnight costs |
| P11 | **Parked (not a 30-minute trade): last 15 minutes.** New day low closed by the 14:45 bar -> buy 15:15 open (+0.114% gross / +0.054% net, t 2.1, 13 of 22 days; first 11 days +0.10%, last 12 days ~0) | Interesting, post-hoc, only exists in the 15-minute bar. Test only if you later allow sub-30-minute trades; use ticks to measure spread and exit realism | 1 day | net > 0 at 0.10% on a fresh 20+ day sample |

Success definition for the project: **at least one of P4-P8 (or a P6 feature set) passes the section 3 gate on a 30-day tick-built sample.** If none does, the honest output is "use P2/P3 for volatility-aware sizing and stops, and trade direction discretionally".

## 6. Rejected - do not spend time (just confirm with one regression run if you like)
Candlestick patterns (27 classic patterns) on price or CVD candles -> price direction; bar-to-bar price momentum in any slot; direction filters on the volatility list (trend, VWAP, range position, gap, relative strength, last 2 bars, midday drift, signed volume); breakout entries (day high/low, midday range, with volume); new day highs/lows at any slot on 30-minute bars (buy, sell, continuation); midday coil watchlist as a breakout set; coil width and volume dry-up as breakout predictors (tight/dry coils stay quiet).

## 7. Deliverables
1. `validation_report.md`: data reconciliation, benchmark reproduction, one table per item (n, gross, net at 0.06%/0.10%, t, days positive, discovery vs test, leave-one-out, permutation p, PASS/FAIL), and the variant log.
2. For each PASS: a scanner `scanners/<name>/<name>_scanner.py` with `--date --time --csv`, point-in-time, printing symbol, signal bar, levels (trigger / invalidation), key stats; plus `<NAME>_SPEC.md`.
3. For P2/P3: a daily output of expected move% per stock for the next 1-4 bars, ready to feed position sizing and stops.
4. Do not build scanners for FAIL items; state plainly that they failed.

## 8. Pitfalls already hit (avoid)
- Baseline against the median stock makes everything look positive (+0.04%): use the same-bar cross-sectional **mean**.
- Naive t-stats treat stocks as independent: cluster by day.
- Full-day medians/means in a feature = look-ahead (killed the coil -> late-expansion finding).
- First positive result found after many splits is a hypothesis, not an edge (L1 came after ~25 splits).
- The 15:15 bar is 15 minutes; the 12-bar days end at 14:45; zero-volume bars exist; illiquid stocks inflate range ratios.
- Do not retune thresholds after seeing the test days.

## 9. Reference index (read before coding)
`research/golden_hours/REPORT.md` (time map) - `scanners/afternoon_volatility/` (volatility scanner, `AFTERNOON_VOL_SPEC.md`, direction/breakout/new-extreme reports) - `research/midday_coil/REPORT.md` (coil tests) - `research/cvd_patterns/REPORT.md` (CVD candle tests) - `research/regime/` (regimes A-E, `regime_scanner.py`) - `scanners/oab/` (OAB) - `research/absorption/` (delta efficiency, Mahalanobis outliers, charts).
