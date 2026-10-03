"""Climax Dry-up Breakout (CDB) scanner.

Opening selling climax -> low-volume range above the climax low (sellers
exhausted) -> secondary test that holds -> breakout above the range high on
volume. Reference example: APOLLOTYRE 01-10-2026. See CDB_SPEC.md.

Usage:
    python cdb_scanner.py data/CVD_Scanner_01-10-2026 [more folders...] [-o results.csv]
"""
import argparse
import csv
import glob
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oab"))
sys.path.insert(0, os.path.join(HERE, "..", "absorption_rally"))
from oab_scanner import load  # noqa: E402
from ar_scanner import market_curve  # noqa: E402

PARAMS = dict(
    master_max_delta_pct=-5.0,   # climax bar CVD / volume must be <= this (%)
    master_min_close_loc=0.2,    # climax close position in its range (0 = low, 1 = high)
    min_range_bars=3,            # bars between climax and breakout
    max_range_vol=0.35,          # avg range bar volume / climax volume
    max_range_width=0.6,         # range high-low / climax high-low
    test_cvd_tol=0.10,           # secondary test: intrabar CVD low within this x |climax delta| of prior range low
    fade_bars=2,                 # last N range bars must show almost no selling
    fade_max_push=0.10,          # intrabar sell push <= this x |climax delta|
    bo_min_vol=2.0,              # breakout volume / avg range bar volume
    last_breakout_bar=8,         # latest breakout bar index (8 = 13:15)
)


def scan_stock(d, mkt, p=PARAMS):
    O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
    oc, lc, cc, V, T = d["open_cvd"], d["low_cvd"], d["close_cvd"], d["volume"], d["Time"]
    n = len(C)
    m_delta = cc[0] - oc[0]
    m_rng = H[0] - L[0]
    if m_delta >= 0 or m_rng <= 0 or C[0] >= O[0]:
        return None
    if m_delta / V[0] * 100 > p["master_max_delta_pct"]:
        return None
    if (C[0] - L[0]) / m_rng < p["master_min_close_loc"]:
        return None
    size = abs(m_delta)
    # First bar that closes above the high of all earlier range bars ends the range.
    for k in range(2, min(p["last_breakout_bar"], n - 2) + 1):
        if min(L[1:k + 1]) <= L[0]:
            return None                      # climax low broken
        rh = max(H[1:k])
        if C[k] <= rh:
            continue
        rng = range(1, k)                    # range bars
        if len(rng) < p["min_range_bars"]:
            return None
        rl = min(L[1:k])
        avg_vol = sum(V[1:k]) / len(rng)
        if avg_vol / V[0] > p["max_range_vol"]:
            return None
        if (rh - rl) / m_rng > p["max_range_width"]:
            return None
        # Secondary test: a later range bar's intrabar CVD revisits the earlier range CVD low
        test = None
        for t in range(2, k):
            if lc[t] <= min(lc[1:t]) + p["test_cvd_tol"] * size:
                test = t
                break
        if test is None:
            return None
        # Fade: last bars show almost no intrabar selling
        if any(lc[i] - oc[i] < -p["fade_max_push"] * size for i in range(k - p["fade_bars"], k)):
            return None
        if V[k] / avg_vol < p["bo_min_vol"] or cc[k] - oc[k] <= 0:
            return None
        entry = C[k]
        after_l = L[k + 1:]
        to_close = (C[-1] - entry) / entry * 100
        return dict(
            climax_delta=round(m_delta), climax_delta_pct=round(m_delta / V[0] * 100, 1),
            climax_close_loc=round((C[0] - L[0]) / m_rng, 2), climax_low=L[0],
            range_start=T[1][11:16], range_end=T[k - 1][11:16], range_bars=len(rng),
            range_high=rh, range_low=rl, range_vol_vs_climax=round(avg_vol / V[0], 2),
            range_width_vs_climax=round((rh - rl) / m_rng, 2), test_bar=T[test][11:16],
            range_net_delta=round(cc[k - 1] - oc[1]),
            breakout=T[k][11:16], breakout_vol_vs_range=round(V[k] / avg_vol, 1),
            breakout_delta=round(cc[k] - oc[k]), entry=entry,
            # outcome fields (validation only)
            max_up_pct=round((max(H[k + 1:]) - entry) / entry * 100, 2),
            max_down_pct=round((min(after_l) - entry) / entry * 100, 2),
            to_close_pct=round(to_close, 2),
            vs_market_to_close_pct=round(to_close - (mkt[n - 1] - mkt[k]), 2),
            range_high_lost=min(after_l) < rh,
            range_low_lost=min(after_l) < rl,
        )
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folders", nargs="+")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    allhits = []
    for folder in a.folders:
        data = {}
        for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
            try:
                data[os.path.basename(path)[:-4]] = load(path)
            except ValueError as ex:
                print(f"rejected {os.path.basename(path)}: {ex}", file=sys.stderr)
        mkt = market_curve(data)
        hits = []
        for key, d in data.items():
            h = scan_stock(d, mkt)
            if h:
                sym, _, date = key.rpartition("_")
                hits.append(dict(symbol=sym, date=date, **h))
        allhits += hits
        avg = lambda k: statistics.mean(h[k] for h in hits) if hits else 0.0
        print(f"\n{os.path.basename(folder.rstrip('/'))}: files={len(data)} market(09:15 close->EOD)={mkt[-1]:+.2f}% "
              f"setups={len(hits)} to_close={avg('to_close_pct'):+.2f}% vs_market={avg('vs_market_to_close_pct'):+.2f}% "
              f"range_high_lost={sum(h['range_high_lost'] for h in hits)} range_low_lost={sum(h['range_low_lost'] for h in hits)}")
        for h in hits:
            print(f"  {h['symbol']:12s} climax {h['climax_delta_pct']:+5.1f}% range {h['range_start']}-{h['range_end']} "
                  f"vol={h['range_vol_vs_climax']:.2f}x net={h['range_net_delta']:+d} test={h['test_bar']} "
                  f"bo={h['breakout']} ({h['breakout_vol_vs_range']}x) up={h['max_up_pct']:+.2f} dn={h['max_down_pct']:+.2f} "
                  f"close={h['to_close_pct']:+.2f} vs_mkt={h['vs_market_to_close_pct']:+.2f} rh_lost={h['range_high_lost']}")
    if a.output and allhits:
        with open(a.output, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(allhits[0]))
            w.writeheader()
            w.writerows(allhits)


if __name__ == "__main__":
    main()
