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

---

# Part 2: adding order flow (scripts `orderflow_study.py`, `breakout_study.py`)

## Stage A: order flow inside the coil does not predict direction
Population: stocks with >= 3 of the first 4 bars inside the master (n = 1,288),
decision at 11:15. Outcome: return 11:15 → 14:45 vs the median stock.
Features tested: net delta % of coil volume, master delta, number of
positive-delta bars, last-bar delta, CVD-vs-price divergence, volume dry-up,
intrabar sell push, close position in master range.

Every Spearman correlation is between **−0.04 and +0.02**; the top-vs-bottom
quintile spreads are scattered around zero (−0.17% to +0.00%) with no day
consistency. The same holds for >= 2 inside after 3 bars (n = 1,558).
**Delta building inside the coil does not tell you what happens next.**

## Stage B: the breakout bar is where order flow matters, and it is a fade
First bar that closes outside the master range (after the coil window).
Outcome: direction-signed return from that bar's close to 14:45, minus the
median stock (n = 598 breakouts, 201 up and 397 down; mean −0.07%).

- Delta on the breakout bar (in the break direction) is **negatively**
  correlated with what follows (Spearman −0.12, top vs bottom quintile
  −0.20%, worse on 6 of 6 days).
- Breakouts where delta *agrees* with the break (n = 473): −0.10%, positive
  on only 1 of 6 days. Breakouts where delta *disagrees* (n = 125): +0.04%.
- Strong order flow on a break out of a coil is **exhaustion/absorption**, not
  confirmation. This matches the earlier absorption research (buying
  climax underperforms, selling absorption outperforms).

Fading it (take the opposite side; market-adjusted, no costs):

| Break with delta in break direction | Trades | Fade return | Win | Days + |
|---|---|---|---|---|
| >= 0% | 473 | +0.10% (t 2.7) | 53% | 5/6 |
| >= 15% | 369 | **+0.13% (t 3.2)** | 57% | 5/6 |
| >= 30% | 247 | +0.12% (t 2.5) | 58% | 5/6 |
| >= 45% | 158 | +0.13% (t 2.0) | 58% | 6/6 |
| >= 45%, up breaks only (fade = short) | 31 | +0.26% (t 2.6) | 71% | 5/5 |

The same test with a looser coil (>= 2 inside after 3 bars) gives smaller
numbers (+0.05% to +0.08%).

## Compression does matter, as context for the fade
Same rule (delta in break direction >= 30%), split by how compressed the start was:

| Inside bars among first 4 | Breakouts | Fade return | t |
|---|---|---|---|
| 0–1 (not compressed) | 327 | **−0.00%** | −0.1 |
| 2 | 137 | −0.11% | −1.2 |
| 3–4 (compressed) | 247 | **+0.12%** | +2.5 |

Strong-delta breaks out of a tight coil tend to fail; the same breaks out of a
non-compressed start do not. So compression defines the setting and the
breakout-bar delta defines the signal.

## Verdict
1. The original idea (coil + building delta → energy → continuation) is **not
   supported**. Continuation was weak or negative; the tradable behaviour is a
   reversal after a delta-confirmed break out of a coil.
2. The effect is small and noisy: about +0.12% per trade vs the median stock,
   positive on 5 of 6 days, before costs. It is below typical intraday costs,
   and overlaps with the earlier BEX / buying-climax result.
3. FIVESTAR 28-09 broke out on its 3rd bar (+19% delta), so it falls outside
   this population (the break must come after the coil window). Its break
   did lose about 0.36% against the market afterwards, consistent with the fade.
4. Not yet tested: stops/targets, volume thresholds beyond a simple ratio,
   other timeframes. More days are needed before any of this is relied on.

---

# Part 3: what inside the coil can a user actually use? (`coil_features.py`)

Population: >= 3 of the first 4 bars inside the master, decision at 11:15
(n = 1,288; 53% later break out of the master range, 36% of those up-first by
count: 248 up, 436 down). 14 order-flow and structure features were tested
against three questions: **which edge breaks first**, **will it break at all**,
and **does the break hold**. AUC 0.50 = no information.

| Feature | Which way (AUC) | Which way, within price-location terciles | Breaks at all (AUC) | Break holds (AUC) |
|---|---|---|---|---|
| Close position in master range | **0.87** | **0.67** | 0.43 | 0.49 |
| Coil delta % | 0.64 | **0.52** | 0.45 | 0.48 |
| Delta, last 2 coil bars | 0.67 | 0.52 | 0.45 | 0.46 |
| Delta acceleration | 0.61 | 0.50 | 0.49 | 0.49 |
| Positive-delta bars (of 4) | 0.61 | 0.51 | 0.45 | 0.48 |
| CVD position vs master CVD range | 0.60 | 0.49 | 0.49 | 0.49 |
| CVD low held above master CVD low | 0.52 | 0.47 | 0.51 | 0.52 |
| Absorption bars inside coil | 0.48 | 0.50 | 0.50 | 0.50 |
| **Volume trend (2nd half / 1st half)** | 0.56 | 0.55 | **0.60** | 0.45 |
| Last coil bar volume vs coil average | 0.56 | 0.54 | **0.58** | 0.46 |
| Coil volume vs master volume (dry-up) | 0.56 | 0.48 | 0.51 | 0.47 |
| Master delta % | 0.51 | 0.48 | 0.55 | 0.46 |

## What the data says
1. **Which way: price location, not delta.** Delta looks informative on its own
   (AUC 0.61–0.67) only because delta and price move together; once price
   location is held fixed it falls to 0.50–0.52. Delta inside the coil adds
   nothing about direction.
2. **When: rising volume.** Whether the coil breaks out at all is the one thing
   order flow helps with. Volume rising late in the coil (2nd half / 1st half
   volume) lifts the break rate from **43% (falling) to 62% (rising)**
   (AUC 0.60, ~5 standard errors); the last coil bar's volume against the coil
   average shows the same (45% → 61%).
3. **Absorption bars, CVD structure and the master's delta do nothing** here.
4. **Whether the break holds:** nothing inside the coil predicts it. The only
   predictor is the breakout bar itself (Part 2: delta in the break direction
   >= 15% means the break tends to fail).

## Decision grid at 11:15 (coil = 3+ of first 4 bars inside the master)

Cell = stocks, break-out rate, share of breaks that go **up** first.

| Close position in master range | Volume falling | Volume flat | Volume rising |
|---|---|---|---|
| **Lower third** | n=138, 53% break, **5%** up | n=142, 73% break, **8%** up | n=147, 74% break, **10%** up |
| Middle third | n=219, 36% break, 35% up | n=207, 41% break, 38% up | n=158, 45% break, 38% up |
| **Upper third** | n=73, 47% break, **85%** up | n=80, 58% break, **85%** up | n=124, 69% break, **83%** up |

Volume trend cut-offs: falling <= 0.51, rising > 0.83.

How to read it: lower third plus flat/rising volume means a break is likely
(about 3 in 4) and it is almost always **down**. Upper third plus rising volume
means about 7 in 10 break and 83% of those are **up**. Middle-third coils
resolve least often (36–45%) and show no direction.

## What this does not give you
- **No return edge.** The grid says which master edge is likely to be touched
  and how likely, not that trading it pays. From Part 1, returns from 11:15 to
  14:45 are about +0.06% to +0.10% (market-adjusted) in every location bucket.
- **Breaking down is mechanical for lower-third coils**: price is already near
  the low edge.
- **After the break, only the Part 2 rule has support:** a break with delta
  >= 15% in the break direction tends to reverse (about +0.12% fade return,
  not enough to survive stops or costs; see `scanners/coil_fade`).
- Six days. Treat the grid as a description of this sample until more days
  confirm it.

## Practical checklist for a user
1. Is it a coil? (3+ of the first 4 bars inside the master.)
2. Where is price in the master range? That sets the likely side (lower third:
   down; upper third: up; middle: unclear).
3. Is volume rising in the coil? If yes, expect a decision soon; if falling,
   expect it to stay range-bound (about half stay inside).
4. Ignore coil delta for direction. Use it only as context.
5. When the break comes, check its delta: strong delta in the break direction
   (>= 15% of bar volume) is a warning of a failed break, not a confirmation.
