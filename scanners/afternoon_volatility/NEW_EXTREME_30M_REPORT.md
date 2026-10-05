# 30-minute-only check: new day highs/lows at every slot
Scope rule from now on: **only full 30-minute bars are traded** (entry at a bar open, exit at a bar close). The 15:15 bar is only 15 minutes long, so the late-break fade (`LATE_BREAK_FADE_REPORT.md`) and "buy new lows in the 14:45 bar" (`NEW_LOW_BUY_REPORT.md`) - both of which entered at 15:15 - are **not valid 30-minute trades** and are parked. The last tradable entry is the 14:45 bar (closes 15:15).

`python scanners/afternoon_volatility/new_extreme_30m.py` (output: `new_extreme_30m_output.txt`): 23 days, 6,406 signals (bar closes beyond all earlier highs/lows of the day, signal bars 11:15-14:15), enter next bar open, hold 1 or 2 full bars, 0.06% cost. Four rule sets fixed in advance: buy new lows, sell new highs (reversals) and the two continuation mirrors.

| Rule | Hold | n | Gross | Net | Days positive |
|---|---|---|---|---|---|
| Buy new day lows | 1 bar | 4,285 | -0.039% | -0.099% | 6/23 |
| Buy new day lows | 2 bars | 3,798 | -0.054% | -0.114% | 12/23 |
| Sell new day highs | 1 bar | 2,121 | -0.021% | -0.081% | 6/23 |
| Sell new day highs | 2 bars | 1,837 | -0.029% | -0.089% | 7/23 |
| Sell new day lows (continuation) | 1 / 2 bars | 4,285 / 3,798 | +0.039% / +0.054% | -0.021% / -0.006% | 3/23, 4/23 |
| Buy new day highs (continuation) | 1 / 2 bars | 2,121 / 1,837 | +0.021% / +0.029% | -0.039% / -0.031% | 8/23, 10/23 |

- **Nothing works on 30-minute bars.** All four rules are negative net of cost pooled, and the individual slot results flip sign between the first and second half of the days (e.g. sell new highs at 12:45: H1 +0.23%, H2 +0.01%; sell new lows at 12:15 held 2 bars: +0.30% net on n=562 but the two halves are +0.12% / +0.00%, a one-off among 52 slot cells).
- The 14:15-signal case (buy the new low, hold the 14:45 bar, i.e. the closest 30-minute version of the 14:45 idea) is -0.095% gross, -0.155% net. The earlier +0.11% came from the 15-minute 15:15 bar.
- Which direction a day-extreme will go next is not predictable from the extreme alone on 30-minute bars, consistent with the earlier direction-filter and breakout results.

## What remains usable on the 30-minute timeframe
- Time-of-day map (golden hours, coil zone): where movement is.
- Volatility-ranked afternoon watchlist: which stocks will move most from 14:15 to the close (the move is measured as 14:15 open to close and is fully tradable on 30-minute bars; hold the 14:15/14:45 bars).
- Direction: not predicted by any test so far (filters, breakouts, new extremes, CVD patterns).
Caveats: 23 days, one regime; 52 slot x rule x hold cells, so a couple of nominal hits are expected by chance.
