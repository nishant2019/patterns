import csv,statistics as st,math,sys
R=[{k:(float(v) if k not in("date","sym","time") else v) for k,v in r.items()} for r in csv.DictReader(open("events.csv"))]
# demean forward returns per (day, bar) so the benchmark is the average stock at that time
grp={}
for r in R: grp.setdefault((r["date"],r["bar"]),[]).append(r)
for g in grp.values():
    for f in("f1","f2","feod"):
        m=st.mean(x[f] for x in g)
        for x in g: x[f+"x"]=x[f]-m
PAT={
 "SA  sell-absorb: d<=-30 ret[-.5,.15] spike>=1.5": lambda r:r["dpct"]<=-30 and -.5<=r["ret"]<=.15 and r["vspike"]>=1.5,
 "SA2 sell-absorb: d<=-30 ret[-.15,.15] any vol":   lambda r:r["dpct"]<=-30 and -.15<=r["ret"]<=.15,
 "SC  sell-continue: d<=-30 ret<-.5 spike>=1.5":    lambda r:r["dpct"]<=-30 and r["ret"]<-.5 and r["vspike"]>=1.5,
 "SR  sell-into-rally: d<=-30 ret>.15 spike>=1.5":  lambda r:r["dpct"]<=-30 and r["ret"]>.15 and r["vspike"]>=1.5,
 "BA  buy-absorb: d>=30 ret[-.15,.5]... wait": None,
}
PAT.pop("BA  buy-absorb: d>=30 ret[-.15,.5]... wait")
PAT.update({
 "BA  buy-absorb: d>=30 ret[-.15,.15] spike>=1.5":  lambda r:r["dpct"]>=30 and -.15<=r["ret"]<=.15 and r["vspike"]>=1.5,
 "BA2 buy-absorb: d>=30 ret[-.15,.15] any vol":     lambda r:r["dpct"]>=30 and -.15<=r["ret"]<=.15,
 "BC  buy-climax: d>=30 ret>.5 spike>=1.5":         lambda r:r["dpct"]>=30 and r["ret"]>.5 and r["vspike"]>=1.5,
 "BD  buy-into-drop: d>=30 ret<-.15 spike>=1.5":    lambda r:r["dpct"]>=30 and r["ret"]<-.15 and r["vspike"]>=1.5,
 "DV+ bull div 3bar: price>=0, cvd3<=-20":          lambda r:r["pr3"]>=0 and r["cvd3"]<=-20,
 "DV- bear div 3bar: price<=0, cvd3>=+20":          lambda r:r["pr3"]<=0 and r["cvd3"]>=20,
 "WK+ bar: CVD pushed<=-40 inside, close top 40%":  lambda r:r["push_dn"]<=-40 and r["cloc"]>=.6,
 "WK- bar: CVD pushed>=+40 inside, close bottom 40%":lambda r:r["push_up"]>=40 and r["cloc"]<=.4,
})
def rep(name,rs):
    out=f"{name:52s} n={len(rs):5d}"
    for f in("f1x","f2x","feodx"):
        x=[r[f] for r in rs]
        if len(x)<15: out+="   -";continue
        m=st.mean(x);t=m/(st.pstdev(x)/math.sqrt(len(x)))
        dd={};[dd.setdefault(r["date"],[]).append(r[f]) for r in rs]
        cons=sum(st.mean(v)>0 for v in dd.values())
        out+=f" | {f[:-1]:4s} {m:+.2f} t{t:+4.1f} {cons}/{len(dd)}+"
    print(out)
print("Forward returns vs the average stock at the same time (%), t-stat, days positive")
for k,fn in PAT.items(): rep(k,[r for r in R if fn(r)])
if "split" in sys.argv:
    print("\nSA by time of day / day-range position")
    sa=[r for r in R if PAT["SA  sell-absorb: d<=-30 ret[-.5,.15] spike>=1.5"](r)]
    for lab,fn in [("bars 1-3 (09:45-10:45)",lambda r:r["bar"]<=3),("bars 4-7",lambda r:4<=r["bar"]<=7),("bars 8+",lambda r:r["bar"]>=8),
                   ("near day low (dpos<.33)",lambda r:r["dpos"]<.33),("mid",lambda r:.33<=r["dpos"]<=.67),("near day high (dpos>.67)",lambda r:r["dpos"]>.67),
                   ("spike 1.5-3",lambda r:r["vspike"]<3),("spike >=3",lambda r:r["vspike"]>=3),("d<=-50",lambda r:r["dpct"]<=-50),("d -30..-50",lambda r:r["dpct"]>-50),
                   ("close loc >=.5",lambda r:r["cloc"]>=.5),("close loc <.5",lambda r:r["cloc"]<.5)]:
        rep("  "+lab,[r for r in sa if fn(r)])
