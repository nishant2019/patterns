# Midday coil watchlist scanner - spec for coding agents

## Purpose
List stocks that were compressed (coiling) through the midday coil zone (11:15-13:45) and give their midday range as two trigger levels,
to be checked at 14:15 / 14:45. Built from `research/golden_hours` (506 stocks, 23 trading days of 30-minute OHLCV, `data/ohlc/<SYMBOL>_<from>_<to>_30m.csv`,
columns `timestamp,open,high,low,close,volume`, bars 09:15 ... 15:15 at 30-minute spacing; 15:15 is a 15-minute bar).

## Rule (frozen; do not tune)
At decision time T (default 14:15, i.e. when the 13:45 bar has closed). Use only bars starting before T.
1. `range% = (high-low)/open*100` for every bar so far; `med = median(range%)` over the bars so far that day.
2. Coil bar = `range% < 0.6 * med`.
3. COIL COUNT = number of coil bars among bars starting 11:15 ... T-30min (max 5 at T=14:15).
4. Watchlist if COIL COUNT >= 3 (tier A if >= 4). Rank by count desc, then midday width asc.
5. Midday high/low = max high / min low over those bars. Width% = (hi-lo)/last close. Position = (last close - lo)/(hi - lo).
6. Triggers: close above midday high = long trigger; close below midday low = short trigger.
Extras shown: volume of midday bars vs the morning (09:15-10:45) average.

## Run
```
python scanners/midday_coil/midday_coil_scanner.py --date 2026-10-05 --csv out.csv   # watchlist for a day
python scanners/midday_coil/midday_coil_scanner.py --backtest                           # point-in-time backtest, all days
```

## Validation result (23 days, T = 14:15) - read this before using it
Signal at the close of the 14:15 bar; outcome = move from that close to the day's last close, signed by break direction, minus that day's mean stock move; t clustered by day.

| Group | n | 14:15 bar closes beyond midday range | 14:45 bar range vs median |
|---|---|---|---|
| 0 coil bars | 2,964 | 18% | 1.47 |
| 1-2 | 7,189 | 19% | 1.34 |
| 3 | 1,235 | 19% | 1.21 |
| 4-5 | 251 | 18% | 1.14 |
| Watchlist (3+) | 1,486 | 19% | 1.20 |

- Break probability is the same (about 19%) in every group; coiled stocks do not break more often.
- Their 14:45 bar is not larger than usual (0.99x their own usual 14:45 range vs 1.03x for no-coil stocks).
- Direction after a break (watchlist): excess +/-0.0% to +0.05% to the close, t +0.6 to +1.6, 13-15 of 23 days positive - no edge.
- An earlier "coil -> late expansion" result was a look-ahead artefact (full-day median) and was withdrawn.

So: the scanner is a clean way to see which stocks went quiet and where their midday levels are, **not a validated trade signal**.
Ideas to test next (as new hypotheses, with a discovery/test split on the 23 days): coil width relative to the stock's usual range, position of the coil within the day's range, volume dry-up (VolVsAM low), market-wide regime.
