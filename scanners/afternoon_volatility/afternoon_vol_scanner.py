"""Volatility-ranked afternoon watchlist (30-minute bars). Built from research/midday_coil (loud/wide midday -> bigger afternoon move; direction NOT predicted).
At decision time T (default 14:15; only bars starting before T are used):
  W  = midday range  (high-low of bars 11:15..T-30, as % of last close) / the stock's average of the same quantity over PRIOR days
  Vr = midday mean bar volume / the stock's average of the same quantity over PRIOR days
  SCORE = mean of the day's percentile ranks of W and Vr (0-100). Needs >= 5 prior days. Frozen, nothing tuned.
  Tiers: HOT = W and Vr both in the day's top third; WARM = score >= 66.7 but not both; others are not listed unless --all.
Also printed: the stock's USUAL afternoon move (average |14:15 open -> close| % over prior days) for sizing stops/targets, midday and day levels, VWAP.
Direction is not predicted: pick the side from your own setup (regime, levels, order flow); this list says where movement is likely.
  python scanners/afternoon_volatility/afternoon_vol_scanner.py --date 2026-10-05 [--top 40] [--csv out.csv] [--all]
  python scanners/afternoon_volatility/afternoon_vol_scanner.py --backtest
"""
import argparse, collections, csv, math, os, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "midday_coil"))
import midday_coil_scanner as M
MIN_PRIOR = 5

def features(data, T="14:15"):
    """list of dict per stock-day: decision-time features + (if the afternoon exists) outcomes."""
    rows = []
    for sym, ds in data.items():
        hist = collections.defaultdict(list)
        for day in sorted(ds):
            bars = ds[day]; seen = [b for b in bars if b[0] < T]
            if len(seen) < 8 or seen[0][0] != "09:15": continue
            mid = [b for b in seen if "11:15" <= b[0]]
            if len(mid) < 3 or min(b[1] for b in seen) <= 0: continue
            last = seen[-1][4]; hi = max(b[2] for b in mid); lo = min(b[3] for b in mid)
            width = (hi - lo) / last * 100; vol = st.mean(b[5] for b in mid)
            late = [b for b in bars if b[0] >= T]; tb = [b for b in bars if b[0] == T]
            absmove = abs(late[-1][4] / late[0][1] - 1) * 100 if late and late[0][0] == T else None
            prior = {k: st.mean(v) for k, v in hist.items()} if len(hist["width"]) >= MIN_PRIOR and len(hist["absmove"]) >= MIN_PRIOR else None
            hist["width"].append(width); hist["vol"].append(vol)
            if absmove is not None: hist["absmove"].append(absmove)
            if not prior or min(prior["width"], prior["vol"], prior["absmove"]) <= 0: continue
            tp = [(b[2] + b[3] + b[4]) / 3 for b in seen]; vw = sum(t * b[5] for t, b in zip(tp, seen)) / max(sum(b[5] for b in seen), 1)
            rows.append(dict(sym=sym, day=day, W=width / prior["width"], Vr=vol / prior["vol"], usual=prior["absmove"], absmove=absmove, last=last, hi=hi, lo=lo,
                             dhi=max(b[2] for b in seen), dlo=min(b[3] for b in seen), vwap=vw, turnover=sum(b[5] * b[4] for b in seen) / 1e7,
                             expand=None if absmove is None else absmove / prior["absmove"]))
    return rows

def score_day(rs):
    n = len(rs)
    def pr(key):
        order = sorted(range(n), key=lambda i: rs[i][key]); p = [0.0] * n
        for rank, i in enumerate(order): p[i] = rank / (n - 1) * 100 if n > 1 else 50
        return p
    pw, pv = pr("W"), pr("Vr")
    for i, r in enumerate(rs):
        r["score"] = (pw[i] + pv[i]) / 2; r["pw"] = pw[i]; r["pv"] = pv[i]
        r["tier"] = "HOT" if pw[i] >= 200 / 3 and pv[i] >= 200 / 3 else ("WARM" if r["score"] >= 200 / 3 else "-")
    return rs

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date"); ap.add_argument("--time", default="14:15"); ap.add_argument("--top", type=int, default=40); ap.add_argument("--csv"); ap.add_argument("--all", action="store_true"); ap.add_argument("--backtest", action="store_true")
    a = ap.parse_args(); data = M.load_all(); rows = features(data, a.time); by = collections.defaultdict(list)
    for r in rows: by[r["day"]].append(r)
    for d in by: score_day(by[d])
    if a.backtest: backtest(by); return
    day = a.date or max(by); rs = sorted(by[day], key=lambda r: -r["score"])
    sel = rs if a.all else [r for r in rs if r["tier"] != "-"]
    print(f"Afternoon volatility watchlist {day} @ {a.time}: {len(rs)} scored, HOT {sum(r['tier']=='HOT' for r in rs)}, WARM {sum(r['tier']=='WARM' for r in rs)} (showing top {min(a.top, len(sel))})")
    print(f"{'Tier':5s}{'Symbol':13s}{'Score':>6s}{'Wide x':>8s}{'Vol x':>7s}{'Usual PM%':>10s}{'Last':>10s}{'MidLow':>10s}{'MidHigh':>10s}{'DayLow':>10s}{'DayHigh':>10s}{'VWAP':>10s}{'Turn Cr':>9s}")
    for r in sel[:a.top]:
        print(f"{r['tier']:5s}{r['sym']:13s}{r['score']:6.0f}{r['W']:8.2f}{r['Vr']:7.2f}{r['usual']:10.2f}{r['last']:10.2f}{r['lo']:10.2f}{r['hi']:10.2f}{r['dlo']:10.2f}{r['dhi']:10.2f}{r['vwap']:10.2f}{r['turnover']:9.1f}")
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["tier", "symbol", "score", "wide_x", "vol_x", "usual_pm_pct", "last", "mid_low", "mid_high", "day_low", "day_high", "vwap", "turnover_cr"])
            for r in sel: w.writerow([r["tier"], r["sym"], round(r["score"], 1), round(r["W"], 2), round(r["Vr"], 2), round(r["usual"], 3), r["last"], r["lo"], r["hi"], r["dlo"], r["dhi"], round(r["vwap"], 2), round(r["turnover"], 1)])

def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
        for k, i in enumerate(o): r[i] = k
        return r
    a, b = rk(x), rk(y); ma = mb = (len(x) - 1) / 2
    return sum((p - ma) * (q - mb) for p, q in zip(a, b)) / math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))

def tt(x): return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else float("nan")

def backtest(by):
    days = sorted(d for d in by if all(r["expand"] is not None for r in by[d][:1])); half = len(days) // 2
    print(f"Backtest {len(days)} days (decision 14:15), {sum(len(by[d]) for d in days)} stock-days. EXPAND = afternoon |move| / the stock's own usual; PM move = |14:15 open -> close| in %.")
    print(f"\nBy score decile (D10 = highest score), all days:")
    dec = collections.defaultdict(list)
    for d in days:
        rs = sorted([r for r in by[d] if r["expand"] is not None], key=lambda r: r["score"]); n = len(rs)
        for i, r in enumerate(rs): dec[min(i * 10 // n, 9) + 1].append(r)
    print(f"{'decile':>7s}{'n':>7s}{'EXPAND':>8s}{'PM move%':>10s}{'usual%':>8s}")
    for k in range(1, 11):
        v = dec[k]; print(f"{k:7d}{len(v):7d}{st.mean(r['expand'] for r in v):8.2f}{st.mean(r['absmove'] for r in v):10.2f}{st.mean(r['usual'] for r in v):8.2f}")
    print("\nRank correlation score vs EXPAND per day (mean of daily Spearman, t clustered by day, days positive):")
    for lab, ds_ in (("ALL", days), ("DISC", days[:half]), ("TEST", days[half:])):
        cs = [spearman([r["score"] for r in by[d] if r["expand"] is not None], [r["expand"] for r in by[d] if r["expand"] is not None]) for d in ds_]
        print(f"  {lab:5s} {st.mean(cs):+.3f}  (t {tt(cs):+.1f}, {sum(c > 0 for c in cs)}/{len(cs)} days)")
    print("\nTier vs rest (afternoon move, % and x usual), by half:")
    for lab, ds_ in (("ALL", days), ("DISC", days[:half]), ("TEST", days[half:])):
        for tier in ("HOT", "WARM", "-"):
            v = [r for d in ds_ for r in by[d] if r["tier"] == tier and r["expand"] is not None]
            print(f"  {lab:5s} {tier:5s} n={len(v):5d}  PM move {st.mean(r['absmove'] for r in v):.2f}%  EXPAND {st.mean(r['expand'] for r in v):.2f}  usual {st.mean(r['usual'] for r in v):.2f}%")
    # calibration: predicted move = usual x tier multiple, learned on discovery, checked on test
    mult = {t: st.mean(r["expand"] for d in days[:half] for r in by[d] if r["tier"] == t and r["expand"] is not None) for t in ("HOT", "WARM", "-")}
    print("\nCalibration: multiple of 'usual' learned on discovery:", {k: round(v, 2) for k, v in mult.items()})
    for t in ("HOT", "WARM", "-"):
        v = [r for d in days[half:] for r in by[d] if r["tier"] == t and r["expand"] is not None]
        pred = [r["usual"] * mult[t] for r in v]; act = [r["absmove"] for r in v]
        print(f"  TEST {t:5s} predicted PM move {st.mean(pred):.2f}%  actual {st.mean(act):.2f}%  (median actual / predicted {st.median(a / p for a, p in zip(act, pred)):.2f})")
    print("\nTurnover filter check: HOT tier EXPAND for turnover below / above the median (Rs crore):")
    allr = [r for d in days for r in by[d] if r["tier"] == "HOT" and r["expand"] is not None]; med = st.median(r["turnover"] for r in allr)
    for lab, f in (("below", lambda r: r["turnover"] < med), ("above", lambda r: r["turnover"] >= med)):
        v = [r for r in allr if f(r)]; print(f"  {lab} median {med:.0f} Cr: n={len(v)} EXPAND {st.mean(r['expand'] for r in v):.2f}")

if __name__ == "__main__":
    main()
