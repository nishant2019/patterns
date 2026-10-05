"""One-page regime summary (HTML): every regime, its stocks, and the key levels to watch.

Usage:
    python regime_summary.py 28-09-2026 [--time 11:15] [--top 12] [--outcomes] [-o file.html] [--png file.png]
`--outcomes` adds the realised move to the close (only meaningful on past days).
"""
import argparse, glob, html, os, statistics as st, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab")); sys.path.insert(0, HERE)
from oab_scanner import load
from regime_scanner import analyse, NAMES, PLAN, TIMES
sys.path.insert(0, os.path.join(HERE, "..", "absorption"))
from efficiency_chart import peer_tables, maha_state, window  # joint-outlier test (Mahalanobis)
from regime_study import structure
sys.path.insert(0, os.path.join(HERE, "..", "cvd_patterns"))
from flow_flags import flow_flag

# Historical statistics from REPORT.md (6 days, pooled over six decision times; vs the median stock)
STATS = {
 "A": "+0.17% to close vs the median stock (baseline +0.06%), positive on 6/7 days; 53% later break the master range, 66% of those up",
 "B": "+0.07%, 6/7 days; side set by location: upper third breaks up ~80-93%, lower third breaks down ~91%",
 "C": "+0.005%, 3/7 days: no edge over the baseline; was negative over the first 6 days, so chasing is unproven rather than proven bad",
 "C2": "+0.12%, 5/7 days: trend intact, modest",
 "D": "-0.03%, 2/7 days: weak, avoid longs",
 "D2": "+0.06%, 5/7 days: reclaim candidate, unproven",
 "E": "+0.12%, 7/7 days (the most consistent regime); first break goes down ~65%",
}
ORDER = ["A", "B", "C", "C2", "D", "D2", "E"]
CSS = """
:root{--bg:#fff;--fg:#1f2430;--mut:#6b7280;--line:#e5e7eb;--card:#f8fafc;--A:#14a085;--B:#6b7280;--C:#e11d74;--C2:#3b82f6;--D:#dc2626;--D2:#f59e0b;--E:#9333ea}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f141c;--fg:#e5e7eb;--mut:#94a3b8;--line:#243040;--card:#131a24;--A:#2dd4a4;--B:#94a3b8;--C:#ec4899;--C2:#60a5fa;--D:#f87171;--D2:#fbbf24;--E:#c084fc}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1180px;margin:0 auto;padding:20px 16px 40px}h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mut);margin:0 0 14px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}.chip{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:4px 12px;font-size:13px}.chip b{font-weight:700}
section{border:1px solid var(--line);border-left:5px solid var(--c);background:var(--card);border-radius:10px;margin:0 0 16px;padding:12px 14px}
section h2{font-size:16px;margin:0 0 2px;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}section h2 .n{color:var(--mut);font-weight:400;font-size:13px}
.stat{color:var(--mut);font-size:12.5px;margin:0 0 8px}.plan{font-size:13px;margin:0 0 10px}.plan b{color:var(--c)}
.tbl{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th{font-weight:600;color:var(--mut);text-align:right;padding:4px 6px;border-bottom:1px solid var(--line);white-space:nowrap}td{padding:4px 6px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--card);font-weight:600}td.l,th.l{text-align:left}
tr:last-child td{border-bottom:0}.pos{color:var(--A)}.neg{color:var(--D)}.flag{font-size:11px;border:1px solid var(--line);border-radius:4px;padding:0 5px;color:var(--mut)}
details{margin-top:8px}summary{cursor:pointer;color:var(--mut);font-size:13px}.note{color:var(--mut);font-size:12px;margin-top:18px;border-top:1px solid var(--line);padding-top:10px}
"""

def size_outliers(d, t, tables):
    """SIZE-driven selling outliers (Mahalanobis d > 3.06, driver SIZE, delta < -10%) among bars 1..t. combo = at that bar (10:45 or later, the
    population of the 7-day study) the close was in the lower third of the day's range so far AND inside the master candle."""
    O, H, L, C, V = d["open_price"], d["high_price"], d["low_price"], d["close_price"], d["volume"]
    mH, mL = H[0], L[0]; avgv = sum(V) / len(V); out = []
    for i in range(1, t + 1):
        D, P, raw = window(d, i, i)
        if D >= -10: continue
        lab, dist, drv = maha_state(D, -P, V[i] / (sum(V[:i]) / i), tables["maha"])
        if lab != "OUTLIER" or drv != "SIZE": continue
        hi, lo = max(H[:i + 1]), min(L[:i + 1])
        dpos = (C[i] - lo) / max(hi - lo, 1e-9)
        inside = structure(C[i], mH, mL).startswith("inside")
        out.append(dict(i=i, time=d["Time"][i][11:16], d=dist, D=D, delta=d["close_cvd"][i] - d["open_cvd"][i], size=abs(d["close_cvd"][i] - d["open_cvd"][i]) / avgv, spike=V[i] / (sum(V[:i]) / i),
                        close=C[i], dpos=dpos, inside=inside, combo=i >= 3 and dpos < 1 / 3 and inside, new=(i == t),
                        to_close=(C[11] - C[i]) / C[i] * 100 if len(C) > 11 else None))
    return out

def rows_for(folder, t, tables=None):
    tables = tables or peer_tables()
    out = []
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        try: d = load(path)
        except ValueError: continue
        r = analyse(d, t)
        if not r: continue
        r["symbol"] = os.path.basename(path).rsplit("_", 1)[0]
        mr = r["master_high"] - r["master_low"]
        r["to_hi"] = (r["master_high"] - r["close"]) / mr          # in master ranges (negative = above)
        r["to_lo"] = (r["close"] - r["master_low"]) / mr
        n = len(d["close_price"]); C = d["close_price"]
        r["to_close"] = (C[11] - C[t]) / C[t] * 100 if n > 11 else None
        r["size_out"] = size_outliers(d, t, tables)
        r["flow"] = flow_flag(d, t)
        out.append(r)
    return out

def rank_key(k):
    return {"A": lambda r: (-(r["pos"] >= 2 / 3), r["D"]),                    # upper third first, then heaviest absorbed selling
            "B": lambda r: min(abs(r["to_hi"]), abs(r["to_lo"])),               # closest to a master edge
            "C": lambda r: -r["price_chg"], "C2": lambda r: r["to_hi"], "D": lambda r: r["D"],
            "D2": lambda r: abs(r["to_lo"]), "E": lambda r: -r["D"]}[k]

def levels(k, r):
    """(watch level, label, invalidation level, label) for the plan."""
    mh, ml = r["master_high"], r["master_low"]
    inval_a = min(ml, r["day_low"]) if r["undercut"] else ml
    return {"A": (mh, "break above", inval_a, "close below"), "B": ((mh, "upper edge", ml, "lower edge") if r["pos"] >= .5 else (ml, "lower edge", mh, "upper edge")),
            "C": (mh, "failed if back below", None, ""), "C2": (mh, "hold above", None, ""),
            "D": (ml, "reclaim above", None, ""), "D2": (ml, "reclaim above", None, ""), "E": (ml, "break below", mh, "accept above")}[k]

def table(k, rs, outcomes):
    head = ["Stock", "Close", "Master range", "Position", "Delta*", "Price*", "Vol", "Watch", "Invalid", "Notes"] + (["To close"] if outcomes else [])
    o = ["<div class=tbl><table><thead><tr>" + "".join(f"<th{' class=l' if h in ('Watch','Invalid','Notes') else ''}>{h}</th>" for h in head) + "</tr></thead><tbody>"]
    for r in rs:
        w, wl, iv, il = levels(k, r)
        notes = []
        if r["undercut"]: notes.append(f"<span class=flag>undercut {r['day_low']:g}</span>")
        if r["vol_trend"] >= 1.3: notes.append("<span class=flag>volume rising</span>")
        if r["inside"] >= 3: notes.append(f"<span class=flag>coil {r['inside']} bars</span>")
        so = [x for x in r.get("size_out", []) if x["combo"]]
        if so: notes.append(f"<span class=flag style='border-color:var(--E);color:var(--E)'>SIZE sell outlier {so[-1]['time']}</span>")
        fc, fs, fD, fdesc = r.get("flow", ("-", "", 0, ""))
        if fc in ("BUY", "SELL"):
            col = "var(--E)" if fc == "BUY" else "var(--D)"
            notes.append(f"<span class=flag title='{fdesc}' style='border-color:{col};color:{col}'>FLOW {fc}{'+' if fs else ''} {fD:+.0f}%</span>")
        elif fc == "QUIET": notes.append(f"<span class=flag title='{fdesc}'>QUIET</span>")
        cls = lambda v: "pos" if v > 0 else "neg"
        cells = [f"<td>{html.escape(r['symbol'])}</td>", f"<td>{r['close']:g}</td>", f"<td>{r['master_low']:g} – {r['master_high']:g}</td>",
                 f"<td>{('above high' if r['struct'].startswith('ABOVE') else 'below low' if r['struct'].startswith('BELOW') else r['struct'].replace('inside, ', '') + ' ' + format(r['pos']*100, '.0f') + '%')}</td>",
                 f"<td class={cls(r['D'])}>{r['D']:+.0f}%</td>", f"<td class={cls(r['price_chg'])}>{r['price_chg']:+.2f}%</td>", f"<td>{r['vol_trend']:.1f}×</td>",
                 f"<td class=l>{wl} {w:g}</td>", f"<td class=l>{(il + ' ' + format(iv, 'g')) if iv is not None else '–'}</td>", f"<td class=l>{' '.join(notes)}</td>"]
        if outcomes: cells.append(f"<td class={cls(r['to_close'] or 0)}>{'' if r['to_close'] is None else format(r['to_close'], '+.2f') + '%'}</td>")
        o.append("<tr>" + "".join(cells) + "</tr>")
    o.append("</tbody></table></div>")
    return "".join(o)

def watchlist(rows, outcomes):
    items = []
    for r in rows:
        for x in r.get("size_out", []):
            if x["combo"]: items.append((r, x))
    items.sort(key=lambda rx: (-rx[1]["new"], -rx[1]["i"], -rx[1]["d"]))
    head = ["Stock", "Outlier bar", "Delta", "% of vol", "Size*", "Spike", "d", "Close", "Master range", "Now (regime)"] + (["From outlier to close (raw)"] if outcomes else [])
    o = [f"<section style='--c:var(--E)'><h2>Watchlist · SIZE-driven selling outliers, lower third + inside master <span class=n>{len(items)} bars in {len({r['symbol'] for r, _ in items})} stocks (bars at this decision time first)</span></h2>"
         "<p class=stat>History (7 days, research/absorption/REPORT.md): 72 such bars returned <b>+0.55%</b> to the close vs the median stock (median +0.49%, 74% win, positive on 6 of 7 days); all SIZE-driven selling outliers +0.21%; "
         "either condition alone about +0.04%. The subgroup was found after examining about 25 splits: a hypothesis to confirm on new days, not a rule.</p>"
         "<p class=plan><b>What it is:</b> a bar with at least 10% net selling delta that is a joint outlier (Mahalanobis d &gt; 3.06) because the selling delta was exceptionally large, "
         "while price sat in the lower third of the day's range and inside the master candle (bars from 10:45 on, as in the study). <b>Invalid if:</b> a close below the master low or the day's low since 09:45. *Size = delta in average-bar volumes.</p>"]
    if not items:
        o.append("<p class=stat>No stocks with this flag.</p></section>"); return "".join(o)
    o.append("<div class=tbl><table><thead><tr>" + "".join(f"<th{' class=l' if h in ('Now (regime)',) else ''}>{h}</th>" for h in head) + "</tr></thead><tbody>")
    for r, x in items[:40]:
        cells = [f"<td>{html.escape(r['symbol'])}</td>", f"<td>{x['time']}{' (latest)' if x['new'] else ''}</td>", f"<td class=neg>{x['delta']/1000:+.1f}K</td>", f"<td>{abs(x['D']):.0f}%</td>", f"<td>{x['size']:.2f}</td>", f"<td>{x['spike']:.1f}×</td>", f"<td>{x['d']:.1f}</td>", f"<td>{x['close']:g}</td>",
                 f"<td>{r['master_low']:g} – {r['master_high']:g}</td>", f"<td class=l>{r['regime']} · {r['struct'].replace('inside, ', '')}</td>"]
        if outcomes: cells.append(f"<td class={'pos' if (x['to_close'] or 0) > 0 else 'neg'}>{'' if x['to_close'] is None else format(x['to_close'], '+.2f') + '%'}</td>")
        o.append("<tr>" + "".join(cells) + "</tr>")
    o.append("</tbody></table></div>")
    if len(items) > 40: o.append(f"<p class=stat>{len(items)-40} more bars not shown.</p>")
    o.append("</section>")
    return "".join(o)

def render(date, tm, rows, top, outcomes):
    n = len(rows)
    above = sum(r["struct"].startswith("ABOVE") for r in rows); below = sum(r["struct"].startswith("BELOW") for r in rows)
    counts = {k: sum(r["regime"] == k for r in rows) for k in ORDER}
    pdate = date.replace("-", " ")
    body = [f"<h1>Regime summary · {pdate} · {tm}</h1><p class=sub>{n} stocks. Regimes from master-candle structure and price-vs-delta flow since the 09:45 open. Levels are the master (09:15) candle's range and the day's low since 09:45. *Delta = net CVD change since 09:45 as % of volume; Price = price change since 09:45; Vol = volume trend (recent bars vs earlier).</p>"]
    body.append("<div class=chips>" + f"<span class=chip>Above master high <b>{above}</b> ({100*above/n:.0f}%)</span><span class=chip>Below master low <b>{below}</b> ({100*below/n:.0f}%)</span>" + "".join(f"<span class=chip>{k} <b>{counts[k]}</b></span>" for k in ORDER) + "</div>")
    body.append(watchlist(rows, outcomes))
    for k in ORDER:
        rs = sorted([r for r in rows if r["regime"] == k], key=rank_key(k))
        bias, trig, inv = PLAN[k]
        body.append(f"<section style='--c:var(--{k})'><h2>{k} · {NAMES[k]} <span class=n>{len(rs)} stocks" + (f", top {top} shown" if len(rs) > top else "") + f"</span></h2><p class=stat>History: {STATS[k]}</p>"
                    f"<p class=plan><b>Bias:</b> {html.escape(bias)} <b>Plan:</b> {html.escape(trig)} <b>Invalid if:</b> {html.escape(inv)}</p>")
        if rs:
            body.append(table(k, rs[:top], outcomes))
            if len(rs) > top: body.append(f"<details><summary>Show the other {len(rs)-top} stocks</summary>{table(k, rs[top:], outcomes)}</details>")
        else: body.append("<p class=stat>No stocks in this regime.</p>")
        body.append("</section>")
    body.append("<p class=note>Edges are small and relative to the median stock (regime A about +0.11% above a +0.06% baseline, before costs), measured over 7 trading days and shrinking as days are added. Use the regimes to decide where to look and what to avoid, not as automatic entries. Flags on the last bar: FLOW BUY/SELL = |delta| >= 30% of volume, the next bar usually continues the same way (selling about 65%, buying about 56%; + = bullish marubozu / three white soldiers); QUIET = CVD doji or spinning top, next bar usually narrower. They describe flow persistence, not price direction (no price edge found). Rankings: A upper-third first then heaviest absorbed selling; B closest to a master edge; C largest move; D most selling; D2 closest to the master low; E heaviest buying.</p>")
    return f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Regime summary {pdate} {tm}</title><style>{CSS}</style></head><body><main>{''.join(body)}</main></body></html>"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("date"); ap.add_argument("--time", default="11:15"); ap.add_argument("--top", type=int, default=10); ap.add_argument("--outcomes", action="store_true")
    ap.add_argument("-o", "--output"); ap.add_argument("--png")
    a = ap.parse_args()
    folder = os.path.join(HERE, "..", "..", "data", f"CVD_Scanner_{a.date}")
    rows = rows_for(folder, TIMES[a.time])
    out = a.output or os.path.join(HERE, "summaries", f"regime_summary_{a.date}_{a.time.replace(':', '')}{'_review' if a.outcomes else ''}.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(render(a.date, a.time, rows, a.top, a.outcomes))
    print("wrote", out, f"({len(rows)} stocks)")
    if a.png:
        subprocess.run(["/opt/pw-browsers/chromium-1194/chrome-linux/chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", f"--screenshot={a.png}", "--window-size=1240,3400", "file://" + os.path.abspath(out)], check=True, capture_output=True)
        print("wrote", a.png)

if __name__ == "__main__":
    main()
