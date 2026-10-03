"""SIZE-driven selling outliers (Mahalanobis, driver SIZE, delta < 0) across every day: what separates winners from losers?
Outcome = return from the outlier bar's close to the 14:45 close minus the median stock over the same bars. Only bars 09:45-14:15 (index 1-10)."""
import glob, os, statistics as st, sys, math, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "regime"))
from efficiency_chart import peer_tables, maha_state, window, load
from regime_scanner import analyse, classify
LAST = 11

def tt(x): return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else 0

def collect(tables):
    rows = []; allsell = []
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]; data = {}
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try: d = load(p)
            except ValueError: continue
            if len(d["close_price"]) > LAST and d["Time"][LAST][11:16] == "14:45": data[os.path.basename(p).rsplit("_", 1)[0]] = d
        mke = [st.median((d["close_price"][LAST] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values()) for i in range(LAST)]
        for sym, d in data.items():
            O, H, L, C, V = d["open_price"], d["high_price"], d["low_price"], d["close_price"], d["volume"]
            if H[0] <= L[0]: continue
            avgv = sum(V) / len(V)
            for i in range(1, LAST):
                D, P, raw = window(d, i, i)
                if D >= -10: continue
                fe = (C[LAST] - C[i]) / C[i] * 100 - mke[i]
                allsell.append(fe)
                lab, dist, drv = maha_state(D, -P, V[i] / (sum(V[:i]) / i), tables["maha"])
                if lab != "OUTLIER" or drv != "SIZE": continue
                reg = classify(*[analyse(d, i)[k] for k in ("struct", "flow")]) if i >= 3 else "n/a"
                hi, lo = max(H[:i + 1]), min(L[:i + 1])
                rows.append(dict(date=date, sym=sym, i=i, D=D, size=abs(d["close_cvd"][i] - d["open_cvd"][i]) / avgv, spike=V[i] / (sum(V[:i]) / i), ret=raw,
                                 dpos=(C[i] - lo) / max(hi - lo, 1e-9), reg=reg, mstruct=analyse(d, i)["struct"].split(",")[0] if i >= 3 else "n/a", fe=fe, d=dist))
    return rows, allsell

def line(lab, g, base):
    if len(g) < 8: print(f"  {lab:34s} n={len(g)}"); return
    x = [r["fe"] for r in g]; dd = {}; [dd.setdefault(r["date"], []).append(r["fe"]) for r in g]
    print(f"  {lab:34s} n={len(g):4d} mean {st.mean(x):+.3f}% median {st.median(x):+.3f}% win {100*sum(v>0 for v in x)/len(x):3.0f}% (t {tt(x):+.1f}) days+ {sum(st.mean(v)>0 for v in dd.values())}/{len(dd)}")

if __name__ == "__main__":
    T = peer_tables(); R, allsell = collect(T)
    base = st.mean(allsell)
    print(f"{len(R)} SIZE-driven selling outliers in {len({(r['date'], r['sym']) for r in R})} stock-days; baseline (all selling bars with D<-10%, {len(allsell)}): mean {base:+.3f}% median {st.median(allsell):+.3f}% win {100*sum(v>0 for v in allsell)/len(allsell):.0f}%")
    line("ALL", R, base)
    x = sorted(r["fe"] for r in R); print(f"  without the top 5% (n={len(x)-len(x)//20}): mean {st.mean(x[:len(x)-len(x)//20]):+.3f}%; trimmed 10% both ends: {st.mean(x[len(x)//10:len(x)-len(x)//10]):+.3f}%")
    print("\nBy day:")
    for d in sorted({r["date"] for r in R}, key=lambda x: (x[3:5], x[:2])): line(d, [r for r in R if r["date"] == d], base)
    print("\nBy time of the outlier bar:")
    for lab, fn in (("09:45-10:15", lambda r: r["i"] <= 2), ("10:45-11:15", lambda r: 3 <= r["i"] <= 4), ("11:45-12:15", lambda r: 5 <= r["i"] <= 6), ("12:45-13:15", lambda r: 7 <= r["i"] <= 8), ("13:45-14:15", lambda r: r["i"] >= 9)): line(lab, [r for r in R if fn(r)], base)
    print("\nBy size of the delta (in average bar volumes):")
    for lab, fn in (("< 0.5", lambda r: r["size"] < .5), ("0.5 - 1.5", lambda r: .5 <= r["size"] < 1.5), (">= 1.5", lambda r: r["size"] >= 1.5)): line(lab, [r for r in R if fn(r)], base)
    print("\nBy price move in the bar:")
    for lab, fn in (("fell (< -0.3%)", lambda r: r["ret"] < -.3), ("flat (-0.3..+0.3%)", lambda r: -.3 <= r["ret"] <= .3), ("rose (> +0.3%)", lambda r: r["ret"] > .3)): line(lab, [r for r in R if fn(r)], base)
    print("\nBy volume spike:")
    for lab, fn in (("< 1x (quiet)", lambda r: r["spike"] < 1), ("1-3x", lambda r: 1 <= r["spike"] < 3), (">= 3x", lambda r: r["spike"] >= 3)): line(lab, [r for r in R if fn(r)], base)
    print("\nBy position in the day's range so far (0 = at the low):")
    for lab, fn in (("lower third", lambda r: r["dpos"] < .33), ("middle", lambda r: .33 <= r["dpos"] < .67), ("upper third", lambda r: r["dpos"] >= .67)): line(lab, [r for r in R if fn(r)], base)
    print("\nBy structure vs master candle at that bar:")
    for v in sorted({r["mstruct"] for r in R}): line(v, [r for r in R if r["mstruct"] == v], base)
    print("\nBy regime at that bar (from 10:45 on):")
    for v in ("A", "B", "C", "C2", "D", "D2", "E"): line("regime " + v, [r for r in R if r["reg"] == v], base)
    c = collections.Counter((r["date"], r["sym"]) for r in R); rep = [k for k, v in c.items() if v >= 2]
    print(f"\nStock-days with 2+ outlier bars: {len(rep)}")
    sym_days = collections.Counter(r["sym"] for r in R)
    print("Stocks flagged on 3+ days:", sorted([(s, len({r['date'] for r in R if r['sym'] == s})) for s in sym_days if len({r['date'] for r in R if r['sym'] == s}) >= 3], key=lambda x: -x[1])[:15])
    import pickle; pickle.dump(R, open(os.path.join(HERE, "_os.pkl"), "wb"))
