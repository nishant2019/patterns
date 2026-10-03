"""CVD candles vs price candles.

CVD candle for each bar = (open_cvd, high_cvd, low_cvd, close_cvd), exactly what the screenshot plots.
Tests (all point-in-time, outcome = return from the signal bar close to the 14:45 close minus the median stock):
  A. bar-level relationship: price candle colour x CVD candle colour, and CVD candle wicks
  B. structure: does the CVD candle chart break out of the MASTER candle's CVD range before / after price does?
"""
import glob, os, sys, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import load
LAST = 11

def days():
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]; data = {}
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try: d = load(p)
            except ValueError: continue
            if len(d["close_price"]) > LAST and d["Time"][LAST][11:16] == "14:45":
                data[os.path.basename(p).rsplit("_", 1)[0]] = d
        yield date, data

def tstat(x):
    return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else 0

def report(lab, rows, key="f2"):
    if len(rows) < 15: print(f"  {lab:58s} n={len(rows)}"); return
    x = [r[key] for r in rows]; dd = {}
    [dd.setdefault(r["date"], []).append(r[key]) for r in rows]
    print(f"  {lab:58s} n={len(rows):5d} {st.mean(x):+.3f}% (t {tstat(x):+.1f}) days+ {sum(st.mean(v) > 0 for v in dd.values())}/{len(dd)}")

if __name__ == "__main__":
    A = []; B = []
    for date, data in days():
        mk2 = [st.median((d["close_price"][min(i + 2, LAST)] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values()) for i in range(LAST)]
        mke = [st.median((d["close_price"][LAST] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values()) for i in range(LAST)]
        for sym, d in data.items():
            O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
            oc, hc, lc, cc, V = d["open_cvd"], d["high_cvd"], d["low_cvd"], d["close_cvd"], d["volume"]
            f = lambda i, h, mk: ((C[min(i + h, LAST)] - C[i]) / C[i] * 100) - mk[i]
            # ---- A: bar-level
            for i in range(1, LAST):
                crng = max(hc[i] - lc[i], 1e-9)
                A.append(dict(date=date, p_up=C[i] > O[i], c_up=cc[i] > oc[i],
                              up_w=(hc[i] - max(oc[i], cc[i])) / crng, lo_w=(min(oc[i], cc[i]) - lc[i]) / crng,
                              crange=crng / V[i] * 100, f2=f(i, 2, mk2), fe=f(i, 99, mke),
                              pret=(C[i] - O[i]) / O[i] * 100, cd=(cc[i] - oc[i]) / V[i] * 100))
            # ---- B: structure vs master (bar 0). CVD master range = [low_cvd0, high_cvd0]
            mH, mL, cH, cL = H[0], L[0], hc[0], lc[0]
            if mH <= mL or cH <= cL: continue
            cvd_first = price_first = None
            for i in range(1, LAST):
                p_out = 1 if C[i] > mH else (-1 if C[i] < mL else 0)
                c_out = 1 if cc[i] > cH else (-1 if cc[i] < cL else 0)
                if p_out and price_first is None: price_first = (i, p_out, c_out)
                if c_out and cvd_first is None: cvd_first = (i, c_out, p_out)
            for kind, ev in (("cvd_first", cvd_first), ("price_first", price_first)):
                if ev and ev[0] < LAST - 1:
                    i, s, other = ev
                    B.append(dict(date=date, kind=kind, k=i, side=s, other=other, f2=s * f(i, 2, mk2), fe=s * f(i, 99, mke),
                                  lead=(cvd_first and price_first and (cvd_first[0] < price_first[0])) or (cvd_first and not price_first)))
    print("=== A. Price candle colour x CVD candle colour (every bar 09:45-14:15; outcome vs median stock)")
    for pu in (True, False):
        for cu in (True, False):
            g = [r for r in A if r["p_up"] == pu and r["c_up"] == cu]
            report(f"price {'up  ' if pu else 'down'} / CVD {'up  ' if cu else 'down'}", g); report("   to close", g, "fe")
    print("  (divergent colours: price up/CVD down = effort sold into strength; price down/CVD up = buying into weakness)")
    print("\n=== A2. CVD candle wicks (share of the CVD candle's high-low range)")
    for lab, fn in (("CVD lower wick >= 60% (CVD sold off inside bar, recovered)", lambda r: r["lo_w"] >= .6),
                    ("CVD upper wick >= 60% (CVD spiked up inside bar, faded)", lambda r: r["up_w"] >= .6),
                    ("long CVD body, no wicks (both wicks < 15%)", lambda r: r["lo_w"] < .15 and r["up_w"] < .15)):
        report(lab, [r for r in A if fn(r)]); report("   to close", [r for r in A if fn(r)], "fe")
    print("\n=== B. Which breaks the MASTER candle's range first: price candles or CVD candles?")
    pf = [r for r in B if r["kind"] == "price_first"]; cf = [r for r in B if r["kind"] == "cvd_first"]
    print(f"stocks with a price break: {len(pf)}, with a CVD break: {len(cf)}")
    print("Direction-signed 2-bar / to-close return from the first break bar (vs median stock):")
    report("price breaks first (any)", pf); report("CVD breaks first (any)", cf)
    print("  When the CVD candle breaks out of its master range, was price already outside the master range?")
    report("CVD break, price still INSIDE master range  (CVD leads)", [r for r in cf if r["other"] == 0]); report("   to close", [r for r in cf if r["other"] == 0], "fe")
    report("CVD break, price already broke SAME direction", [r for r in cf if r["other"] == r["side"]]); report("   to close", [r for r in cf if r["other"] == r["side"]], "fe")
    report("CVD break, price broke OPPOSITE direction (divergence)", [r for r in cf if r["other"] == -r["side"]]); report("   to close", [r for r in cf if r["other"] == -r["side"]], "fe")
    report("price break, CVD still INSIDE its master range (price leads)", [r for r in pf if r["other"] == 0]); report("   to close", [r for r in pf if r["other"] == 0], "fe")
    report("price break with CVD already broken same dir (confirmed)", [r for r in pf if r["other"] == r["side"]]); report("   to close", [r for r in pf if r["other"] == r["side"]], "fe")
    report("price break, CVD broke OPPOSITE dir (divergence)", [r for r in pf if r["other"] == -r["side"]]); report("   to close", [r for r in pf if r["other"] == -r["side"]], "fe")
