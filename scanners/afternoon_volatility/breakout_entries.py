"""Breakout entries on the afternoon volatility watchlist (point-in-time; bars: 14:15, 14:45, 15:15*; 18 usable days, 9 discovery / 9 test).
Events, fixed in advance (entry at the OPEN of the bar after the signal bar; exit at the day's last close; round-trip cost 0.06%):
  E1 DAYBRK  : 14:15 bar closes above the day high / below the day low of all earlier bars        -> enter 14:45 open
  E2 MIDBRK  : 14:15 bar closes above the midday (11:15-13:45) high / below its low                -> enter 14:45 open
  E3 +VOL    : E1 or E2 with 14:15-bar volume >= 1.5x the mean midday bar volume
  E4 LATE    : 14:45 bar closes beyond the day high/low so far (incl. 14:15)                       -> enter 15:15 open
  S-variants : same entries with a stop at the opposite extreme of the signal bar (exit at the stop level, or the open if it gaps through)
  FADE       : the mirror trade (take the opposite side of the same events)
Universes: HOT, WARM, HOT+WARM (the watchlist), REST (not on the list), ALL.
Reported per universe: n, mean net return per trade (after cost), hit rate, days positive, t clustered by day, discovery/test, plus market-neutral excess (minus the mean move of all stocks over the same entry->exit window that day, before cost).
"""
import collections, math, os, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import afternoon_vol_scanner as A
M = A.M; COST = 0.06

def tt(x): return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else float("nan")

def trade(bars, entry_t, side, stop=None):
    """enter at open of bar entry_t, exit at last close, optional stop level; returns % return signed by side."""
    idx = [i for i, b in enumerate(bars) if b[0] == entry_t]
    if not idx: return None
    i0 = idx[0]; entry = bars[i0][1]
    if stop is not None:
        for b in bars[i0:]:
            if side > 0 and b[3] <= stop: ex = min(b[1], stop) if b is bars[i0] else stop; return ((ex / entry - 1) * 100) * side
            if side < 0 and b[2] >= stop: ex = max(b[1], stop) if b is bars[i0] else stop; return ((ex / entry - 1) * 100) * side
    return ((bars[-1][4] / entry - 1) * 100) * side

def main():
    data = M.load_all(); rows = A.features(data, "14:15"); by = collections.defaultdict(list)
    for r in rows: by[r["day"]].append(r)
    for d in by: A.score_day(by[d])
    days = sorted(by); half = len(days) // 2; disc, test = set(days[:half]), set(days[half:])
    # market move over the same entry->exit windows (all stocks, that day)
    mkt = {}
    for d in days:
        for t in ("14:45", "15:15"):
            v = [(data[r["sym"]][d][-1][4] / b[1] - 1) * 100 for r in by[d] for b in data[r["sym"]][d] if b[0] == t and data[r["sym"]][d][-1][0] > t or (b[0] == t and False)]
            mkt[d, t] = st.mean(v) if v else 0.0
    trades = []   # (event, variant, tier, day, net%, excess%)
    for d in days:
        for r in by[d]:
            bars = data[r["sym"]][d]; b14 = [b for b in bars if b[0] == "14:15"]; b45 = [b for b in bars if b[0] == "14:45"]
            if not b14 or not b45 or bars[-1][0] <= "14:45": continue
            b14, b45 = b14[0], b45[0]; c = b14[4]
            midv = st.mean(b[5] for b in bars if "11:15" <= b[0] < "14:15")
            ev = {}
            s1 = 1 if c > r["dhi"] else (-1 if c < r["dlo"] else 0)
            s2 = 1 if c > r["hi"] else (-1 if c < r["lo"] else 0)
            ev["E1 DAYBRK"] = (s1, "14:45", b14); ev["E2 MIDBRK"] = (s2, "14:45", b14)
            vol_ok = b14[5] >= 1.5 * midv
            ev["E3 +VOL"] = ((s1 or s2) if vol_ok else 0, "14:45", b14)
            dh = max(r["dhi"], b14[2]); dl = min(r["dlo"], b14[3]); c2 = b45[4]
            s4 = 1 if c2 > dh else (-1 if c2 < dl else 0)
            ev["E4 LATE"] = (s4, "15:15", b45)
            for name, (s, et, sb) in ev.items():
                if s == 0: continue
                for var in ("hold", "stop", "FADE"):
                    if var == "stop" and name == "E4 LATE": continue
                    side = -s if var == "FADE" else s
                    stop = (sb[3] if s > 0 else sb[2]) if var == "stop" else None
                    if var == "FADE": stop = None
                    ret = trade(bars, et, side, stop)
                    if ret is None: continue
                    for tier in {"HOT": ["HOT", "HOT+WARM"], "WARM": ["WARM", "HOT+WARM"], "-": ["REST"]}[r["tier"]] + ["ALL"]:
                        trades.append((name, var, tier, d, ret - COST, ret - side * mkt[d, et]))
    print(f"{len(days)} days (discovery {len(disc)}, test {len(test)}); cost {COST}% round trip per trade\n")
    print(f"{'event':11s}{'variant':7s}{'universe':10s}{'n':>6s} | {'net%':>7s} {'hit%':>5s} | {'t':>5s} {'days+':>7s} | {'DISC net':>8s} {'t':>5s} | {'TEST net':>8s} {'t':>5s} | {'excess%':>8s}")
    res = []
    for ev in ("E1 DAYBRK", "E2 MIDBRK", "E3 +VOL", "E4 LATE"):
        for var in ("hold", "stop", "FADE"):
            for tier in ("HOT", "HOT+WARM", "REST", "ALL"):
                T = [t for t in trades if t[0] == ev and t[1] == var and t[2] == tier]
                if len(T) < 40: continue
                def pd(ds):
                    g = collections.defaultdict(list)
                    for t in T:
                        if t[3] in ds: g[t[3]].append(t[4])
                    return [st.mean(v) for v in g.values() if len(v) >= 3]
                a = pd(set(days)); di = pd(disc); te = pd(test)
                if len(a) < 5: continue
                hit = st.mean(1 if t[4] > -COST else 0 for t in T) * 100   # gross win
                ex = st.mean(t[5] for t in T)
                res.append((ev, var, tier, len(T), st.mean(t[4] for t in T), tt(a), st.mean(di), tt(di), st.mean(te), tt(te)))
                print(f"{ev:11s}{var:7s}{tier:10s}{len(T):6d} | {st.mean(t[4] for t in T):+7.3f} {hit:5.1f} | {tt(a):+5.1f} {sum(x>0 for x in a):3d}/{len(a):<3d} | {st.mean(di):+8.3f} {tt(di):+5.1f} | {st.mean(te):+8.3f} {tt(te):+5.1f} | {ex:+8.3f}")
        print()
    ok = [x for x in res if x[1] != "FADE" and x[6] > 0 and x[8] > 0 and x[9] >= 2]
    ok2 = [x for x in res if x[6] > 0 and x[8] > 0 and x[9] >= 2]
    print("Gate (net of cost > 0 in BOTH halves, test t >= 2):", [(x[0], x[1], x[2], round(x[4], 3)) for x in ok2] or "none")
    print(f"{len(res)} rows tested; chance expectation of test t>=2 about {len(res)*.025:.1f} (one-sided)")

if __name__ == "__main__":
    main()
