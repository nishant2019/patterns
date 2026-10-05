# Golden hours and coiling hours (506 stocks x 7 days, 30-minute bars; 3,544 stock-days per slot)

Run: `python research/golden_hours/golden_report.py` -> `slot_matrix.csv/.md`, `golden_hours.html/.png`, `run_output.txt`.
Range/volume are indexed to each stock's own day average, so stocks are comparable. 15:15 is a 15-minute bar.

| Slot | Type | Range index | Volume index | % of day volume | Bars moving >0.5% | Coil bars | Score |
|---|---|---|---|---|---|---|---|
| 09:15 | OPEN DRIVE | 2.52 | 2.04 | 16.0 | 72% | 0% | 97 |
| 09:45 | ACTIVE | 1.22 | 1.09 | 8.6 | 39% | 2% | 83 |
| 10:15 | transition | 0.96 | 0.82 | 6.5 | 29% | 9% | 73 |
| 10:45 | transition | 0.89 | 0.76 | 6.0 | 28% | 11% | 63 |
| 11:15-12:45 | COIL ZONE | 0.75-0.78 | 0.69-0.73 | 5.5-5.8 | 15-22% | 18-22% | 15-32 |
| 13:15 | coil zone (but 27% move) | 0.76 | 0.70 | 5.6 | 27% | 19% | 47 |
| 13:45 | COIL ZONE (deadest) | 0.69 | 0.71 | 5.6 | 16% | 26% | 20 |
| 14:15 | transition | 0.82 | 0.92 | 7.3 | 22% | 19% | 47 |
| 14:45 | CLOSE VOLUME | 1.11 | 2.05 | 16.2 | 32% | 5% | 73 |
| 15:15* | transition | 0.94 | 1.15 | 8.8 | 24% | 13% | 52 |

## Findings
1. **Golden hours = 09:15-10:45 and 14:45.** 09:15 and 14:45 each carry 16% of the day's volume; 09:15 moves >0.5% in 72% of stock-days (midday: 15-22%). 09:45 is the next best window; 10:15-10:45 are a fading continuation of the morning.
2. **Coil zone = 11:15-13:45.** Volume is ~70% of a normal bar, range is ~75%, a third of bars are choppy (body < 30% of range), and 18-26% of bars are compressed (13:45 highest at 26%). Coils persist: after a compressed bar, the next bar is compressed again 22-34% of the time and expands (>1.5x median) only 8-11% of the time.
3. **Coiling is repeatable.** Midday slots had above-average range on 0/7 days; 09:15, 09:45 and 14:45 were above average on 7/7, 7/7 and 5/7 days.
4. **Midday coil -> late expansion:** stocks with 3+ compressed bars between 11:15 and 13:45 had a bigger 14:45 bar (range index 1.29 vs 1.11 for 1-2 coil bars and 1.02 for none) and broke their midday range by 14:15 in 32% of cases (vs 21% and 16%). Coiling stocks are therefore the ones to watch at 14:15-14:45 (the range sets up the level; this does not say which side).
5. **Direction is NOT reliable.** After removing the market-wide move, a bar's direction does not predict the next bar's direction in any slot (~50%); 09:45, 13:45 and 15:15 lean slightly to reversal (44-48%). The raw hit rates (e.g. 62% at 10:45) are the whole market moving together on a few days, not stock-level momentum. Breakout-bar follow-through is also ~0 (14:45 and 15:15 negative, t about -2.7, 0/7 days positive).
6. **Cost reality:** a 0.06% round trip is ~3% of a 09:15 bar's range (2.2%) but ~9-10% of a midday bar's range (0.6-0.7%), so midday trades start with a much larger cost handicap.

## How to use it
- Take discretionary trades in the active windows (09:15-10:45 and 14:45); size down or stand aside 11:15-13:45.
- Use the midday coil to build a watchlist (3+ compressed bars; master/coil range as levels) and look at it from 14:15.
- Do not treat "previous bar was up/down" as a signal in any slot.

## Caveats
- 7 days only, and market-wide days dominate the slot-to-slot comparison; the 09:15/14:45 volume spikes are structural (open and close), so those are robust, but the finer ordering between midday slots is not.
- This measures activity and compression, not profitability: no slot showed a directional edge by itself.
