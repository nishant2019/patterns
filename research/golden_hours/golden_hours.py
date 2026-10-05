"""Golden hours & coiling hours: per 30-minute slot statistics across all stock-days (price + volume, CVD only for flow persistence).
Run:  python research/golden_hours/golden_hours.py   -> slot_matrix.csv, slot_matrix.md, golden_hours.html/png
Definitions (all point-in-time; 'ref' = the stock's own average over that day, so stocks are comparable):
  RangeIdx   = bar range% / stock-day mean bar range%          (>1 = more active than that stock's day)
  VolIdx     = bar volume / stock-day mean bar volume
  Eff        = |close-open| / (high-low)                       (1 = one-way bar, 0 = pure chop)
  Coil%      = share of bars with range < 0.6 x the stock-day median bar range  (a compressed bar)
  Coil2%     = Coil bar that also follows a Coil bar (2+ bars in a row)
  Expand%    = after a coil bar, share of next bars with range > 1.5 x stock-day median
  Momentum   = prev bar direction taken at this bar's open: hit% (this bar closes in prev bar's direction) and edge% (signed return, minus same-slot mean)
  Brk-FT     = bar closes beyond the previous 2 bars' range: share where NEXT bar continues in the same direction, next-bar edge%
  CVDpers%   = |delta| >= 30% bar -> next bar same delta sign %
  Cross-day consistency = days (of N) where the slot's RangeIdx is above the day mean
"""
import glob, os, sys, statistics as st, collections, math, csv, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import load

def stockdays():
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try: d = load(p)
            except Exception: continue
            if len(d["close_price"]) >= 12: yield date, os.path.basename(p).rsplit("_", 1)[0], d

def main():
    acc = collections.defaultdict(lambda: collections.defaultdict(list))   # slot -> metric -> values
    perday = collections.defaultdict(lambda: collections.defaultdict(list)) # slot -> day -> rangeidx
    bar_dir = collections.defaultdict(list)                                  # (date, slot) for same-slot mean of signed returns
    recs = []; store = []
    for date, sym, d in stockdays():
        O, H, L, C, V = d["open_price"], d["high_price"], d["low_price"], d["close_price"], d["volume"]
        oc, cc = d["open_cvd"], d["close_cvd"]
        n = len(C); slots = [t[11:16] for t in d["Time"]]
        rng = [(H[i] - L[i]) / O[i] * 100 for i in range(n)]
        mr, mv, md = st.mean(rng), st.mean(V), st.median(rng)
        if mr <= 0 or mv <= 0: continue
        ret = [(C[i] - O[i]) / O[i] * 100 for i in range(n)]
        store.append((date, sym, slots, ret, [H[i] for i in range(n)], [L[i] for i in range(n)], list(C)))
        for i in range(n):
            acc[slots[i]]["move05"].append(abs(ret[i]) > 0.5); acc[slots[i]]["chop"].append(abs(C[i] - O[i]) / max(H[i] - L[i], 1e-9) < .3)
        coil = [rng[i] < .6 * md for i in range(n)]
        for i in range(n):
            s = slots[i]
            acc[s]["rangeidx"].append(rng[i] / mr); acc[s]["rng"].append(rng[i])
            acc[s]["volidx"].append(V[i] / mv); acc[s]["volshare"].append(V[i] / sum(V) * 100)
            acc[s]["eff"].append(abs(C[i] - O[i]) / max(H[i] - L[i], 1e-9))
            acc[s]["coil"].append(coil[i]); perday[s][date].append(rng[i] / mr)
            if i >= 1 and coil[i - 1]:
                acc[s]["coil2"].append(coil[i]); acc[s]["expand"].append(rng[i] > 1.5 * md)
            if i < n - 1:
                D = (cc[i] - oc[i]) / V[i] * 100
                if abs(D) >= 30:
                    nD = cc[i + 1] - oc[i + 1]
                    acc[slots[i + 1]]["cvdpers"].append((nD > 0) == (D > 0))
        # mom hit
        for i in range(1, n):
            if ret[i - 1] != 0: acc[slots[i]]["momhit"].append((ret[i] > 0) == (ret[i - 1] > 0))
    # signed-return edges (mom / brk) relative to same-slot unconditional drift are ~0, report raw signed mean + t
    # ---- second pass: idiosyncratic (market-neutral) momentum and breakout follow-through, t clustered by DAY
    mean_ret = collections.defaultdict(list)
    for date, sym, slots, ret, Hh, Ll, Cc in store:
        for i, s_ in enumerate(slots): mean_ret[date, s_].append(ret[i])
    mr_ = {k: st.mean(v) for k, v in mean_ret.items()}
    mom = collections.defaultdict(lambda: collections.defaultdict(list)); brk = collections.defaultdict(lambda: collections.defaultdict(list)); mhit = collections.defaultdict(list)
    for date, sym, slots, ret, Hh, Ll, Cc in store:
        rel = [ret[i] - mr_[date, slots[i]] for i in range(len(slots))]
        n = len(slots)
        for i in range(1, n):
            if rel[i - 1] != 0:
                mom[slots[i]][date].append(rel[i] * (1 if rel[i - 1] > 0 else -1)); mhit[slots[i]].append((rel[i] > 0) == (rel[i - 1] > 0))
        for i in range(2, n - 1):
            ph, pl = max(Hh[i - 2], Hh[i - 1]), min(Ll[i - 2], Ll[i - 1])
            sg = 1 if Cc[i] > ph else (-1 if Cc[i] < pl else 0)
            if sg: brk[slots[i + 1]][date].append(rel[i + 1] * sg)
    def dayt(dct):
        m = [st.mean(v) for v in dct.values() if v]
        allv = [x for v in dct.values() for x in v]
        return (st.mean(allv), (st.mean(m) / (st.pstdev(m) / math.sqrt(len(m))) if len(m) > 2 and st.pstdev(m) > 0 else float("nan")), sum(1 for x in m if x > 0), len(m), len(allv)) if allv else (float("nan"),) * 2 + (0, 0, 0)
    order = sorted(acc)
    rows = []
    for s in order:
        a = acc[s]; r = {"slot": s + ("*" if s == "15:15" else ""), "n": len(a["rangeidx"])}
        r["Range%"] = st.mean(a["rng"]); r["RangeIdx"] = st.mean(a["rangeidx"]); r["VolIdx"] = st.mean(a["volidx"]); r["Vol%day"] = st.mean(a["volshare"])
        r["Eff"] = st.mean(a["eff"]); r["Coil%"] = st.mean(a["coil"]) * 100
        r["Coil2%"] = st.mean(a["coil2"]) * 100 if a["coil2"] else float("nan"); r["Expand%"] = st.mean(a["expand"]) * 100 if a["expand"] else float("nan")
        r["Move>0.5%"] = st.mean(a["move05"]) * 100; r["Chop%"] = st.mean(a["chop"]) * 100
        r["MomHit%"] = st.mean(mhit[s]) * 100 if mhit[s] else float("nan")
        e = dayt(mom[s]); r["MomEdge%"], r["MomT"], r["MomDays+"] = e[0], e[1], f"{e[2]}/{e[3]}"
        e = dayt(brk[s]); r["BrkFT%"], r["BrkT"], r["BrkDays+"], r["BrkN"] = e[0], e[1], f"{e[2]}/{e[3]}", e[4]
        r["CVDpers%"] = st.mean(a["cvdpers"]) * 100 if a["cvdpers"] else float("nan")
        pd_ = perday[s]; r["Days>mean"] = f"{sum(st.mean(v) > 1 for v in pd_.values())}/{len(pd_)}"
        rows.append(r)
    cols = list(rows[0].keys())
    with open(os.path.join(HERE, "slot_matrix.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(cols); [w.writerow([("%.3f" % r[c] if isinstance(r[c], float) else r[c]) for c in cols]) for r in rows]
    # ranking
    act = sorted(rows, key=lambda r: -r["RangeIdx"]); quiet = sorted(rows, key=lambda r: -r["Coil%"])
    md = ["| Slot | n | Range% | RangeIdx | VolIdx | Vol%day | Eff | Move>0.5% | Chop% | Coil% | Coil2% | Expand% | MomHit% | MomEdge% (t, days+) | BrkFT% (t, days+) | CVDpers% | Days>mean |", "|" + "---|" * 17]
    for r in rows:
        md.append(f"| {r['slot']} | {r['n']} | {r['Range%']:.2f} | {r['RangeIdx']:.2f} | {r['VolIdx']:.2f} | {r['Vol%day']:.1f} | {r['Eff']:.2f} | {r['Move>0.5%']:.0f} | {r['Chop%']:.0f} | {r['Coil%']:.0f} | {r['Coil2%']:.0f} | {r['Expand%']:.0f} | {r['MomHit%']:.1f} | {r['MomEdge%']:+.3f} ({r['MomT']:+.1f}, {r['MomDays+']}) | {r['BrkFT%']:+.3f} ({r['BrkT']:+.1f}, {r['BrkDays+']}) | {r['CVDpers%']:.0f} | {r['Days>mean']} |")
    open(os.path.join(HERE, "slot_matrix.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))
    return rows

if __name__ == "__main__":
    main()
