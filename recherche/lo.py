import pandas as pd, numpy as np, heapq
T=pd.read_csv(r'C:/Users/grego/AppData/Local/Temp/claude/C--Users-grego-OneDrive-Daytrading/14097890-a20f-4bd4-aa6c-ea576741d02f/scratchpad/trades.csv',parse_dates=['tin','tout'])
L=T[T.side>0].sort_values('tin').reset_index(drop=True)

print('=== LONG ONLY, par symbole ===')
rows=[]
for s,g in L.groupby('sym'):
    r=g.r.values; w=r[r>0]; l=r[r<=0]
    if len(r)<20: continue
    rng=np.random.default_rng(5); bs=rng.choice(r,size=(3000,len(r)),replace=True).mean(axis=1)
    rows.append(dict(sym=s,n=len(r),expR=r.mean(),PF=w.sum()/-l.sum(),wr=(r>0).mean(),
        RR=w.mean()/abs(l.mean()),lo=np.percentile(bs,2.5),hi=np.percentile(bs,97.5)))
print(pd.DataFrame(rows).sort_values('expR',ascending=False).round(3).to_string(index=False))

print('\n=== LONG ONLY : split temporel (holdout strict) ===')
for lab,sub in (('IS  <2022',L[L.tin<'2022-01-01']),('OOS >=2022',L[L.tin>='2022-01-01'])):
    r=sub.r.values; w=r[r>0]; l=r[r<=0]
    rng=np.random.default_rng(5); bs=rng.choice(r,size=(3000,len(r)),replace=True).mean(axis=1)
    print(f'{lab}: n={len(r):>4} expR={r.mean():+.3f} IC95=[{np.percentile(bs,2.5):+.3f},{np.percentile(bs,97.5):+.3f}] PF={w.sum()/-l.sum():.2f} wr={(r>0).mean()*100:.1f}% R:R={w.mean()/abs(l.mean()):.2f}')

def sim(D,risk,maxpos,cap0=50000.):
    eq=cap0; heap=[]; curve=[(D.tin.iloc[0],eq)]; tk=0
    for _,row in D.iterrows():
        while heap and heap[0][0]<=row.tin:
            to,rd,rr=heapq.heappop(heap); eq+=rd*rr; curve.append((to,eq))
        if len(heap)>=maxpos: continue
        heapq.heappush(heap,(row.tout,eq*risk,row.r)); tk+=1
    while heap:
        to,rd,rr=heapq.heappop(heap); eq+=rd*rr; curve.append((to,eq))
    cv=pd.Series([v for _,v in curve],index=[t for t,_ in curve]).sort_index()
    cv=cv[~cv.index.duplicated(keep='last')]
    dd=((cv.cummax()-cv)/cv.cummax()).max(); yrs=(cv.index[-1]-cv.index[0]).days/365.25
    return eq,(eq/cap0)**(1/yrs)-1,dd,cv,tk

print('\n=== PORTEFEUILLE LONG ONLY, 50 000 $ ===')
print(f"{'risque':>7}{'maxpos':>7}{'pris':>6}{'final':>13}{'CAGR':>8}{'maxDD':>8}{'Calmar':>8}")
for risk in (0.005,0.0075,0.01,0.015,0.02):
    for mp in (3,5,8):
        eq,cagr,dd,cv,tk=sim(L,risk,mp)
        print(f"{risk*100:>6.2f}%{mp:>7}{tk:>6}{eq:>12,.0f}${cagr*100:>7.1f}%{dd*100:>7.1f}%{cagr/dd:>8.2f}")

eq,cagr,dd,cv,tk=sim(L,0.01,5)
a=cv.resample('YE').last().ffill().pct_change().dropna()*100
print(f'\n=== annuel @ risque 1%/trade, max 5 positions  (final {eq:,.0f}$, CAGR {cagr*100:.1f}%, maxDD {dd*100:.1f}%) ===')
print(a.round(1).to_string())
print(f'annees positives: {(a>0).sum()}/{len(a)}  |  pire annee: {a.min():.1f}%  |  {tk/14.6:.0f} trades/an')
