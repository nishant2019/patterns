# Midday coil: tight width and volume dry-up as new hypotheses
`python research/midday_coil/coil_width_volume.py` (output in `run_output.txt`). Point-in-time at 14:15; 18 usable days (the first 5 are baseline warm-up), 9,104 stock-days; discovery = first 9 days, test = last 9. Definitions were fixed before the run: relative width and relative volume are each measured against the stock's own average over prior days; "tight" / "dry" = bottom third of that day's stocks.

## Results (group minus rest, averaged over days; t clustered by day)
| Hypothesis | Metric | Discovery | Test |
|---|---|---|---|
| H1 tight | Break by 14:45 close | +10.3 pts (t 5.1, 9/9 days) | +15.9 pts (t 7.1, 9/9) |
| H1 tight | Late-session move vs own usual | -0.22x (0/9 days higher) | -0.23x (0/9) |
| H1 tight | Follow-through after a 14:15 break | -0.01% (t -0.3) | +0.07% (t 2.9) |
| H2 dry-up | Break by 14:45 close | +5.0 pts (t 3.2) | +6.5 pts (t 4.9) |
| H2 dry-up | Late-session move vs own usual | -0.19x (0/9) | -0.26x (0/9) |
| H2 dry-up | Follow-through after a 14:15 break | +0.04% (t 0.7) | +0.12% (t 1.9) |
| H3 both | Late-session move vs own usual | -0.21x (0/9) | -0.27x (0/9) |
| H3 both | Follow-through after a break | +0.03% (t 0.9) | +0.05% (t 1.1) |

Absolute: tight stocks' late-session move is 1.11x their usual vs 1.34x for the rest; they break the midday range by 14:45 in 47% of cases vs 34%.

## Conclusions
1. **Tight and dry coils do not "explode" later - they stay quiet.** Late-session movement is 17-20% below normal for tight/dry stocks on every one of 18 days, in discovery and test alike (volatility clustering: a quiet midday predicts a quiet afternoon). This is the reverse of the "coil -> expansion" idea, and it is robust.
2. **They do break their (narrow) range more often (47% vs 34%), on all 18 days** - but with a smaller-than-usual move afterwards. A narrow range is simply easier to exceed, so the break is cheap, not a sign of energy. This is my interpretation, not separately tested.
3. **Direction after the break: weak, not consistent.** Excess follow-through is +0.00 to +0.12% (best: dry-up, test +0.12%, t 1.9; tight, test +0.07%, t 2.9 but discovery -0.01%). After a 0.06% round trip there is nothing left, and discovery does not agree with test, so no hypothesis passes the gate (same sign in both halves, test t >= 2, positive after costs).
4. **Inside the 3+ coil watchlist**, tight/dry subsets are even quieter (EXPAND 0.95-1.07x vs about 1.3x); dry-up does not raise breaks there (35% vs 39%).
5. Coil count is almost unrelated to relative width (corr -0.05) and volume (corr -0.01): the three measure different things. Width and volume are moderately related (+0.41).

## Verdict
Neither hypothesis gives a trade signal. Useful as a *negative* filter: tight/dry midday coils are the stocks least likely to move in the last 90 minutes, so deprioritise them for afternoon trades. If anything, the stocks that did NOT go quiet (wider, higher-volume midday) carry the late-session movement.
Caveats: 18 days, one market regime; the follow-through samples are small (about 200-350 breaks per half).

# Part 2 - the stocks that did NOT go quiet (`active_midday.py`, output in `run_output_active.txt`)
Groups fixed in advance (top third of that day's stocks): A LOUD (relative volume), B WIDE (relative width), C both, D no compressed bars. Same 18 days, 9/9 split.

| Group | Late-session move vs own usual (group minus rest) | Break by 14:45 | Excess return 14:15 open -> close | Continues midday drift (MOMO) |
|---|---|---|---|---|
| A LOUD | +0.27x (17/18 days; disc +0.23, test +0.30) | -5.7 pts | +0.044% (t 2.7) | -0.009% (t -0.6) |
| B WIDE | +0.28x (17/18; disc +0.27, test +0.28) | -12.5 pts | +0.058% (t 3.5) | -0.019% (t -1.0) |
| C both | +0.34x (18/18; disc +0.33, test +0.35) | -11.6 pts | +0.060% (t 2.5) | -0.008% (t -0.3) |
| D no coil bars | -0.01x | +0.4 pts | -0.006% | -0.018% (t -1.2) |

1. **Activity persists (robust).** Stocks that were loud/wide at midday move 1.44-1.53x their usual in the last 90 minutes vs 1.27x for the average stock; the effect is on 17-18 of 18 days and in both halves. This is the mirror image of "quiet stays quiet": it is volatility clustering. Combined loud+wide is the strongest group (+0.34x).
2. **But direction is not predictable.** Continuing the midday drift or the position in the midday range gives about -0.01 to -0.04% in every group, equal to the all-stock baseline (-0.016%, t -2.0, slight fade). Break-by-14:45 rates are *lower* for wide groups (their range is wide, harder to exceed).
3. **A small positive excess return remains (+0.04 to +0.06% from 14:15 open to the close, t 2.5-3.5, positive in 14-15 of 18 days, both halves positive).** It does not look like beta (it is larger on market-down days: +0.09% vs +0.01%) but it is below a 0.06% round-trip cost, and it may partly reflect skew: the comparison is against the cross-sectional mean. Not a tradable edge by itself.
4. "No compressed bars" (D) is not the same thing as "active": it shows nothing. The signal is in relative width and volume, not in the coil count.

**Use:** relative midday width and volume (vs the stock's own prior days) tell you where afternoon *movement* will be (a volatility filter for choosing what to trade / how wide to place stops), not which way it will go. Direction still needs another reason.
Caveats: 18 days, one regime; excess return not tested net of costs beyond the rough comparison above.
