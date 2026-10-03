"""Price-only compression study: first bar = master candle; do later bars coiling inside it
predict range expansion / master-range breakout?

Decision time t (after bar t closes). Features use bars 1..t only (point-in-time).
Outcomes use bars t+1..end of day (through the 14:45 bar so every stock has the same bars).
No VIX in the data: day-level volatility regime is proxied by the median master-bar range
across all stocks that day.
"""
import glob, os, sys, statistics as st, math, csv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import load

LAST = 11  # last bar index used (14:45 bar) so all stocks align


def collect(t):
    rows = []
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]
        data = {}
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try:
                d = load(p)
            except ValueError:
                continue
            if len(d["close_price"]) > LAST and d["Time"][LAST][11:16] == "14:45":
                data[os.path.basename(p).rsplit("_", 1)[0]] = d
        regime = st.median((d["high_price"][0] - d["low_price"][0]) / d["open_price"][0] * 100 for d in data.values())
        mkt_fwd = [st.median((d["close_price"][LAST] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values()) for i in range(LAST)]
        for sym, d in data.items():
            O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
            mH, mL = H[0], L[0]
            mr = mH - mL
            if mr <= 0 or O[0] <= 0:
                continue
            idx = range(1, t + 1)
            inside = [H[i] <= mH and L[i] >= mL for i in idx]
            closein = [mL <= C[i] <= mH for i in idx]
            rng = [(H[i] - L[i]) / mr for i in idx]
            cl_hi, cl_lo = max(H[1:t + 1]), min(L[1:t + 1])
            # forward outcomes from the close of bar t
            fH, fL = max(H[t + 1:LAST + 1]), min(L[t + 1:LAST + 1])
            up_bo = any(C[i] > mH for i in range(t + 1, LAST + 1))
            dn_bo = any(C[i] < mL for i in range(t + 1, LAST + 1))
            fwd = (C[LAST] - C[t]) / C[t] * 100
            rows.append(dict(
                date=date, sym=sym, t=t,
                n_inside=sum(inside), frac_inside=sum(inside) / t,
                all_inside=all(inside), n_closein=sum(closein),
                avg_rng=st.mean(rng),                      # mean bar range / master range
                cluster=(cl_hi - cl_lo) / mr,              # combined range of bars 1..t / master range
                last_rng=rng[-1],
                shrink=rng[-1] / max(rng[0], 1e-9),        # last bar range / first inside bar range
                master_pct=mr / O[0] * 100,                # master range as % of price (stock's own scale)
                regime=regime,
                # outcomes
                exp=(fH - fL) / mr,                        # remaining-day range / master range
                exp_vs_cluster=(fH - fL) / max(cl_hi - cl_lo, 1e-9),
                move=abs(fwd) / (mr / O[0] * 100),         # |forward return| in master-range units
                brk=up_bo or dn_bo, up=up_bo, dn=dn_bo,
                fwd=fwd, fwd_rel=fwd - mkt_fwd[t]))
    return rows


def pearson(a, b):
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else 0.0


def spearman(a, b):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
        for k, i in enumerate(order): r[i] = k
        return r
    return pearson(rank(a), rank(b))


if __name__ == "__main__":
    for t in (3, 4, 5):
        R = collect(t)
        print(f"\n===== decision after bar {t} ({'+'.join(['09:45','10:15','10:45','11:15','11:45'][:t]) if t<=5 else ''}): n={len(R)} stock-days")
        print(f"all-inside rate {100*sum(r['all_inside'] for r in R)/len(R):.1f}%   mean bars inside {st.mean(r['n_inside'] for r in R):.2f}/{t}   median cluster/master {st.median(r['cluster'] for r in R):.2f}")
        print("Spearman correlation of compression metric with later outcomes (negative = tighter coil -> bigger later expansion)")
        print(f"{'metric':12s} {'vs exp':>8s} {'vs move':>8s} {'vs breakout':>12s}")
        for f in ("n_inside", "avg_rng", "cluster", "last_rng", "shrink", "master_pct"):
            print(f"{f:12s} {spearman([r[f] for r in R],[r['exp'] for r in R]):+8.2f} {spearman([r[f] for r in R],[r['move'] for r in R]):+8.2f} {spearman([r[f] for r in R],[float(r['brk']) for r in R]):+12.2f}")
