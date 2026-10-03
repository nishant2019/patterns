# 29-09-2026: out-of-sample day (506 stocks, nothing re-tuned)

Market: the median stock was +0.39% from the 09:15 close at the last bar, 63% of stocks up; afternoon weakness (median −0.37% from 11:15 to 14:45).
Thirteen-bar stocks 333, twelve-bar stocks 173.

## Result per tool
| Tool | 29-09 result | Reading vs the earlier 6-day findings |
|---|---|---|
| **OAB** | 5 setups (DLF, EXIDEIND, JSL, THYROCARE, YATHARTH), 3 broke out. Long-only (stop at master low): avg −0.17%, 2 of 5 won, 2 stopped, −0.14% vs average stock | Weak: below the market, the first day OAB lagged by this much since 16-09 |
| **Selling absorption (SAB/SA)** | 21 events: next 2 bars +0.11% vs median, to close **−0.03%** (32% beat the median) | Did not hold on the day; refined SAB still +0.23% over 2 bars but −0.01% to close |
| **Buying exhaustion (BEX)** | 19 events: **+0.45%** over 2 bars, **+0.67%** to close vs median | Opposite of the research (bearish); the 7-day BEX to-close return is now −0.20% (t −1.7, 3 of 7 days) |
| **Coil-breakout fade** | 51 signals (37 short fades of up-breaks, 14 long), hold to close with no stop +0.06%; stops at 1.0 × master range +0.28% (67% win); breakout-bar stop +0.01% to +0.08% | Positive, first day stops did not hurt; shorts worked as the afternoon faded |
| **Regime A (absorbed selling)** | 32 at 11:15: −0.04% vs median; 26 at 12:45: −0.06% | Below baseline (+0.13% / +0.04%) on this day: 44% / 58% win |
| Regime C (breakout, buying confirmed) | 95 at 11:15: +0.28%; 12:45: −0.03% | Reverse of its negative history at 11:15 |
| Regime C2 | +0.31% (11:15), 0.00% (12:45) | Positive at 11:15 |
| Regime D | +0.18% (11:15), +0.11% (12:45) | Breakdowns bounced |
| Regime E | +0.55% (11:15, 78% win), +0.64% (12:45) | Best regime of the day |

## Updated 7-day tallies
- OAB: 83 setups, 55% broke out vs a 32% baseline; window-end → close +0.13% (29-09: −0.33%).
- Regime A pooled (6 decision times, 7 days): **+0.17%** vs the +0.06% baseline, positive on 6 of 7 days (29-09: −0.10%); was +0.24% over 6/6 days before.
- Regime C pooled: +0.005% (was −0.06%), 3 of 7 days positive; regime E: **+0.12%, positive on 7 of 7 days**.
- SA: +0.11% next 2 bars (t 3.5), 6 of 7 days; refined SAB +0.20% (t 4.4), 5 of 7 days.
- BEX (≥50% delta): to close −0.20% (t −1.7), 3 of 7 days: no longer significant.

## Takeaway
29-09 weakened or reversed most findings (OAB, regime A, SAB to the close, and the bearish BEX / regime C read) and supported the coil fade. The edges that looked
small and consistent over 6 days look smaller and less consistent over 7. Treat the 6-day numbers as optimistic.

Files: `scanners/oab/results/oab_29-09-2026.csv`, `scanners/coil_fade/results/signals_29-09-2026.csv`, `research/absorption/absorption_events_29-09-2026.csv`.

## SIZE-driven selling outliers (Mahalanobis, `research/absorption/outlier_scanner.py`)
`python research/absorption/outlier_scanner.py 29-09-2026` lists bars with |delta| >= 10% of volume whose delta size, price move and
volume spike are a joint outlier (d > 3.06) with the SIZE driver on the selling side: **28 bars in 24 stocks** (list in
`research/absorption/outliers_size_selling_29-09-2026.csv`). Biggest by distance: CHAMBLFERT 11:15 (−254K, −95% of volume, 7.8× spike, price flat),
CHOICEIN 12:45, RELIGARE 13:45, AWL 10:15 (−932K), FINCABLES, BLISSGVS, KRBL. Against the median stock, the 23 with later bars returned
+0.19% over 2 bars and +0.21% to the close, but only 39% won; a few large winners (KANSAINER +3.5%, BLISSGVS +1.8%, AWL +1.6%, KRBL +1.2%) drive the mean.
