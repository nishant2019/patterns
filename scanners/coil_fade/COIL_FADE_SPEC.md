# Coil-breakout fade

Scanner and backtest for fading delta-confirmed breakouts out of a coil.
Basis: `research/compression/REPORT.md` (strong order flow on a break out of a
tight coil tends to fail).

## Rules (point-in-time; signal at the close of the breakout bar)

1. Master candle = first 30-minute bar.
2. Coil: at least 3 of the next 4 bars lie fully inside the master
   (high <= master high, low >= master low).
3. Breakout: the first later bar that closes outside the master range. It
   qualifies only if its delta (CVD change as % of bar volume) in the break
   direction is >= 15%. If the first break is not delta-confirmed, no signal.
4. Fade: up-break → SHORT at the close; down-break → LONG.

Parameters: `PARAMS` in `coil_fade_scanner.py` (`coil_bars=4`, `min_inside=3`,
`min_delta=15`).

## Usage

```bash
python scanners/coil_fade/coil_fade_scanner.py scan data/CVD_Scanner_* -o scanners/coil_fade/results/signals.csv
python scanners/coil_fade/coil_fade_scanner.py backtest data/CVD_Scanner_* --cost 0.10
```

## Backtest (6 days, 3,040 stock-days, 415 signals: 114 short, 301 long)

Entry at the breakout-bar close. Exit at the stop, the target, or the last bar.
If a bar touches both the stop and the target, the stop is assumed first. No
costs unless stated. Stop modes: `bar` = breakout bar extreme, `bar+` = that
plus 0.25 × master range, `edge` = far master edge plus 0.25 × master range,
`mr<x>` = x × master range from entry.

| Stop | Target | Trades | Win | Avg / trade | Avg R | Stopped | Days + |
|---|---|---|---|---|---|---|---|
| bar | master edge | 374 | 28% | −0.06% | −0.34 | 268 | 1/6 |
| bar | midpoint | 374 | 15% | −0.03% | −0.19 | 310 | 3/6 |
| bar+ | master edge | 399 | 55% | −0.13% | −0.24 | 159 | 2/6 |
| bar+ | hold to close | 399 | 32% | −0.15% | −0.29 | 213 | 2/6 |
| edge | master edge | 393 | 42% | −0.08% | −0.31 | 225 | 2/6 |
| 0.5 × master range | hold to close | 399 | 37% | −0.16% | −0.22 | 159 | 2/6 |
| 1.0 × master range | hold to close | 399 | 46% | −0.09% | −0.08 | 59 | 3/6 |
| 1.5 × master range | hold to close | 399 | 49% | +0.01% | −0.02 | 19 | 4/6 |
| 2.0 × master range | hold to close | 399 | 50% | +0.05% | 0.00 | 5 | 4/6 |
| **No stop** | hold to close | 399 | 50% | **+0.07%** | 0.00 | 0 | 4/6 |

Without a stop, the fade made +0.07% per trade (+0.16% against the median
stock), consistent with the research (+0.12% to +0.13%). Shorts: +0.16%,
longs: +0.04% (+0.15% / +0.16% market-adjusted). By day, raw: 15-09 −0.47%,
16-09 +0.13%, 17-09 +0.27%, 18-09 +0.09%, 28-09 −0.00%, 01-10 +0.28%.

With a 0.10% round-trip cost every variant loses money (no-stop: about −0.03%).

## Conclusion

**Stops do not work with this edge.** The edge is a small drift (about 0.1%)
toward the close, while a typical 30-minute bar ranges about 0.7% and the median
master range is 1.9%. The breakout-bar extreme is only about 0.15% from the
entry, so 70%+ of trades are stopped out by noise; every stop tighter than
1.5 × master range lowers the result, and the tightest are the worst. The
results improve monotonically as the stop widens and are best with none. The
signal is real in the research sense (a small statistical bias) but there is no
stop placement in this data that turns it into a tradeable positive-expectancy
rule, and it does not clear realistic costs.

Caveats: 6 days only; one parameter set (not tuned); entries use signal bar
closes; the 15-09 day (a broad selloff) is the main drag in raw terms.
