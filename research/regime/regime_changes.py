"""Regime changes between two decision times (default 11:15 -> 12:45).

For a date: transition matrix, the stocks that changed regime, and (on past days) what they did afterwards.
With --all-days the transition statistics are pooled over every day in data/ (return from the second
decision time to 14:45 vs the median stock, from regime_study.collect).
Usage:
    python regime_changes.py 28-09-2026 [--from 11:15] [--to 12:45] [--outcomes]
    python regime_changes.py --all-days [--from 11:15] [--to 12:45]
"""
import argparse, glob, os, sys, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab")); sys.path.insert(0, HERE)
from oab_scanner import load
from regime_scanner import analyse, NAMES, TIMES, classify
from regime_study import collect

ORDER = ["A", "B", "C", "C2", "D", "D2", "E"]

def day_rows(date, t1, t2):
    folder = os.path.join(HERE, "..", "..", "data", f"CVD_Scanner_{date}")
    out = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        try: d = load(path)
        except ValueError: continue
        r1, r2 = analyse(d, t1), analyse(d, t2)
        if not r1 or not r2: continue
        C = d["close_price"]; n = len(C)
        sym = os.path.basename(path).rsplit("_", 1)[0]
        out[sym] = dict(a=r1, b=r2, to_close=(C[11] - C[t2]) / C[t2] * 100 if n > 11 else None)
    return out

def tt(x): return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else 0

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("date", nargs="?"); ap.add_argument("--from", dest="t1", default="11:15"); ap.add_argument("--to", dest="t2", default="12:45")
    ap.add_argument("--all-days", action="store_true"); ap.add_argument("--outcomes", action="store_true"); ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args(); t1, t2 = TIMES[a.t1], TIMES[a.t2]
    if a.all_days:
        R1 = {(r["date"], r["sym"]): r for r in collect(t1)}; R2 = {(r["date"], r["sym"]): r for r in collect(t2)}
        base = st.mean(r["fwd_rel"] for r in R2.values())
        print(f"Pooled over all days: regime at {a.t1} -> regime at {a.t2}; return {a.t2} -> 14:45 vs median stock (baseline {base:+.3f}%)")
        print(f"{'transition':14s} {'n':>5s} {'return':>8s} {'t':>5s} {'days+':>6s}")
        keys = {}
        for k, r2 in R2.items():
            if k in R1: keys.setdefault((classify(R1[k]["struct"], R1[k]["flow"]), classify(r2["struct"], r2["flow"])), []).append(r2)
        for (x, y), g in sorted(keys.items(), key=lambda kv: -len(kv[1])):
            if len(g) < 40: continue
            dd = {}; [dd.setdefault(r["date"], []).append(r["fwd_rel"]) for r in g]
            print(f"{x+' -> '+y:14s} {len(g):5d} {st.mean(r['fwd_rel'] for r in g):+7.3f}% {tt([r['fwd_rel'] for r in g]):+5.1f} {sum(st.mean(v)>0 for v in dd.values()):>3d}/{len(dd)}")
        ent = [r for k, r in R2.items() if k in R1 and classify(r["struct"], r["flow"]) == "A" and classify(R1[k]["struct"], R1[k]["flow"]) != "A"]
        stay = [r for k, r in R2.items() if k in R1 and classify(r["struct"], r["flow"]) == "A" and classify(R1[k]["struct"], R1[k]["flow"]) == "A"]
        for lab, g in (("entered A (was not A earlier)", ent), ("stayed in A", stay)):
            if g: print(f"  {lab:32s} n={len(g):4d} {st.mean(r['fwd_rel'] for r in g):+.3f}%")
        return
    rows = day_rows(a.date, t1, t2)
    n = len(rows)
    print(f"{a.date}: regimes at {a.t1} -> {a.t2}  ({n} stocks)")
    mat = {x: {y: 0 for y in ORDER} for x in ORDER}
    for r in rows.values(): mat[r["a"]["regime"]][r["b"]["regime"]] += 1
    print("from \\ to " + "".join(f"{y:>5s}" for y in ORDER) + "   total")
    for x in ORDER: print(f"{x:9s} " + "".join(f"{mat[x][y]:5d}" for y in ORDER) + f"  {sum(mat[x].values()):6d}")
    moved = [(s, r) for s, r in rows.items() if r["a"]["regime"] != r["b"]["regime"]]
    print(f"\n{len(moved)} stocks changed regime ({100*len(moved)/n:.0f}%); stayed {n-len(moved)}")
    def show(title, cond):
        g = [(s, r) for s, r in moved if cond(r)]
        print(f"\n{title}: {len(g)}")
        for s, r in sorted(g, key=lambda x: x[1]["b"]["D"])[:a.top]:
            b = r["b"]
            print(f"  {s:12s} {r['a']['regime']:>2s} -> {b['regime']:<2s} {b['struct']:20s} close {b['close']:g} (master {b['master_low']:g}-{b['master_high']:g}) delta {b['D']:+.0f}% price {b['price_chg']:+.2f}%" + (f"  -> to close {r['to_close']:+.2f}%" if a.outcomes and r["to_close"] is not None else ""))
    show("Entered A (absorbed selling inside the range)", lambda r: r["b"]["regime"] == "A")
    show("Left A", lambda r: r["a"]["regime"] == "A")
    show("New breakouts (to C or C2)", lambda r: r["b"]["regime"] in ("C", "C2") and r["a"]["regime"] not in ("C", "C2"))
    show("New breakdowns (to D)", lambda r: r["b"]["regime"] == "D" and r["a"]["regime"] != "D")
    show("Reclaimed the master range (from D/D2 to inside)", lambda r: r["a"]["regime"] in ("D", "D2") and r["b"]["regime"] in ("A", "B", "E"))
if __name__ == "__main__":
    main()
