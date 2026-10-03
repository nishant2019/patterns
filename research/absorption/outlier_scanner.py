"""Mahalanobis joint-outlier scanner (bars with |delta| >= 10% of volume).

Lists bars whose (|delta| %, price move along the delta, ln volume spike) are a joint outlier (d > 3.06), with the driver
(PRICE-, PRICE+, SIZE, VOLUME). The reference distribution is fitted on every day in data/.
Usage:
    python outlier_scanner.py 29-09-2026 [--driver SIZE] [--side selling|buying|both] [-o out.csv]
"""
import argparse, csv, glob, os, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from efficiency_chart import peer_tables, maha_state, window, load


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("date"); ap.add_argument("--driver", default="SIZE", choices=["SIZE", "PRICE-", "PRICE+", "VOLUME", "any"])
    ap.add_argument("--side", default="selling", choices=["selling", "buying", "both"]); ap.add_argument("-o", "--output")
    a = ap.parse_args()
    tables = peer_tables()
    folder = os.path.join(HERE, "..", "..", "data", f"CVD_Scanner_{a.date}")
    data = {}
    for p in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        try: data[os.path.basename(p).rsplit("_", 1)[0]] = load(p)
        except ValueError: pass
    nmax = max(len(d["close_price"]) for d in data.values())
    def med_fwd(i, h):
        return st.median((d["close_price"][min(i + h, len(d["close_price"]) - 1)] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values() if len(d["close_price"]) > i)
    mk2 = [med_fwd(i, 2) for i in range(nmax)]; mke = [st.median((d["close_price"][-1] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values() if len(d["close_price"]) > i) for i in range(nmax)]
    rows = []
    for sym, d in data.items():
        O, C, V, T = d["open_price"], d["close_price"], d["volume"], d["Time"]
        if d["high_price"][0] <= d["low_price"][0]: continue
        n = len(C); avgv = sum(V) / n
        for i in range(1, n):
            D, P, raw = window(d, i, i)
            if abs(D) < 10: continue
            sg = 1 if D > 0 else -1
            lab, dist, drv = maha_state(D, sg * P, V[i] / (sum(V[:i]) / i), tables["maha"])
            if lab != "OUTLIER": continue
            if a.driver != "any" and drv != a.driver: continue
            if a.side == "selling" and D >= 0: continue
            if a.side == "buying" and D <= 0: continue
            last = i == n - 1
            rows.append(dict(symbol=sym, time=T[i][11:16], delta=int(d["close_cvd"][i] - d["open_cvd"][i]), delta_pct=round(D, 1), delta_in_avg_bars=round(abs(d["close_cvd"][i] - d["open_cvd"][i]) / avgv, 2),
                             ret_pct=round(raw, 2), vol_spike=round(V[i] / (sum(V[:i]) / i), 2), d=round(dist, 1), driver=drv, close=C[i],
                             fwd_2bars=None if last else round((C[min(i + 2, n - 1)] - C[i]) / C[i] * 100 - mk2[i], 2),
                             fwd_close=None if last else round((C[-1] - C[i]) / C[i] * 100 - mke[i], 2)))
    rows.sort(key=lambda r: -r["d"])
    print(f"{a.date}: {len(rows)} {a.driver}-driven {a.side} outliers in {len({r['symbol'] for r in rows})} stocks")
    print(f"{'stock':12s} {'time':5s} {'delta':>9s} {'D%':>6s} {'xAvgBar':>7s} {'ret%':>6s} {'spike':>6s} {'d':>5s} {'drv':6s} {'2 bars':>7s} {'to close':>8s}  (returns vs median stock)")
    for r in rows:
        print(f"{r['symbol']:12s} {r['time']:5s} {r['delta']:9d} {r['delta_pct']:6.1f} {r['delta_in_avg_bars']:7.2f} {r['ret_pct']:6.2f} {r['vol_spike']:6.2f} {r['d']:5.1f} {r['driver']:6s} {'' if r['fwd_2bars'] is None else format(r['fwd_2bars'], '+.2f'):>7s} {'' if r['fwd_close'] is None else format(r['fwd_close'], '+.2f'):>8s}")
    f = [r for r in rows if r["fwd_close"] is not None]
    if f:
        print(f"\nwith later bars: {len(f)}; vs median stock: next 2 bars {st.mean(r['fwd_2bars'] for r in f):+.3f}%  to close {st.mean(r['fwd_close'] for r in f):+.3f}%  win {100*sum(r['fwd_close']>0 for r in f)/len(f):.0f}%")
    if a.output and rows:
        with open(a.output, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

if __name__ == "__main__":
    main()
