"""Builds the one-page golden-hours matrix (HTML+PNG) from golden_hours.main() and runs the 'does midday coiling lead to a 14:45 expansion' check."""
import os, sys, csv, statistics as st, subprocess, collections, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import golden_hours as G

def coil_to_late():
    out = collections.defaultdict(list)
    for date, sym, d in G.stockdays():
        O, H, L, C = d["open_price"], d["high_price"], d["low_price"], d["close_price"]
        n = len(C)
        if n < 12 or d["Time"][11][11:16] != "14:45": continue
        slots = [t[11:16] for t in d["Time"]]
        rng = [(H[i] - L[i]) / O[i] * 100 for i in range(n)]; md = st.median(rng); mr = st.mean(rng)
        if mr <= 0 or md <= 0: continue
        mid = [i for i in range(n) if "11:15" <= slots[i] <= "13:45"]
        k = sum(rng[i] < .6 * md for i in mid)
        grp = "3+ coil bars 11:15-13:45" if k >= 3 else ("1-2 coil bars" if k >= 1 else "no coil bars")
        mhH, mlL = max(H[i] for i in mid), min(L[i] for i in mid)
        i14 = slots.index("14:15"); i15 = slots.index("14:45")
        out[grp].append((rng[i14] / mr, rng[i15] / mr, abs(C[i15] - O[i14]) / O[i14] * 100,
                         1 if (C[i14] > mhH or C[i14] < mlL) else 0))
    return out

def label(r, allr):
    if r["RangeIdx"] > 2: return "OPEN DRIVE"
    if r["VolIdx"] > 1.8: return "CLOSE VOLUME"
    if r["Coil%"] >= 17 and r["RangeIdx"] < .8: return "COIL ZONE"
    if r["RangeIdx"] >= 1.0: return "ACTIVE"
    return "TRANSITION"

def main():
    rows = G.main()
    for r in rows: r["label"] = label(r, rows)
    def rank(key, rev=True):
        s = sorted(rows, key=lambda r: r[key], reverse=rev); return {r["slot"]: i for i, r in enumerate(s)}
    rk = [rank("RangeIdx"), rank("Move>0.5%"), rank("VolIdx"), rank("Coil%", False), rank("Eff")]
    for r in rows: r["score"] = 100 * (1 - st.mean(k[r["slot"]] for k in rk) / (len(rows) - 1))
    print("\nOpportunity score (mean rank of RangeIdx, Move>0.5%, VolIdx, low Coil%, Eff):")
    for r in sorted(rows, key=lambda r: -r["score"]): print(f"  {r['slot']:6s} {r['score']:5.0f}  {r['label']}")
    lc = coil_to_late()
    print("\nMidday coil (11:15-13:45) -> later activity (RangeIdx, breakout of the midday range at 14:15):")
    for g, v in sorted(lc.items()):
        print(f"  {g:26s} n={len(v):5d}  14:15 RangeIdx {st.mean(x[0] for x in v):.2f}  14:45 RangeIdx {st.mean(x[1] for x in v):.2f}  |14:15->14:45 move| {st.mean(x[2] for x in v):.2f}%  broke midday range by 14:15: {st.mean(x[3] for x in v)*100:.0f}%")
    # ---- HTML heat matrix
    cols = [("Range%", "Avg range %", "{:.2f}", False), ("RangeIdx", "Range index", "{:.2f}", False), ("VolIdx", "Volume index", "{:.2f}", False), ("Vol%day", "% of day volume", "{:.1f}", False),
            ("Move>0.5%", "Bars moving >0.5%", "{:.0f}%", False), ("Eff", "Body/range", "{:.2f}", False), ("Chop%", "Chop bars", "{:.0f}%", True),
            ("Coil%", "Coil bars", "{:.0f}%", True), ("Coil2%", "Coil after coil", "{:.0f}%", True), ("Expand%", "Expand after coil", "{:.0f}%", False), ("score", "Opportunity score", "{:.0f}", False)]
    def colour(v, lo, hi, rev):
        t = 0.5 if hi == lo or v != v else (v - lo) / (hi - lo)
        if rev: t = 1 - t
        a = .12 + .5 * t
        return f"rgba(20,160,133,{a:.2f})" if t >= .5 else f"rgba(224,70,63,{.12 + .5 * (1 - t):.2f})"
    ranges = {k: (min(r[k] for r in rows if r[k] == r[k]), max(r[k] for r in rows if r[k] == r[k])) for k, *_ in cols}
    tag = {"OPEN DRIVE": "#2563eb", "CLOSE VOLUME": "#2563eb", "ACTIVE": "#14a085", "TRANSITION": "#6b7280", "COIL ZONE": "#e0463f"}
    h = ["<table><thead><tr><th>Slot</th><th>Type</th>" + "".join(f"<th>{c[1]}</th>" for c in cols) + "</tr></thead><tbody>"]
    for r in rows:
        h.append(f"<tr><td class=s>{r['slot']}</td><td><span class=t style='background:{tag[r['label']]}'>{r['label']}</span></td>" + "".join(
            f"<td style='background:{colour(r[k], *ranges[k], rev)}'>{'-' if r[k] != r[k] else f.format(r[k])}</td>" for k, _, f, rev in cols) + "</tr>")
    h.append("</tbody></table>")
    css = "body{font-family:system-ui,sans-serif;margin:20px;color:#1f2430;background:#fff}h1{font-size:20px;margin:0 0 4px}p{font-size:12px;color:#6b7280;margin:4px 0 12px;max-width:1100px}table{border-collapse:collapse;font-size:12px}th,td{padding:7px 9px;text-align:center;border:1px solid #fff}th{font-size:11px;color:#6b7280;font-weight:600;max-width:78px}td.s{font-weight:700;text-align:left}.t{color:#fff;font-size:10px;font-weight:700;padding:3px 7px;border-radius:4px;white-space:nowrap}"
    n = rows[0]["n"]; ndays = rows[0]["Days>mean"].split("/")[1]
    html = (f"<!doctype html><html><head><meta charset=utf-8><title>Golden hours</title><style>{css}</style></head><body><h1>Golden hours &amp; coiling hours - 30-minute slots</h1>"
            f"<p>{n} stock-days per slot . Green = better for the column's goal (more movement, more volume, less coiling), red = worse. Range/volume index are relative to each stock's own day average (1.0 = average bar). Coil bar = range below 0.6x that stock's median bar. 15:15* is a 15-minute bar. Opportunity score = mean rank of range index, share of >0.5% bars, volume index, low coil share and body/range.</p>"
            + "".join(h) + "<p>Movement and coiling are reliable (they repeat on every day); bar-to-bar direction is not: after removing the market-wide move, a bar's direction does not predict the next bar in most slots (about 49%); 09:45, 14:45 and 15:15 lean mildly to reversal (46-48%).</p></body></html>")
    out = os.path.join(HERE, "golden_hours.html"); open(out, "w").write(html)
    subprocess.run(["/opt/pw-browsers/chromium-1194/chrome-linux/chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", f"--screenshot={os.path.join(HERE, 'golden_hours.png')}", "--window-size=1320,700", "file://" + out], check=True, capture_output=True)
    print("wrote", out)

if __name__ == "__main__":
    main()
