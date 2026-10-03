"""Stock regime classifier for discretionary planning.

At a decision time t (default 11:15 = bar 4) every stock is placed in one regime from two point-in-time inputs:
  structure : where price sits vs the master (first) candle  - ABOVE / BELOW / inside (lower, middle, upper third)
  flow      : price vs net delta since the 09:45 open        - D = CVD change / volume (%), P = price change (%)
Regimes (statistics: research/regime/REPORT.md):
  A  Absorbed selling inside the range  (accumulation)   inside middle/upper third, D <= -10%, price flat/up
  B  Balanced inside the master range                    inside, any other flow (bias set by location)
  C  Extended breakout, buying confirmed (chase risk)    ABOVE master high, D >= +10%, price up
  C2 Breakout holding                                    ABOVE master high, other flow
  D  Breakdown, selling confirmed                        BELOW master low, D <= -10%, price down
  D2 Below master low, flow not confirming (reclaim?)    BELOW master low, other flow
  E  Buying absorbed (breaks lean down, no return edge)  D >= +10%, price flat/down, not already above the range
Usage:
    python regime_scanner.py data/CVD_Scanner_28-09-2026 [--time 11:15] [--regime A] [--card TCS] [-o regimes.csv]
"""
import argparse, csv, glob, os, sys, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab")); sys.path.insert(0, HERE)
from oab_scanner import load
from regime_study import structure, flow

TIMES = {"10:45": 3, "11:15": 4, "11:45": 5, "12:15": 6, "12:45": 7, "13:15": 8}

NAMES = {"A": "Absorbed selling inside range (accumulation)", "B": "Balanced inside the master range", "C": "Extended breakout, buying confirmed",
         "C2": "Breakout holding", "D": "Breakdown, selling confirmed", "D2": "Below master low, flow not confirming", "E": "Buying absorbed (breaks lean down, no return edge)"}

def classify(struct, fl):
    inside = struct.startswith("inside")
    if inside and "selling ABSORBED" in fl and ("upper" in struct or "middle" in struct): return "A"
    if struct.startswith("ABOVE"): return "C" if "buying, price up" in fl else "C2"
    if struct.startswith("BELOW"): return "D" if "selling, price down" in fl else "D2"
    if "buying ABSORBED" in fl: return "E"
    return "B"

def analyse(d, t):
    O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
    oc, cc, V = d["open_cvd"], d["close_cvd"], d["volume"]
    mH, mL = H[0], L[0]
    if mH <= mL or len(C) <= t: return None
    P = (C[t] - O[1]) / O[1] * 100
    D = (cc[t] - oc[1]) / sum(V[1:t + 1]) * 100
    s, f = structure(C[t], mH, mL), flow(P, D)
    half = (t + 1) // 2
    vt = sum(V[t - half + 1:t + 1]) / half / (sum(V[1:t - half + 1]) / max(t - half, 1))
    low_since = min(L[1:t + 1])
    return dict(regime=classify(s, f), struct=s, flow=f, D=round(D, 1), price_chg=round(P, 2), vol_trend=round(vt, 2),
                master_high=mH, master_low=mL, close=C[t], day_low=low_since, undercut=low_since < mL,
                pos=round((C[t] - mL) / (mH - mL), 2), inside=sum(H[i] <= mH and L[i] >= mL for i in range(1, t + 1)))

PLAN = {
 "A": ("Long bias while the range holds.", "Add on a close above the master high (or the range high of the coil) with volume rising; wait for a pullback that holds the master low / undercut low.", "Close below the master low (or below the undercut low if one formed): selling is no longer being absorbed."),
 "B": ("Neutral; side set by location.", "Upper third: watch the master high (about 80-90% of breaks are up); lower third: watch the master low (about 90% of breaks are down). Rising volume inside the coil = a decision is near.", "A close through either master edge changes the regime."),
 "C": ("Do not chase.", "Prefer to wait for a pullback into the master range that holds, or fade only on signs of failure (strong delta on the breakout bar that fails to extend).", "A close back inside the master range = failed breakout; a new high with delta efficiency collapsing = absorption at the top."),
 "C2": ("Trend intact, no extra edge.", "Pullbacks that hold the master high are the cleaner entries than the extension.", "Close back inside the master range."),
 "D": ("Avoid longs; weak.", "Only look for a long if selling stops being efficient (absorbed bars, CVD recovering) and price reclaims the master low.", "Reclaim of the master low with positive delta would change the regime."),
 "D2": ("Reclaim candidate, unproven.", "Needs a close back above the master low with delta confirming; otherwise the break lower is the default.", "No reclaim by the next bars."),
 "E": ("Neutral; breaks lean down but there is no return edge in the data.", "Only a close through the master low is meaningful (first breaks go down about 65% of the time).", "Price accepting above the master high with efficient buying."),
}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder"); ap.add_argument("--time", default="11:15"); ap.add_argument("--regime"); ap.add_argument("--card"); ap.add_argument("-o", "--output")
    a = ap.parse_args(); t = TIMES[a.time]
    rows = []
    for path in sorted(glob.glob(os.path.join(a.folder, "*.csv"))):
        try: d = load(path)
        except ValueError: continue
        r = analyse(d, t)
        if r:
            r["symbol"] = os.path.basename(path).rsplit("_", 1)[0]
            n = len(d["close_price"]); C = d["close_price"]
            r["to_close"] = round((C[min(12, n - 1)] - C[t]) / C[t] * 100, 2) if n > 11 else ""
            rows.append(r)
    counts = {k: sum(r["regime"] == k for r in rows) for k in NAMES}
    print(f"{a.folder} @ {a.time}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    sel = [r for r in rows if (not a.regime or r["regime"] == a.regime)]
    if a.card:
        r = next(r for r in rows if r["symbol"] == a.card)
        bias, trig, inv = PLAN[r["regime"]]
        print(f"\n{r['symbol']} @ {a.time}: REGIME {r['regime']} - {NAMES[r['regime']]}\n  structure: {r['struct']} (close {r['close']}, master {r['master_low']}-{r['master_high']}, {r['inside']}/{t} bars inside)\n  flow: {r['flow']} (delta {r['D']:+.0f}% of volume since 09:45, price {r['price_chg']:+.2f}%), volume trend {r['vol_trend']}x{'  [undercut low %s]' % r['day_low'] if r['undercut'] else ''}\n  bias: {bias}\n  plan: {trig}\n  invalidation: {inv}")
    elif a.regime:
        for r in sorted(sel, key=lambda r: -r["pos"]):
            print(f"  {r['symbol']:12s} {r['struct']:20s} D {r['D']:+5.0f}% price {r['price_chg']:+.2f}% vol {r['vol_trend']:.1f}x  master {r['master_low']}-{r['master_high']} close {r['close']}" + (f"  -> to close {r['to_close']:+.2f}%" if r["to_close"] != "" else ""))
    if a.output and rows:
        with open(a.output, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

if __name__ == "__main__":
    main()
