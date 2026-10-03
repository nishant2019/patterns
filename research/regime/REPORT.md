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
