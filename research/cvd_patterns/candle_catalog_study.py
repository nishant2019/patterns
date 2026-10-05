"""Classic candlestick pattern catalogue applied to CVD candles (and, as a control, to price candles).
Directional patterns: outcome signed in the pattern's implied direction. Neutral patterns: |return| vs baseline |return|.
Outcome = price return after signal-bar close (1 bar, 2 bars, to 14:45) minus the same-day/bar cross-sectional mean stock.
Discovery = first 4 days, Test = last 3. t-stats clustered by (day, bar). Holm-style threshold printed.
"""
import sys, os, statistics as st, collections, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "compression"))
from cvd_candles import days, LAST
from cvd_pattern_study import tstat

def detect(o, h, l, c, i):
    """o,h,l,c lists; returns {name: dir} for patterns completing on bar i (dir +1 bull, -1 bear, 0 neutral). Needs i>=3."""
    out = {}
    B = lambda k: abs(c[k] - o[k]); R = lambda k: max(h[k] - l[k], 1e-9)
    up = lambda k: c[k] > o[k]; dn = lambda k: c[k] < o[k]
    top = lambda k: max(o[k], c[k]); bot = lambda k: min(o[k], c[k])
    uw = lambda k: h[k] - top(k); lw = lambda k: bot(k) - l[k]
    avgb = st.mean(B(k) for k in range(i - 3, i)) + 1e-9
    longb = lambda k: B(k) > 1.0 * avgb and B(k) / R(k) > .6
    small = lambda k: B(k) < .35 * avgb or B(k) / R(k) < .3
    doji = lambda k: B(k) / R(k) < .1
    mid = lambda k: (o[k] + c[k]) / 2
    dtr = c[i - 1] < c[i - 3]; utr = c[i - 1] > c[i - 3]       # prior trend on the CVD line
    k = i
    # ---- 1 bar
    if doji(k): out["doji"] = 0
    if doji(k) and lw(k) > .6 * R(k) and uw(k) < .1 * R(k): out["dragonfly doji"] = 1
    if doji(k) and uw(k) > .6 * R(k) and lw(k) < .1 * R(k): out["gravestone doji"] = -1
    if doji(k) and uw(k) > .35 * R(k) and lw(k) > .35 * R(k): out["long-legged doji"] = 0
    if B(k) / R(k) < .3 and uw(k) > .25 * R(k) and lw(k) > .25 * R(k) and not doji(k): out["spinning top"] = 0
    if lw(k) > 2 * B(k) and uw(k) < .3 * B(k) + 1e-9 and B(k) / R(k) > .1 and dtr: out["hammer"] = 1
    if lw(k) > 2 * B(k) and uw(k) < .3 * B(k) + 1e-9 and B(k) / R(k) > .1 and utr: out["hanging man"] = -1
    if uw(k) > 2 * B(k) and lw(k) < .3 * B(k) + 1e-9 and B(k) / R(k) > .1 and dtr: out["inverted hammer"] = 1
    if uw(k) > 2 * B(k) and lw(k) < .3 * B(k) + 1e-9 and B(k) / R(k) > .1 and utr: out["shooting star"] = -1
    if up(k) and B(k) / R(k) > .9: out["bullish marubozu"] = 1
    if dn(k) and B(k) / R(k) > .9: out["bearish marubozu"] = -1
    if up(k) and longb(k) and lw(k) < .05 * R(k) and dtr: out["bullish belt hold"] = 1
    if dn(k) and longb(k) and uw(k) < .05 * R(k) and utr: out["bearish belt hold"] = -1
    # ---- 2 bar
    j = i - 1
    if up(k) and dn(j) and c[k] >= o[j] and o[k] <= c[j] and B(k) > B(j): out["bullish engulfing"] = 1
    if dn(k) and up(j) and c[k] <= o[j] and o[k] >= c[j] and B(k) > B(j): out["bearish engulfing"] = -1
    if up(k) and dn(j) and top(k) < top(j) and bot(k) > bot(j) and longb(j): out["bullish harami"] = 1
    if dn(k) and up(j) and top(k) < top(j) and bot(k) > bot(j) and longb(j): out["bearish harami"] = -1
    if doji(k) and dn(j) and longb(j) and top(k) < top(j) and bot(k) > bot(j): out["bullish harami cross"] = 1
    if doji(k) and up(j) and longb(j) and top(k) < top(j) and bot(k) > bot(j): out["bearish harami cross"] = -1
    if dn(j) and longb(j) and up(k) and o[k] <= c[j] and c[k] > mid(j) and c[k] < o[j]: out["piercing line"] = 1
    if up(j) and longb(j) and dn(k) and o[k] >= c[j] and c[k] < mid(j) and c[k] > o[j]: out["dark cloud cover"] = -1
    tol = .05 * R(k)
    if dn(j) and up(k) and abs(l[k] - l[j]) < tol and dtr: out["tweezer bottom"] = 1
    if up(j) and dn(k) and abs(h[k] - h[j]) < tol and utr: out["tweezer top"] = -1
    if h[k] < h[j] and l[k] > l[j]: out["inside bar"] = 0
    if h[k] > h[j] and l[k] < l[j]: out["outside bar"] = 0
    if up(k) and dn(j) and o[k] == c[j] and c[k] > o[j]: out["bullish counterattack-ish (open=prev close, close>prev open)"] = 1
    if dn(k) and up(j) and o[k] == c[j] and c[k] < o[j]: out["bearish counterattack-ish (open=prev close, close<prev open)"] = -1
    if dn(j) and dn(k) and c[k] < c[j] and abs(c[k] - c[j]) < .15 * B(j) and longb(j): out["on-neck"] = -1
    # ---- 3 bar
    a = i - 2
    if dn(a) and longb(a) and small(j) and up(k) and c[k] > mid(a): out["morning star"] = 1
    if up(a) and longb(a) and small(j) and dn(k) and c[k] < mid(a): out["evening star"] = -1
    if dn(a) and longb(a) and doji(j) and up(k) and c[k] > mid(a): out["morning doji star"] = 1
    if up(a) and longb(a) and doji(j) and dn(k) and c[k] < mid(a): out["evening doji star"] = -1
    if up(a) and up(j) and up(k) and c[j] > c[a] and c[k] > c[j] and o[j] > o[a] and o[k] > o[j] and min(B(a), B(j), B(k)) / R(k) > .0 and all(B(x) / R(x) > .5 for x in (a, j, k)): out["three white soldiers"] = 1
    if dn(a) and dn(j) and dn(k) and c[j] < c[a] and c[k] < c[j] and o[j] < o[a] and o[k] < o[j] and all(B(x) / R(x) > .5 for x in (a, j, k)): out["three black crows"] = -1
    if dn(a) and up(j) and top(j) < top(a) and bot(j) > bot(a) and up(k) and c[k] > o[a]: out["three inside up"] = 1
    if up(a) and dn(j) and top(j) < top(a) and bot(j) > bot(a) and dn(k) and c[k] < o[a]: out["three inside down"] = -1
    if dn(a) and up(j) and c[j] >= o[a] and o[j] <= c[a] and up(k) and c[k] > c[j]: out["three outside up"] = 1
    if up(a) and dn(j) and c[j] <= o[a] and o[j] >= c[a] and dn(k) and c[k] < c[j]: out["three outside down"] = -1
    if doji(a) and doji(j) and doji(k): out["tri-star"] = 0
    if dn(a) and dn(j) and dn(k) and c[k] < c[j] < c[a] and up(i) is False and False: pass
    # ---- 3 up/down candles then 4th bar reverses through (three-line strike)
    if i >= 3:
        z = i - 3
        if up(z) and up(a) and up(j) and c[a] > c[z] and c[j] > c[a] and dn(k) and o[k] >= c[j] and c[k] < o[z]: out["bearish three-line strike"] = -1
        if dn(z) and dn(a) and dn(j) and c[a] < c[z] and c[j] < c[a] and up(k) and o[k] <= c[j] and c[k] > o[z]: out["bullish three-line strike"] = 1
    return out

def collect(kind):
    rows = []; base = []
    for date, data in days():
        mk = {(i, h): st.mean((d["close_price"][min(i + h, LAST)] / d["close_price"][i] - 1) * 100 for d in data.values())
              for i in range(LAST) for h in (1, 2, 99)}
        for sym, d in data.items():
            if kind == "cvd": o, h, l, c = d["open_cvd"], d["high_cvd"], d["low_cvd"], d["close_cvd"]
            else: o, h, l, c = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
            P = d["close_price"]
            for i in range(3, 10):
                f = {hh: (P[min(i + hh, LAST)] / P[i] - 1) * 100 - mk[i, hh] for hh in (1, 2, 99)}
                raw2 = (P[i + 2] / P[i] - 1) * 100
                base.append((date, i, abs(raw2)))
                for name, dr in detect(o, h, l, c, i).items():
                    rows.append((name, dr, date, i, f[1], f[2], f[99], abs(raw2)))
    return rows, base

def clus(rs, k, sign):
    g = collections.defaultdict(list)
    for r in rs: g[r[2], r[3]].append(sign * r[k])
    m = [st.mean(v) for v in g.values()]
    x = [sign * r[k] for r in rs]
    return len(x), st.mean(x), (tstat(m) if len(m) > 5 else 0), sum(v > 0 for v in x) / len(x) * 100

def run(kind):
    rows, base = collect(kind)
    dates = sorted({r[2] for r in rows}, key=lambda s: s[6:] + s[3:5] + s[:2]); disc, test = set(dates[:4]), set(dates[4:])
    bg = collections.defaultdict(list)
    for d_, i, a in base: bg[d_, i].append(a)
    by = collections.defaultdict(list)
    for r in rows: by[r[0], r[1]].append(r)
    res = []
    for (name, dr), rs in by.items():
        if len(rs) < 100: continue
        if dr:
            a = clus([r for r in rs if r[2] in disc], 5, dr); b = clus([r for r in rs if r[2] in test], 5, dr)
            res.append((name, dr, clus(rs, 4, dr), clus(rs, 5, dr), a, b, clus(rs, 6, dr)))
        else:  # neutral: |ret| minus same-bar mean |ret|
            def vol(sub):
                g = collections.defaultdict(list)
                for r in sub: g[r[2], r[3]].append(r[7] - st.mean(bg[r[2], r[3]]))
                m = [st.mean(v) for v in g.values()]
                x = [r[7] - st.mean(bg[r[2], r[3]]) for r in sub]
                return len(x), st.mean(x), tstat(m) if len(m) > 5 else 0, 0
            res.append((name, 0, vol(rs), vol(rs), vol([r for r in rs if r[2] in disc]), vol([r for r in rs if r[2] in test]), vol(rs)))
    return res

if __name__ == "__main__":
    out = {}
    for kind in ("cvd", "price"):
        res = run(kind); out[kind] = res
        D = [r for r in res if r[1]]; N = [r for r in res if not r[1]]
        print(f"\n===== {kind.upper()} candles: {len(D)} directional patterns (signed 2-bar excess %, clustered t), n>=100 =====")
        print(f"{'pattern':40s}{'dir':>4s}{'n':>7s} | {'1-bar':>8s} | {'2-bar':>8s} {'t':>5s} {'hit%':>5s} | {'DISC':>7s} {'t':>5s} | {'TEST':>7s} {'t':>5s} | {'to close':>8s}")
        for r in sorted(D, key=lambda r: -abs(r[3][2])):
            print(f"{r[0]:40s}{r[1]:+4d}{r[3][0]:7d} | {r[2][1]:+.3f}% | {r[3][1]:+.3f}% {r[3][2]:+5.1f} {r[3][3]:5.1f} | {r[4][1]:+.3f} {r[4][2]:+5.1f} | {r[5][1]:+.3f} {r[5][2]:+5.1f} | {r[6][1]:+.3f}%")
        sig = [r for r in D if abs(r[4][2]) >= 2]
        rep = [r for r in sig if r[4][1] * r[5][1] > 0 and abs(r[5][2]) >= 1.65]
        thr = 2.0 if True else 0
        print(f"-> discovery |t|>=2: {len(sig)}/{len(D)} (chance ~{len(D)*.05:.1f}); replicated in test: {len(rep)}", [r[0] for r in rep])
        pooled = [(r[3][0], r[3][1], r[1]) for r in D]
        w = sum(n for n, _, _ in pooled); print(f"-> pattern-weighted mean signed 2-bar excess: {sum(n*m for n,m,_ in pooled)/w:+.4f}%  (all {w} signals)")
        print(f"\n{kind.upper()} neutral patterns: |2-bar move| minus baseline (%)")
        for r in sorted(N, key=lambda r: -abs(r[3][2])):
            print(f"  {r[0]:30s} n={r[3][0]:6d} {r[3][1]:+.3f}% t{r[3][2]:+5.1f} | disc {r[4][1]:+.3f} t{r[4][2]:+4.1f} | test {r[5][1]:+.3f} t{r[5][2]:+4.1f}")
