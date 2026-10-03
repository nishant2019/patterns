# Master-candle compression: price-only study (6 days, ~3,040 stock-days)

Idea: the first 30-minute bar is the master candle; later bars that stay inside
it are "coiling", and more inside bars means more stored energy. This study
tests the price-only half before adding order flow. Script:
`compression_study.py` (uses bars through 14:45 so every stock aligns).

No VIX is in the data. Day-level volatility is proxied by the median master-bar
range across all stocks that day (`regime` field).

## How common is it?
After 4 bars (decision at 11:15): 0 bars inside the master for 27% of stocks,
1 inside 15%, 2 inside 16%, 3 inside 20%, **4 inside 23%**. Median combined
range of bars 1-4 is 0.79x the master range.

## Does tighter compression predict expansion? No, it predicts containment
Outcome = what happens from 11:45 to 14:45.

| Compression (bars 1-4) | Stocks | Breakout of master range later | Later day range / master |
|---|---|---|---|
| 0 bars inside | 815 | 95% | 1.32 |
| 2 inside | 475 | 79% | 1.21 |
| 4 inside | 693 | **50%** | **0.84** |
| Tightest quintile (cluster ≤ 0.53× master) | 608 | 59% | **0.73** |
| Widest quintile (cluster > 1.19× master) | 606 | 92% | 1.56 |

Rank correlation of "bar range / master range" with later expansion is
**+0.49 to +0.56**: tighter coils are followed by *smaller* later ranges, not
bigger ones.

Absolute check (does a compressed coil expand beyond volatility persistence?):

| Quintile of coil/master ratio | Master range | Coil bar range | Later bar range | Later / coil |
|---|---|---|---|---|
| Q1 (tightest, ratio 0–0.27) | 3.21% | 0.70% | 0.68% | **1.06** |
| Q3 | 2.05% | 0.79% | 0.69% | 0.94 |
| Q5 (loosest, 0.54+) | 1.45% | 1.04% | 0.76% | 0.81 |

After the opening bar, a typical 30-minute bar is ~0.7% regardless. The master
bar is just an unusually large opening bar, so "compressed relative to master"
largely means "normal intraday volatility after a wide open". Later bars are
no larger than the coil's own bars even in the tightest quintile. **So on price
alone, compression does not predict expansion in this data.**

## What price location does predict: which side breaks first
Among compressed stocks (>= 3 of first 4 bars inside, n = 1,288; 53% broke out):

| Close (11:15) position in master range | Stocks | First breakout is up |
|---|---|---|
| Lower third | 385 | **9%** |
| Middle third | 599 | 37% |
| Upper third | 272 | **84%** |

Coil center in the master range shows the same pattern (15% / 42% / 63% up).
This is largely the obvious effect that price breaks the nearer edge first. It
does **not** translate into an edge: return from 11:15 to 14:45 vs the average
stock is about +0.06% to +0.10% in every bucket.

## Conclusions
1. The premise "more inside bars = more energy" is not supported by price
   action alone. Compression predicts the stock stays contained.
2. Compression measured relative to the master bar is confounded by the large
   opening bar. Measure it in the stock's own volatility (bar range %).
3. Direction needs another input; price location mostly tells you which edge is
   nearer, not what pays. This is where order flow has to do the work.
