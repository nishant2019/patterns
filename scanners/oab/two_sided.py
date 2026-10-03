"""Two-sided OAB trade backtest.

After an OAB signal (window end), trade whichever side of the window breaks
first on a 30m close:
  long  = close above window high -> stop at window low (or mid)
  short = close below window low  -> stop at window high (or mid)
Entry at the trigger bar close; exit at the stop price if a later bar's
low/high touches it, otherwise at the last bar's close (intraday only).
Results are in % of entry and in R (risk = entry-to-stop distance).

Usage:
    python two_sided.py data/CVD_Scanner_* [--stop opposite|mid] [--baseline] [-o trades.csv]
"""
import argparse
import csv
import glob
import os
import statistics

from oab_scanner import PARAMS, load, scan_stock

BASELINE = dict(PARAMS, heavy_min_ret=-9.0, heavy_max_ret=9.0, heavy_max_delta=999.0,
                min_close_in_window=0.0, max_price_chg=0.5, max_hold=1.5)


def trade(d, hit, stop_mode="opposite"):
    H, L, C, T = d["high_price"], d["low_price"], d["close_price"], d["Time"]
    times = [t[11:16] for t in T]
    e = times.index(hit["end"])
    wh, wl = hit["window_high"], hit["window_low"]
    mid = (wh + wl) / 2
    for k in range(e + 1, len(C)):
        side = "long" if C[k] > wh else "short" if C[k] < wl else None
        if not side:
            continue
        entry = C[k]
        if side == "long":
            stop = wl if stop_mode == "opposite" else mid
            risk = entry - stop
            hit_k = next((j for j in range(k + 1, len(C)) if L[j] <= stop), None)
            exitp = stop if hit_k is not None else C[-1]
            pnl = exitp - entry
        else:
            stop = wh if stop_mode == "opposite" else mid
            risk = stop - entry
            hit_k = next((j for j in range(k + 1, len(C)) if H[j] >= stop), None)
            exitp = stop if hit_k is not None else C[-1]
            pnl = entry - exitp
        return dict(side=side, trigger=times[k], entry=entry, stop=round(stop, 2),
                    exit=round(exitp, 2), stopped=hit_k is not None,
                    pnl_pct=round(pnl / entry * 100, 2),
                    r=round(pnl / risk, 2) if risk > 0 else 0.0,
                    risk_pct=round(risk / entry * 100, 2))
    return dict(side="none", trigger="", entry="", stop="", exit="", stopped="",
                pnl_pct=0.0, r=0.0, risk_pct="")


def report(label, trades):
    t = [x for x in trades if x["side"] != "none"]
    print(f"\n{label}: signals={len(trades)} trades={len(t)} no_trigger={len(trades) - len(t)}")
    for side in ("long", "short", None):
        s = [x for x in t if side is None or x["side"] == side]
        if not s:
            continue
        wins = sum(x["pnl_pct"] > 0 for x in s)
        print(f"  {side or 'all':5s} n={len(s):3d} win={wins:3d} ({100 * wins / len(s):3.0f}%) "
              f"avg={statistics.mean(x['pnl_pct'] for x in s):+.2f}% total={sum(x['pnl_pct'] for x in s):+.2f}% "
              f"avgR={statistics.mean(x['r'] for x in s):+.2f} stopped={sum(x['stopped'] for x in s)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--stop", choices=["opposite", "mid"], default="opposite")
    ap.add_argument("--baseline", action="store_true", help="use the loose baseline setup instead of OAB")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    params = BASELINE if a.baseline else PARAMS
    allt = []
    for folder in a.folders:
        day = []
        for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
            try:
                d = load(path)
            except ValueError:
                continue
            hit = scan_stock(d, params)
            if hit:
                sym, _, date = os.path.basename(path)[:-4].rpartition("_")
                day.append(dict(symbol=sym, date=date, window=f"{hit['start']}-{hit['end']}",
                                window_high=hit["window_high"], window_low=hit["window_low"],
                                **trade(d, hit, a.stop)))
        report(os.path.basename(folder.rstrip("/")), day)
        allt += day
    report(f"ALL ({'baseline' if a.baseline else 'OAB'}, stop={a.stop})", allt)
    if not a.baseline:
        print()
        for x in allt:
            print(f"  {x['date']} {x['symbol']:11s} {x['window']} {x['side']:5s} {x['trigger'] or '-':5s} "
                  f"pnl={x['pnl_pct']:+.2f}% R={x['r']:+.2f} {'STOP' if x['stopped'] is True else ''}")
    if a.output and allt:
        with open(a.output, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(allt[0]))
            w.writeheader()
            w.writerows(allt)


if __name__ == "__main__":
    main()
