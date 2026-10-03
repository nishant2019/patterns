"""Inside the coil: which order-flow characteristics (delta, volume, absorption, CVD structure)
carry information? Population: >=3 of the first 4 bars inside the master (n~1,290), decision at 11:15.

Targets: (1) which master edge breaks first (up vs down) among stocks that break out;
         (2) does it break out at all; (3) does the breakout hold (continue) or fail.
Price location of the 11:15 close inside the master range is the strongest known predictor of (1),
so every feature is also evaluated *within* location terciles to see if it adds anything.
"""
import glob, os, sys, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import load
LAST, T_ = 11, 4

def collect():
    rows = []
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]; data = {}
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try: d = load(p)
            except ValueError: continue
            if len(d["close_price"]) > LAST and d["Time"][LAST][11:16] == "14:45":
                data[os.path.basename(p).rsplit("_", 1)[0]] = d
        mk = [st.median((d["close_price"][LAST] - d["close_price"][i]) / d["close_price"][i] * 100 for d in data.values()) for i in range(LAST)]
        for sym, d in data.items():
            O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
            oc, hc, lc, cc, V = d["open_cvd"], d["high_cvd"], d["low_cvd"], d["close_cvd"], d["volume"]
            mH, mL = H[0], L[0]; mr = mH - mL
            t = T_
            if mr <= 0 or sum(H[i] <= mH and L[i] >= mL for i in range(1, t + 1)) < 3: continue
            idx = range(1, t + 1); cv = sum(V[1:t + 1])
            dl = {i: cc[i] - oc[i] for i in range(t + 1)}
            first = next((i for i in range(t + 1, LAST + 1) if C[i] > mH or C[i] < mL), None)
            m_cvd_lo, m_cvd_hi = min(lc[0], oc[0], cc[0]), max(hc[0], oc[0], cc[0])
            coil_cvd_lo = min(lc[i] for i in idx)
            half = V[1] + V[2], V[3] + V[4]
            # absorption bars in the coil: intrabar CVD swing down >= 25% of bar volume but bar closed with CVD recovered >= 60% of it
            absb = sum(1 for i in idx if (oc[i] - lc[i]) / V[i] * 100 >= 25 and (cc[i] - lc[i]) >= 0.6 * (oc[i] - lc[i]))
            row = dict(
                date=date, sym=sym,
                pos=(C[t] - mL) / mr,
                coil_d=sum(dl[i] for i in idx) / cv * 100,
                late_d=(dl[3] + dl[4]) / (V[3] + V[4]) * 100,              # delta in the last two coil bars
                early_d=(dl[1] + dl[2]) / (V[1] + V[2]) * 100,
                d_accel=(dl[3] + dl[4]) / (V[3] + V[4]) * 100 - (dl[1] + dl[2]) / (V[1] + V[2]) * 100,
                pos_bars=sum(dl[i] > 0 for i in idx),
                vol_trend=half[1] / half[0],                              # 2nd-half coil volume / 1st-half
                dryup=(cv / t) / V[0],
                last_vol=V[t] / (cv / t),
                absb=absb,
                cvd_hold=(coil_cvd_lo - m_cvd_lo) / max(m_cvd_hi - m_cvd_lo, 1e-9),   # coil CVD low relative to master CVD range (>0 = held above)
                cvd_pos=(cc[t] - m_cvd_lo) / max(m_cvd_hi - m_cvd_lo, 1e-9),
                master_d=dl[0] / V[0] * 100,
                price_vs_cvd=((C[t] - C[0]) / mr) * 100 - (cc[t] - cc[0]) / max(abs(dl[0]), 1) * 10,  # divergence
                side=None if first is None else (1 if C[first] > mH else -1),
                brk=first is not None)
            if first is not None and first < LAST:
                sg = row["side"]; row["cont"] = sg * ((C[LAST] - C[first]) / C[first] * 100 - mk[first])
            rows.append(row)
    return rows

def auc(pos, neg):
    if not pos or not neg: return 0.5
    return sum((x > y) + .5 * (x == y) for x in pos for y in neg) / (len(pos) * len(neg))

if __name__ == "__main__":
    R = collect(); B = [r for r in R if r["brk"]]
    print(f"coil stocks {len(R)}; broke out {len(B)} ({100*len(B)/len(R):.0f}%); up-first {sum(r['side']>0 for r in B)} down-first {sum(r['side']<0 for r in B)}")
    feats = ["pos", "coil_d", "late_d", "early_d", "d_accel", "pos_bars", "vol_trend", "dryup", "last_vol", "absb", "cvd_hold", "cvd_pos", "master_d", "price_vs_cvd"]
    terc = sorted(r["pos"] for r in B); c1, c2 = terc[len(terc) // 3], terc[2 * len(terc) // 3]
    print("\n(1) DIRECTION of first break (AUC for predicting UP-first; 0.5 = none). 'within loc' = average AUC inside price-location terciles")
    print(f"{'feature':13s} AUC_all  within_loc  | AUC for 'breaks at all'  | AUC for continuation (>0 return after break)")
    for f in feats:
        a = auc([r[f] for r in B if r["side"] > 0], [r[f] for r in B if r["side"] < 0])
        w = []
        for lo, hi in ((-9, c1), (c1, c2), (c2, 9)):
            g = [r for r in B if lo < r["pos"] <= hi]; u = [r[f] for r in g if r["side"] > 0]; n_ = [r[f] for r in g if r["side"] < 0]
            if len(u) >= 15 and len(n_) >= 15: w.append(auc(u, n_))
        b2 = auc([r[f] for r in R if r["brk"]], [r[f] for r in R if not r["brk"]])
        Cn = [r for r in B if "cont" in r]
        # continuation: orient the feature in the break direction
        c3 = auc([r["side"] * r[f] for r in Cn if r["cont"] > 0], [r["side"] * r[f] for r in Cn if r["cont"] <= 0]) if f != "pos" else auc([r["side"] * (r[f] - .5) for r in Cn if r["cont"] > 0], [r["side"] * (r[f] - .5) for r in Cn if r["cont"] <= 0])
        print(f"{f:13s} {a:.2f}     {st.mean(w) if w else float('nan'):.2f}        | {b2:.2f}                      | {c3:.2f}")
