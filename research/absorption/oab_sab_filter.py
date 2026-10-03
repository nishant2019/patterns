"""Test SAB (selling absorption bar) as a filter on OAB setups.

For each OAB setup, flag whether an SAB bar occurred (a) inside the OAB window,
(b) on the window's last bar, (c) anywhere up to the window end. Compare
window-end -> close return vs the average stock, and breakout rate.
"""
import glob
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
sys.path.insert(0, HERE)
from oab_scanner import PARAMS, load, scan_stock  # noqa: E402
from absorption_scanner import events  # noqa: E402

DAYS = sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*")))
rows = []
for folder in DAYS:
    date = folder.rsplit("_", 1)[1]
    data = {}
    for p in glob.glob(os.path.join(folder, "*.csv")):
        try:
            data[os.path.basename(p).rsplit("_", 1)[0]] = load(p)
        except ValueError:
            pass
    n = min(len(d["close_price"]) for d in data.values())
    avg_to_close = [st.mean((d["close_price"][-1] - d["close_price"][i]) / d["close_price"][i] * 100
                            for d in data.values()) for i in range(n)]
    for sym, d in data.items():
        hit = scan_stock(d, PARAMS)
        if not hit:
            continue
        times = [t[11:16] for t in d["Time"]]
        e, s = times.index(hit["end"]), times.index(hit["start"])
        sab = {times.index(ev["time"]) for ev in events(d) if ev["kind"] == "SAB"}
        rows.append(dict(date=date, sym=sym, s=s, e=e, bo=bool(hit["breakout"]),
                         rel=hit["to_close_pct"] - avg_to_close[e],
                         sab_in=any(s <= b <= e for b in sab), sab_last=e in sab,
                         sab_upto=any(b <= e for b in sab),
                         sab_after=any(b > e for b in sab),
                         sab_win_ex_last=any(s <= b < e for b in sab)))


def line(label, rs):
    if not rs:
        print(f"{label:46s} n=  0")
        return
    rel = [r["rel"] for r in rs]
    print(f"{label:46s} n={len(rs):3d} breakout={100 * sum(r['bo'] for r in rs) / len(rs):3.0f}% "
          f"vs_market={st.mean(rel):+.2f}% beat={100 * sum(x > 0 for x in rel) / len(rel):3.0f}% "
          f"days+={sum(1 for d in sorted({r['date'] for r in rs}) if st.mean(r['rel'] for r in rs if r['date'] == d) > 0)}/{len({r['date'] for r in rs})}")


print(f"OAB setups: {len(rows)} over {len(DAYS)} days (return = window end -> close, minus average stock)\n")
line("ALL OAB", rows)
for key, nm in [("sab_in", "SAB inside OAB window"), ("sab_last", "SAB on window's last bar"),
                ("sab_win_ex_last", "SAB in window, before last bar"), ("sab_upto", "SAB anywhere up to window end"),
                ("sab_after", "SAB AFTER window end (later bar)")]:
    line(f"  with {nm}", [r for r in rows if r[key]])
    line(f"  without {nm}", [r for r in rows if not r[key]])
print("\nPer day, OAB with vs without SAB inside window:")
for d in sorted({r["date"] for r in rows}):
    w = [r for r in rows if r["date"] == d and r["sab_in"]]
    wo = [r for r in rows if r["date"] == d and not r["sab_in"]]
    f = lambda x: f"n={len(x):2d} {st.mean(r['rel'] for r in x):+.2f}%" if x else "n= 0   -  "
    print(f"  {d}  with SAB {f(w)}   without {f(wo)}")
print("\nOAB setups that had SAB inside the window:")
for r in sorted([r for r in rows if r["sab_in"]], key=lambda r: r["date"]):
    print(f"  {r['date']} {r['sym']:11s} rel={r['rel']:+.2f}% breakout={r['bo']}")
