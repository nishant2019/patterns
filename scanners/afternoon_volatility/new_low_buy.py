"""Buy new day lows made in the 14:45 bar (long only), 23 days. Hypothesis from late_break_fade.py (found post hoc, so treated with extra suspicion).
Signal (fixed): the 14:45 bar closes below the lowest low of every earlier bar that day. Trade: buy the 15:15 open, sell the 15:15 close (last bar, 15 minutes), cost 0.06%.
Checks: halves/thirds, leave-one-day-out, per-day-equal weighting, within-day permutation test against random same-day stocks, placebos
(any red 14:45 bar, near-low without a new low, wick-only new low), by liquidity, price, breadth of the day's new lows, and break size.
"""
import collections, math, os, random, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import afternoon_vol_scanner as A
M = A.M; COST = 0.06; random.seed(7)

def tt(x): return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else float("nan")

def events():
    data = M.load_all(); out = []
    for sym, ds in data.items():
        for day, bars in ds.items():
            ix = {b[0]: i for i, b in enumerate(bars)}
            if "14:45" not in ix or bars[-1][0] != "15:15" or "15:15" not in ix: continue
            i = ix["14:45"]; before = bars[:i]
            if len(before) < 10 or min(b[1] for b in bars) <= 0: continue
            lo = min(b[3] for b in before); hi = max(b[2] for b in before); b45 = bars[i]; b15 = bars[ix["15:15"]]
            rng = max(b45[2] - b45[3], 1e-9)
            out.append(dict(sym=sym, day=day, ret=(b15[4] / b15[1] - 1) * 100, close_low=b45[4] < lo, wick_low=(b45[3] < lo and b45[4] >= lo), red=b45[4] < b45[1],
                            near=(b45[4] - lo) / max(hi - lo, 1e-9) < 0.1 and b45[4] >= lo, dist=(lo - b45[4]) / lo * 100 if b45[4] < lo else 0,
                            lowerwick=(min(b45[1], b45[4]) - b45[3]) / rng, close_pos=(b45[4] - b45[3]) / rng, turnover=sum(b[5] * b[4] for b in before) / 1e7, price=b45[4],
                            v45=b45[5] / max(st.mean(b[5] for b in before), 1)))
    return out

def stats(label, evs, cost=COST, quiet=False):
    g = collections.defaultdict(list)
    for e in evs: g[e["day"]].append(e["ret"] - cost)
    dm = [st.mean(v) for v in g.values() if len(v) >= 3]; allv = [x for v in g.values() for x in v]
    if len(allv) < 20 or len(dm) < 4:
        if not quiet: print(f"  {label:46s} n={len(allv)}")
        return None
    r = (st.mean(allv), st.mean(dm), tt(dm), sum(x > 0 for x in dm), len(dm), len(allv))
    if not quiet: print(f"  {label:46s} n={r[5]:5d} gross {r[0]+cost:+.3f}%  net {r[0]:+.3f}%  day-equal net {r[1]:+.3f}%  t {r[2]:+4.1f}  days+ {r[3]}/{r[4]}  hit {st.mean(1 if x > 0 else 0 for x in allv)*100:4.1f}%")
    return r

def main():
    E = events(); days = sorted({e["day"] for e in E}); n = len(days)
    mk = collections.defaultdict(list)
    for e in E: mk[e["day"]].append(e["ret"])
    mkt = {d: st.mean(v) for d, v in mk.items()}
    sig = [e for e in E if e["close_low"]]
    print(f"{len(E)} stock-days, {n} days; signal events: {len(sig)}\n")
    print("MAIN (buy at 15:15 open, sell at close):")
    stats("new day low by 14:45 close", sig)
    for c in (0.03, 0.10): stats(f"  cost {c}%", sig, cost=c)
    print("\nStability:")
    h = n // 2; stats("first 11 days", [e for e in sig if e["day"] in days[:h]]); stats("last 12 days", [e for e in sig if e["day"] in days[h:]])
    for k in range(0, n, 8): stats(f"days {k+1}-{min(k+8, n)}", [e for e in sig if e["day"] in days[k:k + 8]])
    byday = collections.Counter(e["day"] for e in sig)
    print("  events per day, top 5:", byday.most_common(5))
    print("  leave-one-day-out net range:", end=" ")
    loo = [stats("", [e for e in sig if e["day"] != d], quiet=True) for d in days]
    loo = [x for x in loo if x]; print(f"{min(x[0] for x in loo):+.3f}% .. {max(x[0] for x in loo):+.3f}%, day-equal t range {min(x[2] for x in loo):+.1f} .. {max(x[2] for x in loo):+.1f}")
    # permutation test: within each day, draw the same number of random stocks (excluding nothing) and compare mean last-bar return
    obs = st.mean(e["ret"] for e in sig); byd = collections.defaultdict(list)
    for e in E: byd[e["day"]].append(e["ret"])
    cnt = collections.Counter(e["day"] for e in sig); sims = []
    for _ in range(2000):
        v = []
        for d, k in cnt.items(): v += random.sample(byd[d], k)
        sims.append(st.mean(v))
    p = sum(s >= obs for s in sims) / len(sims)
    print(f"\nPermutation test (random same-day stocks, same count per day): observed mean gross {obs:+.3f}%, random mean {st.mean(sims):+.3f}% (sd {st.pstdev(sims):.3f}), one-sided p = {p:.3f}")
    print("\nPlacebos (long, same entry/exit):")
    stats("any red 14:45 bar", [e for e in E if e["red"]]); stats("near the day low, no new low (bottom 10% of range)", [e for e in E if e["near"]])
    stats("wick-only new low (low < prior lows, close above)", [e for e in E if e["wick_low"]]); stats("ALL stocks (baseline = last-bar drift)", E)
    print("\nBy context:")
    s = sorted(e["turnover"] for e in sig); t1, t2 = s[len(s) // 3], s[2 * len(s) // 3]
    stats(f"low turnover (<{t1:.0f} Cr)", [e for e in sig if e["turnover"] <= t1]); stats("mid turnover", [e for e in sig if t1 < e["turnover"] <= t2]); stats(f"high turnover (>{t2:.0f} Cr)", [e for e in sig if e["turnover"] > t2])
    stats("price < 200", [e for e in sig if e["price"] < 200]); stats("price 200-1000", [e for e in sig if 200 <= e["price"] < 1000]); stats("price >= 1000", [e for e in sig if e["price"] >= 1000])
    breadth = {d: byday[d] / len(byd[d]) * 100 for d in days}
    med = st.median(breadth.values()); print(f"  breadth = % of stocks making a new low at 14:45 (median day {med:.1f}%)")
    stats("broad-selloff days (breadth above median)", [e for e in sig if breadth[e["day"]] > med]); stats("narrow days (breadth below median)", [e for e in sig if breadth[e["day"]] <= med])
    stats("market down into the close (14:45 bar weak days) n/a: use next-bar market up", [e for e in sig if mkt[e["day"]] > 0]); stats("days when market last bar down", [e for e in sig if mkt[e["day"]] <= 0])
    stats("lower wick on the 14:45 bar >= 40% (rejection)", [e for e in sig if e["lowerwick"] >= .4]); stats("closed at the bar low (close_pos <= 20%)", [e for e in sig if e["close_pos"] <= .2])
    s = sorted(e["dist"] for e in sig); a, b = s[len(s) // 3], s[2 * len(s) // 3]
    stats(f"small break (<= {a:.2f}%)", [e for e in sig if e["dist"] <= a]); stats("large break", [e for e in sig if e["dist"] > b])
    stats("volume of 14:45 bar >= 2x earlier average", [e for e in sig if e["v45"] >= 2])
    print("\nMarket-neutral: subtract each day's mean last-bar return")
    g = collections.defaultdict(list)
    for e in sig: g[e["day"]].append(e["ret"] - mkt[e["day"]])
    dm = [st.mean(v) for v in g.values() if len(v) >= 3]; print(f"  excess gross {st.mean([x for v in g.values() for x in v]):+.3f}%  day-equal t {tt(dm):+.1f}  days+ {sum(x > 0 for x in dm)}/{len(dm)}")

if __name__ == "__main__":
    main()
