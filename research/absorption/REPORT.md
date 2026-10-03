# Absorption patterns in 30-minute CVD data

Deep analysis of every 30-minute bar of every stock across 5 NSE trading days
(15-09, 16-09, 17-09, 18-09 and 01-10-2026; ~2,530 stock-days, 25,340 bars),
looking for **buying and selling absorption** and related order-flow patterns.

## Background (internet research)

- **Absorption** is a bar with heavy aggressive flow but little price
  movement: passive limit orders soak up the aggression. Negative delta with
  price holding means buyers absorbing selling (potential bottom); positive
  delta with price stalling means sellers absorbing buying (potential top).
  This is the order-flow form of Wyckoff's *effort vs. result*.
  ([LuxAlgo](https://www.luxalgo.com/library/concept/delta-divergence/),
  [OrderFlowLabs](https://orderflowlabs.com/blogs/theblog/footprint-chart-guide),
  [United Daytraders](https://united-daytraders.com/blog/delta-cvd-advanced-order-flow))
- **Delta divergence**: price makes a higher high while CVD makes a lower high
  (bearish), or a lower low with a higher CVD low (bullish). Practitioners
  treat it as a warning, not an entry.
  ([LuxAlgo](https://www.luxalgo.com/library/concept/delta-divergence/),
  [AlphaX](https://alphax.trading/dictionary/delta-divergence))
- **Academic evidence**: order imbalance moves prices at the same time and
  predicts only very short-horizon returns; persistent price pressure from
  imbalances tends to reverse later, consistent with liquidity providers
  managing inventory.
  ([Chordia & Subrahmanyam, SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=354122),
  [Chordia, Roll & Subrahmanyam](https://www.anderson.ucla.edu/documents/areas/fac/finance/21-05.pdf))

## Method

- `events.py` builds one row per stock-bar with point-in-time features: bar
  delta % of volume, bar return, volume vs. earlier bars, close location,
  intrabar CVD push, 3-bar price/CVD change, position in the day's range.
- Forward returns: next 1 bar, next 2 bars, to the close. Each is measured
  **against the average stock at the same bar on the same day**, so market
  direction is removed.
- `grid.py` maps forward return across delta × price-return buckets.
- `patterns.py` tests 12 textbook definitions (absorption, continuation,
  climax, divergence, intrabar rejection) with t-stats and day-by-day
  consistency.

## Findings

Forward returns are vs. the average stock (%). "Days +" = days with a positive
average out of 5.

| Pattern | Definition | Events | Next 2 bars | To close | Days + (2 bars) |
|---|---|---|---|---|---|
| **Selling absorption (SA)** | delta ≤ −30%, bar return −0.5…+0.15%, volume ≥ 1.5× | 287 | **+0.15%** (t 3.8) | **+0.16%** (t 3.0) | 5/5 |
| SA, refined (SAB) | + volume 1.5–3×, lower half of day range | 166 | **+0.25%** (t 4.4) | **+0.19%** (t 2.9) | 4/5 |
| Selling continuation | delta ≤ −30%, return < −0.5%, volume ≥ 1.5× | 223 | +0.04% | +0.10% | 3/5 |
| Buying absorption (BA) | delta ≥ +30%, return −0.15…+0.15%, volume ≥ 1.5× | 105 | −0.02% | −0.04% | 2/5 |
| Buying climax | delta ≥ +30%, return > +0.5%, volume ≥ 1.5× | 231 | −0.11% (t −1.9) | −0.18% (t −2.2) | 0/5 |
| **Buying exhaustion (BEX)** | delta ≥ +50%, return > +0.5%, volume ≥ 1.5× | 100 | −0.12% | **−0.39%** (t −3.5) | 1/5 (to close: 1/5) |
| Bullish 3-bar divergence | price up, CVD ≤ −20% | 1,072 | +0.04% | +0.11% (t 3.0) | 4/5 |
| Bearish 3-bar divergence | price down, CVD ≥ +20% | 833 | +0.03% | +0.03% | 3/5 |

### 1. Selling absorption works, and is the strongest pattern

Heavy net selling (≥ 30% of bar volume) that fails to push price down,
on above-normal volume, is followed by outperformance on all 5 days.
It is stronger:
- near the day's low (lower third: +0.20% next 2 bars, t 3.6, 5/5 days),
- on a moderate volume spike (1.5–3×: +0.19%, t 4.0); spikes ≥ 3× did not
  work (+0.02%), consistent with block trades rather than absorption,
- with heavier selling (delta ≤ −50%: +0.18%).

Time of day did not matter much.

### 2. Buying absorption does NOT work the same way

The textbook mirror (heavy buying, price flat) has no edge (−0.02%). Markets
here are not symmetric: what predicts underperformance is **buying
exhaustion**, i.e. very heavy buying (≥ 50% of volume) that *does* lift price
sharply on a volume spike. These stocks lag the market by −0.39% to the close
on 4 of 5 days. This matches the academic finding that price pressure from
one-sided flow tends to reverse.

### 3. Divergences are weak

The 3-bar bullish divergence (price up while CVD falls) adds +0.11% to the
close, but it fires on 1,000+ bars and does little over the next hour.
The bearish divergence has no edge.

## SAB as a filter on OAB

`oab_sab_filter.py` checks whether an SAB bar occurs inside each OAB window
(67 OAB setups, 5 days; return = window end → close vs average stock).

| OAB subset | Setups | Breakout | vs market | Beat market |
|---|---|---|---|---|
| All OAB | 67 | 60% | +0.21% | 58% |
| SAB inside window | **2** | 50% | +1.01% | 2/2 |
| No SAB inside window | 65 | 60% | +0.18% | 57% |
| Relaxed SAB (any volume/location) inside window | 49 | 59% | +0.23% | 55% |
| No relaxed SAB inside window | 18 | 61% | +0.15% | 67% |

**SAB does not work as a filter on OAB, mainly because they almost never
co-occur.** OAB windows are quiet by design (heavy bar CVD ≤ 45% of volume,
compressing range), while SAB needs a volume spike of 1.5–3× and CVD ≤ −30%.
Only PNB (15-09) and TORNTPHARM (17-09) had both. Relaxing SAB to any volume
makes it overlap (49 of 67) but then it adds nothing (+0.23% vs +0.15%,
breakout rate unchanged). They are two separate signals, best used
independently.

## Update: 28-09-2026 added (6 days, ~3,040 stock-days, 30,400 bars)

28-09 was a mildly down day (median stock −0.37%, 34% up). Nothing was
re-tuned.

| Pattern | 5 days | 6 days | 28-09 alone |
|---|---|---|---|
| Selling absorption (SA), next 2 bars | +0.15% (t 3.8), 5/5 days | **+0.13% (t 3.7), 6/6 days** | +0.00% (n=66) |
| SA, to close | +0.16% | +0.12% | −0.04% |
| SAB refined, next 2 bars | +0.25% (t 4.4), 4/5 | **+0.20% (t 4.3), 4/6** | −0.01% (n=42) |
| SAB refined, to close | +0.19%, 5/5 | **+0.15% (t 2.7), 5/6** | −0.01% |
| Buying exhaustion (BEX), to close | −0.39% (t −3.5), 4/5 | **−0.32% (t −2.9)**, negative 4/6 | **+0.26%** (n=11) |
| Buying climax, to close | −0.18% | −0.15% (t −2.0) | +0.06% |
| Buying absorption, to close | −0.04% | −0.05% | −0.12% |

- **SA/SAB is still positive over 6 days but 28-09 was the first day with no
  effect.** The edge shrank (+0.25% → +0.20% over two bars). It is a
  small, noisy average edge, not a reliable per-day one.
- **BEX weakened**: it reversed on 28-09 (+0.26% to close) and is now
  negative on 4 of 6 days instead of 4 of 5. Still negative overall, but
  less convincing.
- **SAB as an OAB filter**: still not useful. Only 2 of 78 OAB setups
  contain an SAB bar; an SAB bar *after* the window preceded poor results
  (6 setups, 17% breakout, −0.32% vs market) but that is too few to act on.

## Caveats

- **Five days.** Results are consistent across days but the sample is still
  small; refined thresholds (SAB, BEX) were chosen on this data.
- **About 20 definitions were tested.** SA (t 3.8) and BEX (t −3.5) would
  survive a multiple-testing correction; the weaker patterns might not.
- **No costs.** +0.15–0.25% over an hour is close to typical intraday
  round-trip costs, so the edge is thin as a standalone trade.
- **Overlap.** Some events are consecutive bars of the same stock.

## Files

- `events.py` – builds `events.csv` (bar-level table; regenerate, not committed).
- `grid.py`, `patterns.py` – the analysis (`python patterns.py split` for subgroups).
- `absorption_scanner.py` – lists SAB and BEX events per stock and day.
- `absorption_events.csv` – all SAB/BEX events for the 5 days.

---

## Delta power vs price move per candle (`delta_power.py`)

Per-bar delta = `close_cvd − open_cvd`. Power of delta = how far price moved
per unit of delta (price move per 10K of delta, in the delta's direction),
plus where the bar's delta and range rank among all 36,456 stock-bars
(percentile of |delta| % of volume, percentile of high-low range).

**TCS 28-09** (the CSV bar deltas are −21.5K, −3.6K, −26.7K, …; the −25K and
−37K quoted in discussion match the CVD *levels* after the 09:45 and 10:45
bars, −25.1K and −36.8K, not the per-bar deltas):

| Bar | Delta | Delta % of vol | \|delta\| pct-rank | HL % | HL pct-rank | Return | Move per 10K delta |
|---|---|---|---|---|---|---|---|
| 09:15 | −21.5K | −4.5 | 13 | 1.87 | 92 | −1.75% | **+0.82%** |
| 09:45 | −3.6K | −1.4 | 4 | 0.63 | 50 | −0.15% | +0.40% |
| **10:15** | **−26.7K** | −14.3 | 39 | 0.55 | 42 | −0.29% | **+0.11%** |
| 10:45 | +15.0K | +10.9 | 31 | 0.41 | 25 | +0.08% | +0.05% |
| 11:15 | +31.7K | +27.2 | 66 | 0.45 | 29 | +0.30% | +0.09% |
| 11:45 | +47.8K | +27.0 | 66 | 0.59 | 46 | +0.52% | +0.11% |
| 12:15 | +26.0K | +21.2 | 55 | 0.35 | 17 | +0.07% | +0.03% |
| 12:45 | +42.9K | +28.6 | 68 | 0.37 | 19 | +0.28% | +0.07% |
| 13:15 | +25.8K | +12.5 | 35 | 0.60 | 46 | +0.03% | +0.01% |
| 13:45 | +1.8K | +2.0 | 6 | 0.26 | 7 | −0.13% | −0.71% |
| 14:15 | +10.7K | +6.9 | 20 | 0.46 | 31 | −0.33% | −0.31% |
| 14:45 | +0.5K | +0.2 | 1 | 0.43 | 27 | +0.02% | n/a |

Reading:
- The master bar moved price **0.82% per 10K of delta**; every later bar with
  >= 10K delta moved it about **0.06%** (median), i.e. 14 times less. The
  open was a thin, gap-driven move; the later sellers had far less impact.
- The 10:15 bar had the **largest negative delta of the day** (−26.7K) in a
  small candle (HL 0.55%, 30% of the master) that still undercut the master
  low and closed lower (−0.29%); the next bar had no selling inside it.
  Consistent with selling absorption, though price impact per 10K delta
  (0.11) is not different from later buying bars, so it is not unique by this
  measure.
- **Buying lost power at the top:** from 13:15 buying delta (+25.8K, +1.8K,
  +10.7K) produced +0.03%, −0.13% and −0.33%, i.e. price moved against buyers
  as the range high was approached; this precedes the fade into the close.

**Does price impact per unit of delta predict anything?** Across 12,869
selling bars (delta <= −10% of volume) split into impact quintiles, and 9,437
buying bars: forward returns are about the same in every quintile
(+0.03% / +0.03% to +0.08% for selling, baseline +0.03% / +0.055%), with no
monotone pattern. Only the coarse split shows anything: bars with delta
>= 30% selling where price did **not** follow (n = 1,766) returned +0.11% to
the close (t 4.7) vs +0.07% where price followed (baseline +0.055%), a small
effect consistent with the selling-absorption result above.

A linear model of bar move on delta % explains only 15% of bar-to-bar price
movement (R² 0.15), too weak to give a per-candle "expected move".

---

## Delta efficiency (`delta_efficiency.py`)

How much price movement does the delta actually produce? For a window of
bars, `D` = net delta as % of window volume, `P` = price move in master-bar
ranges, `beta` = pooled slope of P on D (24,304 windows; correlation 0.40
rolling, 0.42 since 09:45). **Delta efficiency DE = P / (beta × D)**:

| DE | Meaning |
|---|---|
| > 1.5 | over-efficient: price ran further than that delta normally buys |
| 0.5 – 1.5 | normal |
| 0 – 0.5 | inefficient: delta mostly absorbed |
| <= 0 | price moved **against** the delta |

Only windows with |D| >= 10% are classified. Two views: **rolling** (last 4
bars) and **day-to-date** (since the 09:45 open, i.e. after the opening bar).
`python delta_efficiency.py show TCS 28-09-2026` prints both series for any
stock-day.

**TCS 28-09:** rolling DE was over-efficient (2.0–3.0) from 11:45 to 13:15
as +11% to +26% delta lifted price +0.7% to +1.2%; it fell to normal (0.75)
at 13:45 and to **−0.49 (against delta)** at 14:15 when +13.5% delta came with
price down 0.13%. Since-09:45 efficiency stayed over-efficient to 13:45
(2.1–2.3) and dropped to normal (1.3) at 14:15. So the delta was efficient
while the range was being built and stopped being efficient near the top.

**Does efficiency predict anything?** (vs the median stock, next 2 bars / to
close; baseline +0.03% / +0.05%)

| Window | State | Delta selling: to close | Delta buying: to close |
|---|---|---|---|
| Rolling 4 bars | against delta | **+0.09%** (t 4.1, 5/6 days) | +0.03% |
| | inefficient | +0.09% (6/6) | −0.02% |
| | over-efficient | +0.07% | +0.01% |
| Since 09:45 | **against delta** | **+0.14%** (t 6.0, 5/6) | **+0.09%** (t 3.5, 6/6) |
| | inefficient | +0.03% | −0.01% |
| | normal | −0.04% (t −2.1) | +0.05% |
| | over-efficient | +0.01% | −0.03% |

- The one state that stands out is **day-to-date delta efficiency <= 0** (price
  has moved opposite to the net delta since the open): both sides beat the
  baseline by about +0.05% to +0.10% to the close. It is positive for selling
  (price held up despite sellers) and for buying (price fell despite buyers),
  so it behaves like "a divergence between day delta and day price", not a
  directional signal.
- Over-efficient delta (price following delta strongly) shows no continuation.
- The effect sizes (about 0.1%) are small, similar to the earlier absorption
  results, and the rolling buckets are not monotone. Efficiency is a useful
  descriptive read of who is in control, but not a stand-alone edge.

---

## Efficiency labels on a candle chart (`efficiency_chart.py`)

```bash
python research/absorption/efficiency_chart.py TCS 28-09-2026 --png tcs.png   # writes charts/TCS_28-09-2026.html
```

One self-contained HTML/SVG per stock-day (light and dark themes, hover tooltips
on every candle): price candles with the master range shaded, CVD candles
(open/high/low/close), per-bar delta, and three label rows: **Bar** (this
candle alone), **Roll 4** (last 4 bars) and **Since 09:45** (day so far).
Examples: `charts/TCS_28-09-2026.html` / `.png`.

**Definition used on the chart (changed from the DE ratio above).** The
regression-based DE ratio is skewed: because delta explains only 15% of price
movement, the fitted impact is tiny and 42% of selling windows came out
"over-efficient". The chart therefore ranks each window against peers with a
similar |delta| (|delta| decile, pooled over all stocks and days):

| Label | Rule |
|---|---|
| STRONG | price moved more than 67% of peers with the same delta |
| NORM | 33rd–67th percentile |
| ABSORBED | at or below the 33rd percentile (delta did little) |
| AGAINST | price moved opposite to the delta |
| – | \|net delta\| < 10% of volume |

**TCS 28-09 on the chart:** the 10:45 (+15K), 12:15 (+26K) and 13:15 (+26K)
bars are ABSORBED (percentiles 21, 18 and 8), the 11:45 (+48K) bar STRONG (76);
Roll 4 goes NORM → STRONG (12:45) → NORM → ABSORBED (13:45) → AGAINST (14:15);
Since 09:45 turns ABSORBED at 14:15. The 10:15 selling bar (−26.7K) ranks NORM
(p59), not absorbed, when compared with peers of similar delta: its 0.29% move
is mid-pack once the stock's large opening range is accounted for.

**Do the labels predict anything?** (`efficiency_label_test.py`, forward to the
close vs the median stock; baseline +0.055%)

| Window | Label | After selling delta | After buying delta |
|---|---|---|---|
| Bar | any | +0.03% … +0.07% | +0.03% … +0.06% (no pattern) |
| Roll 4 | ABSORBED | **+0.093%** (t 4.3, 6/6) | +0.016% |
| Roll 4 | STRONG | +0.070% | +0.042% |
| Since 09:45 | **AGAINST** | **+0.118%** (t 4.9, 6/6) | **+0.117%** (t 4.2, 5/6) |
| Since 09:45 | NORM | −0.039% (t −2.0) | −0.043% (t −1.8) |

Same conclusion as before, with the new labels: single-bar labels carry no
information; the only labels that stand out are Roll-4 ABSORBED selling and
day-level AGAINST (price moved opposite to the net delta since the open),
about +0.04% to +0.06% above baseline. The chart is for reading who is in
control, not for generating signals.

---

## CVD swing marker on the candle chart

Added to `efficiency_chart.py`: a diamond above the price candle and a **CVD
swing** chip row. Swing = `high_cvd − low_cvd` as a % of the stock-day's
average bar volume, ranked against all 30,400 bars. **TWO-WAY** (filled
diamond) = top-20% swing whose net delta is <= 30% of the swing, i.e. heavy
flow in both directions that netted out; **SWING** (outline) = top-20% swing
that ended one-sided. Tooltips give the CVD excursion below and above the bar's
open.

The swing is measured against the day's average bar volume (not the bar's
own volume) because a very high-volume bar otherwise hides its own swing:
DABUR's 14:15 bar (volume 4.1x, CVD −65K inside, net −3K) is only p60 on this
scale, so it is **not** flagged; the flagged bars are the larger swings
relative to the stock's normal size.

Do flagged bars predict? (vs the median stock, baseline +0.03% / +0.055%)

| Bars | Count | Next 2 bars | To close |
|---|---|---|---|
| TWO-WAY | 287 (1%) | +0.06% | +0.05% (t 0.8) |
| SWING (one-sided) | 4,239 (14%) | +0.00% | +0.01% (t 0.5) |
| TWO-WAY, CVD dipped below open and recovered | 130 | +0.07% | **+0.16%** (t 2.3, 5/6 days) |
| TWO-WAY, CVD spiked above open and faded | 157 | +0.05% | −0.05% (t −0.6) |

Overall the marker carries no edge. The one hint, a recovered CVD dip
(sell push absorbed) followed by about +0.1% over baseline, is small and has
130 events.

Examples (28-09): `charts/TCS_…`, `AUROPHARMA_…`, `DABUR_…`, `IREDA_…`
(IREDA's 12:15 bar is TWO-WAY: CVD ran +509K above and −169K below its open on
7.2x the master's volume and finished −146K; the stock then ran out of buyers
and CVD fell from +654K to −109K by 14:45 while price stayed above the master
range).

---

## Replacing percentiles with outlier statistics (`efficiency_metrics.py`)

**Why change:** a percentile is a rank. It flags a fixed third of bars as "absorbed" by
construction and saturates (p99 and p99.9 look alike), so it cannot say how *unusual*
a bar is. Outlier statistics measure the deviation in standard units, so only real
outliers are flagged and the size of the deviation is visible.

### Metrics researched and implemented
Common inputs: `D` = net delta % of volume; `Pd` = price move (in master-bar ranges)
signed along the delta (negative = price moved against it); peers = bars in the same
|D| decile, pooled over all stocks and days. Positive score = delta did less than usual.

| Metric | Calculation | Source / idea |
|---|---|---|
| Percentile (old) | rank of Pd among peers | – |
| Classical conditional z | (Pd − mean) / std of peers | standard z-score |
| **Robust z (MAD)** | **(Pd − median) / (1.4826 × MAD)** of peers; \|z\| ≥ 3.5 outlier, ≥ 3 soft | modified z-score ([robust statistics](https://www.researchgate.net/publication/256752600_Detecting_outliers_Do_not_use_standard_deviation_around_the_mean_use_absolute_deviation_around_the_median), [MAD-scaled z](https://metricgate.com/docs/mad-scaled-z-score/)) |
| Kyle-lambda residual | OLS Pd = λ·\|D\| + c; residual / residual std in the peer decile | Kyle's price-impact regression ([overview](https://onepagecode.substack.com/p/quant-trading-kyles-price-impact)) |
| Amihud-style impact | Pd ÷ (\|delta\| / day-average bar volume), then robust z vs peers of similar size | Amihud illiquidity, \|return\| per unit of volume (correlation with Kyle's λ about 0.82 in the literature, [study](https://arxiv.org/abs/2607.01377)) |
| Mahalanobis distance | √((x−μ)ᵀS⁻¹(x−μ)) on (\|D\|, Pd, ln volume spike); outlier if d² > χ²(3, 97.5%) = 9.35 | multivariate outliers ([robust variant](https://www.sciencedirect.com/science/article/abs/pii/S0022103117302123)) |
| CUSUM | S_t = max(0, S_{t−1} + z_t − k), k = 0.5, alarm at S ≥ 4, per stock-day | sequential change detection on residuals ([control charts](https://www.net.in.tum.de/fileadmin/TUM/members/muenz/documents/muenz08control-charts.pdf)) |

Reviewed but not used: **VPIN** (mean absolute buy-sell imbalance over equal-volume buckets, an
order-flow toxicity measure rather than an efficiency measure, [description](https://metricgate.com/docs/vpin-order-flow-toxicity/));
**Isolation Forest** (needs scikit-learn, which is not installed; it also tends to find only the
"loudest" outliers, [comparison](https://arxiv.org/pdf/2006.08238)); **EWMA** (like CUSUM, for small persistent shifts).

### Results (25,907 bars with |delta| ≥ 10% of volume, 7 days)
1. **The ranking is almost identical across the conditional metrics.** Spearman agreement
   between percentile, classical z, robust z and Kyle residual is 0.99–1.00; Amihud 0.96;
   Mahalanobis 0.84; CUSUM 0.72. They differ in scale and tail behaviour, not in which bars
   they rank as absorbed.
2. **The classical z-score masks outliers; the robust z-score finds them.** Beyond |z| ≥ 3.5 the
   classical z flags 0.9% of bars (its standard deviation is inflated by the outliers themselves);
   robust z flags 3.4% (normal expectation 0.05%). Robust z reaches +21 absorbed and −44
   efficient, so outliers are far heavier-tailed than a normal model suggests.
   Beyond |z| ≥ 2: classical 4.7%, robust 11.6%, Amihud 11.5%.
3. **Forward information is nil for every metric.** Spearman IC with the next 2 bars and with
   the return to the close is between −0.015 and +0.025 for all metrics; the top decile ("most
   absorbed") minus bottom decile ("most efficient") spread is −0.09% to +0.05% and positive
   on only 1–6 of 7 days.
   Robust-z bands, selling bars (return to close vs the median stock; baseline +0.065%):
   z ≥ +3.5 (110 bars) +0.01%; +2 to +3.5 (329) −0.06%; |z| < 2 (13,042) +0.07%; z ≤ −3.5 (275) +0.04%.
   Buying bars: z ≥ +3.5 (63) −0.03%; +2 to +3.5 (298) +0.04%; z ≤ −3.5 (426) +0.06%.
   CUSUM alarms (first bar with S ≥ 4): selling bars (95) −0.14%, buying bars (58) +0.13%, both not significant.
   So efficiency on its own does not reproduce the earlier selling-absorption (SA) result,
   which also needed a volume spike of 1.5–3×.

### Recommendation and chart change
Use the **robust conditional z-score (median/MAD)**: simplest to compute, handles the heavy tails
that classical z hides, gives a magnitude (z −3.4 vs −1.4 where a percentile would say p97 vs p91),
and flags only genuine deviations. The chart now shows
`z = −(Pd − median) / (1.4826 × MAD)` per bar, rolling-4 window and since-09:45 window:
z ≥ +2 ABSORBED (AGAINST if price actually moved opposite to the delta; almost every z ≥ +2 bar is
an AGAINST bar because the typical move is small relative to the spread), −2 < z < 2 NORM, z ≤ −2 STRONG.
Compared with the percentile version it labels about 12% of bars instead of two-thirds, and a move
of slightly the wrong sign (noise) is no longer called AGAINST. The Mahalanobis distance (adds the volume
spike) and CUSUM (persistence) are available in `efficiency_metrics.py` if a joint or sequential flag is wanted.
Like the percentile labels, none of these is a forecast; they describe how unusual the flow was.

Label test with the new chart labels (`efficiency_label_test.py`; return to the close vs the median
stock, baseline +0.06%): bar-level AGAINST after selling −0.04% (t −0.8), STRONG after selling +0.03%; rolling
and day-level AGAINST after buying +0.15% and +0.17% (t +2.0, 6/7 and 4/7 days), the same small divergence signal as before.

---

## Mahalanobis joint-outlier marker on the chart

A new chip row ("Joint outlier") and a square below the price candle flag bars that are unusual
in the **combination** of three things, not just in one: the size of the delta, the price move
along the delta, and the volume spike.

- **x = (|D|, Pd, ln volume spike)** for each bar with |delta| ≥ 10% of volume.
- **Distance** d = √((x − μ)ᵀ S⁻¹ (x − μ)), with μ and S fitted on all 25,907 such bars
  (mean |D| 30.7%, mean Pd 0.14 master ranges, mean ln spike −0.40; marginal std 17.4, 0.28, 0.83).
- **OUTLIER** when d² > 9.35 (chi-square, 3 degrees of freedom, 97.5%), i.e. d > 3.06.
- **Driver** = the component with the largest marginal z: **PRICE−** (price moved less than usual for the delta = absorbed),
  **PRICE+** (price moved more than usual), **SIZE** (an exceptionally large delta) or **VOLUME**
  (exceptionally high or low volume). Hover text shows d and the driver; non-outlier bars show their d value.

It flags 4.3% of those bars (1,113; a normal model would give 2.5%, so the tails are heavier).
The chart only tests bars with at least 10% net delta, so a heavy two-way bar with small net delta
(for example IREDA's 12:15 bar with 7.2× volume and −3% delta) is not flagged here; the CVD swing marker covers it.

On the ten charted stocks only IREDA has outliers: 09:45 (d 3.4, PRICE+, +278K delta moved price +1.45%) and
11:45 (d 4.5, PRICE+, +258K delta, volume 3.2× the master's).

**Forward return to the close by driver** (vs the median stock; baseline +0.055%; all 7 days):

| Driver | Bars | Selling bars | Buying bars |
|---|---|---|---|
| PRICE− (absorbed) | 88 / 48 | +0.11% (t 0.8) | +0.15% (t 0.7) |
| PRICE+ (efficient) | 127 / 216 | +0.17% (t 1.7) | +0.06% |
| SIZE (huge delta) | 320 / 141 | **+0.21%** (t 3.9, 6/7 days) | +0.08% |
| VOLUME | 84 / 89 | +0.22% (t 2.3) | **−0.20%** (t −2.0, 2/7 days) |
| All outliers | 1,113 | | +0.116% (t 3.2) |

Eight groups were tested, so only the large ones are worth a second look. Notably: selling bars whose delta is
exceptionally large (SIZE) were followed by about +0.21% to the close (6 of 7 days), and high-volume buying
outliers by −0.20%. These are consistent with large selling being followed by relief and with heavy buying
being a poor sign, but they need more days before they are used.
