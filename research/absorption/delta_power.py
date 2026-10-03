"""Delta power vs price move per candle.

Per-bar delta = close_cvd - open_cvd. Price impact model fitted across every bar of every
stock-day (volatility-normalised):   move_n = b * delta% + c
    move_n = bar return % / master-bar range %      (so volatile and quiet stocks are comparable)
    delta% = bar delta as % of bar volume
Absorption score for a bar = how much LESS (or opposite) the price moved than that delta predicts,
signed so that positive = the delta was absorbed:
    A = -sign(delta) * (actual - predicted) / residual_std
A > 0 with negative delta = selling absorbed; A > 0 with positive delta = buying absorbed.
"""
import glob, os, sys, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import load
LAST = 11

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
            for i in range(LAST + 1):
                row = dict(date=date, sym=sym, i=i, t=d["Time"][i][11:16], delta=cc[i] - oc[i], dpct=(cc[i] - oc[i]) / V[i] * 100,
                           ret=(C[i] - O[i]) / O[i] * 100, hl=(H[i] - L[i]) / O[i] * 100, vol=V[i],
                           mn=(C[i] - O[i]) / O[i] * 100 / mr, hn=(H[i] - L[i]) / O[i] * 100 / mr)
                if 1 <= i < LAST:
                    row["f2"] = (C[min(i + 2, LAST)] - C[i]) / C[i] * 100 - mk2[i]
                    row["fe"] = (C[LAST] - C[i]) / C[i] * 100 - mke[i]
                out.append(row)
    return out

def ols(x, y):
    mx, my = st.mean(x), st.mean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    return b, my - b * mx

if __name__ == "__main__":
    R = bars()
    b, c = ols([r["dpct"] for r in R], [r["mn"] for r in R])
    res = [r["mn"] - (b * r["dpct"] + c) for r in R]; sd = st.pstdev(res)
    for r, e in zip(R, res):
        r["A"] = -(1 if r["delta"] > 0 else -1) * e / sd
    mean_mn = st.mean(r["mn"] for r in R)
    r2 = 1 - sum(e * e for e in res) / sum((r["mn"] - mean_mn) ** 2 for r in R)
    print(f"{len(R)} bars. Price impact: normalised move = {b:.4f} x delta% + {c:+.4f}  (R^2 {r2:.2f}: delta explains {100*r2:.0f}% of bar-to-bar price movement)")
    print(f"  +10 points of delta % moves a bar by about {b*10:.2f} of the master-bar range")
    # TCS table
    print("\nTCS 28-09: delta power vs move per candle")
    print("time   delta     delta%vol  ret%    HL%    move/master  predicted  A(absorb)  reading")
    for r in R:
        if r["sym"] == "TCS" and r["date"] == "28-09-2026":
            pred = b * r["dpct"] + c
            read = "" 
            if abs(r["dpct"]) >= 10 and r["A"] >= 1: read = ("SELLING absorbed" if r["delta"] < 0 else "BUYING absorbed")
            elif abs(r["dpct"]) >= 10 and r["A"] <= -1: read = ("sellers pushed price more than expected" if r["delta"] < 0 else "buyers pushed price more than expected")
            print(f"{r['t']} {r['delta']/1000:+7.1f}K {r['dpct']:+7.1f}   {r['ret']:+.2f}  {r['hl']:.2f}   {r['mn']:+.2f}     {pred:+.2f}     {r['A']:+.2f}     {read}")
    import pickle; pickle.dump((R, b, c, sd), open(os.path.join(HERE, "_dp.pkl"), "wb"))
