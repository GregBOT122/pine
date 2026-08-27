import glob, numpy as np, pandas as pd
CACHE=r'C:/Users/grego/dev/Daytrading/bot/xaubot/xaubot/data/cache'
FRICTION={'XAUUSD':.015,'XAGUSD':.030,'US30':.012,'US500':.012,'USTEC':.014,'EURUSD':.008,
 'GBPUSD':.010,'USDJPY':.010,'BTCUSDT':.090,'ETHUSDT':.090,'SOLUSDT':.090,
 'AAPL':.020,'MSFT':.020,'NVDA':.020,'GOOGL':.025,'AMZN':.025,'TSLA':.030}   # META exclu: split 20:1 non ajuste
N,K,M,E,MAXB=40,1.5,3.5,200,400

def load(s):
    fs=sorted(glob.glob(f'{CACHE}/{s}_H1_*.parquet'))
    if not fs: return None
    d=pd.concat([pd.read_parquet(f) for f in fs]); d=d[~d.index.duplicated()].sort_index()
    return d[['open','high','low','close']].dropna().resample('4h').agg(
        {'open':'first','high':'max','low':'min','close':'last'}).dropna()

def atr(d,n=14):
    pc=d.close.shift(1)
    tr=pd.concat([d.high-d.low,(d.high-pc).abs(),(d.low-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False).mean()

def bt(d,fric):
    o,h,l,c=d.open.values,d.high.values,d.low.values,d.close.values
    A=atr(d).values; Em=d.close.ewm(span=E,adjust=False).mean().values
    hh=d.high.rolling(N).max().shift(1).values; ll=d.low.rolling(N).min().shift(1).values
    n=len(d); out=[]; i=max(N,E,20)+1
    while i<n-1:
        a=A[i]
        if not np.isfinite(a) or a<=0: i+=1; continue
        sd=1 if (c[i]>hh[i] and c[i]>Em[i]) else (-1 if (c[i]<ll[i] and c[i]<Em[i]) else 0)
        if sd==0: i+=1; continue
        j=i+1; entry=o[j]; R=K*a; stop=entry-sd*R; ext=entry; xp=None; k=j
        while k<n and k-j<MAXB:
            if sd>0:
                if l[k]<=stop: xp=min(stop,o[k]); break
                ext=max(ext,h[k]); stop=max(stop,ext-M*A[k])
            else:
                if h[k]>=stop: xp=max(stop,o[k]); break
                ext=min(ext,l[k]); stop=min(stop,ext+M*A[k])
            k+=1
        if xp is None: k=min(k,n-1); xp=c[k]
        out.append((d.index[j],d.index[k],sd,(sd*(xp-entry)-entry*fric/100)/R,k-j))
        i=k+1
    return pd.DataFrame(out,columns=['tin','tout','side','r','bars'])

T=[]
for s,f in FRICTION.items():
    d=load(s)
    if d is None or len(d)<600: continue
    t=bt(d,f); t['sym']=s; T.append(t)
T=pd.concat(T).sort_values('tin').reset_index(drop=True)
r=T.r.values; w=r[r>0]; ls=r[r<=0]
rng=np.random.default_rng(11); bs=rng.choice(r,size=(5000,len(r)),replace=True).mean(axis=1)
print(f'=== POOLE {T.sym.nunique()} symboles, H4, Donchian{N}/stop{K}ATR/trail{M}ATR ===')
print(f'n={len(r)}   expR={r.mean():+.4f}   IC95=[{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]')
print(f'PF={w.sum()/-ls.sum():.3f}   winrate={(r>0).mean()*100:.1f}%   R:R={w.mean()/abs(ls.mean()):.2f}   avgW={w.mean():+.2f}R  avgL={ls.mean():+.2f}R')
print(f'pire trade={r.min():.1f}R   meilleur={r.max():.1f}R   duree med={T.bars.median():.0f}xH4 = {T.bars.median()*4/24:.1f} j')
print(f'\nrepartition long/short: long expR={T[T.side>0].r.mean():+.3f} (n={(T.side>0).sum()})  short expR={T[T.side<0].r.mean():+.3f} (n={(T.side<0).sum()})')

def sim(risk,maxpos,cap0=50000.):
    eq=cap0; open_=[]; curve=[]
    for _,row in T.iterrows():
        open_=[p for p in open_ if p[0]<=row.tin] and open_
        due=[p for p in open_ if p[0]<=row.tin]
        for p in due: eq+=p[1]*p[2]
        open_=[p for p in open_ if p[0]>row.tin]
        if len(open_)>=maxpos: curve.append((row.tin,eq)); continue
        open_.append((row.tout,eq*risk,row.r))
        curve.append((row.tin,eq))
    for p in open_: eq+=p[1]*p[2]
    cv=pd.Series(dict(curve)); cv.loc[T.tout.max()]=eq; cv=cv.sort_index()
    dd=((cv.cummax()-cv)/cv.cummax()).max()
    yrs=(cv.index[-1]-cv.index[0]).days/365.25
    return eq,(eq/cap0)**(1/yrs)-1,dd,yrs,cv

print(f'\n=== PORTEFEUILLE 50 000 $ (positions concurrentes, {len(r)/14.6:.0f} trades/an) ===')
for risk in (0.0025,0.005,0.0075,0.01):
    for mp in (4,6):
        eq,cagr,dd,yrs,cv=sim(risk,mp)
        print(f'risque {risk*100:>5.2f}%/trade, max {mp} pos : final={eq:>11,.0f}$  CAGR={cagr*100:>5.1f}%  maxDD={dd*100:>5.1f}%  Calmar={cagr/dd:.2f}')
_,_,_,_,cv=sim(0.005,6)
print('\n=== equity annuel, risque 0.5%, max 6 pos ===')
print((cv.resample('YE').last().pct_change().dropna()*100).round(1).to_string())
T['an']=T.tin.dt.year
print('\n=== R total par annee ===')
print(T.groupby('an').r.agg(n='count',expR='mean',totR='sum').round(2).to_string())
T.to_csv(r'C:/Users/grego/AppData/Local/Temp/claude/C--Users-grego-OneDrive-Daytrading/14097890-a20f-4bd4-aa6c-ea576741d02f/scratchpad/trades.csv',index=False)
