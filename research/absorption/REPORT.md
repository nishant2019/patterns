# Absorption patterns in 30-minute CVD data

Deep analysis of every 30-minute bar of every stock across 5 NSE trading days
(15-09, 16-09, 17-09, 18-09 and 01-10-2026; ~2,530 stock-days, 25,340 bars),
looking for **buying and selling absorption** and related order-flow patterns.

## Background (internet research)

- **Absorption** is a bar with heavy aggressive flow but little price
  movement: passive limit orders soak up the aggression. Negative delta with
  price holding means buyers absorbing selling (potential bottom); positive
  delta with price stalling means sellers absorbing buying (potential top).
  This is the order-flow form of Wyckoff's *effort vs. result*.
  ([LuxAlgo](https://www.luxalgo.com/library/concept/delta-divergence/),
  [OrderFlowLabs](https://orderflowlabs.com/blogs/theblog/footprint-chart-guide),
  [United Daytraders](https://united-daytraders.com/blog/delta-cvd-advanced-order-flow))
- **Delta divergence**: price makes a higher high while CVD makes a lower high
  (bearish), or a lower low with a higher CVD low (bullish). Practitioners
  treat it as a warning, not an entry.
  ([LuxAlgo](https://www.luxalgo.com/library/concept/delta-divergence/),
  [AlphaX](https://alphax.trading/dictionary/delta-divergence))
- **Academic evidence**: order imbalance moves prices at the same time and
  predicts only very short-horizon returns; persistent price pressure from
  imbalances tends to reverse later, consistent with liquidity providers
  managing inventory.
  ([Chordia & Subrahmanyam, SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=354122),
  [Chordia, Roll & Subrahmanyam](https://www.anderson.ucla.edu/documents/areas/fac/finance/21-05.pdf))

## Method

- `events.py` builds one row per stock-bar with point-in-time features: bar
  delta % of volume, bar return, volume vs. earlier bars, close location,
  intrabar CVD push, 3-bar price/CVD change, position in the day's range.
- Forward returns: next 1 bar, next 2 bars, to the close. Each is measured
  **against the average stock at the same bar on the same day**, so market
  direction is removed.
- `grid.py` maps forward return across delta × price-return buckets.
- `patterns.py` tests 12 textbook definitions (absorption, continuation,
  climax, divergence, intrabar rejection) with t-stats and day-by-day
  consistency.

## Findings

Forward returns are vs. the average stock (%). "Days +" = days with a positive
average out of 5.

| Pattern | Definition | Events | Next 2 bars | To close | Days + (2 bars) |
|---|---|---|---|---|---|
| **Selling absorption (SA)** | delta ≤ −30%, bar return −0.5…+0.15%, volume ≥ 1.5× | 287 | **+0.15%** (t 3.8) | **+0.16%** (t 3.0) | 5/5 |
| SA, refined (SAB) | + volume 1.5–3×, lower half of day range | 166 | **+0.25%** (t 4.4) | **+0.19%** (t 2.9) | 4/5 |
| Selling continuation | delta ≤ −30%, return < −0.5%, volume ≥ 1.5× | 223 | +0.04% | +0.10% | 3/5 |
| Buying absorption (BA) | delta ≥ +30%, return −0.15…+0.15%, volume ≥ 1.5× | 105 | −0.02% | −0.04% | 2/5 |
| Buying climax | delta ≥ +30%, return > +0.5%, volume ≥ 1.5× | 231 | −0.11% (t −1.9) | −0.18% (t −2.2) | 0/5 |
| **Buying exhaustion (BEX)** | delta ≥ +50%, return > +0.5%, volume ≥ 1.5× | 100 | −0.12% | **−0.39%** (t −3.5) | 1/5 (to close: 1/5) |
| Bullish 3-bar divergence | price up, CVD ≤ −20% | 1,072 | +0.04% | +0.11% (t 3.0) | 4/5 |
| Bearish 3-bar divergence | price down, CVD ≥ +20% | 833 | +0.03% | +0.03% | 3/5 |

### 1. Selling absorption works, and is the strongest pattern

Heavy net selling (≥ 30% of bar volume) that fails to push price down,
on above-normal volume, is followed by outperformance on all 5 days.
It is stronger:
- near the day's low (lower third: +0.20% next 2 bars, t 3.6, 5/5 days),
- on a moderate volume spike (1.5–3×: +0.19%, t 4.0); spikes ≥ 3× did not
  work (+0.02%), consistent with block trades rather than absorption,
- with heavier selling (delta ≤ −50%: +0.18%).

Time of day did not matter much.

### 2. Buying absorption does NOT work the same way

The textbook mirror (heavy buying, price flat) has no edge (−0.02%). Markets
here are not symmetric: what predicts underperformance is **buying
exhaustion**, i.e. very heavy buying (≥ 50% of volume) that *does* lift price
sharply on a volume spike. These stocks lag the market by −0.39% to the close
on 4 of 5 days. This matches the academic finding that price pressure from
one-sided flow tends to reverse.

### 3. Divergences are weak

The 3-bar bullish divergence (price up while CVD falls) adds +0.11% to the
close, but it fires on 1,000+ bars and does little over the next hour.
The bearish divergence has no edge.

## SAB as a filter on OAB

`oab_sab_filter.py` checks whether an SAB bar occurs inside each OAB window
(67 OAB setups, 5 days; return = window end → close vs average stock).

| OAB subset | Setups | Breakout | vs market | Beat market |
|---|---|---|---|---|
| All OAB | 67 | 60% | +0.21% | 58% |
| SAB inside window | **2** | 50% | +1.01% | 2/2 |
| No SAB inside window | 65 | 60% | +0.18% | 57% |
| Relaxed SAB (any volume/location) inside window | 49 | 59% | +0.23% | 55% |
| No relaxed SAB inside window | 18 | 61% | +0.15% | 67% |

**SAB does not work as a filter on OAB, mainly because they almost never
co-occur.** OAB windows are quiet by design (heavy bar CVD ≤ 45% of volume,
compressing range), while SAB needs a volume spike of 1.5–3× and CVD ≤ −30%.
Only PNB (15-09) and TORNTPHARM (17-09) had both. Relaxing SAB to any volume
makes it overlap (49 of 67) but then it adds nothing (+0.23% vs +0.15%,
breakout rate unchanged). They are two separate signals, best used
independently.

## Caveats

- **Five days.** Results are consistent across days but the sample is still
  small; refined thresholds (SAB, BEX) were chosen on this data.
- **About 20 definitions were tested.** SA (t 3.8) and BEX (t −3.5) would
  survive a multiple-testing correction; the weaker patterns might not.
- **No costs.** +0.15–0.25% over an hour is close to typical intraday
  round-trip costs, so the edge is thin as a standalone trade.
- **Overlap.** Some events are consecutive bars of the same stock.

## Files

- `events.py` – builds `events.csv` (bar-level table; regenerate, not committed).
- `grid.py`, `patterns.py` – the analysis (`python patterns.py split` for subgroups).
- `absorption_scanner.py` – lists SAB and BEX events per stock and day.
- `absorption_events.csv` – all SAB/BEX events for the 5 days.
