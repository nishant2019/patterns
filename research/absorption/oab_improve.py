"""Which point-in-time features at OAB window end predict window-end -> close return vs the average stock?

Tested on the 'base' set (OAB with bar-level/location filters removed, ~450 setups) and on OAB itself (~67).
"""
import glob, os, sys, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scanners", "oab"))
from oab_scanner import PARAMS, load, scan_stock

BASE = dict(PARAMS, heavy_min_ret=-9.0, heavy_max_ret=9.0, heavy_max_delta=999.0,
            min_close_in_window=0.0, max_price_chg=0.5, max_hold=1.5)

def collect():
    rows = []
    for folder in sorted(glob.glob(os.path.join(HERE, "..", "..", "data", "CVD_Scanner_*"))):
        date = folder.rsplit("_", 1)[1]
        data = {}
        for p in glob.glob(os.path.join(folder, "*.csv")):
            try: data[os.path.basename(p).rsplit("_", 1)[0]] = load(p)
            except ValueError: pass
        n = min(len(d["close_price"]) for d in data.values())
        a2c = [st.mean((d["close_price"][-1]-d["close_price"][i])/d["close_price"][i]*100 for d in data.values()) for i in range(n)]
        dayret = [st.mean((d["close_price"][i]-d["close_price"][0])/d["close_price"][0]*100 for d in data.values()) for i in range(n)]
        for sym, d in data.items():
            hb = scan_stock(d, BASE)
            if not hb: continue
            oab = scan_stock(d, PARAMS) is not None
            O,H,L,C=d["open_price"],d["high_price"],d["low_price"],d["close_price"]
            oc,cc,V=d["open_cvd"],d["close_cvd"],d["volume"]
            T=[t[11:16] for t in d["Time"]]; e=T.index(hb["end"]); s=T.index(hb["start"])
            hi,lo=max(H[:e+1]),min(L[:e+1]); wv=sum(V[s:e+1])/(e-s+1)
            rows.append(dict(date=date,sym=sym,oab=oab,e=e,bo=bool(hb["breakout"]),
                rel=hb["to_close_pct"]-a2c[e],
                dpos=(C[e]-lo)/max(hi-lo,1e-9),
                relstr=(C[e]-C[0])/C[0]*100-dayret[e],
                mkt=dayret[e],
                bars=e-s+1,
                wvol=wv/(sum(V[:s])/s) if s>0 else 1,           # window avg volume vs prior bars
                wvol_m=wv/V[0],
                lastd=(cc[e]-oc[e])/V[e]*100,                   # last bar delta %
                lastspike=V[e]/(sum(V[:e])/e),
                cvdsell=hb["cvd_selling_pct"],
                closewin=hb["close_in_window"],
                hold=hb["hold_pct"],
                hlratio=hb["last_hl_pct"]/max(hb["first_hl_pct"],1e-9),
                heavyd=hb["heavy_delta_pct"],heavyr=hb["heavy_ret_pct"],
                late=e))
    return rows

def auc(rs,f):
    a=[r[f] for r in rs if r["rel"]>0];b=[r[f] for r in rs if r["rel"]<=0]
    return sum((x>y)+.5*(x==y) for x in a for y in b)/(len(a)*len(b))

if __name__=="__main__":
    R=collect()
    base=R; oab=[r for r in R if r["oab"]]
    feats=["dpos","relstr","mkt","bars","wvol","wvol_m","lastd","lastspike","cvdsell","closewin","hold","hlratio","heavyd","heavyr","late"]
    print(f"base n={len(base)} (rel>0: {sum(r['rel']>0 for r in base)}), OAB n={len(oab)}")
    print(f"{'feature':10s} AUC_base AUC_oab | mean rel by tercile of feature (base): low / mid / high")
    for f in sorted(feats,key=lambda f:-abs(auc(base,f)-.5)):
        xs=sorted(r[f] for r in base);c1,c2=xs[len(xs)//3],xs[2*len(xs)//3]
        t=[[r["rel"] for r in base if r[f]<=c1],[r["rel"] for r in base if c1<r[f]<=c2],[r["rel"] for r in base if r[f]>c2]]
        print(f"{f:10s} {auc(base,f):.2f}     {auc(oab,f):.2f}    | "+" / ".join(f"{st.mean(x):+.2f}" if x else "-" for x in t)+f"   (cuts {c1:.2f}, {c2:.2f})")
