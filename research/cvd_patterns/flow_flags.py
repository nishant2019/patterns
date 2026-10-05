"""CVD-only flags (7-day study, research/cvd_patterns/REPORT.md part 3). They say how the FLOW is likely to behave next bar, not where price goes.
FLOW BUY / FLOW SELL : |bar delta| >= 30% of volume -> next bar tends to push the same way (selling 65%, buying 56% of the time; ~+8% delta vs baseline).
                       STRONG when it is a bullish marubozu or three white soldiers (the only shapes that add information beyond delta size).
QUIET                : CVD doji / spinning top -> next CVD bar tends to be narrower (-1.3 to -1.9% of volume).
"""
def flow_flag(d, i):
    o, h, l, c, V = d["open_cvd"], d["high_cvd"], d["low_cvd"], d["close_cvd"], d["volume"]
    D = (c[i] - o[i]) / V[i] * 100
    rng = max(h[i] - l[i], 1e-9); body = abs(c[i] - o[i]); bf = body / rng
    uw = (h[i] - max(o[i], c[i])) / rng; lw = (min(o[i], c[i]) - l[i]) / rng
    if abs(D) >= 30:
        strong = False
        if D > 0:
            soldiers = i >= 2 and all(c[k] > o[k] and c[k] / 1 > c[k - 1] / 1 and (c[k] - o[k]) / max(h[k] - l[k], 1e-9) > .5 for k in (i - 1, i)) and c[i - 2] > o[i - 2] and (c[i - 2] - o[i - 2]) / max(h[i - 2] - l[i - 2], 1e-9) > .5 and o[i - 1] > o[i - 2] and o[i] > o[i - 1]
            strong = bf > .9 or soldiers
        return ("BUY" if D > 0 else "SELL", "STRONG" if strong else "", D,
                "big delta bar: next bar continues the same way (buying ~56%, selling ~65% of the time)")
    if bf < .1 or (bf < .3 and uw > .25 and lw > .25):
        return ("QUIET", "", D, "CVD doji / spinning top: next CVD bar tends to be narrower")
    return ("-", "", D, "")
