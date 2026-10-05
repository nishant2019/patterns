"""CVD candle pattern catalogue: do they predict forward price?
Signal at close of bar i (i=2..9). Outcome = return of next 1 / 2 bars minus the median stock for the same bar/day.
Discovery = first 4 days, Test = last 3 days (parameters fixed before looking at test).
"""
import sys, os, statistics as st, math, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "compression"))
from cvd_candles import days, LAST

def ctstat(rs, k):
    g = collections.defaultdict(list)
    for r in rs: g[r[1], r[3]].append(r[k])
    m = [st.mean(v) for v in g.values()]
    return (len(m), st.mean(m), tstat(m)) if len(m) > 5 else (len(m), 0, 0)

def tstat(x):
    return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else 0

def patterns(d, i):
    O, C, V = d["open_cvd"], d["close_cvd"], d["volume"]
    H, L = d["high_cvd"], d["low_cvd"]
    P, PO = d["close_price"], d["open_price"]
    out = []
    body = lambda k: C[k] - O[k]
    rng = lambda k: max(H[k] - L[k], 1e-9)
    up = lambda k: body(k) > 0
    dn = lambda k: body(k) < 0
    D = body(i) / V[i] * 100
    bf = abs(body(i)) / rng(i)                       # body fraction of CVD range
    lw = (min(O[i], C[i]) - L[i]) / rng(i); uw = (H[i] - max(O[i], C[i])) / rng(i)
    pup = P[i] > PO[i]
    # --- 1 bar
    out.append("C1 CVD candle UP" if up(i) else "C1 CVD candle DOWN")
    if abs(D) >= 30: out.append("C1 big body %s (|D|>=30%%)" % ("UP" if D > 0 else "DOWN"))
    if abs(D) < 5: out.append("C1 doji (|D|<5%)")
    if lw > .5 and bf < .5: out.append("C1 CVD hammer (long lower wick)")
    if uw > .5 and bf < .5: out.append("C1 CVD shooting star (long upper wick)")
    if D > 10 and not pup: out.append("C1 divergence: CVD up, price down")
    if D < -10 and pup: out.append("C1 divergence: CVD down, price up")
    if bf > .8 and D > 10: out.append("C1 marubozu CVD up")
    if bf > .8 and D < -10: out.append("C1 marubozu CVD down")
    # --- 2 bar
    j = i - 1
    if up(i) and dn(j) and C[i] >= O[j] and O[i] <= C[j]: out.append("C2 bullish CVD engulfing")
    if dn(i) and up(j) and C[i] <= O[j] and O[i] >= C[j]: out.append("C2 bearish CVD engulfing")
    if H[i] < H[j] and L[i] > L[j]: out.append("C2 CVD inside bar")
    if H[i] > H[j] and L[i] < L[j]: out.append("C2 CVD outside bar")
    if dn(j) and up(i) and C[i] > H[j]: out.append("C2 CVD reversal up through prior high")
    if up(j) and dn(i) and C[i] < L[j]: out.append("C2 CVD reversal down through prior low")
    # --- 3 bar
    if up(i) and up(j) and up(i - 2): out.append("C3 three CVD up candles")
    if dn(i) and dn(j) and dn(i - 2): out.append("C3 three CVD down candles")
    if H[i] > H[j] > H[i - 2] and L[i] > L[j] > L[i - 2]: out.append("C3 CVD higher highs+lows")
    if H[i] < H[j] < H[i - 2] and L[i] < L[j] < L[i - 2]: out.append("C3 CVD lower highs+lows")
    if dn(i - 2) and abs(body(j)) < .3 * abs(body(i - 2)) and up(i) and C[i] > (O[i - 2] + C[i - 2]) / 2: out.append("C3 CVD morning star")
    if up(i - 2) and abs(body(j)) < .3 * abs(body(i - 2)) and dn(i) and C[i] < (O[i - 2] + C[i - 2]) / 2: out.append("C3 CVD evening star")
    # --- structure of CVD vs day so far
    if C[i] > max(H[k] for k in range(i)): out.append("S new day-high CVD close")
    if C[i] < min(L[k] for k in range(i)): out.append("S new day-low CVD close")
    # CVD makes new high while price does not (and vice versa)
    pmax = max(d["high_price"][k] for k in range(i))
    pmin = min(d["low_price"][k] for k in range(i))
    if H[i] > max(H[k] for k in range(i)) and d["high_price"][i] <= pmax: out.append("S CVD new high, price not (bull divergence)")
    if L[i] < min(L[k] for k in range(i)) and d["low_price"][i] >= pmin: out.append("S CVD new low, price not (absorption)")
    if d["high_price"][i] > pmax and H[i] <= max(H[k] for k in range(i)): out.append("S price new high, CVD not (bear divergence)")
    if d["low_price"][i] < pmin and L[i] >= min(L[k] for k in range(i)): out.append("S price new low, CVD not (bull divergence)")
    return out

def collect():
    rows = []
    for date, data in days():
        mk = {}
        for i in range(LAST):
            for h in (1, 2):
                mk[i, h] = st.mean((d["close_price"][min(i + h, LAST)] / d["close_price"][i] - 1) * 100 for d in data.values())
        for sym, d in data.items():
            C = d["close_price"]
            for i in range(2, 10):
                f = {h: (C[i + h] / C[i] - 1) * 100 - mk[i, h] for h in (1, 2)}
                for p in patterns(d, i):
                    rows.append((p, date, sym, i, f[1], f[2]))
    return rows

if __name__ == "__main__":
    rows = collect()
    dates = sorted({r[1] for r in rows}, key=lambda s: s[6:] + s[3:5] + s[:2])
    disc, test = set(dates[:4]), set(dates[4:])
    print("days:", dates, "\ndiscovery:", sorted(disc), "test:", sorted(test))
    byp = collections.defaultdict(list)
    for r in rows: byp[r[0]].append(r)
    allf = [r[5] for r in rows]
    base = collections.defaultdict(list)
    out = []
    for p, rs in byp.items():
        def stat(sub, k=5):
            x = [r[k] for r in sub]
            c = ctstat(sub, k)
            return (len(x), st.mean(x), c[2]) if len(x) > 20 else (len(x), 0, 0)
        a, b = [r for r in rs if r[1] in disc], [r for r in rs if r[1] in test]
        out.append((p, len(rs), stat(rs), stat(a), stat(b), stat(rs, 4)))
    out.sort(key=lambda o: -abs(o[2][2]))
    print(f"\n{len(out)} patterns, {len(rows)} pattern-bars. Outcome = next-2-bar return minus the cross-sectional MEAN stock (%).")
    print(f"{'pattern':50s}{'n':>7s} | {'ALL 2bar':>16s} | {'DISC':>14s} | {'TEST':>14s} | 1bar")
    for p, n, s, a, b, s1 in out:
        print(f"{p:50s}{n:7d} | {s[1]:+.3f}% t{s[2]:+5.1f} | {a[1]:+.3f} t{a[2]:+4.1f} | {b[1]:+.3f} t{b[2]:+4.1f} | {s1[1]:+.3f} t{s1[2]:+.1f}")
    # replication: discovery |t|>=2 -> does test keep sign?
    sig = [o for o in out if abs(o[3][2]) >= 2]
    rep = [o for o in sig if o[3][1] * o[4][1] > 0 and abs(o[4][2]) >= 1.65]
    print(f"\nDiscovery |t|>=2: {len(sig)} patterns; same sign AND test |t|>=1.65: {len(rep)}")
    for o in rep: print("  ", o[0], f"disc {o[3][1]:+.3f}% test {o[4][1]:+.3f}% (n_test={o[4][0]})")
    print(f"Chance expectation of |t|>=2 among {len(out)} null patterns: ~{len(out)*0.05:.1f}")
