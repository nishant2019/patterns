"""Opening Absorption Breakout (OAB) scanner.

Finds stocks where aggressive selling (negative CVD) is absorbed above the
opening master candle's low while price holds near the top of a tight window.
See OAB_SPEC.md for the full logic.

Usage:
    python oab_scanner.py data/CVD_Scanner_01-10-2026 [-o results.csv]
"""
import argparse
import csv
import glob
import os
import sys

COLUMNS = ["Time", "open_price", "high_price", "low_price", "close_price",
           "open_cvd", "high_cvd", "low_cvd", "close_cvd", "volume"]

# Parameters chosen on the 01-10-2026 universe (see OAB_SPEC.md).
PARAMS = dict(
    master_candidates=(0, 1),  # master = 09:15 or 09:45 candle
    max_gap=1,                 # window starts at most 1 bar after the master
    min_bars=3,                # minimum window length
    max_post_master=-0.5,      # close vs master close must be >= this (%)
    min_price_chg=-0.3,        # window price change lower bound (%)
    max_price_chg=0.3,         # window price change upper bound (%)
    min_cvd_selling=10.0,      # net CVD selling as % of window volume
    max_hold=0.8,              # window low within this % above master low
    require_compression=True,  # last bar HL% < first bar HL%
    heavy_min_ret=-0.25,       # heaviest-selling bar return lower bound (%)
    heavy_max_ret=0.2,         # heaviest-selling bar return upper bound (%)
    heavy_max_delta=45.0,      # heaviest-selling bar CVD as % of its volume
    min_close_in_window=0.45,  # last close position in window range (0..1)
)


def load(path):
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or any(c not in rows[0] for c in COLUMNS):
        raise ValueError("missing columns")
    d = {k: [float(r[k]) for r in rows] for k in COLUMNS[1:]}
    d["Time"] = [r["Time"] for r in rows]
    if d["Time"] != sorted(d["Time"]):
        raise ValueError("timestamps not sorted")
    if min(d["volume"]) < 0:
        raise ValueError("negative volume")
    if len(rows) < 5:
        raise ValueError("too few candles")
    return d


def scan_stock(d, p=PARAMS):
    """Return the first valid OAB setup (point-in-time) plus outcome fields, or None."""
    O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
    oc, cc, V, T = d["open_cvd"], d["close_cvd"], d["volume"], d["Time"]
    n = len(C)
    hl = [(H[i] - L[i]) / O[i] * 100 for i in range(n)]
    delta = [cc[i] - oc[i] for i in range(n)]
    best = None
    for m in p["master_candidates"]:
        for s in range(m + 1, min(m + 2 + p["max_gap"], n)):
            for e in range(s + p["min_bars"] - 1, n - 1):  # need >=1 bar after window
                if min(L[s:e + 1]) <= L[m]:
                    break  # master low broken; longer windows fail too
                post_master = (C[e] - C[m]) / C[m] * 100
                price_chg = (C[e] - O[s]) / O[s] * 100
                cvd_sell = -(cc[e] - oc[s]) / sum(V[s:e + 1]) * 100
                win_hi, win_lo = max(H[s:e + 1]), min(L[s:e + 1])
                hold = (win_lo - L[m]) / L[m] * 100
                if post_master < p["max_post_master"]:
                    continue
                if not p["min_price_chg"] <= price_chg <= p["max_price_chg"]:
                    continue
                if cvd_sell < p["min_cvd_selling"] or hold > p["max_hold"]:
                    continue
                if p["require_compression"] and not hl[e] < hl[s]:
                    continue
                hb = min(range(s, e + 1), key=lambda i: delta[i])
                if delta[hb] >= 0:
                    continue
                hb_ret = (C[hb] - O[hb]) / O[hb] * 100
                hb_delta = -delta[hb] / V[hb] * 100
                if not p["heavy_min_ret"] <= hb_ret <= p["heavy_max_ret"]:
                    continue
                if hb_delta > p["heavy_max_delta"]:
                    continue
                close_in_win = (C[e] - win_lo) / max(win_hi - win_lo, 1e-9)
                if close_in_win < p["min_close_in_window"]:
                    continue
                if best is None or (e, m) < (best["_e"], best["_m"]):
                    best = dict(
                        _e=e, _m=m,
                        master=T[m][11:16], master_low=L[m], master_close=C[m],
                        start=T[s][11:16], end=T[e][11:16], bars=e - s + 1,
                        post_master_pct=round(post_master, 2),
                        price_chg_pct=round(price_chg, 2),
                        cvd_selling_pct=round(cvd_sell, 2),
                        hold_pct=round(hold, 2),
                        first_hl_pct=round(hl[s], 2), last_hl_pct=round(hl[e], 2),
                        heavy_bar=T[hb][11:16], heavy_ret_pct=round(hb_ret, 2),
                        heavy_delta_pct=round(hb_delta, 1),
                        close_in_window=round(close_in_win, 2),
                        window_high=win_hi, window_low=win_lo, signal_close=C[e],
                    )
                break  # first valid end for this start
    if best is None:
        return None
    # Outcome fields (future data, for validation only)
    e = best.pop("_e")
    best.pop("_m")
    bo = next((k for k in range(e + 1, n) if C[k] > best["window_high"]), None)
    best.update(
        breakout=T[bo][11:16] if bo is not None else "",
        breakout_to_close_pct=round((C[-1] - C[bo]) / C[bo] * 100, 2) if bo is not None else "",
        window_low_hit_after_bo=(min(L[bo + 1:], default=9e9) <= best["window_low"]) if bo is not None else "",
        max_up_pct=round((max(H[e + 1:]) - C[e]) / C[e] * 100, 2),
        max_down_pct=round((min(L[e + 1:]) - C[e]) / C[e] * 100, 2),
        to_close_pct=round((C[-1] - C[e]) / C[e] * 100, 2),
    )
    return best


def scan_folder(folder, p=PARAMS):
    results, rejected = [], []
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        name = os.path.basename(path)
        symbol, _, date = name[:-4].rpartition("_")
        try:
            hit = scan_stock(load(path), p)
        except ValueError as ex:
            rejected.append((name, str(ex)))
            continue
        if hit:
            results.append(dict(symbol=symbol, date=date, **hit))
    return results, rejected


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", help="folder of <SYMBOL>_<DATE>.csv files")
    ap.add_argument("-o", "--output", help="write results CSV here")
    a = ap.parse_args()
    results, rejected = scan_folder(a.folder)
    n_files = len(glob.glob(os.path.join(a.folder, "*.csv")))
    bo = [r for r in results if r["breakout"]]
    print(f"files={n_files} rejected={len(rejected)} setups={len(results)} breakouts={len(bo)}")
    for name, why in rejected:
        print(f"  rejected {name}: {why}", file=sys.stderr)
    for r in results:
        print(f"{r['symbol']:12s} {r['start']}-{r['end']} cvd_sell={r['cvd_selling_pct']:5.1f}% "
              f"heavy={r['heavy_bar']} ({r['heavy_ret_pct']:+.2f}%, {r['heavy_delta_pct']:.0f}%) "
              f"close_in_win={r['close_in_window']:.2f} breakout={r['breakout'] or '-'} to_close={r['to_close_pct']:+.2f}%")
    if a.output and results:
        with open(a.output, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(results[0]))
            w.writeheader()
            w.writerows(results)


if __name__ == "__main__":
    main()
