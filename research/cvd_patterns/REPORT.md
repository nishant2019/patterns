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

## Part 2 – patterns at key levels (`cvd_levels_study.py`)
Levels (point-in-time): master 09:15 range, running day high/low, running VWAP. Touch = bar extreme within 0.2% of the level, closing on the right side.
Bullish patterns at support / bearish at resistance, outcome signed in the implied direction, vs same-bar mean stock. 42 combos, 7 days, discovery 4 / test 3.
- Touching a level alone: no edge (|move| ≤ 0.02% over 2 bars).
- Pattern + level: 3 combos had |t|≥2 in discovery (chance ≈ 2), **0 replicated**.
- Only recurring hint: "CVD makes a new low but price doesn't" at VWAP/master-low support: +0.05–0.06% over 2 bars, +0.07–0.09% to close
  (t 2.1–2.6 pooled, n≈740 each, ~5.6 trading days positive in discovery, weaker on test). Same effect as in the pattern-only study; a hypothesis for more data, not an edge after costs.
- Bearish patterns at resistance: nothing (even slightly wrong-signed).
