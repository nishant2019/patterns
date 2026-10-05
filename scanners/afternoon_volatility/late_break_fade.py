"""Fading late breakouts, on ALL 23 days (no watchlist history needed). Rule fixed in advance (E4 from breakout_entries.py):
  signal : the 14:45 bar closes above the highest high / below the lowest low of every bar before it (day so far incl. the 14:15 bar)
  trade  : FADE it - short after an up-break, long after a down-break; enter at the 15:15 open, exit at the 15:15 bar close (last bar of the day, a 15-minute bar)
  cost   : 0.06% round trip (sensitivity 0.03 / 0.10 shown)
Reported: pooled, first/second half of the days, by side, by size of the break, by 14:45-bar volume, by market direction, versus placebos
(fade of ANY 14:45 bar direction, fade of non-breakout bars) to see whether the breakout adds anything. t clustered by day.
"""
import collections, math, os, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import afternoon_vol_scanner as A
M = A.M; COST = 0.06

def tt(x): return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else float("nan")

def events():
    data = M.load_all(); out = []
    for sym, ds in data.items():
        for day, bars in ds.items():
            ix = {b[0]: i for i, b in enumerate(bars)}
            if "14:45" not in ix or "15:15" not in ix or bars[-1][0] != "15:15": continue
            i = ix["14:45"]; before = bars[:i]
            if len(before) < 10 or min(b[1] for b in bars) <= 0: continue
            hi = max(b[2] for b in before); lo = min(b[3] for b in before); b45 = bars[i]; b15 = bars[ix["15:15"]]
            c = b45[4]; rng = [(b[2] - b[3]) / b[1] * 100 for b in before]; med = st.median(rng)
            sig = 1 if c > hi else (-1 if c < lo else 0)
            ret = (b15[4] / b15[1] - 1) * 100            # long return of the last bar from its open
            gap = (b15[1] / c - 1) * 100                  # signal close -> entry open
            dist = ((c - hi) / hi * 100 if sig > 0 else (lo - c) / lo * 100) if sig else 0
            out.append(dict(sym=sym, day=day, sig=sig, ret=ret, gap=gap, dist=dist, med=med, v45=b45[5] / max(st.mean(b[5] for b in before), 1),
                            body=(b45[4] - b45[1]) / b45[1] * 100, close_pos=(c - b45[3]) / max(b45[2] - b45[3], 1e-9)))
    return out

def summarize(label, evs, days, cost=COST, side_key="sig"):
    """fade return = -sig * ret ; per-day means -> t"""
    g = collections.defaultdict(list)
    for e in evs: g[e["day"]].append(-e[side_key] * e["ret"] - cost)
    dm = [st.mean(v) for d, v in g.items() if len(v) >= 3]
    allv = [x for v in g.values() for x in v]
    if len(allv) < 20 or len(dm) < 4: print(f"  {label:44s} n={len(allv)}"); return None
    gross = st.mean(allv) + cost
    print(f"  {label:44s} n={len(allv):5d} gross {gross:+.3f}%  net {st.mean(allv):+.3f}%  hit(net>0) {st.mean(1 if x > 0 else 0 for x in allv)*100:4.1f}%  t {tt(dm):+5.1f}  days+ {sum(x > 0 for x in dm)}/{len(dm)}")
    return st.mean(allv), tt(dm)

def main():
    evs = events(); days = sorted({e["day"] for e in evs}); n = len(days); h = n // 2
    mu = collections.defaultdict(list)
    for e in evs: mu[e["day"]].append(e["ret"])
    mk = {d: st.mean(v) for d, v in mu.items()}
    brk = [e for e in evs if e["sig"] != 0]
    print(f"{len(evs)} stock-days over {n} days ({days[0]}..{days[-1]}); late breakouts (E4): {len(brk)} ({len(brk)/len(evs)*100:.1f}% of stock-days)\n")
    print("POOLED, fading the breakout (short up-breaks, long down-breaks), enter 15:15 open, exit close:")
    summarize("all days", brk, days)
    for c in (0.03, 0.10): summarize(f"cost sensitivity {c}%", brk, days, cost=c)
    print("\nBy half (first {} / second {} days):".format(h, n - h))
    summarize("first half", [e for e in brk if e["day"] in days[:h]], days); summarize("second half", [e for e in brk if e["day"] in days[h:]], days)
    for k in range(0, n, 6): summarize(f"days {k+1}-{min(k+6, n)}", [e for e in brk if e["day"] in days[k:k + 6]], days)
    print("\nBy side:")
    summarize("up-breaks (fade = short)", [e for e in brk if e["sig"] > 0], days); summarize("down-breaks (fade = long)", [e for e in brk if e["sig"] < 0], days)
    print("\nBy break size (distance beyond the level, terciles):")
    s = sorted(e["dist"] for e in brk); t1, t2 = s[len(s) // 3], s[2 * len(s) // 3]
    summarize(f"small (<= {t1:.2f}%)", [e for e in brk if e["dist"] <= t1], days); summarize("medium", [e for e in brk if t1 < e["dist"] <= t2], days); summarize(f"large (> {t2:.2f}%)", [e for e in brk if e["dist"] > t2], days)
    print("\nBy 14:45 bar volume vs the day's earlier average:")
    summarize("volume < 1.5x", [e for e in brk if e["v45"] < 1.5], days); summarize("volume >= 1.5x", [e for e in brk if e["v45"] >= 1.5], days); summarize("volume >= 2.5x", [e for e in brk if e["v45"] >= 2.5], days)
    print("\nBy close position inside the 14:45 bar (breaks that closed on the extreme vs pulled back):")
    summarize("closed in the top/bottom 20% of its bar", [e for e in brk if (e["sig"] > 0 and e["close_pos"] >= .8) or (e["sig"] < 0 and e["close_pos"] <= .2)], days)
    summarize("closed elsewhere", [e for e in brk if not ((e["sig"] > 0 and e["close_pos"] >= .8) or (e["sig"] < 0 and e["close_pos"] <= .2))], days)
    print("\nBy market direction that day (mean last-bar return of all stocks):")
    summarize("market last bar up", [e for e in brk if mk[e["day"]] > 0], days); summarize("market last bar down", [e for e in brk if mk[e["day"]] <= 0], days)
    print("\nMarket-neutral version (subtract the day's mean last-bar return from the fade P&L, side-adjusted):")
    g = collections.defaultdict(list)
    for e in brk: g[e["day"]].append(-e["sig"] * (e["ret"] - mk[e["day"]]))
    dm = [st.mean(v) for v in g.values() if len(v) >= 3]; print(f"  excess gross {st.mean([x for v in g.values() for x in v]):+.3f}%  t {tt(dm):+.1f}  days+ {sum(x > 0 for x in dm)}/{len(dm)}")
    print("\nPlacebos (same entry/exit):")
    summarize("fade EVERY 14:45 bar's direction (up bar -> short)", [dict(e, sig=(1 if e["body"] > 0 else -1)) for e in evs if e["body"] != 0], days)
    summarize("fade non-breakout 14:45 bars only", [dict(e, sig=(1 if e["body"] > 0 else -1)) for e in evs if e["sig"] == 0 and e["body"] != 0], days)
    summarize("CONTINUE the late breakout", [dict(e, sig=-e["sig"]) for e in brk], days)
    print("\nSlippage check: signal close -> entry open gap, in the fade direction (negative = the open already moved against the fade; avg % ):")
    print(f"  mean gap in fade direction {st.mean(-e['sig'] * e['gap'] for e in brk):+.3f}%  (positive = open already reverted toward the fade entry; this is included in the return above because entry is at the open)")
    print("\nPer-day fade net (%):")
    g = collections.defaultdict(list)
    for e in brk: g[e["day"]].append(-e["sig"] * e["ret"] - COST)
    print("  " + "  ".join(f"{d[5:]}:{st.mean(v):+.2f}({len(v)})" for d, v in sorted(g.items())))

if __name__ == "__main__":
    main()
