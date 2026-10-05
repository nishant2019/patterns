"""Control: do CVD candle patterns add anything beyond plain delta persistence?
Next-bar delta %vol is residualised against the signal bar's own delta (D, 10 equal-count bins) and the 2-bar-prior delta, per bar index; then patterns are re-scored."""
import sys, os, statistics as st, collections, bisect
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "compression"))
from cvd_candles import days
from candle_catalog_study import detect
from cvd_pattern_study import tstat
recs = []
for date, data in days():
    for sym, d in data.items():
        o, h, l, c, V = d["open_cvd"], d["high_cvd"], d["low_cvd"], d["close_cvd"], d["volume"]
        for i in range(3, 10):
            D = lambda k: (c[k]-o[k]) / V[k] * 100
            recs.append(dict(date=date, i=i, D0=D(i), D1=D(i-1), y=D(i+1), pats=detect(o, h, l, c, i)))
def bins(vals, n=10):
    s = sorted(vals); return [s[int(len(s)*k/n)] for k in range(1, n)]
b0, b1 = bins([r["D0"] for r in recs]), bins([r["D1"] for r in recs])
cell = collections.defaultdict(list)
for r in recs: r["cell"] = (r["i"], bisect.bisect(b0, r["D0"]), bisect.bisect(b1, r["D1"])); cell[r["cell"]].append(r["y"])
mu = {k: st.mean(v) for k, v in cell.items()}
for r in recs: r["res"] = r["y"] - mu[r["cell"]]
rows = collections.defaultdict(list)
for r in recs:
    for n, dr in r["pats"].items():
        if dr: rows[n, dr].append(r)
print(f"{'pattern':36s}{'n':>6s} | {'raw dDelta1':>11s} | {'residual (beyond own delta)':>28s}  t")
base_all = st.mean(r["y"] for r in recs)
out = []
for (n, dr), rs in rows.items():
    if len(rs) < 100: continue
    g = collections.defaultdict(list)
    for r in rs: g[r["date"], r["i"]].append(dr * r["res"])
    m = [st.mean(v) for v in g.values()]
    raw = st.mean(dr * (r["y"] - base_all) for r in rs)
    out.append((n, len(rs), raw, st.mean(dr * r["res"] for r in rs), tstat(m)))
for n, k, raw, res, t in sorted(out, key=lambda x: -abs(x[4])): print(f"{n:36s}{k:6d} | {raw:+10.2f}% | {res:+10.2f}%  t{t:+5.1f}")
print(f"\n{sum(abs(o[4])>=2 for o in out)}/{len(out)} patterns still |t|>=2 after controlling for own delta + prior delta (chance ~{len(out)*.05:.1f})")
