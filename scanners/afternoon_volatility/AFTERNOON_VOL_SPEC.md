# Volatility-ranked afternoon watchlist - spec for coding agents

## Purpose
At 14:15 rank stocks by how much they are likely to move in the last 90 minutes (14:15 bar open to close), so you know where to look and how wide to set stops.
**It does not predict direction.** Derived from `research/midday_coil` (loud/wide midday -> bigger afternoon move, robust on 17-18 of 18 days; no directional edge).

## Data
`data/ohlc/<SYMBOL>_<from>_<to>_30m.csv`, columns `timestamp,open,high,low,close,volume`, 30-minute bars 09:15 ... 15:15 (15:15 is a 15-minute bar). 506 stocks, 23 days.

## Rule (frozen; point-in-time at T = 14:15, only bars starting before T)
1. Midday bars = bars starting 11:15 ... T-30min.
2. `W` = (max high - min low of midday bars) / last close * 100, divided by the stock's average of that quantity over prior days.
3. `Vr` = mean volume of the midday bars, divided by the stock's average of that quantity over prior days.
4. Stocks need >= 5 prior days (also of afternoon moves). SCORE = mean of the day's percentile ranks of W and Vr (0-100).
5. HOT = W and Vr both in the top third of that day's stocks; WARM = SCORE >= 66.7 but not both; others hidden unless `--all`.
6. Printed for sizing: USUAL afternoon move = the stock's average |14:15 open -> close| % over prior days; midday high/low, day high/low, VWAP, turnover (Rs crore).

## Run
```
python scanners/afternoon_volatility/afternoon_vol_scanner.py --date 2026-10-05 --top 40 --csv out.csv
python scanners/afternoon_volatility/afternoon_vol_scanner.py --backtest
```

## Validation (18 usable days, 9124 stock-days; discovery 9 / test 9)
- Daily rank correlation of SCORE with afternoon movement vs the stock's own usual: +0.105 (t 11.4, 18/18 days); discovery +0.096, test +0.113.
- Afternoon move in multiples of the stock's usual: HOT 1.54x, WARM 1.35x, rest 1.18x (test: 1.57 / 1.35 / 1.20).
- In absolute terms: HOT 0.64%, WARM 0.55%, rest 0.53% (test 0.67 / 0.57 / 0.58). Only the top score decile stands out clearly (0.73% vs 0.50-0.57% for deciles 1-9, EXPAND 1.68x).
- Calibration learned on discovery (HOT 1.52x, WARM 1.35x, rest 1.16x of usual): test predictions 0.70 / 0.61 / 0.59% vs actual 0.67 / 0.57 / 0.58% (mean); the median actual is about 70% of the predicted mean (moves are right-skewed).
- HOT stocks with turnover above the median show a larger multiple (1.63x) than below (1.45x), so prefer liquid names.

## Limits
Direction is not predicted (see `research/midday_coil/REPORT.md`: no continuation of midday drift, excess return after breaks about 0). 18 days, one regime. The usual-move baseline needs history, so the first 5 days per stock are unusable.
