"""Build a bar-level event table for absorption research.

One row per (stock, day, bar) with point-in-time features and market-relative
forward returns. The market is the median stock's forward return over the same
bars on the same day.
"""
import csv
import glob
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scanners", "oab"))
from oab_scanner import load  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")


def build():
    rows = []
    for folder in sorted(glob.glob(os.path.join(ROOT, "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]
        data = {}
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try:
                d = load(p)
            except ValueError:
                continue
            if len(d["close_price"]) >= 12 and min(d["volume"]) > 0:
                data[os.path.basename(p).rsplit("_", 1)[0]] = d
        n = min(len(d["close_price"]) for d in data.values())
        # market forward returns, per bar: median across stocks
        def fwd(d, i, h):
            j = min(i + h, n - 1)
            return (d["close_price"][j] - d["close_price"][i]) / d["close_price"][i] * 100
        mk = {h: [statistics.median(fwd(d, i, h) for d in data.values()) for i in range(n)] for h in (1, 2, 99)}
        for sym, d in data.items():
            O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
            oc, hc, lc, cc, V = d["open_cvd"], d["high_cvd"], d["low_cvd"], d["close_cvd"], d["volume"]
            dayvol = []
            for i in range(1, n - 1):
                prior_v = sum(V[:i]) / i
                rng = max(H[i] - L[i], 1e-9)
                delta = cc[i] - oc[i]
                k = 3 if i >= 3 else i
                rows.append(dict(
                    date=date, sym=sym, bar=i, time=d["Time"][i][11:16],
                    dpct=delta / V[i] * 100,                         # bar delta % of volume
                    ret=(C[i] - O[i]) / O[i] * 100,                 # bar return
                    hl=(H[i] - L[i]) / O[i] * 100,
                    vspike=V[i] / prior_v,
                    cloc=(C[i] - L[i]) / rng,                       # close location in bar
                    # intrabar CVD extremes vs open, as % of volume
                    push_up=(hc[i] - oc[i]) / V[i] * 100,
                    push_dn=(lc[i] - oc[i]) / V[i] * 100,
                    # 3-bar price and CVD change (divergence)
                    pr3=(C[i] - C[i - k]) / C[i - k] * 100,
                    cvd3=(cc[i] - cc[i - k]) / sum(V[i - k + 1:i + 1]) * 100,
                    dayret=(C[i] - C[0]) / C[0] * 100 - 0,
                    dpos=(C[i] - min(L[:i + 1])) / max(max(H[:i + 1]) - min(L[:i + 1]), 1e-9),
                    f1=fwd(d, i, 1) - mk[1][i],
                    f2=fwd(d, i, 2) - mk[2][i],
                    feod=fwd(d, i, 99) - mk[99][i],
                ))
    return rows


if __name__ == "__main__":
    rows = build()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "events.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    print(len(rows), "events ->", out)
