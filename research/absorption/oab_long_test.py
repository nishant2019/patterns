"""Long-only OAB trade test + candidate refinements (leave-one-day-out check)."""
import glob, os, sys, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import PARAMS, load, scan_stock
from oab_improve import BASE, collect

# per-trade: entry at window-end close, stop = master low, exit stop/target/close
def run(exit_mode):
    out = []
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try: d = load(p)
            except ValueError: continue
            sym = os.path.basename(p).rsplit("_", 1)[0]
            h = scan_stock(d, PARAMS)
            if not h: continue
            T = [t[11:16] for t in d["Time"]]; e = T.index(h["end"])
            H, L, C = d["high_price"], d["low_price"], d["close_price"]
            entry = C[e]; stop = h["master_low"]; risk = entry - stop
            exitp = C[-1]; why = "close"
            for k in range(e + 1, len(C)):
                if L[k] <= stop: exitp, why = stop, "stop"; break
                if exit_mode and H[k] >= entry + exit_mode * risk: exitp, why = entry + exit_mode * risk, "target"; break
            out.append(dict(date=date, sym=sym, pnl=(exitp-entry)/entry*100, r=(exitp-entry)/risk, why=why, risk=risk/entry*100, **{k: h[k] for k in ("cvd_selling_pct", "bars")}, e=e))
    return out

print("Long-only OAB: entry at window-end close, stop = master low (no costs)")
print("exit            n  win%  avg%/trade  avgR  stopped targets  median risk%")
for lab, m in [("hold to close", 0), ("target 1R", 1), ("target 2R", 2), ("target 3R", 3)]:
    t = run(m)
    print(f"{lab:14s} {len(t):3d} {100*sum(x['pnl']>0 for x in t)/len(t):4.0f}  {st.mean(x['pnl'] for x in t):+.2f}      {st.mean(x['r'] for x in t):+.2f}  {sum(x['why']=='stop' for x in t):5d} {sum(x['why']=='target' for x in t):6d}   {st.median(x['risk'] for x in t):.2f}")

t = run(0)
print("\nHold-to-close by day:")
for d in sorted({x["date"] for x in t}):
    s = [x for x in t if x["date"] == d]; print(f"  {d} n={len(s):2d} avg {st.mean(x['pnl'] for x in s):+.2f}%  win {100*sum(x['pnl']>0 for x in s)/len(s):.0f}%")

R = collect(); oab = [r for r in R if r["oab"]]
print("\nCandidate refinements on OAB (window end -> close vs average stock):")
def line(lab, rs):
    if not rs: print(f"  {lab:34s} n=0"); return
    rel=[r['rel'] for r in rs]; dd={}
    [dd.setdefault(r['date'],[]).append(r['rel']) for r in rs]
    print(f"  {lab:34s} n={len(rs):3d} vs_mkt={st.mean(rel):+.2f}% beat={100*sum(x>0 for x in rel)/len(rel):3.0f}% breakout={100*sum(r['bo'] for r in rs)/len(rs):3.0f}% days+={sum(st.mean(v)>0 for v in dd.values())}/{len(dd)}")
line("all OAB", oab)
for lab, fn in [("cvd_selling <= 25%", lambda r: r['cvdsell']<=25), ("cvd_selling > 25%", lambda r: r['cvdsell']>25),
                ("bars >= 4", lambda r: r['bars']>=4), ("bars == 3", lambda r: r['bars']==3),
                ("window ends >= 11:15 (e>=4)", lambda r: r['e']>=4), ("window ends <= 10:45", lambda r: r['e']<4),
                ("cvd<=25 & bars>=4", lambda r: r['cvdsell']<=25 and r['bars']>=4)]:
    line(lab, [r for r in oab if fn(r)])
print("\nSame refinements on the broader base set (n=%d), where there is more data:" % len(R))
line("all base", R)
for lab, fn in [("cvd_selling <= 25%", lambda r: r['cvdsell']<=25), ("cvd_selling > 25%", lambda r: r['cvdsell']>25),
                ("bars >= 4", lambda r: r['bars']>=4), ("bars == 3", lambda r: r['bars']==3),
                ("window ends >= 11:15", lambda r: r['e']>=4), ("window ends <= 10:45", lambda r: r['e']<4)]:
    line(lab, [r for r in R if fn(r)])
