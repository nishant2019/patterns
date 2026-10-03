"""Delta efficiency: how much price movement a given amount of net delta actually produces.

For a window of bars (rolling last N bars, or the day so far after the opening bar):
    D  = net delta over the window, as % of the window's volume          (CVD change / volume * 100)
    P  = price return over the window (close_end / open_start - 1) in %, divided by the stock's master-bar
         range % (so quiet and volatile stocks are comparable)
    beta = pooled slope of P on D across every window of every stock-day (price per point of delta)
    DE = P / (beta * D)
Reading:  DE ~ 1  normal: price moved as much as delta usually moves it
          DE > 1.5  over-efficient: price ran further than the delta explains (thin book / momentum)
          0 < DE < 0.5  inefficient: delta was mostly absorbed (price barely moved)
          DE <= 0  price moved AGAINST the delta (absorption / opposite flow)
Only windows with |D| >= 10% are classified (below that there is no delta to be efficient or not).
"""
import glob, os, sys, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import load
LAST, N, DMIN = 11, 4, 10.0

def rows_for_all():
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
            O, H, L, C, oc, cc, V = (d[k] for k in ("open_price", "high_price", "low_price", "close_price", "open_cvd", "close_cvd", "volume"))
            mr = (H[0] - L[0]) / O[0] * 100
            if mr <= 0: continue
            for t in range(N - 1, LAST):               # rolling window of N bars ending at bar t
                s = t - N + 1
                for kind, a in (("roll", s), ("day", 1)):
                    if kind == "day" and t < 3: continue
                    D = (cc[t] - oc[a]) / sum(V[a:t + 1]) * 100
                    P = (C[t] - O[a]) / O[a] * 100 / mr
                    row = dict(date=date, sym=sym, t=t, tm=d["Time"][t][11:16], kind=kind, D=D, P=P, Praw=(C[t] - O[a]) / O[a] * 100)
                    if t < LAST:
                        row["f2"] = (C[min(t + 2, LAST)] - C[t]) / C[t] * 100 - mk2[t]
                        row["fe"] = (C[LAST] - C[t]) / C[t] * 100 - mke[t]
                    out.append(row)
    return out

def tt(x):
    return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else 0

def label(de):
    if de is None: return "no delta (|D|<10%)"
    if de <= 0: return "AGAINST delta"
    if de < .5: return "inefficient (absorbed)"
    if de <= 1.5: return "normal"
    return "over-efficient"


def show(R, sym, date):
    """Print the rolling-4-bar and since-09:45 efficiency series for one stock-day."""
    roll = {r["t"]: r for r in R if r["sym"] == sym and r["date"] == date and r["kind"] == "roll"}
    day = {r["t"]: r for r in R if r["sym"] == sym and r["date"] == date and r["kind"] == "day"}
    print(f"{sym} {date}: delta efficiency (DE 1.0 = price moved as much as delta normally moves it)")
    print("bar   | rolling 4 bars: D%vol  price%   DE    reading                | since 09:45: D%vol  price%   DE    reading")
    for t in sorted(roll):
        a, b = roll[t], day.get(t)
        f = lambda x: "  n/a" if x["DE"] is None else f"{x['DE']:+5.2f}"
        print(f"{a['tm']} |   {a['D']:+7.1f}   {a['Praw']:+.2f}  {f(a)}  {label(a['DE']):22s} |" + (f"  {b['D']:+7.1f}   {b['Praw']:+.2f}  {f(b)}  {label(b['DE'])}" if b else ""))


if __name__ == "__main__":
    R = rows_for_all()
    beta = {}
    for kind in ("roll", "day"):
        g = [r for r in R if r["kind"] == kind]
        mx, my = st.mean(r["D"] for r in g), st.mean(r["P"] for r in g)
        beta[kind] = sum((r["D"] - mx) * (r["P"] - my) for r in g) / sum((r["D"] - mx) ** 2 for r in g)
        c = sum((r["D"] - mx) * (r["P"] - my) for r in g) / math.sqrt(sum((r["D"] - mx) ** 2 for r in g) * sum((r["P"] - my) ** 2 for r in g))
        print(f"{kind:4s} windows n={len(g):6d}: price (in master ranges) per 1 point of delta% = {beta[kind]:.4f}; correlation of window price move with window delta = {c:.2f}")
    for r in R:
        r["DE"] = r["P"] / (beta[r["kind"]] * r["D"]) if abs(r["D"]) >= DMIN else None
    if len(sys.argv) == 4 and sys.argv[1] == "show":
        show(R, sys.argv[2], sys.argv[3]); sys.exit()
    import pickle; pickle.dump((R, beta), open(os.path.join(HERE, "_de.pkl"), "wb"))
    for kind in ("roll", "day"):
        g = [r for r in R if r["kind"] == kind and r["DE"] is not None]
        print(f"\n===== {kind.upper()} efficiency, |D| >= {DMIN:.0f}%: n={len(g)}")
        buckets = [("price moved AGAINST delta (DE <= 0)", lambda x: x <= 0), ("inefficient, 0 < DE < 0.5", lambda x: 0 < x < .5), ("normal, 0.5-1.5", lambda x: .5 <= x <= 1.5), ("over-efficient, DE > 1.5", lambda x: x > 1.5)]
        print(f"{'':40s} {'delta SELLING (D<=-10)':>34s} | {'delta BUYING (D>=+10)':>34s}   (fwd vs median stock: 2 bars / to close, days+ for close)")
        for lab, fn in buckets:
            line = f"{lab:40s}"
            for sgn in (-1, 1):
                s = [r for r in g if sgn * r["D"] > 0 and fn(r["DE"]) and "f2" in r]
                if len(s) < 15: line += f"{'n=%d' % len(s):>35s} |"; continue
                dd = {}; [dd.setdefault(r["date"], []).append(r["fe"]) for r in s]
                line += f" n={len(s):5d} {st.mean(r['f2'] for r in s):+.3f}/{st.mean(r['fe'] for r in s):+.3f} (t {tt([r['fe'] for r in s]):+.1f}) {sum(st.mean(v) > 0 for v in dd.values())}/{len(dd)} |"
            print(line)
        b2 = [r for r in R if r["kind"] == kind and "f2" in r]
        print(f"baseline all windows: {st.mean(r['f2'] for r in b2):+.3f}/{st.mean(r['fe'] for r in b2):+.3f}")
