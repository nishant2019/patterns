# CVD candle patterns – predictive power (7 days, ~506 stocks, 30-min bars)

Study: `cvd_pattern_study.py` (29 patterns: 1-bar, 2-bar, 3-bar, CVD-vs-price structure; 126k pattern-bars).
Signal at bar close (bars 2-9); outcome = next 1 / 2 bar price return minus the cross-sectional mean stock of the same day/bar.
Discovery = 4 days, test = 3 days; t-stats clustered by (day, bar) because stocks move together.

## Findings
1. **Price direction: no usable edge.** After removing the market-wide baseline, all 29 patterns are within about ±0.02% over 2 bars
   (a 30-min bar moves ~0.4%). Only 2 of 29 had |t|≥2 in discovery (chance gives ~1.5) and 0 replicated in the test days.
2. **First pass was misleading:** against the *median* stock every pattern looked positive (+0.04%, t up to 8). That was the mean>median skew
   and stock-to-stock correlation, not a pattern effect. Always baseline against the same-bar mean and cluster the t-stat.
3. **Divergences do not predict.** "CVD new low, price not" (absorption) +0.016% (t 2.1, test t 1.3); "CVD up, price down" flipped sign (+0.02 → −0.05).
4. **What does persist is order flow itself:** after a big selling bar (|D|≥30%), the next bar is also net selling 64.7% of the time
   (big buying → buying 55.6%). The sign of delta carries over, but price does not follow with a tradable size.

## Verdict
CVD candle shapes describe what happened (who was aggressive, whether it was absorbed) – they are not standalone entry signals.
Use them as context (regime, levels, absorption labels), not as triggers. Not tested: intraday-to-close horizon, combining with levels, costs.
