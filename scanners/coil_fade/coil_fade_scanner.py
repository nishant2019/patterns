"""Coil-breakout fade scanner and backtest.

Setup (all point-in-time, signal at the close of the breakout bar):
  1. Master candle = first 30-minute bar.
  2. Coil: at least `min_inside` of the next `coil_bars` bars lie fully inside the master
     (high <= master high and low >= master low).
  3. Breakout: first later bar that closes outside the master range, with bar delta
     (CVD change as % of bar volume) in the break direction >= `min_delta`.
  4. Fade: up-break -> SHORT at that close; down-break -> LONG.
Research basis: research/compression/REPORT.md (delta-confirmed breaks out of a coil tend to fail).

Stops (risk above/below the entry):  bar   = breakout bar extreme
                                     bar+  = breakout bar extreme + 0.25 x master range
                                     edge  = master range edge on the far side + 0.25 x master range
Targets:                             edge  = back to the master edge that was broken (failed breakout)
                                     mid   = master midpoint
                                     close = hold to the last bar
                                     mr<x>  = x * master range from entry (e.g. mr1.5); none = no stop
Exit order within one bar is assumed worst-case: stop before target.

Usage:
    python coil_fade_scanner.py scan data/CVD_Scanner_<date> [...]          # list signals
    python coil_fade_scanner.py backtest data/CVD_Scanner_* [--cost 0.10]   # stop/target grid
"""
import argparse
import csv
import glob
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "oab"))
from oab_scanner import load  # noqa: E402

PARAMS = dict(coil_bars=4, min_inside=3, min_delta=15.0)


def scan_stock(d, p=PARAMS):
    O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
    oc, cc, V, T = d["open_cvd"], d["close_cvd"], d["volume"], d["Time"]
    n = len(C)
    mH, mL = H[0], L[0]
    mr = mH - mL
    t = p["coil_bars"]
    if mr <= 0 or n < t + 3:
        return None
    inside = sum(H[i] <= mH and L[i] >= mL for i in range(1, t + 1))
    if inside < p["min_inside"]:
        return None
    for k in range(t + 1, n):
        if mL <= C[k] <= mH:
            continue
        sgn = 1 if C[k] > mH else -1
        delta = (cc[k] - oc[k]) / V[k] * 100 * sgn
        if delta < p["min_delta"]:
            return None                       # first break was not delta-confirmed: no signal
        return dict(side="short" if sgn > 0 else "long", time=T[k][11:16], k=k, entry=C[k],
                    broke="up" if sgn > 0 else "down", inside=inside, delta_pct=round(delta, 1),
                    bar_hi=H[k], bar_lo=L[k], master_hi=mH, master_lo=mL,
                    master_range_pct=round(mr / O[0] * 100, 2))
    return None


def trade(d, sig, stop_mode, target_mode):
    """Simulate the fade from the signal bar close. Returns dict or None if no later bar."""
    H, L, C = d["high_price"], d["low_price"], d["close_price"]
    k, n, entry = sig["k"], len(C), sig["entry"]
    if k >= n - 1:
        return None
    mr = sig["master_hi"] - sig["master_lo"]
    short = sig["side"] == "short"
    if stop_mode == "none":
        stop = entry + 99 * mr if short else entry - 99 * mr
    elif stop_mode.startswith("mr"):   # fixed distance = multiple of the master range from entry
        m = float(stop_mode[2:])
        stop = entry + m * mr if short else entry - m * mr
    elif stop_mode == "bar":
        stop = sig["bar_hi"] if short else sig["bar_lo"]
    elif stop_mode == "bar+":
        stop = sig["bar_hi"] + 0.25 * mr if short else sig["bar_lo"] - 0.25 * mr
    else:  # edge
        stop = sig["master_hi"] + 0.25 * mr if short else sig["master_lo"] - 0.25 * mr
        stop = max(stop, sig["bar_hi"]) if short else min(stop, sig["bar_lo"])
    edge = sig["master_hi"] if short else sig["master_lo"]
    mid = (sig["master_hi"] + sig["master_lo"]) / 2
    target = {"edge": edge, "mid": mid, "close": None}[target_mode]
    risk = abs(stop - entry)
    if risk <= 0:
        return None
    exit_p, why = C[-1], "close"
    for j in range(k + 1, n):
        if (short and H[j] >= stop) or (not short and L[j] <= stop):
            exit_p, why = stop, "stop"
            break
        if target is not None and ((short and L[j] <= target) or (not short and H[j] >= target)):
            exit_p, why = target, "target"
            break
    pnl = (entry - exit_p) if short else (exit_p - entry)
    return dict(pnl_pct=pnl / entry * 100, r=pnl / risk, why=why, risk_pct=risk / entry * 100)


def load_days(folders):
    out = []
    for folder in folders:
        date = folder.rstrip("/").rsplit("_", 1)[1]
        for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
            try:
                d = load(path)
            except ValueError:
                continue
            out.append((date, os.path.basename(path).rsplit("_", 1)[0], d))
    return out


def cmd_scan(a):
    rows = []
    for date, sym, d in load_days(a.folders):
        s = scan_stock(d)
        if s:
            rows.append(dict(date=date, symbol=sym, **{k: v for k, v in s.items() if k != "k"}))
    print(f"signals: {len(rows)}")
    for r in rows:
        print(f"  {r['date']} {r['time']} {r['symbol']:12s} {r['side']:5s} @ {r['entry']} (broke {r['broke']}, delta {r['delta_pct']:+.0f}%, "
              f"{r['inside']}/4 inside, master range {r['master_range_pct']}%)")
    if a.output and rows:
        with open(a.output, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


def cmd_backtest(a):
    days = load_days(a.folders)
    sigs = [(date, sym, d, s) for date, sym, d in days if (s := scan_stock(d))]
    print(f"{len(days)} stock-days, {len(sigs)} signals ({sum(s['side']=='short' for *_, s in sigs)} short, {sum(s['side']=='long' for *_, s in sigs)} long), cost {a.cost}% round trip\n")
    print(f"{'stop':5s} {'target':6s} {'n':>4s} {'win%':>5s} {'avg%':>7s} {'net%':>7s} {'avgR':>6s} {'stopped':>8s} {'target':>7s} {'close':>6s}  per-day net% (days+)")
    best = None
    for sm, tms in (("bar", ("edge", "mid", "close")), ("bar+", ("edge", "mid", "close")), ("edge", ("edge", "mid", "close")),
                    ("mr0.5", ("close",)), ("mr1.0", ("close",)), ("mr1.5", ("close",)), ("mr2.0", ("close",)), ("none", ("close",))):
        for tm in tms:
            tr = [(date, trade(d, s, sm, tm)) for date, sym, d, s in sigs]
            tr = [(dt, x) for dt, x in tr if x]
            net = [x["pnl_pct"] - a.cost for _, x in tr]
            days_ = {}
            [days_.setdefault(dt, []).append(x["pnl_pct"] - a.cost) for dt, x in tr]
            dpos = sum(st.mean(v) > 0 for v in days_.values())
            print(f"{sm:5s} {tm:6s} {len(tr):4d} {100*sum(v>0 for v in net)/len(net):5.0f} {st.mean(x['pnl_pct'] for _, x in tr):+7.3f} {st.mean(net):+7.3f} {st.mean(x['r'] for _, x in tr):+6.2f} "
                  f"{sum(x['why']=='stop' for _, x in tr):8d} {sum(x['why']=='target' for _, x in tr):7d} {sum(x['why']=='close' for _, x in tr):6d}  "
                  + " ".join(f"{st.mean(v):+.2f}" for _, v in sorted(days_.items(), key=lambda kv: (kv[0][3:5], kv[0][:2]))) + f" ({dpos}/{len(days_)})")
    if a.output:
        rows = []
        for date, sym, d, s in sigs:
            for sm, tm in (("bar", "edge"), ("bar+", "edge"), ("bar+", "close")):
                x = trade(d, s, sm, tm)
                if x:
                    rows.append(dict(date=date, symbol=sym, side=s["side"], time=s["time"], entry=s["entry"], stop_mode=sm, target_mode=tm, **{k: round(v, 3) if isinstance(v, float) else v for k, v in x.items()}))
        with open(a.output, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan"); s.add_argument("folders", nargs="+"); s.add_argument("-o", "--output"); s.set_defaults(fn=cmd_scan)
    b = sub.add_parser("backtest"); b.add_argument("folders", nargs="+"); b.add_argument("--cost", type=float, default=0.0); b.add_argument("-o", "--output"); b.set_defaults(fn=cmd_backtest)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
