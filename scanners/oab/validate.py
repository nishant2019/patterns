"""Validate OAB across one or more trading days.

Reports breakout rate and returns per day and overall, a parameter
sensitivity sweep, and an out-of-sample check where parameters are chosen on
one half of the stock-days and measured on the other half.

Usage:
    python validate.py data/CVD_Scanner_01-10-2026 [data/CVD_Scanner_<date> ...]
"""
import argparse
import glob
import itertools
import os
import random
import statistics

from oab_scanner import PARAMS, load, scan_stock

GRID = dict(
    heavy_min_ret=[-9.0, -0.35, -0.25, -0.15],
    heavy_max_delta=[999.0, 60.0, 45.0],
    min_close_in_window=[0.0, 0.3, 0.45],
    min_cvd_selling=[10.0, 15.0],
    require_compression=[True, False],
    max_price_chg=[0.5, 0.3],
    max_hold=[1.5, 0.8],
)


def load_all(folders):
    data = {}
    for folder in folders:
        for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
            try:
                data[os.path.basename(path)[:-4]] = load(path)
            except ValueError:
                pass
    return data


def summarize(hits):
    n = len(hits)
    bo = [h for h in hits if h["breakout"]]
    return dict(
        setups=n, breakouts=len(bo),
        rate=100 * len(bo) / n if n else 0.0,
        to_close=statistics.mean(h["to_close_pct"] for h in hits) if n else 0.0,
        bo_to_close=statistics.mean(h["breakout_to_close_pct"] for h in bo) if bo else 0.0,
    )


def fmt(s):
    return (f"setups={s['setups']:3d} breakouts={s['breakouts']:3d} ({s['rate']:4.0f}%) "
            f"window->close={s['to_close']:+.2f}% breakout->close={s['bo_to_close']:+.2f}%")


def run(data, params):
    out = {}
    for key, d in data.items():
        h = scan_stock(d, params)
        if h:
            out[key] = h
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--splits", type=int, default=20)
    ap.add_argument("--no-sweep", action="store_true")
    a = ap.parse_args()
    data = load_all(a.folders)
    dates = sorted({k.rpartition("_")[2] for k in data})
    print(f"stock-days={len(data)} dates={dates}\n")

    hits = run(data, PARAMS)
    print("Current PARAMS")
    print("  ALL   ", fmt(summarize(list(hits.values()))))
    for dt in dates:
        print(f"  {dt}", fmt(summarize([h for k, h in hits.items() if k.endswith(dt)])))
    loose = run(data, dict(PARAMS, heavy_min_ret=-9.0, heavy_max_ret=9.0, heavy_max_delta=999.0,
                           min_close_in_window=0.0, max_price_chg=0.5, max_hold=1.5))
    print("  baseline (no bar-level / location filters):", fmt(summarize(list(loose.values()))))
    if a.no_sweep:
        return

    keys = list(GRID)
    results = []
    for vals in itertools.product(*GRID.values()):
        p = dict(PARAMS, **dict(zip(keys, vals)))
        results.append((p, run(data, p)))

    def score(h):  # breakout rate shrunk toward ~20% so tiny samples don't win
        return (sum(1 for x in h.values() if x["breakout"]) + 1) / (len(h) + 5)

    print("\nTop 10 parameter sets (all data)")
    for p, h in sorted(results, key=lambda t: -score(t[1]))[:10]:
        print(" ", {k: p[k] for k in keys}, fmt(summarize(list(h.values()))))

    rng = random.Random(7)
    names = list(data)
    oos, base = [], []
    for _ in range(a.splits):
        train = set(rng.sample(names, len(names) // 2))
        best_p, best_h = max(results, key=lambda t: score({k: v for k, v in t[1].items() if k in train}))
        test = [v for k, v in best_h.items() if k not in train]
        oos.append(summarize(test)["rate"])
        base.append(summarize([v for k, v in loose.items() if k not in train])["rate"])
    print(f"\nOut-of-sample ({a.splits} random half splits): chosen-params breakout rate "
          f"{statistics.mean(oos):.1f}% vs baseline {statistics.mean(base):.1f}%")


if __name__ == "__main__":
    main()
