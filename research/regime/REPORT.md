# Stock regimes for discretionary planning

Built from the earlier research (6 days, ~3,040 stock-days): master-candle
structure, delta efficiency, price-vs-CVD divergence, absorption. At a chosen
decision time (10:45 to 13:15) every stock is placed in one of seven regimes
using only data up to that bar. Code: `regime_study.py` (statistics),
`regime_scanner.py` (classifier and plan cards).

```bash
python research/regime/regime_scanner.py data/CVD_Scanner_28-09-2026 --time 11:15            # counts per regime
python research/regime/regime_scanner.py data/CVD_Scanner_28-09-2026 --time 11:15 --regime A  # list a regime
python research/regime/regime_scanner.py data/CVD_Scanner_28-09-2026 --time 11:15 --card TCS  # plan card
```

## One-page summary
```bash
python research/regime/regime_summary.py 28-09-2026 --time 11:15 --png summary.png   # morning
python research/regime/regime_summary.py 28-09-2026 --time 12:45                     # midday
```
Writes `summaries/regime_summary_<date>_<time>.html` (single file, light/dark):
header chips (counts per regime, share above/below the master range), then one
card per regime A–E with its historical statistics, bias, plan and
invalidation, and a table of the stocks (top 10 by a regime-specific ranking,
the rest in a collapsible list) with close, master range, position,
delta/price since 09:45, volume trend, the level to watch, the invalidation
level and flags (undercut low, coil bars, rising volume). `--outcomes` adds the
realised move to the close for review on past days. Examples:
`summaries/regime_summary_28-09-2026_1115.html` and `_1245.html` (with PNG previews).

## Inputs
- **Structure**: where the latest close sits against the master (first) candle:
  ABOVE its high, BELOW its low, or inside (lower / middle / upper third).
- **Flow**: price change since the 09:45 open vs net delta since 09:45
  (D = CVD change as % of volume). D within ±10% = neutral; otherwise delta
  and price either agree (confirmed) or price fails to follow (absorbed).

## Regimes and what each did afterwards
Return = decision time to the 14:45 close minus the median stock. The
all-stock baseline is about **+0.05%** (the mean sits slightly above the
median). Days+ = days (of 6) with a positive average. Pooled over six
decision times (10:45, 11:15, 11:45, 12:15, 12:45, 13:15; overlapping, so
treat as one sample, not six).

| Regime | Rule | Pooled n | Return | Days + | First break of the master range | Reading |
|---|---|---|---|---|---|---|
| **A  Absorbed selling inside range** | inside middle/upper third, D <= −10%, price flat or up | 725 | **+0.24%** | **6/6** | 56% break, 69% of those up | Best regime: sellers absorbed, price held in the upper part of the range |
| B  Balanced inside the master | inside, any other flow | 8,558 | +0.07% | 5/6 | 49% break; up 38% | Modest; side set by location (see below) |
| **C  Extended breakout, buying confirmed** | ABOVE master high, D >= +10%, price up | 1,199 | **−0.06%** | 2/6 | 96% already broke, 98% up | Chasing underperforms (consistent with the fade result) |
| C2 Breakout holding | ABOVE master high, other flow | 1,584 | +0.10% | 4/6 | up | Trend intact, no extra edge |
| **D  Breakdown, selling confirmed** | BELOW master low, D <= −10%, price down | 3,349 | **−0.04%** | 2/6 | 99% already broke, down | Weak; avoid longs |
| D2 Below master low, flow not confirming | BELOW master low, other flow | 2,099 | +0.06% | 4/6 | down | Reclaim candidate, unproven |
| E  Buying absorbed | D >= +10%, price flat/down, not above the range | 714 | +0.09% | 6/6 | 64% break, only 35% up | No return edge, but breaks lean down |

Regime A by decision time: +0.31% (10:45, 6/6 days), +0.27% (11:15, 5/6),
+0.23% (11:45, 4/6), +0.13% (12:15, 4/6), +0.31% (12:45, 6/6), +0.16%
(13:15, 4/6), against baselines of +0.04% to +0.06%. Regime C was negative at
all six times (−0.00% to −0.10%) and positive on only 1 to 4 of 6 days.

Other findings used in the playbook:
- **Where a break will happen** (inside regimes): lower third breaks down
  ~91% of the time, upper third breaks up ~79–93%, middle is 37–44%
  (a descriptive guide to which edge matters, not a return edge).
- **Relative strength vs the market does not persist** (return since 09:15 close
  minus median, quintiles: no pattern), so it is not a regime input.
- **Rising volume inside a coil** raises the chance of a break (43% → 62%).

## Playbook (discretionary plan per regime)

| Regime | Bias | Plan | Invalidation |
|---|---|---|---|
| A | Long bias while the range holds | Add on a close above the master/coil high with rising volume, or on a pullback that holds the master low / undercut low | Close below the master low (or the undercut low): selling no longer absorbed |
| B | Neutral; side from location | Upper third: watch the master high; lower third: watch the master low. Rising volume = a decision is near | A close through either edge changes the regime |
| C | Do not chase | Wait for a pullback that holds the range, or fade only on signs of failure (strong delta on the break that fails to extend) | A close back inside the master range = failed break |
| C2 | Trend intact | Pullbacks to the master high are cleaner entries than the extension | Close back inside the range |
| D | Avoid longs | Only a reclaim of the master low with positive delta changes this | No reclaim |
| D2 | Reclaim candidate, unproven | Needs a close back above the master low with delta confirming | No reclaim |
| E | Neutral; breaks lean down | Only a close through the master low is meaningful | Acceptance above the master high with efficient buying |

Each plan card also prints the key levels: master high and low, the day's low
since 09:45 (an undercut below the master low is flagged), the share of bars
inside the master and the volume trend.

## 28-09-2026 at 11:15 (507 stocks)
A = 19, B = 278, C = 20, C2 = 14, D = 85, D2 = 63, E = 27. The A list:
SONACOMS, CHAMBLFERT, LGEINDIA, GLAND, SANDUMA, SARDAEN, PIDILITIND,
BAJAJHFL, UPL, AFCONS, J&KBANK, PRICOLLTD, SAILIFE, PTC, SAPPHIRE, BORORENEW,
IGIL, PREMEXPLN, IEX. Their raw returns to the close ranged from −1.78%
(SONACOMS) to +2.01% (SARDAEN), about −0.2% on average on a day when the
median stock lost about 0.4% from 11:15.

The stocks charted earlier at 11:15: TCS B (inside lower third), MPHASIS B,
NETWEB B (inside upper third, price +1.4%), DABUR B, AUROPHARMA B, KERNEX D2
(below master low; it later reclaimed and gained +2.8%), IREDA C (above the
master high, buying confirmed; +0.5%), NESTLEIND C (above; −0.6%), APOLLOTYRE
D2, COALINDIA E (−0.85%). Most of the stocks examined by hand fall in B: the
regimes describe the broad state, not these specific setups.

## Caveats
- **Six days.** Regime A has about 94 to 142 stock-days at each decision time,
  and days overlap across decision times. Thresholds (10% delta, ±0.2% price)
  were chosen once and not tuned.
- **Edge is small and relative.** Regime A's +0.24% is about +0.19% over the
  baseline and is measured against the median stock, not as a stand-alone
  profit; at typical intraday costs (about 0.10% round trip) it is
  marginal. Use the regimes to choose where to look and what to avoid,
  not as an automatic trade.
- **Undercut-and-reclaim setups** (TCS, KERNEX, MPHASIS) are not a separate
  regime because the earlier test found no edge for them; the card flags an
  undercut for the discretionary trader.
- Down days dominate the sample (2 selloffs, 2 mild down days, 1 rally, 1 flat),
  so confirm on more days before relying on the C and D results.

---

## Regime changes (`regime_changes.py`) and the 28-09-2026 run

```bash
python research/regime/regime_changes.py 28-09-2026 --outcomes      # transition matrix + who moved
python research/regime/regime_changes.py --all-days                 # pooled transition statistics
```
Outputs: `summaries/regime_changes_28-09-2026_1115_to_1245.txt` and
`summaries/regime_changes_all_days_1115_to_1245.txt`.

### 28-09-2026: how the regimes did (return to 14:45 vs the median stock)
A mild down day: the median stock lost 0.50% from 11:15 and 0.22% from 12:45;
only 18% to 30% of first breaks of the master range went up.

| Regime | At 11:15: n | Raw | vs median | At 12:45: n | Raw | vs median |
|---|---|---|---|---|---|---|
| A absorbed selling | 19 | −0.40% | +0.10% | 12 | −0.15% | +0.07% |
| B balanced | 278 | −0.44% | +0.06% | 229 | −0.15% | +0.06% |
| C extended breakout, buying confirmed | 20 | −0.50% | −0.00% | 17 | −0.40% | **−0.19%** |
| C2 breakout holding | 14 | +0.11% | **+0.61%** | 17 | +0.08% | **+0.30%** |
| D breakdown, selling confirmed | 85 | −0.53% | −0.03% | 111 | −0.21% | +0.01% |
| D2 below master low, not confirming | 63 | −0.49% | +0.01% | 103 | −0.16% | +0.06% |
| E buying absorbed | 27 | −0.40% | +0.10% | 17 | −0.31% | −0.10% |

Against the +0.05% baseline, regime A added only about +0.05% on this day,
well below its +0.19% average, and C again lagged at 12:45 (−0.19%, 35% win).
The strongest result was C2 (breakouts that held), small samples.

### Who changed regime between 11:15 and 12:45 (506 stocks)
174 stocks (34%) changed regime; most stayed in B (193). Notable flows: 30 B
to D and 35 B to D2 (breakdowns on a down day), 13 D/D2 reclaimed the range, 11
new breakouts (8 to C2, 3 to C). Only 4 stocks entered A (STLTECH +2.06% to the
close, SHREEJISPG +0.01%, MARICO −0.72%, ASIANPAINT −0.35%) and 11 left A (10 went
to B, 1 to D); the leavers fell back to the lower third of the master range and
were roughly flat against the market on average.

### Pooled over six days (11:15 → 12:45, return from 12:45 to 14:45 vs median)
| Transition | n | Return | Days + |
|---|---|---|---|
| **Entered A at 12:45** (was not A at 11:15) | 49 | **+0.47%** (t 2.6) | **6/6** |
| A → B | 49 | +0.28% (t 2.0) | 5/6 |
| A → A | 45 | +0.13% | 5/6 |
| A at 11:15, any later state | 142 | +0.19% | 5/6 |
| D → D | 353 | **−0.10%** (t −2.4) | 1/6 |
| B → C | 74 | −0.12% | 3/6 |
| C2 → C2 | 153 | +0.14% | 5/6 |

- Entering regime A later in the day was the best transition (+0.47% over 49
  stock-days, positive on every day) but small and overlapping with the A
  results above.
- Staying below the master low (D → D) was the weakest (−0.10%, positive on
  only 1 of 6 days).
- Stocks that were in A and fell back to B still beat the median (+0.28%), so
  leaving A is not by itself a reason to drop the idea.

---

## Update: 29-09-2026 added (7 days, out of sample, nothing re-tuned)

29-09: median stock +0.39% from the 09:15 close at the last bar; afternoon fade.
Regime A (absorbed selling) returned −0.04% (11:15) and −0.06% (12:45) vs the
median stock, below baseline; regime C returned +0.28% at 11:15 (reverse of its
history); regime E was the best (+0.55% / +0.64%, 78% / 67% win). Pooled over
six decision times and 7 days: A +0.17% (6 of 7 days, was +0.24% over 6 of 6), B +0.07%, C +0.005% (3 of 7 days),
C2 +0.12%, D −0.03% (2 of 7 days), D2 +0.06%, E +0.12% (7 of 7 days). The A advantage shrinks
from about +0.19% to about +0.11% over baseline, and the C weakness is gone, so
treat the playbook's "avoid C" advice as unproven. See `research/day_reports/29-09-2026_out_of_sample.md`.

---

## Watchlist flag: SIZE-driven selling outliers (lower third + inside master)

The regime summary page now opens with a **Watchlist** section and adds a **SIZE sell outlier hh:mm** flag in the Notes column of any stock that qualifies.

- **Qualifies** when, at a bar from 10:45 on (the population of the 7-day study), the bar had at least 10% net selling delta and was a Mahalanobis joint outlier (d > 3.06) driven by the **size** of the selling delta, while the close was in the **lower third of the day's range so far** and **inside the master candle**.
- **Columns:** stock, outlier bar (marked "latest" if it is the last completed bar), delta (shares), share of volume, size in average bars, volume spike, distance d, close, master range, and the stock's regime now. Review pages (`--outcomes`) add the raw return from the outlier bar to the close.
- **History line** (`research/absorption/REPORT.md`): 72 such bars returned +0.55% to the close vs the median stock (median +0.49%, 74% win, 6 of 7 days); all SIZE-driven selling outliers +0.21%; either condition alone about +0.04%. The subgroup was chosen after examining about 25 splits and must be confirmed forward.
- **Invalidation:** a close below the master low, or below the day's low since 09:45.

Counts and raw return from the outlier bar to the close (not vs the median stock; the median stock lost 0.4% to 0.5% after 11:15 on both days):

| Day, time | Qualifying bars | Stocks | Raw return to close |
|---|---|---|---|
| 28-09, 11:15 | 4 | 4 | −0.23% |
| 28-09, 12:45 | 8 | 7 | −0.07% |
| 29-09, 11:15 | 2 (1 at the latest bar) | 2 | +0.86% |
| 29-09, 12:45 | 2 | 2 | +0.86% |

The flag is rare (2 to 8 bars per day), so a day gives only a handful of observations; it will take many days to confirm.
Pages: `summaries/regime_summary_<date>_<time>.html` (live) and `_review.html` (with outcomes).
