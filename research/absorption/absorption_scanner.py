"""Absorption event scanner (bar-level, point-in-time).

SAB  Selling Absorption  (bullish): bar CVD delta <= -30% of its volume, bar
     return between -0.5% and +0.15%, volume 1.5-3x the average of earlier
     bars, close in the lower half of the day's range so far.
BEX  Buying Exhaustion   (bearish): bar CVD delta >= +50% of its volume, bar
     return > +0.5%, volume >= 1.5x the average of earlier bars.

Every condition uses only the bar itself and earlier bars. See REPORT.md.

Usage:
    python absorption_scanner.py data/CVD_Scanner_<date> [...] [-o events.csv]
"""
import argparse
import csv
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scanners", "oab"))
from oab_scanner import load  # noqa: E402

SAB = dict(max_delta=-30.0, min_ret=-0.5, max_ret=0.15, min_spike=1.5, max_spike=3.0, max_day_pos=0.5)
BEX = dict(min_delta=50.0, min_ret=0.5, min_spike=1.5)


def events(d):
    O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
    oc, cc, V, T = d["open_cvd"], d["close_cvd"], d["volume"], d["Time"]
    out = []
    for i in range(1, len(C)):
        if V[i] <= 0:
            continue
        dpct = (cc[i] - oc[i]) / V[i] * 100
        ret = (C[i] - O[i]) / O[i] * 100
        spike = V[i] / (sum(V[:i]) / i)
        hi, lo = max(H[:i + 1]), min(L[:i + 1])
        pos = (C[i] - lo) / max(hi - lo, 1e-9)
        kind = None
        if (dpct <= SAB["max_delta"] and SAB["min_ret"] <= ret <= SAB["max_ret"]
                and SAB["min_spike"] <= spike < SAB["max_spike"] and pos < SAB["max_day_pos"]):
            kind = "SAB"
        elif dpct >= BEX["min_delta"] and ret > BEX["min_ret"] and spike >= BEX["min_spike"]:
            kind = "BEX"
        if kind:
            fwd = lambda h: round((C[min(i + h, len(C) - 1)] - C[i]) / C[i] * 100, 2)
            out.append(dict(kind=kind, time=T[i][11:16], close=C[i], delta_pct=round(dpct, 1),
                            bar_ret_pct=round(ret, 2), vol_spike=round(spike, 2), day_pos=round(pos, 2),
                            fwd_2bars_pct=fwd(2) if i < len(C) - 1 else "", fwd_close_pct=fwd(99) if i < len(C) - 1 else ""))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folders", nargs="+")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    rows = []
    for folder in a.folders:
        for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
            try:
                d = load(path)
            except ValueError:
                continue
            sym, _, date = os.path.basename(path)[:-4].rpartition("_")
            for e in events(d):
                rows.append(dict(date=date, symbol=sym, **e))
    for kind in ("SAB", "BEX"):
        k = [r for r in rows if r["kind"] == kind]
        print(f"{kind}: {len(k)} events, {len({(r['date'], r['symbol']) for r in k})} stock-days")
        for r in k:
            print(f"  {r['date']} {r['time']} {r['symbol']:12s} delta={r['delta_pct']:+6.1f}% ret={r['bar_ret_pct']:+.2f}% "
                  f"spike={r['vol_spike']:.1f}x pos={r['day_pos']:.2f} fwd2={r['fwd_2bars_pct']} close={r['fwd_close_pct']}")
    if a.output and rows:
        with open(a.output, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    main()
