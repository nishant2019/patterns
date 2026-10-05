# Breakout entries on the afternoon watchlist
`python scanners/afternoon_volatility/breakout_entries.py` (output: `breakout_output.txt`). 18 usable days (9 discovery / 9 test). Entry at the open of the bar after the signal bar, exit at the day's last close, 0.06% round-trip cost, market-neutral excess shown separately. Events fixed in advance: E1 day-high/low break by the 14:15 bar, E2 break of the midday range, E3 either with 14:15-bar volume >= 1.5x midday average, E4 late break (14:45 bar close beyond the day range, enter 15:15). Variants: hold to close, stop at the signal bar's opposite extreme, and the FADE (mirror) trade.

## Results
| Event (hold) | Universe | n | Net per trade | Hit% | Test net (t) |
|---|---|---|---|---|---|
| E1 day-high/low break | HOT+WARM | 162 | -0.113% | 45.7 | -0.249% (-2.1) |
| E2 midday-range break | HOT+WARM | 254 | -0.158% | 44.1 | -0.305% (-2.3) |
| E3 break + volume | HOT+WARM | 131 | -0.075% | 45.8 | -0.211% (-2.0) |
| E4 late break (15:15 entry) | HOT+WARM | 181 | -0.128% | 43.6 | -0.100% (-2.2) |
| E1/E2 breakouts, no watchlist | REST | 466 / 896 | -0.012% / -0.044% | 52.8 / 49.6 | ~0 |

- **Buying the breakout loses**, and it loses more on the volatility watchlist than elsewhere (HOT+WARM -0.11 to -0.16% per trade vs -0.01 to -0.04% in REST). Gross of cost the watchlist breakouts are about -0.05 to -0.10%: the stocks that are moving most tend to give some of it back after the break. Stops do not help (slightly worse; hit rate falls to 38-40%).
- **The fade is flat to slightly positive gross, but only in the test half and not net:** E1/E2 fades on HOT+WARM net -0.007% / +0.038% per trade (t +0.1 / +0.5); discovery -0.09% / -0.08%, test +0.13% / +0.19%, so the sign flips between halves. Gross (before cost) the fade is about +0.10-0.12% on the watchlist, +0.09% for E4 fades across all stocks.
- **Late breakouts (E4) reverse most reliably:** continuing a 14:45 breakout loses -0.15% net across all stocks (t -7.2, 1 of 18 days positive, both halves negative); fading it earns +0.03% net / +0.09% gross (hit 55%), but it is not significant (t +1.0) and is a 15-minute trade.
- **Gate (net of cost > 0 in both halves and test t >= 2): nothing passes** (44 combinations, about 1 chance pass expected).

## Conclusion
On this data, breakout continuation is not an edge in the afternoon, including on the high-movement watchlist; if anything breakouts mean-revert into the close, most clearly in the last bar. Mean reversion after a late break is the only consistent direction (gross about +0.09%), too small for a 0.06% round trip plus slippage. Event counts are small (80-250 trades per cell for the watchlist), so treat the fade results as a hypothesis to retest on more days, not a signal.
Caveats: 18 days, one regime; entry at the next bar open uses the bar's full range as the stop (coarse for 30-minute bars); no slippage beyond the 0.06% cost.
