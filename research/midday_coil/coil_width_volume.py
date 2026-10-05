"""New hypotheses on the midday coil (decision 14:15, point-in-time; 23 days of 30-min OHLCV).
Pre-registered before looking:
  H1 TIGHT  : relative width W = midday (hi-lo)/last / that stock's average of the same quantity over PRIOR days. Tight = bottom third of W among all stocks that day.
  H2 DRY-UP : relative volume Vr = mean volume of bars 11:15..13:45 / that stock's average of the same quantity over PRIOR days. Dry = bottom third of Vr that day.
  H3 BOTH   : tight and dry.
  (stocks need >=5 prior days; so the first 5 days are warm-up and only used for baselines)
Outcomes (from the 14:15 bar open, nothing earlier):
  EXPAND  = |move 14:15 open -> day close| / that stock's prior-day average of the same move   (>1 = bigger than usual)
  BREAK   = 14:15 bar closes beyond the midday high/low ;  BREAK2 = the 14:15 or the 14:45 bar closes beyond
  FOLLOW  = after a 14:15-close break: move from that close to the day close in the break direction, minus that day's mean stock move
Group-vs-rest difference computed within each day, then averaged across days (t clustered by day). Discovery = first half of the usable days, Test = second half.
"""
import sys, os, collections, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "midday_coil"))
import midday_coil_scanner as M

def tt(x):
    return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else float("nan")

def build():
    data = M.load_all(); rows = []
    for sym, ds in data.items():
        hist = collections.defaultdict(list)
        for day in sorted(ds):
            bars = ds[day]; r = M.scan_bars(bars, "14:15")
            tb = [b for b in bars if b[0] == "14:15"]; nb = [b for b in bars if b[0] == "14:45"]; late = [b for b in bars if b[0] > "14:15"]
            if not r or not tb or not nb or not late: continue
            tb, nb = tb[0], nb[0]
            mid = [b for b in bars if "11:15" <= b[0] < "14:15"]
            q = dict(width=r["width"], vol=st.mean(b[5] for b in mid), absmove=abs(late[-1][4] / tb[1] - 1) * 100)
            prior = {k: st.mean(v) for k, v in hist.items() if len(v) >= 5} if len(hist["width"]) >= 5 else None
            for k, v in q.items(): hist[k].append(v)
            if not prior or prior["width"] <= 0 or prior["vol"] <= 0 or prior["absmove"] <= 0: continue
            brk14 = 1 if tb[4] > r["hi"] else (-1 if tb[4] < r["lo"] else 0)
            brk45 = 1 if nb[4] > r["hi"] else (-1 if nb[4] < r["lo"] else 0)
            rows.append(dict(sym=sym, day=day, coils=r["coils"], W=q["width"] / prior["width"], Vr=q["vol"] / prior["vol"], expand=q["absmove"] / prior["absmove"],
                             brk14=brk14 != 0, brk2=(brk14 != 0 or brk45 != 0), ret_after=(late[-1][4] / tb[4] - 1) * 100, brk=brk14))
    return rows

def main():
    rows = build(); days = sorted({r["day"] for r in rows}); half = len(days) // 2
    disc, test = set(days[:half]), set(days[half:])
    print(f"{len(rows)} stock-days, {len(days)} usable days ({days[0]} .. {days[-1]}); discovery {len(disc)} days, test {len(test)} days")
    by = collections.defaultdict(list)
    for r in rows: by[r["day"]].append(r)
    for d, rs in by.items():
        ws = sorted(r["W"] for r in rs); vs = sorted(r["Vr"] for r in rs); n = len(rs)
        w3, v3 = ws[n // 3], vs[n // 3]
        mu = st.mean(r["ret_after"] for r in rs)
        for r in rs:
            r["tight"] = r["W"] <= w3; r["dry"] = r["Vr"] <= v3; r["both"] = r["tight"] and r["dry"]; r["fol"] = r["brk"] * (r["ret_after"] - mu) if r["brk"] else None
    groups = [("H1 TIGHT (bottom third relative width)", "tight"), ("H2 DRY-UP (bottom third relative volume)", "dry"), ("H3 BOTH tight and dry", "both")]
    metrics = [("EXPAND (|move| vs own usual)", "expand", 1), ("BREAK at 14:15 close (pct pts)", "brk14", 100), ("BREAK2 by 14:45 close (pct pts)", "brk2", 100), ("FOLLOW after break (excess %)", "fol", 1)]
    print("\nGroup minus rest, averaged over days (t clustered by day, days positive). Positive = group has MORE of the metric.")
    for gname, key in groups:
        print(f"\n{gname}")
        for mname, m, scale in metrics:
            line = f"  {mname:34s}"
            for lab, ds_ in (("ALL", set(days)), ("DISC", disc), ("TEST", test)):
                diffs = []; ng = 0
                for d in sorted(ds_):
                    g = [r[m] for r in by[d] if r[key] and r[m] is not None]; o = [r[m] for r in by[d] if not r[key] and r[m] is not None]
                    if len(g) >= 10 and len(o) >= 10: diffs.append((st.mean(g) - st.mean(o)) * scale); ng += len(g)
                line += f" | {lab} {st.mean(diffs):+7.3f} (t {tt(diffs):+4.1f}, {sum(x > 0 for x in diffs)}/{len(diffs)}d, n={ng})" if diffs else f" | {lab} n/a"
            print(line)
    print("\nAbsolute levels (all days): ")
    for gname, key in groups:
        g = [r for r in rows if r[key]]; o = [r for r in rows if not r[key]]
        print(f"  {gname[:40]:40s} n={len(g):5d}  EXPAND {st.mean(r['expand'] for r in g):.2f} vs {st.mean(r['expand'] for r in o):.2f} | BREAK@14:15 {st.mean(r['brk14'] for r in g)*100:.1f}% vs {st.mean(r['brk14'] for r in o)*100:.1f}% | BREAK by 14:45 {st.mean(r['brk2'] for r in g)*100:.1f}% vs {st.mean(r['brk2'] for r in o)*100:.1f}%")
    # inside the existing watchlist (3+ coil bars)
    wl = [r for r in rows if r["coils"] >= 3]
    print(f"\nInside the 3+ coil watchlist (n={len(wl)}): tight vs not / dry vs not, EXPAND and BREAK2:")
    for gname, key in groups[:3]:
        g = [r for r in wl if r[key]]; o = [r for r in wl if not r[key]]
        if len(g) > 30 and len(o) > 30: print(f"  {gname[:34]:34s} n={len(g):4d} EXPAND {st.mean(r['expand'] for r in g):.2f} vs {st.mean(r['expand'] for r in o):.2f} | BREAK2 {st.mean(r['brk2'] for r in g)*100:.1f}% vs {st.mean(r['brk2'] for r in o)*100:.1f}%")
    print("\nCorrelation of coil count with relative width / relative volume (all stock-days):")
    cc = [r["coils"] for r in rows]
    def corr(a, b):
        ma, mb = st.mean(a), st.mean(b); return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    print(f"  corr(coils, W) {corr(cc, [r['W'] for r in rows]):+.2f}   corr(coils, Vr) {corr(cc, [r['Vr'] for r in rows]):+.2f}   corr(W, Vr) {corr([r['W'] for r in rows], [r['Vr'] for r in rows]):+.2f}")

if __name__ == "__main__":
    main()
