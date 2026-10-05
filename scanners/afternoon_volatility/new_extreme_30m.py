"""30-minute-only version: new day-low / day-high closes at EVERY slot, traded only on full 30-minute bars (the 15-minute 15:15 bar is never traded).
Signal: bar s closes below the lowest low (above the highest high) of all earlier bars that day (needs >= 4 earlier bars).
Trade: enter at the open of bar s+1, exit at the close of bar s+1 (hold 1 bar) or of bar s+2 (hold 2 bars); last tradable entry = 14:45 bar closing 15:15 -> hold 1 only after 14:15 signal.
Sides tested (fixed in advance): BUY new lows (reversal), SELL new highs (reversal), and the two continuation mirrors. Cost 0.06%. t = day-equal (mean per day, then across days).
"""
import collections, math, os, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import afternoon_vol_scanner as A
M = A.M; COST = 0.06
def tt(x): return st.mean(x) / (st.pstdev(x) / math.sqrt(len(x))) if len(x) > 2 and st.pstdev(x) > 0 else float("nan")

def main():
    data = M.load_all(); rows = []
    for sym, ds in data.items():
        for day, bars in ds.items():
            if len(bars) != 13 or min(b[1] for b in bars) <= 0: continue
            for i in range(4, 11):                       # signal bars 11:15..14:15 (index 4..10) so bar i+1 is a full 30m bar (<= 14:45 = idx 11)
                before = bars[:i]; lo = min(b[3] for b in before); hi = max(b[2] for b in before); c = bars[i][4]
                sg = -1 if c < lo else (1 if c > hi else 0)
                if sg == 0: continue
                e = bars[i + 1][1]; r1 = (bars[i + 1][4] / e - 1) * 100
                r2 = (bars[i + 2][4] / e - 1) * 100 if i + 2 <= 11 else None       # second bar must also be a full 30m bar (index <= 11)
                rows.append(dict(day=day, slot=bars[i][0], sg=sg, r1=r1, r2=r2))
    days = sorted({r["day"] for r in rows}); half = len(days) // 2
    mk = collections.defaultdict(list)
    for sym, ds in data.items():
        for day, bars in ds.items():
            if len(bars) == 13:
                for i in range(4, 11): mk[day, bars[i][0], 1].append((bars[i + 1][4] / bars[i + 1][1] - 1) * 100)
    def summ(sel, key, side, cost=COST):
        g = collections.defaultdict(list)
        for r in sel:
            if r[key] is None: continue
            g[r["day"]].append(side * r[key] - cost)
        dm = [st.mean(v) for v in g.values() if len(v) >= 3]; allv = [x for v in g.values() for x in v]
        if len(allv) < 30 or len(dm) < 5: return None
        d1 = [st.mean(v) for d, v in g.items() if d in days[:half] and len(v) >= 3]; d2 = [st.mean(v) for d, v in g.items() if d in days[half:] and len(v) >= 3]
        return len(allv), st.mean(allv) + cost, st.mean(allv), tt(dm), sum(x > 0 for x in dm), len(dm), (st.mean(d1) if d1 else float("nan")), (st.mean(d2) if d2 else float("nan"))
    print(f"{len(rows)} signal events over {len(days)} days. Net = after {COST}% cost. 'H1/H2' = day-equal net in first/second half.\n")
    for name, sel_f, side in (("BUY new day lows (reversal)", lambda r: r["sg"] < 0, 1), ("SELL new day highs (reversal)", lambda r: r["sg"] > 0, -1),
                              ("SELL new day lows (continuation)", lambda r: r["sg"] < 0, -1), ("BUY new day highs (continuation)", lambda r: r["sg"] > 0, 1)):
        print(name)
        for hold, key in (("hold 1 bar", "r1"), ("hold 2 bars", "r2")):
            print(f"  {hold}")
            tot = summ([r for r in rows if sel_f(r)], key, side)
            if tot: print(f"    {'ALL slots':8s} n={tot[0]:5d} gross {tot[1]:+.3f}% net {tot[2]:+.3f}% t {tot[3]:+4.1f} days+ {tot[4]}/{tot[5]}  H1 {tot[6]:+.3f} H2 {tot[7]:+.3f}")
            for s in ("11:15", "11:45", "12:15", "12:45", "13:15", "13:45", "14:15"):
                x = summ([r for r in rows if sel_f(r) and r["slot"] == s], key, side)
                if x: print(f"    {s:8s} n={x[0]:5d} gross {x[1]:+.3f}% net {x[2]:+.3f}% t {x[3]:+4.1f} days+ {x[4]}/{x[5]}  H1 {x[6]:+.3f} H2 {x[7]:+.3f}")
        print()

if __name__ == "__main__":
    main()
