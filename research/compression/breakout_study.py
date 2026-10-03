"""Order flow on the breakout bar: after a compressed start, does delta/volume on the bar that
closes outside the master range separate continuation from failure?

Entry = close of the first bar (after the coil window) that closes outside the master range.
Direction = side of the break. Outcome = direction * (return from entry close to 14:45 close
minus median stock over same bars), in %. No costs.
"""
import glob, os, sys, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab")); sys.path.insert(0, HERE)
from oab_scanner import load
from orderflow_study import sp, rank
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
        mk = [st.median((d["close_price"][LAST] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values()) for i in range(LAST)]
        for sym, d in data.items():
            O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
            oc, lc, hc, cc, V = d["open_cvd"], d["low_cvd"], d["high_cvd"], d["close_cvd"], d["volume"]
            mH, mL = H[0], L[0]; mr = mH - mL
            if mr <= 0: continue
            if sum(H[i] <= mH and L[i] >= mL for i in range(1, t + 1)) < min_inside: continue
            k = next((i for i in range(t + 1, LAST) if C[i] > mH or C[i] < mL), None)   # need >=1 bar after entry
            if k is None: continue
            sgn = 1 if C[k] > mH else -1
            coilv = sum(V[1:k]) / (k - 1)
            dk = (cc[k] - oc[k]) / V[k] * 100 * sgn                    # delta on breakout bar, in break direction
            rows.append(dict(
                date=date, sym=sym, side=sgn, k=k,
                bo_d=dk, agree=dk > 0,
                bo_spike=V[k] / coilv, bo_vs_master=V[k] / V[0],
                bo_range=(H[k] - L[k]) / mr,                           # breakout bar range / master range
                bo_close=((C[k] - L[k]) / max(H[k] - L[k], 1e-9)) if sgn > 0 else ((H[k] - C[k]) / max(H[k] - L[k], 1e-9)),  # close near the extreme in break dir
                coil_d=sgn * sum(cc[i] - oc[i] for i in range(1, k)) / sum(V[1:k]) * 100,
                master_d=sgn * (cc[0] - oc[0]) / V[0] * 100,
                push=sgn * ((hc[k] if sgn > 0 else lc[k]) - oc[k]) / V[k] * 100,   # intrabar extreme CVD in break direction
                ret=sgn * ((C[LAST] - C[k]) / C[k] * 100 - mk[k]),
                abs_ret=sgn * (C[LAST] - C[k]) / C[k] * 100))
    return rows

if __name__ == "__main__":
    for t, mi in ((4, 3), (3, 2)):
        R = collect(t, mi)
        print(f"\n===== t={t}, >= {mi} inside | {len(R)} breakouts (up {sum(r['side']>0 for r in R)}, down {sum(r['side']<0 for r in R)}) | mean market-adj ret in break direction {st.mean(r['ret'] for r in R):+.3f}%  win {100*sum(r['ret']>0 for r in R)/len(R):.0f}%")
        for lab, rs in (("up breaks", [r for r in R if r['side'] > 0]), ("down breaks", [r for r in R if r['side'] < 0])):
            print(f"  {lab:11s} n={len(rs):4d} mean {st.mean(r['ret'] for r in rs):+.3f}%")
        print(f"{'feature':11s} Spearman | mean ret by quintile low->high (Q5-Q1, days positive)")
        for f in ("bo_d", "bo_spike", "bo_vs_master", "bo_range", "bo_close", "coil_d", "master_d", "push"):
            x = [r[f] for r in R]; y = [r["ret"] for r in R]
            o = sorted(range(len(R)), key=lambda i: x[i]); qs = [[R[i] for i in o[len(o) * q // 5:len(o) * (q + 1) // 5]] for q in range(5)]
            m = [st.mean(r["ret"] for r in q) for q in qs]; days = sorted({r["date"] for r in R})
            dp = sum(st.mean(r["ret"] for r in qs[4] if r["date"] == dd) - st.mean(r["ret"] for r in qs[0] if r["date"] == dd) > 0 for dd in days if any(r["date"]==dd for r in qs[4]) and any(r["date"]==dd for r in qs[0]))
            print(f"{f:11s} {sp(x, y):+.3f}   | " + " ".join(f"{v:+.2f}" for v in m) + f"  ({m[4]-m[0]:+.2f}, {dp}/{len(days)})")
        print("delta agrees with break direction vs not:")
        for lab, rs in (("  agrees", [r for r in R if r['agree']]), ("  disagrees", [r for r in R if not r['agree']])):
            print(f"{lab:12s} n={len(rs):4d} mean {st.mean(r['ret'] for r in rs):+.3f}%  win {100*sum(r['ret']>0 for r in rs)/len(rs):.0f}%  days+ {sum(st.mean(r['ret'] for r in rs if r['date']==d)>0 for d in {r['date'] for r in rs})}/{len({r['date'] for r in rs})}")
