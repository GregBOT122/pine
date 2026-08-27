"""Combien de symboles supplementaires achetent vraiment de la puissance ?
On mesure c dans sd_null = c/sqrt(n) pour des sous-univers homogenes vs melanges."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,r'C:/Users/grego/AppData/Local/Temp/claude/C--Users-grego-OneDrive-Daytrading/14097890-a20f-4bd4-aa6c-ea576741d02f/scratchpad')
import null_shift as NS
DATA=NS.DATA; walk=NS.walk; MINSH=300
for s in list(DATA): DATA[s]['ts']=NS.load(s).index.values
I0={s:int(np.searchsorted(D['ts'],np.datetime64('2022-01-01'))) for s,D in DATA.items()}

def run(syms,k_of):
    a=[]
    for s in syms:
        D=DATA[s]; i0=I0[s]; L=D['n']-i0
        sig=D['sig']; sig=sig[sig>=i0]
        a.extend(walk(np.sort(((sig-i0-k_of(L))%L)+i0),D['KX'],D['R']))
    return np.array(a)

GROUPES={
 'crypto (3)'      : ['BTCUSDT','ETHUSDT','SOLUSDT'],
 'actions US (7)'  : ['AAPL','MSFT','NVDA','GOOGL','AMZN','TSLA','USTEC'],
 'FX (4)'          : ['EURUSD','GBPUSD','USDJPY','XAGUSD'],
 'indices+or (4)'  : ['US30','US500','XAUUSD','USTEC'],
 'melange (6)'     : ['BTCUSDT','AAPL','EURUSD','US30','XAUUSD','TSLA'],
 'tout (17)'       : list(DATA),
}
rng=np.random.default_rng(31)
print(f"{'groupe':<18}{'k sym':>6}{'n obs':>7}{'expR':>8}{'null':>8}{'sd_null':>9}{'c':>7}{'c/sym':>8}")
for lab,syms in GROUPES.items():
    syms=[s for s in syms if s in DATA]
    o=run(syms,lambda L:0)
    ns=np.array([run(syms,lambda L,kk=int(rng.integers(MINSH,10**9)): kk%(L-2*MINSH)+MINSH).mean()
                 for _ in range(500)])
    c=ns.std()*np.sqrt(len(o))
    print(f'{lab:<18}{len(syms):>6}{len(o):>7}{o.mean():>+8.3f}{ns.mean():>+8.3f}{ns.std():>9.4f}{c:>7.2f}{c/len(syms):>8.3f}')

# cadence : barres H4 par an selon le marche
print('\n=== cadence de signal selon le marche (2022-2026) ===')
for lab,syms in (('crypto 24/7',['BTCUSDT','ETHUSDT','SOLUSDT']),
                 ('actions',['AAPL','MSFT','NVDA','GOOGL','AMZN','TSLA']),
                 ('FX/indices',['EURUSD','GBPUSD','USDJPY','US30','US500','XAUUSD'])):
    tb=[];tr=[]
    for s in syms:
        D=DATA[s]; i0=I0[s]
        yrs=(pd.Timestamp(str(D['ts'][-1])[:10])-pd.Timestamp('2022-01-01')).days/365.25
        tb.append((D['n']-i0)/yrs)
        sig=D['sig']; sig=sig[sig>=i0]
        tr.append(len(walk(np.sort(sig),D['KX'],D['R']))/yrs)
    print(f'  {lab:<12} {np.mean(tb):>6.0f} barres H4/an   {np.mean(tr):>5.1f} trades longs/symbole/an')
