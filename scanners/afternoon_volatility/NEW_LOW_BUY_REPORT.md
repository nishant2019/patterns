# Buying new day lows made in the 14:45 bar
> **Not a 30-minute trade:** this test enters at the 15:15 bar, which is only 15 minutes long. Parked; see NEW_EXTREME_30M_REPORT.md.
`python scanners/afternoon_volatility/new_low_buy.py` (output: `new_low_buy_output.txt`). 23 days (1 Sep - 5 Oct), 7,674 stock-days, 662 events.
Signal: the 14:45 bar closes below the lowest low of every earlier bar that day. Trade: buy the 15:15 open, sell the 15:15 close (a 15-minute bar), 0.06% round trip. This hypothesis came out of a post-hoc cut in the previous test, so the same 23 days cannot confirm it on their own; stability checks below are the best this data allows.

## Result
| Cut | n | Gross | Net (0.06%) | Day-equal t | Days positive |
|---|---|---|---|---|---|
| All 23 days | 662 | +0.114% | **+0.054%** | +2.1 | 13/22 |
| Cost 0.03% / 0.10% | 662 | +0.114% | +0.084% / +0.014% | +3.1 / +0.8 | 15/22, 11/22 |
| First 11 days | 363 | +0.160% | +0.100% | +2.8 | 8/11 |
| Last 12 days | 299 | +0.059% | **-0.001%** | +0.3 | 5/11 |
| Market-neutral excess | 662 | +0.091% | - | +3.5 | 16/22 |

- **It is not a fluke of one day:** dropping any single day leaves net +0.038% to +0.070% (day-equal t +1.8 to +2.4), even though 09-15 has 151 of the 662 events.
- **A within-day permutation test supports it:** random same-day stocks (same count per day) earn +0.023% gross on average (sd 0.017); the new-low group earns +0.114%, p < 0.001.
- **Placebos do not work:** any red 14:45 bar +0.047% gross (net -0.013%); stocks near the day low without a new low +0.037% (net -0.023%); wick-only new low +0.024% (net -0.036%); all stocks +0.021% (net -0.039%). The new *close* below all earlier lows is what matters.
- **Larger breaks and busier bars are better:** break size above 0.42% nets +0.147% (t +2.9, 12/18 days); smaller breaks +0.07%; 14:45 volume above 2x the earlier average +0.077% (t 2.3). Liquidity and price: positive in most buckets, weakest in the highest-turnover tercile (net +0.028%, day-equal -0.006%).
- **It decays and depends on the close:** the first 11 days net +0.100% (t +2.8); the last 12 days net -0.001% (t +0.3). It earns nothing (+0.004% gross, 2/7 days) on the 7 days when the market's last bar was down (not knowable in advance), versus +0.155% gross on the 15 days it was up.

## Verdict
**Promising, not validated.** There is a real, specific reversal into the close after a new-low 14:45 bar (+0.11% gross, robust to leave-one-day-out and a permutation test, absent in the placebos), but after a realistic 0.06% round trip it is thin (+0.054% net, t 2.1), it is concentrated in the first half of the sample (+0.10% vs ~0.00%), and it needs the market's close to cooperate. Execution in the last 15 minutes (spread, impact and a stock that is breaking down) would eat the rest at 0.10% costs (net +0.014%).
Do not trade it yet. It becomes worth building if it holds on a fresh month of data with the rule unchanged: the pass gate I'd use is net > 0 after 0.06% on a new 20+ day sample, t >= 2, positive in both halves.
Caveats: one regime, post-hoc origin, a 15-minute holding window that bars cannot resolve (a tick-level or 5-minute test would show the true entry/exit and spread).
