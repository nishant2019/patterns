"""Do the peer-percentile efficiency labels (efficiency_chart.py) predict forward returns?
Forward = next 2 bars / to the 14:45 close, minus the median stock; labels per bar, rolling 4 bars, and since 09:45."""
import glob, os, sys, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from efficiency_chart import peer_tables, state, window, load
LAST = 11
tables = peer_tables()
rows = []
for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
    date = folder.rsplit("_", 1)[1]; data = {}
    for p in glob.glob(os.path.join(folder, "*.csv")):
        try: d = load(p)
        except ValueError: continue
        if len(d["close_price"]) > LAST and d["Time"][LAST][11:16] == "14:45": data[p] = d
    mk2 = [st.median((d["close_price"][min(i + 2, LAST)] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values()) for i in range(LAST)]
    mke = [st.median((d["close_price"][LAST] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values()) for i in range(LAST)]
    for p, d in data.items():
        if d["high_price"][0] <= d["low_price"][0]: continue
        C = d["close_price"]
        for t in range(1, LAST):
            f2 = (C[min(t + 2, LAST)] - C[t]) / C[t] * 100 - mk2[t]; fe = (C[LAST] - C[t]) / C[t] * 100 - mke[t]
            D, P, _ = window(d, t, t)
            r = dict(date=date, f2=f2, fe=fe, sign=1 if D > 0 else -1, bar=state(D, P, tables["bar"])[0])
            if t >= 3:
                r["roll"] = state(*window(d, t - 3, t)[:2], tables["roll"])[0]; r["day"] = state(*window(d, 1, t)[:2], tables["day"])[0]
            rows.append(r)
def tt(x): return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else 0
print(f"baseline: 2 bars {st.mean(r['f2'] for r in rows):+.3f}%  to close {st.mean(r['fe'] for r in rows):+.3f}%  (n={len(rows)})")
for kind in ("bar", "roll", "day"):
    print(f"\n{kind}:  label x delta direction  -> n, 2 bars, to close (t, positive days)")
    for lab in ("AGAINST", "ABSORBED", "NORM", "STRONG"):
        for sg, nm in ((-1, "selling"), (1, "buying")):
            g = [r for r in rows if r.get(kind) == lab and r["sign"] == sg]
            if len(g) < 15: continue
            dd = {}; [dd.setdefault(r["date"], []).append(r["fe"]) for r in g]
            print(f"  {lab:9s} {nm:8s} n={len(g):5d}  {st.mean(r['f2'] for r in g):+.3f}%  {st.mean(r['fe'] for r in g):+.3f}% (t {tt([r['fe'] for r in g]):+.1f}, {sum(st.mean(v) > 0 for v in dd.values())}/{len(dd)})")
