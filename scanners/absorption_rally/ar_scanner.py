"""Absorption Rally (AR) scanner.

Heavy net market selling on a volume spike while price RISES: large passive
buyers absorb the selling. Reference example: DABUR 15-09-2026.
See AR_SPEC.md for the logic.

Usage:
    python ar_scanner.py data/CVD_Scanner_15-09-2026 [more folders...] [-o results.csv]
"""
import argparse
import csv
import glob
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "oab"))
from oab_scanner import load  # noqa: E402  (shared CSV loader/validator)

PARAMS = dict(
    max_bars=2,              # window = 1 or 2 consecutive bars
    first_start=1,           # earliest window start (1 = 09:45 bar)
    last_start=8,            # latest window start (8 = 13:15 bar)
    min_cvd_selling=25.0,    # net CVD selling as % of window volume
    min_price_chg=0.3,       # window price change (close[end] vs open[start]) %
    min_vol_spike=2.0,       # avg window bar volume / avg of all prior bars
    max_vol_spike=15.0,      # above this, likely a single block trade, not absorption
    min_rel_strength=0.0,    # (stock - market median) return since 09:15 close, at window end, %
)


def market_curve(data):
    """Median return since the 09:15 close at each bar index across the folder (point-in-time)."""
    n = max(len(d["close_price"]) for d in data.values())
    curve = []
    for i in range(n):
        rets = [(d["close_price"][i] - d["close_price"][0]) / d["close_price"][0] * 100
                for d in data.values() if len(d["close_price"]) > i]
        curve.append(statistics.median(rets))
    return curve


def scan_stock(d, mkt, p=PARAMS):
    O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
    oc, cc, V, T = d["open_cvd"], d["close_cvd"], d["volume"], d["Time"]
    n = len(C)
    for e in range(p["first_start"], n - 1):          # earliest-ending window first
        for k in range(1, p["max_bars"] + 1):
            s = e - k + 1
            if s < p["first_start"] or s > p["last_start"]:
                continue
            vol = sum(V[s:e + 1])
            cvd_sell = -(cc[e] - oc[s]) / vol * 100
            price_chg = (C[e] - O[s]) / O[s] * 100
            spike = (vol / k) / (sum(V[:s]) / s)
            rel = (C[e] - C[0]) / C[0] * 100 - mkt[e]
            if cvd_sell < p["min_cvd_selling"] or price_chg < p["min_price_chg"]:
                continue
            if not p["min_vol_spike"] <= spike <= p["max_vol_spike"] or rel < p["min_rel_strength"]:
                continue
            wh, wl = max(H[s:e + 1]), min(L[s:e + 1])
            bo = next((j for j in range(e + 1, n) if C[j] > wh), None)
            to_close = (C[-1] - C[e]) / C[e] * 100
            mkt_after = mkt[n - 1] - mkt[e]
            return dict(
                start=T[s][11:16], end=T[e][11:16], bars=k,
                cvd_selling_pct=round(cvd_sell, 1), price_chg_pct=round(price_chg, 2),
                vol_spike=round(spike, 1), rel_strength_pct=round(rel, 2),
                window_high=wh, window_low=wl, signal_close=C[e],
                # outcome fields (validation only)
                breakout=T[bo][11:16] if bo is not None else "",
                window_low_broken=min(L[e + 1:]) < wl,
                max_up_pct=round((max(H[e + 1:]) - C[e]) / C[e] * 100, 2),
                max_down_pct=round((min(L[e + 1:]) - C[e]) / C[e] * 100, 2),
                to_close_pct=round(to_close, 2),
                vs_market_to_close_pct=round(to_close - mkt_after, 2),
            )
    return None


def scan_folder(folder, p=PARAMS):
    data = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        try:
            data[os.path.basename(path)[:-4]] = load(path)
        except ValueError as ex:
            print(f"rejected {os.path.basename(path)}: {ex}", file=sys.stderr)
    mkt = market_curve(data)
    out = []
    for key, d in data.items():
        hit = scan_stock(d, mkt, p)
        if hit:
            sym, _, date = key.rpartition("_")
            out.append(dict(symbol=sym, date=date, **hit))
    return out, len(data), mkt


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folders", nargs="+")
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    allhits = []
    for folder in a.folders:
        hits, nfiles, mkt = scan_folder(folder)
        allhits += hits
        bo = sum(1 for h in hits if h["breakout"])
        avg = lambda k: statistics.mean(h[k] for h in hits) if hits else 0.0
        print(f"\n{os.path.basename(folder.rstrip('/'))}: files={nfiles} market(09:15 close->EOD)={mkt[-1]:+.2f}% "
              f"setups={len(hits)} breakouts={bo} to_close={avg('to_close_pct'):+.2f}% "
              f"vs_market={avg('vs_market_to_close_pct'):+.2f}% low_broken={sum(h['window_low_broken'] for h in hits)}")
        for h in sorted(hits, key=lambda h: -h["cvd_selling_pct"] * h["vol_spike"]):
            print(f"  {h['symbol']:12s} {h['start']}-{h['end']} sell={h['cvd_selling_pct']:4.0f}% "
                  f"px={h['price_chg_pct']:+.2f}% spike={h['vol_spike']:4.1f}x rel={h['rel_strength_pct']:+.2f}% "
                  f"bo={h['breakout'] or '-':5s} up={h['max_up_pct']:+.2f} dn={h['max_down_pct']:+.2f} "
                  f"close={h['to_close_pct']:+.2f} vs_mkt={h['vs_market_to_close_pct']:+.2f}")
    if a.output and allhits:
        with open(a.output, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(allhits[0]))
            w.writeheader()
            w.writerows(allhits)


if __name__ == "__main__":
    main()
