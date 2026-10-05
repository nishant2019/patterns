# Fading late breakouts on all 23 days
> **Not a 30-minute trade:** this test enters at the 15:15 bar, which is only 15 minutes long. Parked; see NEW_EXTREME_30M_REPORT.md.
`python scanners/afternoon_volatility/late_break_fade.py` (output: `late_break_fade_output.txt`). The late-break fade (E4) needs no watchlist history, so it uses every day in `data/ohlc` (1 Sep - 5 Oct, 23 days, 7,674 stock-days) instead of the 18 usable for the watchlist. No newer data was available. Rule unchanged from the earlier test: the 14:45 bar closes above the day's highest high / below its lowest low (of all bars before it); fade it (short up-breaks, long down-breaks), enter at the 15:15 open, exit at the close; 0.06% round trip. 990 events (12.9% of stock-days).

| Cut | n | Gross | Net (0.06%) | t | Days positive |
|---|---|---|---|---|---|
| All 23 days | 990 | +0.078% | **+0.018%** | +0.5 | 12/23 |
| First 11 days / last 12 days | 489 / 501 | +0.098% / +0.060% | +0.038% / -0.000% | +0.3 / +0.4 | 5/11, 7/12 |
| Cost 0.03% / 0.10% | 990 | +0.078% | +0.048% / -0.022% | +1.9 / -1.3 | 15/23, 7/23 |
| Up-breaks (short) | 328 | +0.006% | -0.054% | -0.9 | 10/22 |
| Down-breaks (long) | 662 | +0.114% | +0.054% | +2.1 | 13/22 |
| Market-neutral excess | 990 | +0.066% | - | +2.8 | 17/23 |

## What changed with more days
1. **The earlier hint mostly disappears.** On 18 days the all-stock fade looked like +0.03% net; on 23 days it is +0.018% net (t +0.5, 12/23 days positive) and the two halves differ (first +0.038%, second -0.000%). No consistent profit after the 0.06% cost; it is positive only if costs are 0.03% (t +1.9).
2. **All of it comes from down-breaks.** Fading up-breaks earns nothing (+0.006% gross, hit 45%); fading down-breaks, i.e. buying a stock that has just made a new low of the day in the 14:45 bar, earns +0.114% gross / +0.054% net (t +2.1, 13/22 days). Not stable by size (small and large breaks +0.044% net, medium -0.033%) and not related to volume or to where the bar closed.
3. **Reversal into the close is real in relative terms.** Continuing a late breakout loses -0.078% gross (net -0.138%, t -6.0, 3/23 days) and the market-neutral fade excess is +0.066% (t +2.8, 17/23 days). But that is only about the size of the 0.06% cost, and fading *any* 14:45 bar's direction earns only +0.031% gross, so the breakout adds roughly +0.05% over the generic last-bar mean reversion.
4. **Market dependence:** the fade earns +0.040% net on days when the market's last bar is up (9/15 days) and -0.031% net when it is down (3/8 days); it is a long-biased result in a mildly rising close, not a stable signal.
5. The 15:15 bar is only 15 minutes long and the entry gap (signal close -> 15:15 open) is ~0, so slippage depends mostly on spread/impact in the last minutes; nothing here accounts for that.

## Verdict
Fading late breakouts is **not** a validated edge: +0.018% net (t 0.5) after a 0.06% round trip, unstable across halves, one-sided (down-breaks only) and dependent on the market's last bar. The only positive thread is buying new day lows made in the 14:45 bar (+0.054% net, t 2.1, 13/22 days) - a hypothesis to retest on more data (a different month), not something to trade yet. Continuation of late breakouts is clearly worse (-0.14% net).
Caveats: 23 days, one regime (month of Sep-Oct 2026); 09-15 alone contributes 151 events.
