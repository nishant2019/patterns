import csv,statistics as st,math
R=[{k:(float(v) if k not in("date","sym","time") else v) for k,v in r.items()} for r in csv.DictReader(open("events.csv"))]
def summ(rs,f):
    x=[r[f] for r in rs];n=len(x)
    if n<20:return None
    m=st.mean(x);se=st.pstdev(x)/math.sqrt(n)
    days={};[days.setdefault(r["date"],[]).append(r[f]) for r in rs]
    pos=sum(st.mean(v)>0 for v in days.values() if len(v)>=3);tot=sum(1 for v in days.values() if len(v)>=3)
    return n,m,m/se,f"{pos}/{tot}"
db=[(-999,-30),(-30,-15),(-15,-5),(-5,5),(5,15),(15,30),(30,999)]
rb=[(-99,-.5),(-.5,-.15),(-.15,.15),(.15,.5),(.5,99)]
for vs in [(0,1.5),(1.5,99)]:
  for f in ["f2","feod"]:
    print(f"\n=== fwd {f} (market-relative %), vol spike {vs}: rows = bar delta%, cols = bar return%")
    print("delta%      "+"".join(f"{f'{a}..{b}':>22s}" for a,b in rb))
    for a,b in db:
        line=f"{a:>5}..{b:<5} "
        for c,d in rb:
            s=summ([r for r in R if a<=r["dpct"]<b and c<=r["ret"]<d and vs[0]<=r["vspike"]<vs[1]],f)
            line+=f"{'':>22s}" if not s else f"{s[1]:+.2f} t{s[2]:+4.1f} n{s[0]:<5d}{s[3]:>4s} "
        print(line)
