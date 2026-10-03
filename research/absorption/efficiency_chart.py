"""Candle chart with delta-efficiency labels (self-contained HTML + inline SVG).

Panels: price candles (master range shaded) / CVD candles / per-bar delta / efficiency labels.
Efficiency = how far the price move for the delta deviates from what is typical for bars with a similar |delta|,
measured with a robust z-score (median and MAD of peers, pooled over all stocks and days):
  z = -(Pd - median) / (1.4826 x MAD),  Pd = price move in master ranges, signed along the delta.
  Positive z = price moved less than usual (delta absorbed); negative z = price moved more than usual (efficient).
  z >= +2   ABSORBED  (AGAINST when price actually moved opposite to the delta)
  -2 < z < 2  NORM
  z <= -2   STRONG
  -         |net delta| < 10% of volume: not classified
D = net delta % of volume.
Rows:  Bar = this candle alone | Roll 4 = last 4 bars | Since 09:45 = day so far after the opening bar | CVD swing.
CVD swing marker (diamond above the price candle and a chip in the last row): swing = (high_cvd - low_cvd) as % of
the stock-day's average bar volume, ranked vs all bars.  TWO-WAY = top-20% swing whose net delta is <= 30% of the swing (heavy flow in
both directions that netted out); SWING = top-20% swing that ended one-sided.

Usage:
    python efficiency_chart.py TCS 28-09-2026 [-o chart.html] [--png chart.png]
"""
import argparse, bisect, glob, math, os, subprocess, sys, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import load

DMIN = 10.0
STATES = [("AGAINST", "var(--against)"), ("ABSORBED", "var(--ineff)"), ("NORM", "var(--norm)"), ("STRONG", "var(--over)"), ("-", "var(--none)")]


def window(d, a, t):
    """(D, P, raw%) for bars a..t: D = net delta % of window volume, P = price move in master-bar ranges."""
    O, H, L, C, oc, cc, V = (d[k] for k in ("open_price", "high_price", "low_price", "close_price", "open_cvd", "close_cvd", "volume"))
    mr = (H[0] - L[0]) / O[0] * 100
    D = (cc[t] - oc[a]) / sum(V[a:t + 1]) * 100
    P = (C[t] - O[a]) / O[a] * 100 / mr
    return D, P, (C[t] - O[a]) / O[a] * 100


def peer_tables():
    """For each window kind: |D| decile edges and, per decile, (median, 1.4826 x MAD) of Pd = the price move in master ranges signed
    ALONG the delta (positive = price followed the delta, negative = moved against it). Peers = windows with |D| >= DMIN."""
    pts = {k: [] for k in ("bar", "roll", "day")}
    swings = []
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try: d = load(p)
            except ValueError: continue
            n = len(d["close_price"])
            if (d["high_price"][0] - d["low_price"][0]) <= 0: continue
            avgv = sum(d["volume"]) / n
            for t in range(n):
                swings.append((d["high_cvd"][t] - d["low_cvd"][t]) / avgv * 100)
            for t in range(1, n):
                pts["bar"].append(window(d, t, t)[:2])
                if t >= 3:
                    pts["roll"].append(window(d, t - 3, t)[:2])
                    pts["day"].append(window(d, 1, t)[:2])
    tables = {}
    for k, v in pts.items():
        v = sorted((abs(D), (1 if D > 0 else -1) * P) for D, P in v if abs(D) >= DMIN)
        edges = [v[len(v) * q // 10][0] for q in range(1, 10)]
        groups = [[] for _ in range(10)]
        for ad, pd_ in v: groups[bisect.bisect(edges, ad)].append(pd_)
        stats = []
        for g in groups:
            m = st.median(g); mad = st.median(abs(x - m) for x in g) or 1e-9
            stats.append((m, 1.4826 * mad))
        tables[k] = (edges, stats)
    tables["swing"] = sorted(swings)
    return tables


ZMIN = 2.0


def state(D, P, table):
    """Robust conditional z-score of the price move for this delta, vs bars with a similar |delta|:
         z = -(Pd - median) / (1.4826 x MAD)         (positive z = price moved LESS than usual for the delta = absorbed)
    |z| < 2 NORM; z >= 2 ABSORBED (AGAINST if price actually moved opposite to the delta); z <= -2 STRONG (efficient).
    Returns (label, z)."""
    if abs(D) < DMIN: return "-", None
    edges, stats = table
    med, scale = stats[bisect.bisect(edges, abs(D))]
    pd_ = (1 if D > 0 else -1) * P
    z = -(pd_ - med) / scale
    if z >= ZMIN: return ("AGAINST" if pd_ < 0 else "ABSORBED"), z
    if z <= -ZMIN: return "STRONG", z
    return "NORM", z


def swing_state(b, table, avgv):
    """(label, swing %, percentile, net/swing ratio) for one bar. Swing is measured against the stock-day's average
    bar volume, so a high-volume bar is not penalised for its size."""
    rng = b["ch"] - b["cl"]
    pct = 100 * bisect.bisect(table, rng / avgv * 100) / len(table)
    ratio = abs(b["cc"] - b["co"]) / rng if rng > 0 else 1.0
    lab = "-" if pct < 80 else ("TWO-WAY" if ratio <= 0.30 else "SWING")
    return lab, rng / avgv * 100, pct, ratio


def build(sym, date, tables):
    d = load(os.path.join(HERE, "..", "..", "data", f"CVD_Scanner_{date}", f"{sym}_{date}.csv"))
    n = len(d["close_price"])
    O, H, L, C, oc, hc, lc, cc, V, T = (d[k] for k in ("open_price", "high_price", "low_price", "close_price", "open_cvd", "high_cvd", "low_cvd", "close_cvd", "volume", "Time"))
    bars = []
    for i in range(n):
        b = dict(i=i, t=T[i][11:16], o=O[i], h=H[i], l=L[i], c=C[i], co=oc[i], ch=hc[i], cl=lc[i], cc=cc[i], v=V[i], delta=cc[i] - oc[i])
        D, P, raw = window(d, i, i); b["D"] = D; b["ret"] = raw
        if i == 0: b["bar"] = ("MASTER", None)
        else: b["bar"] = state(D, P, tables["bar"])
        b["roll"] = state(*window(d, i - 3, i)[:2], tables["roll"]) if i >= 3 else ("", None)
        b["day"] = state(*window(d, 1, i)[:2], tables["day"]) if i >= 3 else ("", None)
        b["sw"] = swing_state(b, tables["swing"], sum(V) / n)
        bars.append(b)
    return d, bars


def render(sym, date, bars):
    W, left, right = 1120, 118, 30
    n = len(bars); step = (W - left - right) / n; bw = step * 0.5
    X = lambda i: left + step * (i + .5)
    mH, mL = bars[0]["h"], bars[0]["l"]
    pmax, pmin = max(b["h"] for b in bars), min(b["l"] for b in bars)
    pad = (pmax - pmin) * .06; pmax += pad; pmin -= pad
    P0, P1 = 82, 340          # price panel
    C0, C1 = 376, 525         # CVD panel
    D0, D1 = 562, 652         # delta panel
    E0 = 680                  # efficiency strip start
    py = lambda v: P1 - (v - pmin) / (pmax - pmin) * (P1 - P0)
    cmax = max(max(b["ch"] for b in bars), 0); cmin = min(min(b["cl"] for b in bars), 0); cp = (cmax - cmin) * .08
    cmax += cp; cmin -= cp
    cy = lambda v: C1 - (v - cmin) / (cmax - cmin) * (C1 - C0)
    dm = max(abs(b["delta"]) for b in bars) * 1.15
    dy = lambda v: (D0 + D1) / 2 - v / dm * (D1 - D0) / 2
    s = []
    s.append(f'<text x="{left}" y="28" class="title">{sym}  {date.replace("-", " ")}</text>')
    s.append(f'<text x="{left}" y="46" class="sub">Price candles · CVD candles · bar delta · delta efficiency (robust z-score vs bars with similar delta; z>0 = absorbed)</text>')
    # master band
    s.append(f'<rect x="{left}" y="{py(mH):.1f}" width="{W-left-right}" height="{py(mL)-py(mH):.1f}" class="band"/>')
    s.append(f'<line x1="{left}" x2="{W-right}" y1="{py(mH):.1f}" y2="{py(mH):.1f}" class="mline"/><line x1="{left}" x2="{W-right}" y1="{py(mL):.1f}" y2="{py(mL):.1f}" class="mline"/>')
    s.append(f'<text x="{W-right-4}" y="{py(mH)-4:.1f}" class="lbl" text-anchor="end">master high {mH:g}</text><text x="{W-right-4}" y="{py(mL)+12:.1f}" class="lbl" text-anchor="end">master low {mL:g}</text>')
    # price axis
    for k in range(5):
        v = pmin + (pmax - pmin) * k / 4
        s.append(f'<line x1="{left}" x2="{W-right}" y1="{py(v):.1f}" y2="{py(v):.1f}" class="grid"/><text x="{left-8}" y="{py(v)+4:.1f}" class="ax" text-anchor="end">{v:.1f}</text>')
    s.append(f'<text x="{left}" y="{P0-8}" class="pan">Price (shaded = master candle range)</text>')
    for b in bars:
        x = X(b["i"]); up = b["c"] >= b["o"]; cls = "up" if up else "dn"
        tip = (f'{b["t"]}  O {b["o"]:g} H {b["h"]:g} L {b["l"]:g} C {b["c"]:g}  ret {b["ret"]:+.2f}%  delta {b["delta"]/1000:+.1f}K ({b["D"]:+.0f}% of vol)  '
               f'bar efficiency {b["bar"][0]}{"" if b["bar"][1] is None else " (z %+.1f)" % b["bar"][1]}')
        swl, swp, swpc, swr = b["sw"]
        tip += f'  |  CVD swing {swp:.0f}% of avg bar volume (p{swpc:.0f}); CVD fell {(b["co"]-b["cl"])/1000:.1f}K below open, rose {(b["ch"]-b["co"])/1000:.1f}K above; net {b["delta"]/1000:+.1f}K ({swr*100:.0f}% of swing) [{swl}]'
        mark = ""
        if swl != "-":
            mx, my = x, py(b["h"]) - 12
            mark = f'<polygon points="{mx:.1f},{my-6:.1f} {mx+6:.1f},{my:.1f} {mx:.1f},{my+6:.1f} {mx-6:.1f},{my:.1f}" class="mk {"two" if swl=="TWO-WAY" else "one"}"/>'
        s.append(f'<g><title>{tip}</title>{mark}<line x1="{x:.1f}" x2="{x:.1f}" y1="{py(b["h"]):.1f}" y2="{py(b["l"]):.1f}" class="w {cls}"/>'
                 f'<rect x="{x-bw/2:.1f}" y="{py(max(b["o"], b["c"])):.1f}" width="{bw:.1f}" height="{max(abs(py(b["o"])-py(b["c"])), 1):.1f}" class="c {cls}"/></g>')
    # CVD panel
    s.append(f'<rect x="{left}" y="{C0}" width="{W-left-right}" height="{C1-C0}" class="pbox"/><text x="{left}" y="{C0-6}" class="pan">CVD candles (open / high / low / close)</text>')
    s.append(f'<line x1="{left}" x2="{W-right}" y1="{cy(0):.1f}" y2="{cy(0):.1f}" class="zero"/>')
    for k in (cmin, cmax):
        s.append(f'<text x="{left-8}" y="{cy(k)+4:.1f}" class="ax" text-anchor="end">{k/1000:+.0f}K</text>')
    for b in bars:
        x = X(b["i"]); up = b["cc"] >= b["co"]; cls = "up" if up else "dn"
        s.append(f'<g><title>{b["t"]} CVD open {b["co"]/1000:+.1f}K high {b["ch"]/1000:+.1f}K low {b["cl"]/1000:+.1f}K close {b["cc"]/1000:+.1f}K</title>'
                 f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{cy(b["ch"]):.1f}" y2="{cy(b["cl"]):.1f}" class="w {cls}"/>'
                 f'<rect x="{x-bw/2:.1f}" y="{cy(max(b["co"], b["cc"])):.1f}" width="{bw:.1f}" height="{max(abs(cy(b["co"])-cy(b["cc"])), 1):.1f}" class="c {cls}"/></g>')
    # delta panel (bars coloured by this bar's efficiency state)
    s.append(f'<rect x="{left}" y="{D0}" width="{W-left-right}" height="{D1-D0}" class="pbox"/><text x="{left}" y="{D0-6}" class="pan">Bar delta (colour = bar efficiency)</text>')
    s.append(f'<line x1="{left}" x2="{W-right}" y1="{dy(0):.1f}" y2="{dy(0):.1f}" class="zero"/>')
    for b in bars:
        x = X(b["i"]); y0, y1 = dy(0), dy(b["delta"]); fill = dict(STATES).get(b["bar"][0], "var(--none)")
        s.append(f'<rect x="{x-bw/2:.1f}" y="{min(y0, y1):.1f}" width="{bw:.1f}" height="{max(abs(y1-y0), 1):.1f}" style="fill:{fill}"/>'
                 f'<text x="{x:.1f}" y="{(y1-4) if b["delta"]>=0 else (y1+12):.1f}" class="dl" text-anchor="middle">{b["delta"]/1000:+.0f}K</text>')
    # efficiency strip
    rows = [("Bar", "bar"), ("Roll 4", "roll"), ("Since 09:45", "day")]
    for r, (lab, key) in enumerate(rows):
        y = E0 + r * 50
        s.append(f'<text x="{left-8}" y="{y+22}" class="pan" text-anchor="end">{lab}</text>')
        for b in bars:
            st_, de = b[key]; x = X(b["i"])
            if st_ in ("", ):
                continue
            fill = "var(--master)" if st_ == "MASTER" else dict(STATES)[st_]
            s.append(f'<g><title>{b["t"]} {lab}: {st_}{"" if de is None else f" (robust z {de:+.1f}: positive = price moved less than usual for this delta)"}</title><rect x="{x-step*.46:.1f}" y="{y}" width="{step*.92:.1f}" height="38" rx="4" style="fill:{fill}"/>'
                     f'<text x="{x:.1f}" y="{y+16}" class="chip{" n" if st_ == "-" else ""}" text-anchor="middle">{st_}</text>'
                     f'<text x="{x:.1f}" y="{y+31}" class="chip2{" n" if st_ == "-" else ""}" text-anchor="middle">{"" if de is None else "z%+.1f" % de}</text></g>')
    y = E0 + 150
    s.append(f'<text x="{left-8}" y="{y+22}" class="pan" text-anchor="end">CVD swing</text>')
    for b in bars:
        swl, swp, swpc, swr = b["sw"]; x = X(b["i"])
        fill = {"TWO-WAY": "var(--swing)", "SWING": "var(--norm)", "-": "var(--none)"}[swl]
        s.append(f'<g><title>{b["t"]} CVD swing {swp:.0f}% of avg bar volume (p{swpc:.0f}); net {swr*100:.0f}% of swing: {swl}</title><rect x="{x-step*.46:.1f}" y="{y}" width="{step*.92:.1f}" height="38" rx="4" style="fill:{fill}"/>'
                 f'<text x="{x:.1f}" y="{y+16}" class="chip{" n" if swl == "-" else ""}" text-anchor="middle">{swl}</text>'
                 f'<text x="{x:.1f}" y="{y+31}" class="chip2{" n" if swl == "-" else ""}" text-anchor="middle">{swp:.0f}% p{swpc:.0f}</text></g>')
    for b in bars:
        s.append(f'<text x="{X(b["i"]):.1f}" y="{E0+206}" class="ax" text-anchor="middle">{b["t"]}</text>')
    # legend
    lx = left; ly = E0 + 232
    for name, var, desc in (("STRONG", "var(--over)", "z <= -2 efficient"), ("NORM", "var(--norm)", "|z| < 2"), ("ABSORBED", "var(--ineff)", "z >= +2"),
                            ("AGAINST", "var(--against)", "z >= +2, price opposed"), ("-", "var(--none)", "|delta| < 10%")):
        s.append(f'<rect x="{lx}" y="{ly-10}" width="14" height="14" rx="3" style="fill:{var}"/><text x="{lx+20}" y="{ly+2}" class="lg">{name}: {desc}</text>')
        lx += 215
    ly += 22; lx = left
    s.append(f'<polygon points="{lx+6},{ly-10} {lx+12},{ly-4} {lx+6},{ly+2} {lx},{ly-4}" class="mk two"/><text x="{lx+20}" y="{ly+2}" class="lg">TWO-WAY swing: heavy CVD swing that netted out (marker above the candle)</text>')
    s.append(f'<polygon points="{lx+526},{ly-10} {lx+532},{ly-4} {lx+526},{ly+2} {lx+520},{ly-4}" class="mk one"/><text x="{lx+540}" y="{ly+2}" class="lg">one-sided large swing</text>')
    s.append(f'<text x="{left}" y="{ly+28}" class="sub">Efficiency = robust z-score of the price move vs bars with similar |delta|. +z = moved less than usual (absorbed); -z = moved more; |z| >= 2 flagged.</text>')
    s.append(f'<text x="{left}" y="{ly+46}" class="sub">CVD swing = (high CVD - low CVD) as % of the stock-day average bar volume, ranked vs all bars; TWO-WAY = top-20% swing that netted to 30% of itself or less.</text>')
    H_ = E0 + 345
    css = """
:root{--bg:#fff;--fg:#1f2430;--mut:#6b7280;--grid:#e5e7eb;--box:#f8fafc;--band:#2563eb18;--up:#14a085;--dn:#e0463f;--over:#3b82f6;--norm:#9ca3af;--ineff:#f59e0b;--against:#e11d74;--none:#e5e7eb;--master:#6366f1;--chipfg:#fff;--swing:#9333ea}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f141c;--fg:#e5e7eb;--mut:#94a3b8;--grid:#243040;--box:#131a24;--band:#3b82f622;--up:#2dd4a4;--dn:#f87171;--over:#3b82f6;--norm:#6b7280;--ineff:#f59e0b;--against:#ec4899;--none:#2a3441;--master:#6366f1;--swing:#c084fc}}
body{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,-apple-system,Segoe UI,sans-serif}
svg{max-width:100%;height:auto;display:block;margin:0 auto}
.title{font-size:20px;font-weight:700;fill:var(--fg)}.sub{font-size:12px;fill:var(--mut)}.ax{font-size:11px;fill:var(--mut)}.pan{font-size:12px;font-weight:600;fill:var(--mut)}
.lbl{font-size:11px;fill:var(--mut)}.grid{stroke:var(--grid);stroke-width:1}.zero{stroke:var(--mut);stroke-width:1;stroke-dasharray:3 3;opacity:.6}.pbox{fill:var(--box);stroke:var(--grid)}
.band{fill:var(--band)}.mline{stroke:#2563eb;stroke-width:1;stroke-dasharray:5 4;opacity:.7}
.up{stroke:var(--up)}rect.up{fill:var(--up)}.dn{stroke:var(--dn)}rect.dn{fill:var(--dn)}.w{stroke-width:1.5}
.mk{stroke:var(--swing);stroke-width:2}.mk.two{fill:var(--swing)}.mk.one{fill:none}
.chip{font-size:11px;font-weight:700;fill:#fff}.chip2{font-size:11px;fill:#fff;opacity:.95}.chip.n,.chip2.n{fill:var(--mut)}.dl{font-size:10px;fill:var(--mut)}.lg{font-size:11px;fill:var(--fg)}
"""
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{sym} {date} delta efficiency</title><style>{css}</style></head><body>'
            f'<svg viewBox="0 0 {W} {H_}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{sym} candles with CVD and delta efficiency labels">{"".join(s)}</svg></body></html>')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol"); ap.add_argument("date"); ap.add_argument("-o", "--output"); ap.add_argument("--png")
    a = ap.parse_args()
    tables = peer_tables()
    d, bars = build(a.symbol, a.date, tables)
    out = a.output or os.path.join(HERE, "charts", f"{a.symbol}_{a.date}.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(render(a.symbol, a.date, bars))
    print("wrote", out)
    if a.png:
        chrome = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
        subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", f"--screenshot={a.png}", "--window-size=1160,1130", "file://" + os.path.abspath(out)], check=True, capture_output=True)
        print("wrote", a.png)


if __name__ == "__main__":
    main()
