"""CVD candle patterns x key levels. Levels are point-in-time (use only bars < i, VWAP incl. bar i-1).
Support test: bar low within TOL of a level and close >= level. Resistance test: bar high within TOL and close <= level.
Signed outcome: + = move in the direction the pattern implies (long at support / short at resistance), minus same-bar mean stock.
"""
import sys, os, statistics as st, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "compression"))
from cvd_candles import days, LAST
from cvd_pattern_study import tstat
TOL = 0.2  # percent

def tags(d, i):
    O, C, V, H, L = d["open_cvd"], d["close_cvd"], d["volume"], d["high_cvd"], d["low_cvd"]
    rng = max(H[i] - L[i], 1e-9); body = C[i] - O[i]; D = body / V[i] * 100
    lw = (min(O[i], C[i]) - L[i]) / rng; uw = (H[i] - max(O[i], C[i])) / rng
    PH, PL = d["high_price"], d["low_price"]
    bull, bear = [], []
    if D >= 30: bull.append("big CVD body up")
    if D <= -30: bear.append("big CVD body down")
    if lw > .5 and abs(body) / rng < .5: bull.append("CVD hammer")
    if uw > .5 and abs(body) / rng < .5: bear.append("CVD shooting star")
    if L[i] < min(L[k] for k in range(i)) and PL[i] >= min(PL[k] for k in range(i)): bull.append("CVD new low, price not")
    if H[i] > max(H[k] for k in range(i)) and PH[i] <= max(PH[k] for k in range(i)): bear.append("CVD new high, price not")
    j = i - 1
    if body > 0 and C[j] < O[j] and C[i] >= O[j] and O[i] <= C[j]: bull.append("bullish CVD engulfing")
    if body < 0 and C[j] > O[j] and C[i] <= O[j] and O[i] >= C[j]: bear.append("bearish CVD engulfing")
    if D >= 10 and d["close_price"][i] <= d["open_price"][i]: bull.append("CVD up, price down")
    if D <= -10 and d["close_price"][i] >= d["open_price"][i]: bear.append("CVD down, price up")
    return bull, bear

def levels(d, i):
    P, V, H, L = d["close_price"], d["volume"], d["high_price"], d["low_price"]
    vw = sum(P[k] * V[k] for k in range(i)) / sum(V[k] for k in range(i))
    return {"master": (L[0], H[0]), "day": (min(L[k] for k in range(i)), max(H[k] for k in range(i))),
            "vwap": (vw, vw)}

def collect():
    rows = []
    for date, data in days():
        mk = {(i, h): st.mean((d["close_price"][min(i + h, LAST)] / d["close_price"][i] - 1) * 100 for d in data.values())
              for i in range(LAST) for h in (2, 99)}
        for sym, d in data.items():
            C, Hh, Ll = d["close_price"], d["high_price"], d["low_price"]
            for i in range(3, 10):
                f2 = (C[i + 2] / C[i] - 1) * 100 - mk[i, 2]
                fe = (C[LAST] / C[i] - 1) * 100 - mk[i, 99]
                bull, bear = tags(d, i); lv = levels(d, i)
                for name, (lo, hi) in lv.items():
                    sup = Ll[i] <= lo * (1 + TOL / 100) and Ll[i] >= lo * (1 - TOL / 100) and C[i] >= lo
                    res = Hh[i] >= hi * (1 - TOL / 100) and Hh[i] <= hi * (1 + TOL / 100) and C[i] <= hi
                    if sup:
                        rows.append((f"{name} support: touch only", date, i, f2, fe))
                        for t in bull: rows.append((f"{name} support + {t}", date, i, f2, fe))
                        rows.append((f"{name} support + ANY bull pattern", date, i, f2, fe)) if bull else None
                    if res:
                        rows.append((f"{name} resist: touch only", date, i, -f2, -fe))
                        for t in bear: rows.append((f"{name} resist + {t}", date, i, -f2, -fe))
                        rows.append((f"{name} resist + ANY bear pattern", date, i, -f2, -fe)) if bear else None
    return rows

def cst(rs, k):
    g = collections.defaultdict(list)
    for r in rs: g[r[1], r[2]].append(r[k])
    m = [st.mean(v) for v in g.values()]
    x = [r[k] for r in rs]
    return len(x), st.mean(x), (tstat(m) if len(m) > 5 else 0)

if __name__ == "__main__":
    rows = collect()
    dates = sorted({r[1] for r in rows}, key=lambda s: s[6:] + s[3:5] + s[:2])
    disc, test = set(dates[:4]), set(dates[4:])
    by = collections.defaultdict(list)
    for r in rows: by[r[0]].append(r)
    res = []
    for p, rs in by.items():
        a = cst([r for r in rs if r[1] in disc], 3); b = cst([r for r in rs if r[1] in test], 3)
        res.append((p, cst(rs, 3), a, b, cst(rs, 4)))
    res.sort(key=lambda o: -abs(o[1][2]))
    print(f"{len(res)} level x pattern combos. Signed excess return (%), clustered t. TOL={TOL}%")
    print(f"{'combo':52s}{'n':>6s} | {'2-bar':>15s} | {'DISC':>13s} | {'TEST':>13s} | to close")
    for p, s, a, b, e in res:
        if s[0] < 30: continue
        print(f"{p:52s}{s[0]:6d} | {s[1]:+.3f}% t{s[2]:+5.1f} | {a[1]:+.3f} t{a[2]:+4.1f} | {b[1]:+.3f} t{b[2]:+4.1f} | {e[1]:+.3f}% t{e[2]:+.1f}")
    sig = [o for o in res if o[2][0] > 30 and abs(o[2][2]) >= 2]
    rep = [o for o in sig if o[2][1] * o[3][1] > 0 and abs(o[3][2]) >= 1.65]
    print(f"\nDiscovery |t|>=2: {len(sig)}; replicate same sign with test |t|>=1.65: {len(rep)}; chance ~{len(res)*.05:.1f}")
    for o in rep: print("  ", o[0], f"disc {o[2][1]:+.3f} test {o[3][1]:+.3f} n_test {o[3][0]}")
