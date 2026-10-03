"""Comparing ways to score how efficient a bar's delta was (absorption / outlier detection).

Bars with |delta| >= 10% of volume. Quantities per bar:
  D      net delta as % of the bar's volume                       (signed)
  Pd     price move in master-bar ranges, signed ALONG the delta   (positive: price followed the delta; negative: price moved against it)
  size   |delta| / stock-day average bar volume                    (delta size in 'normal bars')
Every metric returns an ABSORPTION score: higher = the delta did less than usual (more absorbed); negative = delta was
unusually efficient. Peers = bars in the same |D| decile (pooled over stocks and days).
Metrics:
  pct    signed percentile of Pd among peers (100 - rank)            [the current chart method, extended to signed Pd]
  zs     classical conditional z of Pd: (Pd - mean) / std within the peer decile
  rz     robust conditional z: (Pd - median) / (1.4826 MAD) within the peer decile              [modified z-score]
  kyle   standardised Kyle-lambda residual: Pd regressed on |D| (pooled OLS), residual / residual std in the peer decile
  amihud price impact per unit of delta in average-volume units: Pd / size, then robust z vs peers with similar size
  maha   signed Mahalanobis distance in (|D|, Pd, ln spike): sqrt((x-mu)' S^-1 (x-mu)), sign = direction of the Pd residual
  cusum  one-sided CUSUM over the stock-day sequence of rz:  S_t = max(0, S_{t-1} + (z_t - k)),  k = 0.5  (persistent absorption)
"""
import glob, math, os, statistics as st, sys, bisect
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import load
LAST, DMIN = 11, 10.0


def bars():
    out = []
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]; data = {}
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try: d = load(p)
            except ValueError: continue
            if len(d["close_price"]) > LAST and d["Time"][LAST][11:16] == "14:45":
                data[os.path.basename(p).rsplit("_", 1)[0]] = d
        mk2 = [st.median((d["close_price"][min(i + 2, LAST)] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values()) for i in range(LAST)]
        mke = [st.median((d["close_price"][LAST] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values()) for i in range(LAST)]
        for sym, d in data.items():
            O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
            oc, cc, V = d["open_cvd"], d["close_cvd"], d["volume"]
            mr = (H[0] - L[0]) / O[0] * 100
            if mr <= 0: continue
            avgv = sum(V) / len(V)
            for i in range(1, LAST):
                D = (cc[i] - oc[i]) / V[i] * 100
                if abs(D) < DMIN: continue
                sg = 1 if D > 0 else -1
                out.append(dict(date=date, sym=sym, i=i, D=D, Pd=sg * (C[i] - O[i]) / O[i] * 100 / mr, size=abs(cc[i] - oc[i]) / avgv,
                                spike=V[i] / (sum(V[:i]) / i), ret=(C[i] - O[i]) / O[i] * 100,
                                f2=(C[min(i + 2, LAST)] - C[i]) / C[i] * 100 - mk2[i], fe=(C[LAST] - C[i]) / C[i] * 100 - mke[i]))
    return out


def deciles(vals, k=10):
    s = sorted(vals); return [s[len(s) * q // k] for q in range(1, k)]


def med_mad(x):
    m = st.median(x); return m, st.median(abs(v - m) for v in x) or 1e-9


def score_all(R):
    # peer decile of |D|
    e = deciles([abs(r["D"]) for r in R]); es = deciles([r["size"] for r in R])
    for r in R: r["b"] = bisect.bisect(e, abs(r["D"])); r["bs"] = bisect.bisect(es, r["size"])
    G = {b: [r for r in R if r["b"] == b] for b in range(10)}; GS = {b: [r for r in R if r["bs"] == b] for b in range(10)}
    stats = {b: (st.mean(x["Pd"] for x in g), st.pstdev(x["Pd"] for x in g), *med_mad([x["Pd"] for x in g]), sorted(x["Pd"] for x in g)) for b, g in G.items()}
    # Kyle lambda: pooled OLS of Pd on |D|
    ax = [abs(r["D"]) for r in R]; mx, my = st.mean(ax), st.mean(r["Pd"] for r in R)
    beta = sum((a - mx) * (r["Pd"] - my) for a, r in zip(ax, R)) / sum((a - mx) ** 2 for a in ax); c = my - beta * mx
    for r in R: r["res"] = r["Pd"] - (beta * abs(r["D"]) + c)
    rs = {b: st.pstdev(x["res"] for x in g) for b, g in G.items()}
    # Amihud-style impact vs size peers
    for r in R: r["imp"] = r["Pd"] / r["size"]
    ams = {b: med_mad([x["imp"] for x in g]) for b, g in GS.items()}
    # Mahalanobis on (|D|, Pd, ln spike)
    X = [(abs(r["D"]), r["Pd"], math.log(r["spike"])) for r in R]
    mu = [st.mean(x[k] for x in X) for k in range(3)]
    S = [[sum((x[a] - mu[a]) * (x[b] - mu[b]) for x in X) / (len(X) - 1) for b in range(3)] for a in range(3)]
    # invert 3x3
    def inv3(m):
        a, b, c_, d, e_, f, g, h, i = m[0][0], m[0][1], m[0][2], m[1][0], m[1][1], m[1][2], m[2][0], m[2][1], m[2][2]
        det = a * (e_ * i - f * h) - b * (d * i - f * g) + c_ * (d * h - e_ * g)
        return [[(e_ * i - f * h) / det, (c_ * h - b * i) / det, (b * f - c_ * e_) / det], [(f * g - d * i) / det, (a * i - c_ * g) / det, (c_ * d - a * f) / det], [(d * h - e_ * g) / det, (b * g - a * h) / det, (a * e_ - b * d) / det]]
    Si = inv3(S)
    for r, x in zip(R, X):
        dv = [x[k] - mu[k] for k in range(3)]
        m2 = sum(dv[a] * Si[a][b] * dv[b] for a in range(3) for b in range(3))
        r["maha_d"] = math.sqrt(max(m2, 0))
    for r in R:
        mean, sd, med, mad, srt = stats[r["b"]]
        r["pct"] = 100 - 100 * bisect.bisect(srt, r["Pd"]) / len(srt)            # high = absorbed
        r["zs"] = -(r["Pd"] - mean) / sd
        r["rz"] = -(r["Pd"] - med) / (1.4826 * mad)
        r["kyle"] = -r["res"] / rs[r["b"]]
        r["amihud"] = -(r["imp"] - ams[r["bs"]][0]) / (1.4826 * ams[r["bs"]][1])
        r["maha"] = (1 if r["res"] < 0 else -1) * r["maha_d"]                      # sign: absorbed side positive
    # CUSUM per stock-day on rz (all bars of the day with delta >= 10% in sequence)
    seq = {}
    for r in sorted(R, key=lambda r: (r["date"], r["sym"], r["i"])): seq.setdefault((r["date"], r["sym"]), []).append(r)
    for g in seq.values():
        s = 0.0
        for r in g: s = max(0.0, s + r["rz"] - 0.5); r["cusum"] = s
    return beta, c


def spearman(a, b):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
            for k in range(i, j + 1): r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    ra, rb = rank(a), rank(b); ma, mb = st.mean(ra), st.mean(rb)
    n = sum((x - ma) * (y - mb) for x, y in zip(ra, rb)); d = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return n / d if d else 0.0


if __name__ == "__main__":
    R = bars(); beta, c = score_all(R)
    print(f"{len(R)} bars with |delta| >= {DMIN:.0f}% of volume ({sum(r['D']<0 for r in R)} selling, {sum(r['D']>0 for r in R)} buying); Kyle slope: Pd = {beta:.4f}|D| {c:+.3f}")
    M = ["pct", "zs", "rz", "kyle", "amihud", "maha", "cusum"]
    print("\n1) Agreement between metrics (Spearman correlation of absorption scores)")
    print("         " + "".join(f"{m:>8s}" for m in M))
    for a in M: print(f"{a:8s} " + "".join(f"{spearman([r[a] for r in R], [r[b] for r in R]):8.2f}" for b in M))
    print("\n2) Shape: how many bars each metric treats as unusual")
    for m in ("zs", "rz", "kyle", "amihud"):
        v = [r[m] for r in R]
        print(f"  {m:7s} |z|>=2: {100*sum(abs(x)>=2 for x in v)/len(v):4.1f}%   |z|>=3: {100*sum(abs(x)>=3 for x in v)/len(v):4.1f}%   |z|>=3.5: {100*sum(abs(x)>=3.5 for x in v)/len(v):4.1f}%   max absorbed {max(v):6.1f}, max efficient {min(v):7.1f}   (normal expectation: 4.6% / 0.27% / 0.05%)")
    v = [r["maha_d"] for r in R]; print(f"  maha    d^2 > chi2(3, 97.5%)=9.35: {100*sum(x*x>9.35 for x in v)/len(v):4.1f}% (expect 2.5%)   cusum>=4: {100*sum(r['cusum']>=4 for r in R)/len(R):4.1f}% of bars")
    print(f"  pct     by construction 33% of bars are 'absorbed' (<= p33) and the scale saturates (p99 vs p99.9 are indistinguishable)")
    print("\n3) Information about what happens next (absorption score vs forward return, Spearman IC; top-decile 'most absorbed' minus bottom-decile 'most efficient')")
    for grp, f in (("SELLING bars (D<0)", lambda r: r["D"] < 0), ("BUYING bars (D>0)", lambda r: r["D"] > 0)):
        g = [r for r in R if f(r)]
        print(f"  {grp}: n={len(g)}")
        print(f"    {'metric':8s} {'IC 2 bars':>10s} {'IC to close':>12s} {'top10% close':>13s} {'bot10% close':>13s} {'spread':>8s} {'days spread>0':>14s}")
        for m in M:
            o = sorted(g, key=lambda r: r[m]); n = len(o); top, bot = o[-n // 10:], o[:n // 10]
            dd = {}
            for r in o[-n // 10:]: dd.setdefault(r["date"], [[], []])[0].append(r["fe"])
            for r in o[:n // 10]: dd.setdefault(r["date"], [[], []])[1].append(r["fe"])
            cons = sum(1 for v in dd.values() if v[0] and v[1] and st.mean(v[0]) - st.mean(v[1]) > 0)
            print(f"    {m:8s} {spearman([r[m] for r in g], [r['f2'] for r in g]):+10.3f} {spearman([r[m] for r in g], [r['fe'] for r in g]):+12.3f} {st.mean(r['fe'] for r in top):+12.3f}% {st.mean(r['fe'] for r in bot):+12.3f}% {st.mean(r['fe'] for r in top) - st.mean(r['fe'] for r in bot):+7.3f}% {cons:>9d}/{len(dd)}")
    import pickle; pickle.dump(R, open(os.path.join(HERE, "_em.pkl"), "wb"))
