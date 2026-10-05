"""Stocks that did NOT go quiet midday (decision 14:15, point-in-time). Same data, warm-up, split and clustering as coil_width_volume.py.
Pre-registered groups (top third of that day's stocks unless stated):
  A LOUD    = top third relative volume (Vr)       B WIDE = top third relative width (W)       C BOTH = loud and wide     D NO-COIL = zero compressed bars (11:15-13:45)
Outcomes from the 14:15 bar open:
  EXPAND  late-session |move| vs the stock's own usual
  MOMO    midday drift (last close vs 11:15 open) x excess return 14:15 open -> day close (+ = late session continues the midday drift), excess = minus that day's mean stock
  POS     close in the top third of the midday range (+1) / bottom third (-1) x the same excess return (+ = continues)
  FOLLOW  after a 14:15 close beyond the midday range: move to day close in the break direction, excess
Group-vs-rest differences within each day, averaged over days; for MOMO/POS the metric is computed inside the group only.
"""
import sys, os, collections, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from coil_width_volume import build, tt

def main():
    rows = build(); days = sorted({r["day"] for r in rows}); half = len(days) // 2
    disc, test = set(days[:half]), set(days[half:]); by = collections.defaultdict(list)
    for r in rows: by[r["day"]].append(r)
    for d, rs in by.items():
        n = len(rs); w3 = sorted(r["W"] for r in rs)[2 * n // 3]; v3 = sorted(r["Vr"] for r in rs)[2 * n // 3]; mu = st.mean(r["ret_open"] for r in rs)
        for r in rs:
            r["A"] = r["Vr"] >= v3; r["B"] = r["W"] >= w3; r["C"] = r["A"] and r["B"]; r["D"] = r["coils"] == 0
            ex = r["ret_open"] - mu
            r["momo"] = ex * (1 if r["drift"] > 0 else -1) if r["drift"] != 0 else None
            r["posx"] = ex * (1 if r["pos"] >= 2 / 3 else (-1 if r["pos"] <= 1 / 3 else 0)) if (r["pos"] >= 2 / 3 or r["pos"] <= 1 / 3) else None
            r["fol"] = r["brk"] * (r["ret_open"] - mu) if r["brk"] else None   # NB uses open->close for simplicity of exposure; also computed from break close below
            r["ex"] = ex
    names = {"A": "A LOUD midday (top third volume vs usual)", "B": "B WIDE midday (top third width vs usual)", "C": "C loud AND wide", "D": "D NO compressed bars"}
    print(f"{len(rows)} stock-days, {len(days)} days; discovery {len(disc)} / test {len(test)}\n")
    # difference metrics
    print("Group minus rest within day (t clustered by day, days positive):")
    for k in "ABCD":
        print(f"\n{names[k]}")
        for mname, m, sc in (("EXPAND (|move| vs own usual)", "expand", 1), ("BREAK by 14:45 close (pts)", "brk2", 100), ("EXCESS return 14:15 open->close", "ex", 1)):
            line = f"  {mname:32s}"
            for lab, ds_ in (("ALL", set(days)), ("DISC", disc), ("TEST", test)):
                dif = []; ng = 0
                for d in sorted(ds_):
                    g = [r[m] for r in by[d] if r[k]]; o = [r[m] for r in by[d] if not r[k]]
                    if len(g) >= 10 and len(o) >= 10: dif.append((st.mean(g) - st.mean(o)) * sc); ng += len(g)
                line += f" | {lab} {st.mean(dif):+7.3f} (t {tt(dif):+4.1f}, {sum(x > 0 for x in dif)}/{len(dif)}d)"
            print(line)
        # direction metrics inside the group
        for mname, m in (("MOMO (continue midday drift)", "momo"), ("POS  (continue range position)", "posx")):
            line = f"  {mname:32s}"
            for lab, ds_ in (("ALL", set(days)), ("DISC", disc), ("TEST", test)):
                dm = []; ng = 0
                for d in sorted(ds_):
                    g = [r[m] for r in by[d] if r[k] and r[m] is not None]
                    if len(g) >= 15: dm.append(st.mean(g)); ng += len(g)
                line += f" | {lab} {st.mean(dm):+7.3f}% (t {tt(dm):+4.1f}, {sum(x > 0 for x in dm)}/{len(dm)}d, n={ng})"
            print(line)
    # baseline for MOMO/POS on all stocks
    print("\nBaseline (all stocks):")
    for mname, m in (("MOMO", "momo"), ("POS", "posx")):
        line = f"  {mname:6s}"
        for lab, ds_ in (("ALL", set(days)), ("DISC", disc), ("TEST", test)):
            dm = [st.mean([r[m] for r in by[d] if r[m] is not None]) for d in sorted(ds_)]
            line += f" | {lab} {st.mean(dm):+7.3f}% (t {tt(dm):+4.1f}, {sum(x > 0 for x in dm)}/{len(dm)}d)"
        print(line)
    print("\nAbsolute late-session move vs own usual (EXPAND):", {k: round(st.mean(r['expand'] for r in rows if r[k]), 2) for k in 'ABCD'}, "all:", round(st.mean(r['expand'] for r in rows), 2))

if __name__ == "__main__":
    main()
