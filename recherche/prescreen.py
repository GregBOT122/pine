import glob, sys, numpy as np, pandas as pd
from collections import defaultdict

CACHE = r'C:/Users/grego/dev/Daytrading/bot/xaubot/xaubot/data/cache'

# friction aller-retour en % du prix (retail realiste, a re-mesurer regle 11)
FRICTION = {
 'XAUUSD':0.015,'XAGUSD':0.030,'US30':0.012,'US500':0.012,'USTEC':0.014,
 'EURUSD':0.008,'GBPUSD':0.010,'USDJPY':0.010,
 'BTCUSDT':0.090,'ETHUSDT':0.090,'SOLUSDT':0.090,
 'AAPL':0.020,'MSFT':0.020,'NVDA':0.020,'META':0.025,'GOOGL':0.025,'AMZN':0.025,'TSLA':0.030,
}

def load(sym, base='H1'):
    fs = sorted(glob.glob(f'{CACHE}/{sym}_{base}_*.parquet'))
    if not fs: return None
    d = pd.concat([pd.read_parquet(f) for f in fs])
    d = d[~d.index.duplicated(keep='first')].sort_index()
    return d[['open','high','low','close']].dropna()

def resample(d, rule):
    if rule is None: return d
    o = d.resample(rule).agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
    return o

def atr(d, n=14):
    h,l,c = d['high'], d['low'], d['close']
    pc = c.shift(1)
    tr = pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def backtest(d, N, kstop, mtrail, emaslow, fric_pct, maxbars=400):
    """Donchian breakout + EMA regime + chandelier ATR trail. Entree a l'open suivant."""
    o,h,l,c = d['open'].values, d['high'].values, d['low'].values, d['close'].values
    A = atr(d,14).values
    E = d['close'].ewm(span=emaslow, adjust=False).mean().values
    hh = d['high'].rolling(N).max().shift(1).values
    ll = d['low'].rolling(N).min().shift(1).values
    n = len(d)
    trades = []
    i = max(N, emaslow, 20) + 1
    while i < n-1:
        a = A[i]
        if not np.isfinite(a) or a<=0: i+=1; continue
        long_sig  = c[i] > hh[i] and c[i] > E[i]
        short_sig = c[i] < ll[i] and c[i] < E[i]
        if not (long_sig or short_sig): i+=1; continue
        side = 1 if long_sig else -1
        j = i+1
        entry = o[j]
        R = kstop*a                      # risque initial en prix
        if R<=0: i+=1; continue
        stop = entry - side*R
        ext  = entry                      # extreme favorable
        exitp=None
        k=j
        while k < n and (k-j) < maxbars:
            if side>0:
                if l[k] <= stop: exitp = min(stop, o[k]); break
                ext = max(ext, h[k]); stop = max(stop, ext - mtrail*A[k])
            else:
                if h[k] >= stop: exitp = max(stop, o[k]); break
                ext = min(ext, l[k]); stop = min(stop, ext + mtrail*A[k])
            k+=1
        if exitp is None:
            k = min(k, n-1); exitp = c[k]
        cost = entry*fric_pct/100.0
        r = (side*(exitp-entry) - cost)/R
        trades.append((d.index[j], r, k-j))
        i = k+1
    return pd.DataFrame(trades, columns=['ts','r','bars'])

def stats(t):
    if len(t)<10: return None
    r = t['r'].values
    g = r[r>0].sum(); ls = -r[r<0].sum()
    pf = g/ls if ls>0 else np.inf
    # bootstrap IC95 sur expR
    rng = np.random.default_rng(7)
    bs = rng.choice(r, size=(2000,len(r)), replace=True).mean(axis=1)
    return dict(n=len(r), expR=r.mean(), pf=pf, wr=(r>0).mean(),
                lo=np.percentile(bs,2.5), hi=np.percentile(bs,97.5),
                med_bars=t['bars'].median())

SYMS = list(FRICTION)
TFS = [('H1',None),('H4','4h'),('D1','1D')]
GRID = [(N,k,m,e) for N in (20,40,55) for k in (1.5,2.0,3.0) for m in (2.5,3.5) for e in (200,)]

rows=[]
for sym in SYMS:
    d0 = load(sym)
    if d0 is None or len(d0)<3000: continue
    for tfname, rule in TFS:
        d = resample(d0, rule)
        if len(d) < 600: continue
        ins = d[d.index < '2024-01-01']; oos = d[d.index >= '2024-01-01']
        if len(ins)<400 or len(oos)<150: continue
        for (N,k,m,e) in GRID:
            ti = backtest(ins,N,k,m,e,FRICTION[sym])
            si = stats(ti)
            if si is None: continue
            to = backtest(oos,N,k,m,e,FRICTION[sym]); so = stats(to)
            rows.append(dict(sym=sym,tf=tfname,N=N,k=k,m=m,
                n_is=si['n'],expR_is=si['expR'],pf_is=si['pf'],lo_is=si['lo'],
                n_oos=(so['n'] if so else 0), expR_oos=(so['expR'] if so else np.nan),
                pf_oos=(so['pf'] if so else np.nan), wr_is=si['wr'], bars=si['med_bars']))
    print(f'{sym} ok', file=sys.stderr, flush=True)

R = pd.DataFrame(rows)
R.to_csv(r'C:/Users/grego/AppData/Local/Temp/claude/C--Users-grego-OneDrive-Daytrading/14097890-a20f-4bd4-aa6c-ea576741d02f/scratchpad/prescreen.csv', index=False)
print('TOTAL COMBOS', len(R))
print('\n=== expR moyen par timeframe (in-sample, tous symboles/params) ===')
print(R.groupby('tf')[['expR_is','pf_is','n_is']].mean().round(3))
print('\n=== expR moyen par symbole, TF=D1 ===')
print(R[R.tf=='D1'].groupby('sym')[['expR_is','pf_is','n_is','expR_oos','n_oos']].mean().round(3).sort_values('expR_is',ascending=False))
print('\n=== expR moyen par symbole, TF=H4 ===')
print(R[R.tf=='H4'].groupby('sym')[['expR_is','pf_is','n_is','expR_oos','n_oos']].mean().round(3).sort_values('expR_is',ascending=False))
