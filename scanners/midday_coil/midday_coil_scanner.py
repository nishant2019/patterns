"""Midday coil watchlist scanner (30-minute bars). Built from research/golden_hours (23 days, 506 stocks).

Idea: 11:15-13:45 is the coil zone. Stocks that spent it compressed are more likely to expand at 14:45 / break their midday range.
Watchlist rule (frozen, no tuning):
  - decision time T (default 14:15, run when the 13:45 bar has closed; only bars starting before T are used)
  - coil bar  = bar range% < 0.6 x median range% of the bars seen so far that day
  - COIL COUNT = coil bars among bars starting 11:15 .. T-30min (max 5 at T=14:15); watchlist = count >= 3  (>=4 = A-list)
  - levels: midday high / low over those bars; BREAK ABOVE / BELOW = close beyond them (e.g. the 14:15 bar close)
Output per stock: coil count, midday range and width %, where the last close sits in the range, volume vs morning, plus the two trigger levels.
Usage:
  python scanners/midday_coil/midday_coil_scanner.py --date 2026-10-05 [--time 14:15] [--csv out.csv]
  python scanners/midday_coil/midday_coil_scanner.py --backtest
"""
import argparse, collections, csv, glob, math, os, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "data", "ohlc")
PARAMS = dict(coil_frac=0.6, start="11:15", min_coils=3, a_list=4)

def load_all(folder=DATA):
    """{symbol: {day: [(HH:MM, o, h, l, c, v), ...]}}"""
    out = {}
    for p in sorted(glob.glob(os.path.join(folder, "*_30m.csv"))):
        sym = os.path.basename(p).split("_")[0]; byday = collections.defaultdict(list)
        for r in csv.DictReader(open(p)):
            try: byday[r["timestamp"][:10]].append((r["timestamp"][11:16], float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), float(r["volume"])))
            except ValueError: pass
        out[sym] = {d: sorted(b) for d, b in byday.items() if len(b) >= 12}
    return out

def scan_bars(bars, T="14:15", P=PARAMS):
    """bars of one stock-day; returns dict or None. Uses only bars starting before T."""
    seen = [b for b in bars if b[0] < T]
    if len(seen) < 8 or seen[0][0] != "09:15": return None
    rng = [(b[2] - b[3]) / b[1] * 100 for b in seen if b[1] > 0]
    if len(rng) != len(seen) or st.median(rng) <= 0: return None
    md = st.median(rng)
    mid = [(b, r) for b, r in zip(seen, rng) if P["start"] <= b[0]]
    if len(mid) < 3: return None
    k = sum(r < P["coil_frac"] * md for _, r in mid)
    hi, lo = max(b[2] for b, _ in mid), min(b[3] for b, _ in mid)
    last = seen[-1][4]
    morning = [b for b in seen if b[0] <= "10:45"]
    return dict(coils=k, mid_bars=len(mid), hi=hi, lo=lo, last=last, width=(hi - lo) / last * 100, pos=(last - lo) / max(hi - lo, 1e-9),
                vol_ratio=st.mean(b[5] for b, _ in mid) / max(st.mean(b[5] for b in morning), 1e-9), med_rng=md)

def scan_date(data, day, T="14:15", P=PARAMS):
    rows = []
    for sym, days in data.items():
        if day not in days: continue
        r = scan_bars(days[day], T, P)
        if r and r["coils"] >= P["min_coils"]:
            r["symbol"] = sym; r["tier"] = "A" if r["coils"] >= P["a_list"] else "B"; rows.append(r)
    rows.sort(key=lambda r: (-r["coils"], r["width"]))
    return rows

def print_rows(rows, day, T):
    print(f"Midday coil watchlist {day} @ {T}: {len(rows)} stocks (A = {sum(r['tier']=='A' for r in rows)})")
    print(f"{'Tier':4s}{'Symbol':14s}{'Coils':>6s}{'Midday low':>12s}{'Midday high':>12s}{'Width%':>8s}{'Last':>10s}{'PosInRange':>11s}{'VolVsAM':>8s}  Triggers")
    for r in rows:
        print(f"{r['tier']:4s}{r['symbol']:14s}{r['coils']:6d}{r['lo']:12.2f}{r['hi']:12.2f}{r['width']:8.2f}{r['last']:10.2f}{r['pos']:11.2f}{r['vol_ratio']:8.2f}  close>{r['hi']:.2f} long / close<{r['lo']:.2f} short")

def t_cluster(by_day):
    m = [st.mean(v) for v in by_day.values() if v]
    return st.mean(m) / (st.pstdev(m) / math.sqrt(len(m))) if len(m) > 2 and st.pstdev(m) > 0 else float("nan"), sum(x > 0 for x in m), len(m)

def backtest(data, T="14:15", P=PARAMS):
    """For every stock-day: group by coil count (0, 1-2, 3, 4-5). Look at the T bar (the 14:15 bar) and what follows.
    Signal at the CLOSE of the T bar: if it closed beyond the midday range -> break (+1 up / -1 down). Outcomes after that close (to the last bar close of the day)."""
    days = sorted({d for s in data.values() for d in s})
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    for day in days:
        recs = []
        for sym, ds in data.items():
            if day not in ds: continue
            bars = ds[day]; r = scan_bars(bars, T, P)
            if not r: continue
            tb = [b for b in bars if b[0] == T]; late = [b for b in bars if b[0] > T]
            if not tb or not late: continue
            tb = tb[0]; o14, c14 = tb[1], tb[4]
            ret_after = (late[-1][4] / c14 - 1) * 100                      # from T-bar close to day close
            rng14 = (tb[2] - tb[3]) / tb[1] * 100 / r["med_rng"]            # range of the T bar vs median
            nxt = [b for b in late if b[0] == "14:45"]
            rng_next = (nxt[0][2] - nxt[0][3]) / nxt[0][1] * 100 / r["med_rng"] if nxt else None
            brk = 1 if c14 > r["hi"] else (-1 if c14 < r["lo"] else 0)
            recs.append((r["coils"], brk, ret_after, rng14, rng_next, abs(late[-1][4] / o14 - 1) * 100, None))
        if not recs: continue
        mu = st.mean(x[2] for x in recs)
        for k, brk, ra, r14, rn, absmove, tier in recs:
            g = "0 coil bars" if k == 0 else ("1-2 coil bars" if k <= 2 else ("3 coil bars" if k == 3 else "4-5 coil bars"))
            for gg in (g, "ALL STOCKS") + (("WATCHLIST (3+)",) if k >= 3 else ()):
                d = groups[gg]
                d["n"].append(1); d["break"].append(brk != 0); d["r14"].append(r14); d["absmove"].append(absmove)
                if rn is not None: d["rnext"].append(rn)
                d.setdefault("day_" + day, [])
                if brk != 0: d["fol"].append((day, brk * (ra - mu))); d["raw"].append((day, brk * ra))
    print(f"Backtest {len(days)} days, decision {T} (signal = T-bar close; outcomes from that close to the day close)")
    print(f"{'group':18s}{'n':>7s} | {'T-bar close breaks midday range':>32s} | {'T-bar range idx':>15s} | {'14:45 bar range idx':>19s} | {'|move| T-open->close':>20s}")
    for g in ("0 coil bars", "1-2 coil bars", "3 coil bars", "4-5 coil bars", "WATCHLIST (3+)", "ALL STOCKS"):
        d = groups[g]
        print(f"{g:18s}{len(d['n']):7d} | {st.mean(d['break'])*100:30.0f}% | {st.mean(d['r14']):15.2f} | {st.mean(d['rnext']):19.2f} | {st.mean(d['absmove']):19.2f}%")
    print("\nDirection after a break (signed: + = continued in the break direction; excess = minus that day's mean stock move after T-bar close):")
    for g in ("WATCHLIST (3+)", "4-5 coil bars", "1-2 coil bars", "0 coil bars", "ALL STOCKS"):
        d = groups[g]; byday = collections.defaultdict(list)
        for day, v in d["fol"]: byday[day].append(v)
        t, pos, nd = t_cluster(byday)
        allv = [v for _, v in d["fol"]]; raw = [v for _, v in d["raw"]]
        if allv: print(f"  {g:18s} n_breaks={len(allv):5d} mean raw {st.mean(raw):+.3f}%  excess {st.mean(allv):+.3f}% (t {t:+.1f}, {pos}/{nd} days positive)")
    return groups

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date"); ap.add_argument("--time", default="14:15"); ap.add_argument("--csv"); ap.add_argument("--backtest", action="store_true"); ap.add_argument("--data", default=DATA)
    a = ap.parse_args(); data = load_all(a.data)
    if a.backtest: backtest(data, a.time); return
    day = a.date or max(d for s in data.values() for d in s)
    rows = scan_date(data, day, a.time); print_rows(rows, day, a.time)
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["tier", "symbol", "coils", "mid_low", "mid_high", "width_pct", "last", "pos_in_range", "vol_vs_am"])
            for r in rows: w.writerow([r["tier"], r["symbol"], r["coils"], r["lo"], r["hi"], round(r["width"], 3), r["last"], round(r["pos"], 3), round(r["vol_ratio"], 3)])

if __name__ == "__main__":
    main()
