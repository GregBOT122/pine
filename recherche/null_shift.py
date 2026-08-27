"""
Null par decalage circulaire, adapte au backtest.

H0 : le signal Donchian ne porte aucune information sur ce qui suit ;
     tout le rendement vient de la derive du marche + de la mecanique de sortie.

Substitut : sig_null[i] = sig[(i+k) mod n], prix INCHANGE.
  - preserve le nombre et le regroupement des signaux (ACF du signal)
  - preserve integralement la dynamique du prix (derive, clusters de vol)
  - detruit l'alignement signal <-> mouvement futur

Astuce de vitesse : le resultat d'une entree longue a la barre i ne depend PAS
du signal. On precalcule donc R[i] et barre_de_sortie[i] pour TOUTES les barres,
une seule fois. Chaque permutation devient une marche sur les seules barres-signal.
"""
import glob, numpy as np, pandas as pd

CACHE=r'C:/Users/grego/dev/Daytrading/bot/xaubot/xaubot/data/cache'
FRICTION={'XAUUSD':.015,'XAGUSD':.030,'US30':.012,'US500':.012,'USTEC':.014,'EURUSD':.008,
 'GBPUSD':.010,'USDJPY':.010,'BTCUSDT':.090,'ETHUSDT':.090,'SOLUSDT':.090,
 'AAPL':.020,'MSFT':.020,'NVDA':.020,'GOOGL':.025,'AMZN':.025,'TSLA':.030}
N,K,M,E,MAXB=40,1.5,3.5,200,400
MINSHIFT=500          # >= ~3 mois en H4 : pas de decalage quasi-identite
B=2000

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

def precompute(d,fric):
    """Pour chaque barre i : R d'un long entre a open[i+1], et sa barre de sortie."""
    o,h,l,c=d.open.values,d.high.values,d.low.values,d.close.values
    A=atr(d).values; n=len(d)
    R=np.full(n,np.nan); KX=np.full(n,-1,dtype=np.int64)
    for i in range(n-1):
        a=A[i]
        if not np.isfinite(a) or a<=0: continue
        j=i+1; entry=o[j]; Rd=K*a
        if Rd<=0: continue
        stop=entry-Rd; ext=entry; xp=np.nan; k=j
        while k<n and k-j<MAXB:
            if l[k]<=stop: xp=min(stop,o[k]); break
            if h[k]>ext: ext=h[k]
            t=ext-M*A[k]
            if t>stop: stop=t
            k+=1
        if not np.isfinite(xp): k=min(k,n-1); xp=c[k]
        R[i]=(xp-entry-entry*fric/100)/Rd; KX[i]=k
    return R,KX

def signals(d):
    c=d.close.values
    em=d.close.ewm(span=E,adjust=False).mean().values
    hh=d.high.rolling(N).max().shift(1).values
    A=atr(d).values
    s=(c>hh)&(c>em)&np.isfinite(A)&(A>0)
    s[:max(N,E,20)+1]=False
    return s

def walk(sig_idx,KX,R):
    """Meme regle que le backtest : pas de nouvelle entree tant qu'on est en position."""
    out=[]; free=-1
    for i in sig_idx:
        if i<=free or KX[i]<0 or not np.isfinite(R[i]): continue
        out.append(R[i]); free=KX[i]
    return out

DATA={}
for s,f in FRICTION.items():
    d=load(s)
    if d is None or len(d)<600: continue
    R,KX=precompute(d,f); sg=signals(d)
    DATA[s]=dict(R=R,KX=KX,sig=np.flatnonzero(sg),n=len(d))
    print(f'{s:8s} n={len(d):>5}  signaux bruts={sg.sum():>4}',flush=True)

def stat(shift_map):
    """expR poole et PF poole sur tous les symboles, pour un decalage donne."""
    allr=[]
    for s,D in DATA.items():
        n=D['n']; k=shift_map[s]
        idx=np.sort((D['sig']-k)%n)     # sig_null[i]=sig[(i+k)%n]  =>  indices decales de -k
        allr.extend(walk(idx,D['KX'],D['R']))
    a=np.array(allr); w=a[a>0]; ls=a[a<=0]
    return a.mean(), (w.sum()/-ls.sum() if ls.sum()<0 else np.inf), len(a)

obs_e,obs_pf,obs_n=stat({s:0 for s in DATA})
print(f'\nOBSERVE : expR={obs_e:+.4f}  PF={obs_pf:.3f}  n={obs_n}')

rng=np.random.default_rng(20260826)
nulls_e=np.empty(B); nulls_pf=np.empty(B); nulls_n=np.empty(B)
for b in range(B):
    k=rng.integers(MINSHIFT,min(D['n'] for D in DATA.values())-MINSHIFT)
    e,p,nn=stat({s:k for s in DATA})       # decalage COMMUN : garde la synchro inter-symboles
    nulls_e[b]=e; nulls_pf[b]=p; nulls_n[b]=nn
    if (b+1)%400==0: print(f'  {b+1}/{B}',flush=True)

p_e=(1+np.sum(nulls_e>=obs_e))/(B+1)
p_pf=(1+np.sum(nulls_pf>=obs_pf))/(B+1)
print(f'\n=== NULL PAR DECALAGE CIRCULAIRE, B={B}, decalage commun >= {MINSHIFT} barres H4 ===')
print(f'null expR : moyenne={nulls_e.mean():+.4f}  ecart-type={nulls_e.std():.4f}')
print(f'            quantiles 50/90/95/99 = {np.percentile(nulls_e,[50,90,95,99]).round(4)}')
print(f'null PF   : moyenne={nulls_pf.mean():.3f}   q95={np.percentile(nulls_pf,95):.3f}')
print(f'null n    : moyenne={nulls_n.mean():.0f}')
print(f'\nOBSERVE expR = {obs_e:+.4f}   ->  p = {p_e:.4f}   (z = {(obs_e-nulls_e.mean())/nulls_e.std():+.2f})')
print(f'OBSERVE PF   = {obs_pf:.3f}    ->  p = {p_pf:.4f}')
print(f'\nPART BETA : le null gagne deja {nulls_e.mean():+.4f} R par trade.')
print(f'  edge net du signal = {obs_e-nulls_e.mean():+.4f} R  ({(obs_e-nulls_e.mean())/obs_e*100:.0f} % du total)')
np.save(r'C:/Users/grego/AppData/Local/Temp/claude/C--Users-grego-OneDrive-Daytrading/14097890-a20f-4bd4-aa6c-ea576741d02f/scratchpad/nulls_e.npy',nulls_e)
