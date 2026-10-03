# Climax Dry-up Breakout (CDB)

An intraday Wyckoff accumulation on 30-minute bars: **opening selling climax →
low-volume range above the climax low (sellers exhausted) → secondary test that
holds → breakout above the range high on volume.**

Reference example: **APOLLOTYRE, 01-10-2026.**

Unlike OAB, the range does **not** need net selling. Cumulative CVD stays
negative because of the climax bar, but inside the range buyers are net
positive. The sellers stop; they are not absorbed.

## APOLLOTYRE 01-10-2026

| Bar | Close | CVD Δ | Intrabar CVD low vs open | Vol vs climax | Wyckoff phase |
|---|---|---|---|---|---|
| 09:15 | 395.60 (−1.59%) | −16.1K | −24.6K | 1.00 | Selling climax; closes 29% off its low |
| 09:45 | 397.15 | +8.8K | −0.4K | 0.25 | Automatic rally (range high 397.75) |
| 10:15 | 396.35 | −0.7K | −2.7K | 0.11 | Dry-up |
| 10:45 | 395.30 | −6.9K | −8.5K | 0.20 | Secondary test: CVD retests −16.6K, price low 394.25 > 392.85 |
| 11:15 | 395.70 | +3.0K | ~0 | 0.10 | No selling left |
| 11:45 | 395.95 | +6.3K | ~0 | 0.14 | No selling left |
| 12:15 | 399.50 (+0.90%) | +24.7K | −1.2K | 1.19 | Breakout above 397.75 (sign of strength) |
| 12:45–13:15 | 400.45 / 399.80 | −56.9K | | 0.84 / 0.65 | Back-up: heavy selling holds above 397.75 |
| 15:15 | 404.00 | | | | Close; high 406.75 |

Entry at the 12:15 close (399.50): max up +1.81%, max down −0.15%, close
+1.13%, +0.87% vs market. The range high was never lost.

## Rules

Signal is the close of the breakout bar. Everything uses only data up to
that bar.

| # | Rule | Default |
|---|---|---|
| 1 | Climax: first bar closes below its open with negative CVD | — |
| 2 | Climax CVD / volume | `≤ −5%` (`master_max_delta_pct`) |
| 3 | Climax close location in its range (buyers already present) | `≥ 0.2` (`master_min_close_loc`) |
| 4 | No later low at or below the climax low, up to the breakout | — |
| 5 | Range = bars from 09:45 until the first close above all earlier range highs; length | `≥ 3` (`min_range_bars`) |
| 6 | Range average volume / climax volume (dry-up) | `≤ 0.35` (`max_range_vol`) |
| 7 | Range width / climax width | `≤ 0.6` (`max_range_width`) |
| 8 | Secondary test: a range bar's intrabar CVD low comes within 10% of \|climax Δ\| of the earlier range CVD low | `test_cvd_tol=0.10` |
| 9 | Fade: last 2 range bars' intrabar sell push ≤ 10% of \|climax Δ\| | `fade_bars=2`, `fade_max_push=0.10` |
| 10 | Breakout bar volume / range average volume, with positive CVD | `≥ 2.0` (`bo_min_vol`) |
| 11 | Breakout no later than 13:15 | `last_breakout_bar=8` |

Intrabar CVD uses the `low_cvd` and `open_cvd` columns.

## Results

| Day | Market | Setups | Result |
|---|---|---|---|
| 01-10-2026 | −0.72% | 1 (APOLLOTYRE) | +1.13% to close, +0.87% vs market |
| 15-09-2026 | −2.45% | 0 | — |

Where the other ~1,000 stock-days dropped out:

| First failing rule | 01-10 | 15-09 |
|---|---|---|
| First bar not a down bar with negative CVD | 272 | 244 |
| Climax CVD weaker than −5% | 28 | 35 |
| Climax closed on its low | 93 | 145 |
| Climax low broken | 92 | 76 |
| Breakout with fewer than 3 range bars | 13 | 1 |
| Range volume not dried up | 4 | 0 |
| No secondary test | 0 | 1 |
| Sellers not faded | 1 | 0 |
| No breakout by 13:15 | 2 | 5 |
| **Pass** | **1** | **0** |

Loosening range volume to 0.5×, dropping the fade and test rules and
lowering breakout volume to 1.5× adds only HEROMOTOCO 01-10, which had net
selling in its range and closed −0.62% after its breakout.

## Known limitations

- **One example.** The rules were written from APOLLOTYRE, so they are certain
  to find it. Whether CDB generalises is unknown until it finds setups on new
  days.
- **Rare by design.** About 0.1% of stock-days pass. Expect 0–2 signals a day.
- **Fixed range start.** The range always starts at 09:45 and the climax is
  always the 09:15 bar.

## Usage

```bash
python scanners/cdb/cdb_scanner.py data/CVD_Scanner_* -o scanners/cdb/results/cdb_all.csv
```
