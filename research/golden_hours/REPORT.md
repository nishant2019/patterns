# Golden hours and coiling hours: 506 stocks x 23 trading days (01 Sep - 05 Oct 2026), 30-minute OHLCV (`data/ohlc/`)

Run: `python research/golden_hours/golden_report.py` -> `slot_matrix.csv/.md`, `golden_hours.html/.png`, `run_output.txt`.
11,638 stock-days per slot. Range and volume are indexed to each stock's own day average, so stocks are comparable. 15:15* is a 15-minute bar.
The first pass used the 7 CVD days; this is the re-run on the larger OHLC set (same conclusions, now much firmer).

| Slot | Type | Range index | Volume index | % of day volume | Bars moving >0.5% | Coil bars | Score |
|---|---|---|---|---|---|---|---|
| 09:15 | OPEN DRIVE | 2.45 | 2.10 | 16.5 | 63% | 0% | 98 |
| 09:45 | ACTIVE | 1.23 | 1.12 | 8.9 | 34% | 2% | 87 |
| 10:15 | ACTIVE | 1.01 | 0.86 | 6.8 | 27% | 7% | 75 |
| 10:45 | transition | 0.92 | 0.79 | 6.2 | 22% | 10% | 62 |
| 11:15 | transition | 0.83 | 0.74 | 5.9 | 18% | 16% | 40 |
| 11:45 | COIL ZONE | 0.79 | 0.72 | 5.7 | 18% | 18% | 42 |
| 12:15 | COIL ZONE | 0.75 | 0.68 | 5.4 | 16% | 23% | 15 |
| 12:45 | COIL ZONE (deadest) | 0.72 | 0.68 | 5.4 | 13% | 27% | 5 |
| 13:15 | COIL ZONE | 0.75 | 0.70 | 5.5 | 19% | 24% | 38 |
| 13:45 | COIL ZONE | 0.77 | 0.77 | 6.1 | 17% | 23% | 32 |
| 14:15 | COIL ZONE (ending) | 0.80 | 0.92 | 7.3 | 18% | 20% | 38 |
| 14:45 | CLOSE VOLUME | 1.05 | 1.88 | 14.9 | 22% | 5% | 68 |
| 15:15* | transition | 0.91 | 1.04 | 8.0 | 20% | 13% | 50 |

## Findings
1. **Golden hours: 09:15, 09:45, 10:15, then 14:45.** 09:15 carries 16.5% of the day's volume and moves >0.5% in 63% of stock-days; 14:45 carries 14.9%. Both are above the stock's day average on 23/23 and 14/23 days; 09:45 on 23/23. Together 09:15-10:15 and 14:45 hold ~48% of the day's volume in 4 of 13 bars.
2. **Coil zone: 11:45-14:15, deepest 12:15-12:45.** Volume 68-72% of a normal bar, 13-19% of bars move >0.5%, and 23-27% of bars are compressed (range < 0.6x the stock's median bar). Every midday slot was below the stock's day-average range on 21-23 of 23 days. 12:45 is the quietest slot.
3. **Coils persist, then release late.** After a compressed midday bar, the next bar is compressed again 24-34% of the time and expands (>1.5x median) only 8-11% of the time. Expansion shows up at 14:45 (22% after a coil, with 5% coil share): stocks with 3+ compressed bars between 11:15 and 13:45 had a bigger 14:45 bar (range index 1.19 vs 1.05 for 1-2 coil bars and 0.96 for none) and had broken their midday range by 14:15 in 28% of cases (19% / 14%). Midday coil stocks are the watchlist for 14:15-14:45; this does not say which side breaks.
4. **Direction is not predictable by slot.** Market-neutral momentum (a bar's direction vs the next bar, after removing that day-slot's average stock move) is ~49% everywhere; 09:45 (47.4%), 14:45 (48.4%) and 15:15 (46%, t -4.9) lean to reversal, positive on only 5-8 of 23 days. Breakout-bar follow-through is ~0 or negative (15:15 -0.06%, t -5.8). Raw hit rates in the 7-day CVD data (62% at 10:45) were market-wide co-movement.
5. **Costs:** a 0.06% round trip is ~3% of a 09:15 bar's range (1.9%) but ~10% of a midday bar's range (0.56-0.62%). Midday trades start with a much bigger handicap.

## How to use it
- Trade in the active windows (09:15-10:15, 14:45); stand aside or size down 12:15-13:45.
- Build the midday watchlist from stocks with 3+ compressed bars (coil range = levels) and check it from 14:15.
- Do not use "previous bar up/down" as a signal; if anything, the last bars of the day fade.

## Caveats
- 23 days, one market regime; month-specific events can move individual days.
- This measures activity and compression, not profitability. No slot showed a directional edge.
- Volume/range spikes at 09:15 and 14:45 are structural (open/close); the exact ordering among midday slots is less reliable.
