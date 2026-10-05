# Direction filters on the afternoon volatility watchlist
`python scanners/afternoon_volatility/direction_filters.py` (output: `direction_output.txt`). Decision 14:15, point-in-time, 18 usable days (9 discovery / 9 test), 9,124 stock-days. Outcome = side x move from the 14:15 open to the day close, raw and as excess over that day's mean stock; t clustered by day; side = continue the filter (a negative result means the fade works).

Filters (fixed beforehand): MORN (close vs day open), VWAP (close vs session VWAP), DPOS (top/bottom third of the day range), GAP (open vs prior close), RELST (day return vs market: top/bottom third of stocks), LAST2 (last two bars), MID (midday drift), VOLD (up-volume minus down-volume share in the midday). Universes: HOT, WARM, HOT+WARM, REST.

## Result: no direction filter works
- 32 tests; 3 had |t| >= 2 (chance expects ~1.6). **None passes the gate** (same sign in both halves, test |t| >= 2, mean excess above the 0.06% round-trip cost).
- **HOT (the stocks with the biggest expected move):** every filter's excess is between -0.03% and +0.02% with |t| <= 1.2; hit rates 50.2-52.2%. The one outlier, GAP (continue the gap), is +0.053% in test (t 3.8) but -0.037% in discovery, so it is not stable.
- **WARM:** relative strength looks decent (+0.053%, t 1.8, 12/18 days; discovery +0.076% t 2.0, test +0.030%), LAST2 leans to a fade (continuing the last 2 bars -0.064%, t -2.1, i.e. fading it +0.06%; test only t -0.9). Both are below or at the cost line and are one-off tests among 32.
- **REST:** nothing beyond a slight fade of VWAP / midday drift / volume direction (excess -0.016 to -0.021%, |t| ~2), i.e. all-stock afternoons mildly mean-revert, but far below costs.
- Raw (not market-adjusted) results are negative for most filters (-0.01% to -0.09%): continuing the day's direction into the close slightly loses on average over these 18 days.

## Conclusion
The volatility watchlist tells you where the movement will be; none of 8 simple direction filters (trend, VWAP, range position, gap, relative strength, last bars, midday drift, volume direction) tells you which way, in any tier. Direction has to come from something outside this data (news/levels/your own setup), or from a richer hypothesis tested on more days. Reasonable next tests, as new hypotheses with a fresh split: break of the day high/low or the midday range *with* volume (event-based entries rather than static filters), and tick-level order flow on the HOT list.
Caveats: 18 days, one regime; 32 tests, so one or two nominal hits are expected by chance.
