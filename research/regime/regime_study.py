"""Regime study: combine structure (where price sits vs the master candle) with order-flow relationship
(price vs CVD since the 09:45 open) at a decision time, and measure what each regime did afterwards.

Decision time t (bar index; 4 = 11:15, 7 = 12:45). Everything uses bars 0..t only.
Outcomes (bars t+1..14:45): market-adjusted return to the 14:45 close; first master-edge break direction; return vs the median stock.
"""
import glob, os, sys, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import load
LAST = 11

def structure(C_t, mH, mL):
    mr = mH - mL
    if C_t > mH: return "ABOVE master high"
    if C_t < mL: return "BELOW master low"
    p = (C_t - mL) / mr
    return "inside, upper third" if p >= 2 / 3 else ("inside, lower third" if p < 1 / 3 else "inside, middle")

def flow(Pchg, D):
    """Relationship between price and delta since the 09:45 open."""
    if abs(D) < 10: return "flow neutral"
    if D > 0: return "buying, price up (confirmed)" if Pchg > 0.2 else ("buying ABSORBED (price flat/down)" if Pchg < 0.1 else "buying, price flat")
    return "selling, price down (confirmed)" if Pchg < -0.2 else ("selling ABSORBED (price flat/up)" if Pchg > -0.1 else "selling, price flat")

def collect(t):
    rows = []
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]; data = {}
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try: d = load(p)
            except ValueError: continue
            if len(d["close_price"]) > LAST and d["Time"][LAST][11:16] == "14:45":
                data[os.path.basename(p).rsplit("_", 1)[0]] = d
        mk_since = [st.median((d["close_price"][i] - d["close_price"][0]) / d["close_price"][0] * 100 for d in data.values()) for i in range(LAST + 1)]
        mk_fwd = st.median((d["close_price"][LAST] - d["close_price"][t]) / d["close_price"][t] * 100 for d in data.values())
        for sym, d in data.items():
            O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
            oc, cc, V = d["open_cvd"], d["close_cvd"], d["volume"]
            mH, mL = H[0], L[0]
            if mH <= mL: continue
            Pchg = (C[t] - O[1]) / O[1] * 100
            D = (cc[t] - oc[1]) / sum(V[1:t + 1]) * 100
            fwd = (C[LAST] - C[t]) / C[t] * 100
            first = next((i for i in range(t + 1, LAST + 1) if C[i] > mH or C[i] < mL), None)
            half = (t + 1) // 2
            vt = sum(V[t - half + 1:t + 1]) / half / (sum(V[1:t - half + 1]) / max(t - half, 1))
            rows.append(dict(date=date, sym=sym, t=t, struct=structure(C[t], mH, mL), flow=flow(Pchg, D),
                             inside=sum(H[i] <= mH and L[i] >= mL for i in range(1, t + 1)), D=D, Pchg=Pchg, vt=vt,
                             rs=(C[t] - C[0]) / C[0] * 100 - mk_since[t],
                             fwd=fwd, fwd_rel=fwd - mk_fwd, side=None if first is None else (1 if C[first] > mH else -1),
                             brk=first is not None))
    return rows

def tt(x): return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else 0

if __name__ == "__main__":
    for t, tm in ((4, "11:15"), (7, "12:45")):
        R = collect(t)
        print(f"\n################ decision time {tm}: {len(R)} stock-days; baseline fwd_rel {st.mean(r['fwd_rel'] for r in R):+.3f}% (mean>median)")
        for key in ("struct", "flow"):
            print(f"\n-- by {key}")
            for v in sorted({r[key] for r in R}):
                g = [r for r in R if r[key] == v]; dd = {}
                [dd.setdefault(r["date"], []).append(r["fwd_rel"]) for r in g]
                b = [r for r in g if r["brk"]]
                print(f"  {v:36s} n={len(g):5d} fwd_rel {st.mean(r['fwd_rel'] for r in g):+.3f}% (t {tt([r['fwd_rel'] for r in g]):+.1f}) days+ {sum(st.mean(x) > 0 for x in dd.values())}/{len(dd)} | break {100*len(b)/len(g):3.0f}% up|break {100*sum(r['side']>0 for r in b)/max(len(b),1):3.0f}%")
        print("\n-- structure x flow  (n >= 40; fwd_rel to close, t, days+)")
        for s_ in sorted({r["struct"] for r in R}):
            for f_ in sorted({r["flow"] for r in R}):
                g = [r for r in R if r["struct"] == s_ and r["flow"] == f_]
                if len(g) < 40: continue
                dd = {}; [dd.setdefault(r["date"], []).append(r["fwd_rel"]) for r in g]
                b = [r for r in g if r["brk"]]
                print(f"  {s_:22s} | {f_:36s} n={len(g):4d} {st.mean(r['fwd_rel'] for r in g):+.3f}% (t {tt([r['fwd_rel'] for r in g]):+.1f}) {sum(st.mean(x)>0 for x in dd.values())}/{len(dd)} | up|break {100*sum(r['side']>0 for r in b)/max(len(b),1):3.0f}% ({len(b)} brk)")
        print("\n-- relative strength vs market at decision time (stock return since 09:15 close minus median), quintiles")
        o = sorted(R, key=lambda r: r["rs"]); n = len(o)
        for q in range(5):
            g = o[n * q // 5:n * (q + 1) // 5]; dd = {}; [dd.setdefault(r["date"], []).append(r["fwd_rel"]) for r in g]
            print(f"  Q{q+1} rs {g[0]['rs']:+.2f}..{g[-1]['rs']:+.2f}%  fwd_rel {st.mean(r['fwd_rel'] for r in g):+.3f}% (t {tt([r['fwd_rel'] for r in g]):+.1f}) days+ {sum(st.mean(x)>0 for x in dd.values())}/{len(dd)}")
