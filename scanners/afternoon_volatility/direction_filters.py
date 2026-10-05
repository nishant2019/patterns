"""Direction filters on the afternoon volatility watchlist (decision 14:15, point-in-time). Pre-registered; 18 usable days, 9 discovery / 9 test.
Each filter gives a side (+1 long / -1 short) from information available at 14:15; outcome = side x (move 14:15 open -> day close),
reported (a) RAW and (b) EXCESS = minus that day's mean stock move (market-neutral). t clustered by day. Costs: 0.06% round trip.
Filters (sign convention = CONTINUE the signal; a negative result means the opposite side/fade works):
  MORN   close vs day open (morning trend)               VWAP  close vs session VWAP
  DPOS   close in top/bottom third of day range so far    GAP   day open vs previous close (gap)
  RELST  stock's day return minus market mean (top/bottom third of that day's stocks)
  LAST2  return of the last 2 bars (13:15 open -> 14:15 open)   MID   midday drift (11:15 open -> close)   VOLD  signed volume: up-bar volume minus down-bar volume share in midday
Universe: HOT tier, WARM tier, HOT+WARM, and the rest, for comparison.
"""
import collections, math, os, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import afternoon_vol_scanner as A
M = A.M
COST = 0.06

def tt(x): return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else float("nan")

def main():
    data = M.load_all(); rows = A.features(data, "14:15"); by = collections.defaultdict(list)
    for r in rows: by[r["day"]].append(r)
    for d in by: A.score_day(by[d])
    days_all = sorted(data[next(iter(data))])
    keep = []
    for d in sorted(by):
        for r in by[d]:
            bars = data[r["sym"]][d]; tb = [b for b in bars if b[0] == "14:15"]
            if not tb or bars[-1][0] <= "14:15": continue
            seen = [b for b in bars if b[0] < "14:15"]; o14 = tb[0][1]
            r["ret"] = (bars[-1][4] / o14 - 1) * 100
            r["morn"] = (r["last"] / seen[0][1] - 1) * 100
            r["vwapd"] = (r["last"] / r["vwap"] - 1) * 100
            r["dpos"] = (r["last"] - r["dlo"]) / max(r["dhi"] - r["dlo"], 1e-9)
            prev = [x for x in sorted(data[r["sym"]]) if x < d]
            r["gap"] = (seen[0][1] / data[r["sym"]][prev[-1]][-1][4] - 1) * 100 if prev else None
            l2 = [b for b in seen if b[0] >= "13:15"]; r["last2"] = (r["last"] / l2[0][1] - 1) * 100 if len(l2) == 2 else None
            mid = [b for b in seen if b[0] >= "11:15"]; r["mid"] = (r["last"] / mid[0][1] - 1) * 100
            up = sum(b[5] for b in mid if b[4] > b[1]); dn = sum(b[5] for b in mid if b[4] < b[1]); r["vold"] = (up - dn) / max(up + dn, 1)
            keep.append(r)
    byd = collections.defaultdict(list)
    for r in keep: byd[r["day"]].append(r)
    days = sorted(byd); half = len(days) // 2; disc, test = days[:half], days[half:]
    for d in days:
        rs = byd[d]; mu = st.mean(r["ret"] for r in rs); n = len(rs)
        morns = sorted(r["morn"] for r in rs)
        rel = [r["morn"] for r in rs]; mm = st.mean(rel); rl = sorted(x - mm for x in rel); lo3, hi3 = rl[n // 3], rl[2 * n // 3]
        for r in rs:
            r["ex"] = r["ret"] - mu; rr = r["morn"] - mm
            sg = lambda v, th=0: 1 if v > th else (-1 if v < -th else 0)
            r["F"] = dict(MORN=sg(r["morn"]), VWAP=sg(r["vwapd"]), DPOS=(1 if r["dpos"] >= 2 / 3 else (-1 if r["dpos"] <= 1 / 3 else 0)),
                          GAP=sg(r["gap"]) if r["gap"] is not None else 0, RELST=(1 if rr >= hi3 else (-1 if rr <= lo3 else 0)),
                          LAST2=sg(r["last2"]) if r["last2"] is not None else 0, MID=sg(r["mid"]), VOLD=sg(r["vold"], 0.2))
    names = ["MORN", "VWAP", "DPOS", "GAP", "RELST", "LAST2", "MID", "VOLD"]
    tiers = [("HOT", lambda r: r["tier"] == "HOT"), ("WARM", lambda r: r["tier"] == "WARM"), ("HOT+WARM", lambda r: r["tier"] != "-"), ("REST", lambda r: r["tier"] == "-")]
    print(f"{len(keep)} stock-days, {len(days)} days (discovery {len(disc)}, test {len(test)}). Signed = side x outcome, side = CONTINUE the filter. Excess = minus the day's mean stock move.\n")
    res = []
    for tn, tf in tiers:
        print(f"== {tn} ==")
        print(f"{'filter':7s}{'n':>6s} | {'RAW mean%':>10s} | {'EXCESS mean% (t, days+)':>26s} | {'DISC exc%':>10s} {'t':>5s} | {'TEST exc%':>10s} {'t':>5s} | hit%")
        for f in names:
            def per_day(ds, key):
                out = []; n_ = 0
                for d in ds:
                    v = [r["F"][f] * r[key] for r in byd[d] if tf(r) and r["F"][f] != 0]
                    if len(v) >= 8: out.append(st.mean(v)); n_ += len(v)
                return out, n_
            ra, n = per_day(days, "ret"); ea, _ = per_day(days, "ex"); ed, _ = per_day(disc, "ex"); et, _ = per_day(test, "ex")
            hit = st.mean(1 if r["F"][f] * r["ex"] > 0 else 0 for d in days for r in byd[d] if tf(r) and r["F"][f] != 0) * 100
            if not ea: continue
            res.append((tn, f, n, st.mean(ra), st.mean(ea), tt(ea), sum(x > 0 for x in ea), len(ea), st.mean(ed), tt(ed), st.mean(et), tt(et)))
            print(f"{f:7s}{n:6d} | {st.mean(ra):+10.3f} | {st.mean(ea):+9.3f} (t {tt(ea):+5.1f}, {sum(x > 0 for x in ea)}/{len(ea)}d) | {st.mean(ed):+10.3f} {tt(ed):+5.1f} | {st.mean(et):+10.3f} {tt(et):+5.1f} | {hit:4.1f}")
        print()
    # gate: same sign disc/test, test |t|>=2, |excess| beyond cost
    print(f"Gate (same sign in both halves, test |t|>=2, |mean excess| > {COST}% cost): ")
    ok = [x for x in res if x[8] * x[10] > 0 and abs(x[11]) >= 2 and abs(x[4]) > COST]
    print("  passing:", [(x[0], x[1], round(x[4], 3)) for x in ok] or "none")
    print(f"  tests run: {len(res)} (chance |t|>=2: ~{len(res)*0.05:.1f}); with |t|>=2 overall: {sum(abs(x[5]) >= 2 for x in res)}")

if __name__ == "__main__":
    main()
