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
