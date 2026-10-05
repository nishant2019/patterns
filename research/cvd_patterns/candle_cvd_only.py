"""CVD candle patterns predicting the CVD itself (no price anywhere: pattern AND outcome are CVD only).
Outcomes after the signal bar: next-bar delta (% of that bar's volume), next-2-bar delta (% of volume), P(next delta same direction as pattern),
next-bar CVD range (% of volume, for neutral patterns). All minus the same-day/same-bar cross-sectional mean. Signed by pattern direction.
Discovery = first 4 days, test = last 3, t clustered by (day, bar).
"""
import sys, os, statistics as st, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "compression"))
from cvd_candles import days, LAST
from cvd_pattern_study import tstat
from candle_catalog_study import detect

def collect():
    rows = []
    for date, data in days():
        pre = collections.defaultdict(list)
        recs = []
        for sym, d in data.items():
            o, h, l, c, V = d["open_cvd"], d["high_cvd"], d["low_cvd"], d["close_cvd"], d["volume"]
            for i in range(3, 10):
                nD1 = (c[i+1]-o[i+1]) / V[i+1] * 100
                nD2 = (c[i+2]-o[i+1]) / (V[i+1]+V[i+2]) * 100
                nR = (h[i+1]-l[i+1]) / V[i+1] * 100
                up1 = 1.0 if nD1 > 0 else 0.0
                recs.append((sym, i, nD1, nD2, up1, nR, detect(o, h, l, c, i)))
                for k, v in (("D1", nD1), ("D2", nD2), ("up", up1), ("R", nR)): pre[i, k].append(v)
        mu = {k: st.mean(v) for k, v in pre.items()}
        for sym, i, nD1, nD2, up1, nR, pats in recs:
            for name, dr in pats.items():
                rows.append((name, dr, date, i, nD1 - mu[i, "D1"], nD2 - mu[i, "D2"], up1 - mu[i, "up"], nR - mu[i, "R"]))
    return rows

def cl(rs, k, s):
    g = collections.defaultdict(list)
    for r in rs: g[r[2], r[3]].append(s * r[k])
    m = [st.mean(v) for v in g.values()]; x = [s * r[k] for r in rs]
    return len(x), st.mean(x), (tstat(m) if len(m) > 5 else 0)

if __name__ == "__main__":
    rows = collect()
    dates = sorted({r[2] for r in rows}, key=lambda s: s[6:] + s[3:5] + s[:2]); disc, test = set(dates[:4]), set(dates[4:])
    by = collections.defaultdict(list)
    for r in rows: by[r[0], r[1]].append(r)
    D, N = [], []
    for (name, dr), rs in by.items():
        if len(rs) < 100: continue
        a = [r for r in rs if r[2] in disc]; b = [r for r in rs if r[2] in test]
        if dr: D.append((name, dr, cl(rs, 4, dr), cl(rs, 5, dr), cl(rs, 6, dr), cl(a, 4, dr), cl(b, 4, dr)))
        else: N.append((name, cl(rs, 7, 1), cl(a, 7, 1), cl(b, 7, 1)))
    print("Directional patterns: signed excess of NEXT CVD bar. dDelta1 = next-bar delta %vol, dDelta2 = next 2 bars %vol, dHit = excess P(next delta same direction)")
    print(f"{'pattern':36s}{'dir':>4s}{'n':>6s} | {'dDelta1':>8s} {'t':>5s} | {'dDelta2':>8s} {'t':>5s} | {'dHit':>7s} {'t':>5s} | {'DISC d1':>8s} {'t':>5s} | {'TEST d1':>8s} {'t':>5s}")
    for r in sorted(D, key=lambda r: -abs(r[2][2])):
        print(f"{r[0]:36s}{r[1]:+4d}{r[2][0]:6d} | {r[2][1]:+7.2f}% {r[2][2]:+5.1f} | {r[3][1]:+7.2f}% {r[3][2]:+5.1f} | {r[4][1]*100:+6.1f}pt {r[4][2]:+5.1f} | {r[5][1]:+7.2f}% {r[5][2]:+5.1f} | {r[6][1]:+7.2f}% {r[6][2]:+5.1f}")
    sig = [r for r in D if abs(r[5][2]) >= 2]; rep = [r for r in sig if r[5][1]*r[6][1] > 0 and abs(r[6][2]) >= 1.65]
    print(f"\n{len(D)} directional patterns; discovery |t|>=2: {len(sig)} (chance ~{len(D)*.05:.1f}); replicated in test: {len(rep)}")
    for r in rep: print("   ", r[0], f"disc {r[5][1]:+.2f}% test {r[6][1]:+.2f}% n={r[2][0]}")
    pos = sum(1 for r in D if r[2][1] > 0)
    print(f"patterns with positive pooled dDelta1: {pos}/{len(D)}; with |t|>=3 pooled: {sum(abs(r[2][2])>=3 for r in D)}")
    print("\nNeutral patterns: next-bar CVD range (%vol) minus baseline")
    for r in sorted(N, key=lambda r: -abs(r[1][2])):
        print(f"  {r[0]:20s} n={r[1][0]:6d} {r[1][1]:+.2f}% t{r[1][2]:+5.1f} | disc {r[2][1]:+.2f} t{r[2][2]:+4.1f} | test {r[3][1]:+.2f} t{r[3][2]:+4.1f}")
