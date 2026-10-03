# Absorption Rally (AR)

**Heavy net market selling on a volume spike while price rises.** Large
passive buyers absorb aggressive sellers so completely that price goes up
anyway. Reference example: **DABUR, 15-09-2026**.

| DABUR 15-09 | Close | Bar return | CVD Δ | CVD % of vol | Volume |
|---|---|---|---|---|---|
| 09:15 master | 382.25 | +0.86% | +78.7K | +20% | 402K |
| **10:15 signal** | 383.00 | **+0.98%** | **−724K** | **−39%** | **1.85M (7.2× prior avg)** |
| 10:45 | 384.45 | +0.38% | −236K | −26% | 910K |
| 11:45 | 388.25 | +1.09% | −148K | −7% | 2.27M |

On a day when 94% of stocks fell (median −2.2%), DABUR closed +0.77% from
its 09:15 close.

## How it differs from OAB

| | OAB | AR |
|---|---|---|
| Price during selling | Flat (−0.3% … +0.3%) | **Rising** (≥ +0.3%) |
| Window | 3+ bars, compression | 1–2 bars, volume spike |
| Selling | ≥ 10% of volume | ≥ 25% of volume |
| Volume | No condition | ≥ 2× prior bars' average |
| Market context | None | Must be outperforming the market median |

OAB's heavy-bar rule rejects selling during a rally because ordinary-volume
cases (ASTERDM 01-10) were noise. AR only accepts that case when volume is
unusually large, which ASTERDM fails (its selling bars had about 0.6× prior
volume).

## Rules (all must pass)

| # | Rule | Default |
|---|---|---|
| 1 | Window of 1–2 consecutive bars, starting 09:45 to 13:15 | `max_bars=2`, `first_start=1`, `last_start=8` |
| 2 | Net CVD selling `−(close_cvd[end] − open_cvd[start]) / Σvol` | `≥ 25%` |
| 3 | Window price change `(close[end] − open[start]) / open[start]` | `≥ +0.3%` |
| 4 | Volume spike: avg window bar volume / avg of all earlier bars | `2.0× … 15.0×` (`min_vol_spike`, `max_vol_spike`) |
| 5 | Relative strength at window end: stock return since 09:15 close minus market median at that bar | `≥ 0%` |

The 15× cap excludes single-bar block trades, which are one large print
rather than continuous passive buying (WEWORK 01-10 11:15: 92% selling on 36×
volume).

The earliest-ending valid window per stock is kept. Every rule uses only data
up to the window end; the market median is computed across the folder at the
same bar, so it is also point-in-time.

Outcome fields (breakout above window high, window low broken, max up/down,
return to close, return vs market to close) are for validation only.

## First results (thresholds set from one example, not tuned)

| Day | Market (median, 09:15 close → EOD) | Setups | Breakouts | Avg to close | Avg vs market | Window low broken |
|---|---|---|---|---|---|---|
| 15-09-2026 | −2.45% | 1 (DABUR) | 1 | +0.57% | +2.21% | 0 |
| 01-10-2026 | −0.72% | 7 | 3 | +0.11% | +0.72% | 6 of 7 |

With the 15× block-trade cap. Before the cap, 01-10 also included WEWORK
(breakout 11:45, +0.53% to close, +1.22% vs market).

01-10 setups: SHREEJISPG, BLISSGVS, IXIGO, SRF, CIPLA, SKIPPER,
STARHEALTH. STARHEALTH was also cited as a motivating example in the original
scanner spec.

## Later days (thresholds unchanged)

| Day | Market | Setups | Breakouts | Avg to close | Avg vs market | Window low broken |
|---|---|---|---|---|---|---|
| 16-09-2026 | +1.80% | 0 | — | — | — | — |
| 17-09-2026 | −0.08% | 26 | 15 | +0.12% | +0.13% | 8 |
| 18-09-2026 | +0.42% | 8 | 6 | +0.11% | −0.26% | 3 |

All five days: 42 setups; +0.20% vs market on average, driven by a few
large winners (YATHARTH, SHREEJISPG, JSL). No clear edge yet.

## Known limitations

- **9 setups over 2 days** is far too few to judge the pattern.
- **Window lows usually break.** On 01-10, 6 of 7 dipped below the window low
  afterward (down 0.8–4.6%), so a stop at the window low would usually be hit.
- **The 15× cap is a judgement call** based on one case (WEWORK). The next
  largest spike in the results is DABUR at 7.2×.
- Both days were down days. Behaviour on up days is unknown.

## Usage

```bash
python scanners/absorption_rally/ar_scanner.py data/CVD_Scanner_* \
    -o scanners/absorption_rally/results/ar_all.csv
```
