"""Order-flow layer on top of master-candle compression.

Population: stocks whose first `t` bars after the master are mostly inside the master candle.
Features (point-in-time, bars 0..t): CVD/delta inside the coil, divergence, volume dry-up, location.
Outcome: return from close of bar t to the 14:45 bar close, minus the median stock (fwd_rel),
plus which master edge breaks first.
"""
import glob, os, sys, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import load
LAST = 11

def collect(t, min_inside):
    rows = []
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]; data = {}
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try: d = load(p)
            except ValueError: continue
            if len(d["close_price"]) > LAST and d["Time"][LAST][11:16] == "14:45":
                data[os.path.basename(p).rsplit("_", 1)[0]] = d
        mk = st.median((d["close_price"][LAST] - d["close_price"][t]) / d["close_price"][t] * 100 for d in data.values())
        for sym, d in data.items():
            O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
            oc, lc, cc, V = d["open_cvd"], d["low_cvd"], d["close_cvd"], d["volume"]
            mH, mL = H[0], L[0]; mr = mH - mL
            if mr <= 0: continue
            ins = sum(H[i] <= mH and L[i] >= mL for i in range(1, t + 1))
            if ins < min_inside: continue
            cv = sum(V[1:t + 1]); mv = V[0]
            dl = [cc[i] - oc[i] for i in range(t + 1)]
            first = next((i for i in range(t + 1, LAST + 1) if C[i] > mH or C[i] < mL), None)
            fwd = (C[LAST] - C[t]) / C[t] * 100
            rows.append(dict(
                date=date, sym=sym, ins=ins,
                pos=(C[t] - mL) / mr,                                  # close position in master range
                coil_d=sum(dl[1:t + 1]) / cv * 100,                   # net delta % of coil volume
                master_d=dl[0] / mv * 100,
                pos_bars=sum(x > 0 for x in dl[1:t + 1]),             # bars with positive delta
                last_d=dl[t] / V[t] * 100,
                cvd_vs_price=(cc[t] - cc[0]) / cv * 100 - (C[t] - C[0]) / C[0] * 100 * 10,  # CVD slope minus price slope (scaled)
                dryup=(cv / t) / mv,                                   # coil avg volume / master volume
                sellpush=st.mean((lc[i] - oc[i]) / V[i] * 100 for i in range(1, t + 1)),  # avg intrabar CVD low, % vol
                fwd=fwd, fwd_rel=fwd - mk,
                side=None if first is None else ("up" if C[first] > mH else "dn"),
                bo_ret=None if first is None else ((C[LAST] - C[first]) / C[first] * 100) * (1 if C[first] > mH else -1)))
    return rows

def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
    for k, i in enumerate(o): r[i] = k
    return r
def sp(a, b):
    ra, rb = rank(a), rank(b); ma, mb = st.mean(ra), st.mean(rb)
    n = sum((x - ma) * (y - mb) for x, y in zip(ra, rb)); d = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return n / d if d else 0

if __name__ == "__main__":
    for t, mi in ((4, 3), (3, 2)):
        R = collect(t, mi)
        print(f"\n===== t={t} bars after master, >= {mi} inside: n={len(R)}  (mean fwd_rel {st.mean(r['fwd_rel'] for r in R):+.3f}%)")
        print(f"{'feature':13s} Spearman vs fwd_rel | mean fwd_rel by quintile (low->high), days positive for Q5-Q1")
        for f in ("coil_d", "master_d", "pos_bars", "last_d", "cvd_vs_price", "dryup", "sellpush", "pos"):
            x = [r[f] for r in R]; y = [r["fwd_rel"] for r in R]
            o = sorted(range(len(R)), key=lambda i: x[i]); qs = [[R[i] for i in o[len(o) * q // 5:len(o) * (q + 1) // 5]] for q in range(5)]
            means = [st.mean(r["fwd_rel"] for r in q) for q in qs]
            days = sorted({r["date"] for r in R}); dpos = sum(st.mean(r["fwd_rel"] for r in qs[4] if r["date"] == dd) - st.mean(r["fwd_rel"] for r in qs[0] if r["date"] == dd) > 0 for dd in days)
            print(f"{f:13s} {sp(x, y):+.3f}              | " + " ".join(f"{m:+.2f}" for m in means) + f"   Q5-Q1 {means[4]-means[0]:+.2f}%  ({dpos}/{len(days)} days)")
