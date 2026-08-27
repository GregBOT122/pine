"""Audit de puissance AVANT pre-enregistrement.
Question : combien de trades en avant pour detecter un edge net de +0,16 R
au-dessus du null, a 80 % de puissance, seuil 5 % unilateral ?"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,r'C:/Users/grego/AppData/Local/Temp/claude/C--Users-grego-OneDrive-Daytrading/14097890-a20f-4bd4-aa6c-ea576741d02f/scratchpad')
import null_shift as NS
DATA=NS.DATA; walk=NS.walk
for s in list(DATA):
    DATA[s]['ts']=NS.load(s).index.values
MINSH=300

def run(i0map, k_of):
    allr=[]
    for s,D in DATA.items():
        i0=i0map[s]; n=D['n']; L=n-i0
        if L<400: continue
        sig=D['sig']; sig=sig[sig>=i0]
        if len(sig)<3: continue
        k=k_of(s,L)
        allr.extend(walk(np.sort(((sig-i0-k)%L)+i0), D['KX'], D['R']))
    return np.array(allr)

def idx(datestr):
    return {s:int(np.searchsorted(D['ts'],np.datetime64(datestr))) for s,D in DATA.items()}

# --- 1. cadence reelle et dispersion, sur la periode recente (tous symboles vivants)
i0=idx('2022-01-01')
obs=run(i0, lambda s,L:0)
yrs=(pd.Timestamp('2026-08-17')-pd.Timestamp('2022-01-01')).days/365.25
print(f'periode 2022-2026 ({yrs:.2f} ans) : {len(obs)} trades longs  ->  {len(obs)/yrs:.0f} trades/an sur 17 symboles')
print(f'  expR={obs.mean():+.4f}   ecart-type par trade = {obs.std():.3f} R')

# --- 2. comment l'ecart-type du null decroit avec la taille de l'echantillon
print('\n=== ecart-type du null selon la fenetre ===')
pts=[]
for cut in ('2012-01-01','2018-01-01','2021-01-01','2022-01-01','2023-06-01','2024-06-01','2025-06-01'):
    im=idx(cut)
    if min(D['n']-im[s] for s,D in DATA.items())<2*MINSH+50: continue
    o=run(im, lambda s,L:0)
    rng=np.random.default_rng(1)
    ns=np.array([run(im, lambda s,L,kk=int(rng.integers(MINSH,10**9)): kk%(L-2*MINSH)+MINSH).mean()
                 for _ in range(400)])
    pts.append((cut,len(o),o.mean(),ns.mean(),ns.std(),len(ns)))
    print(f'  depuis {cut} : n_obs={len(o):>4}  expR={o.mean():+.3f}  null={ns.mean():+.3f}  sd_null={ns.std():.4f}')

# constante d'echelle : sd_null = c / sqrt(n)
c=np.median([sd*np.sqrt(n) for _,n,_,_,sd,_ in pts])
print(f'\n  sd_null ~ c/sqrt(n) avec c = {c:.2f} R  (dispersion effective, correlation inter-symboles incluse)')

# --- 3. puissance
from math import sqrt
from scipy.stats import norm
delta=0.16                       # edge net a detecter (observe 0.386 - null 0.226)
sig_tr=obs.std()
print(f'\n=== PUISSANCE pour delta = {delta:+.2f} R, seuil 5 % unilateral ===')
print(f"{'n trades':>9}{'sd(obs)':>9}{'sd(null)':>10}{'puissance':>11}{'ans @236/an':>13}{'ans @500/an':>13}")
target=None
for n in (200,300,400,600,800,1000,1200,1500,2000,3000):
    se_o=sig_tr/sqrt(n); se_n=c/sqrt(n*1.32)     # le null prend ~32 % de trades en plus
    z=(delta-1.645*se_n)/se_o
    pw=norm.cdf(z)
    if target is None and pw>=0.80: target=n
    print(f'{n:>9}{se_o:>9.4f}{se_n:>10.4f}{pw:>11.2f}{n/236:>13.1f}{n/500:>13.1f}')
print(f'\n  -> 80 % de puissance atteinte vers n = {target} trades')

# --- 4. verification par simulation directe du test de permutation
print('\n=== verification par simulation (500 essais) ===')
rng=np.random.default_rng(77)
null_pool=[]
im=idx('2022-01-01')
for _ in range(120):
    null_pool.append(run(im, lambda s,L,kk=int(rng.integers(MINSH,10**9)): kk%(L-2*MINSH)+MINSH))
null_all=np.concatenate(null_pool)
for n in (400,600,900,1200):
    rej=0
    for _ in range(500):
        o=rng.choice(obs,n,replace=True).mean()
        nd=np.array([rng.choice(null_all,int(n*1.32),replace=True).mean() for _ in range(200)])
        rej += ((1+np.sum(nd>=o))/201)<=0.05
    print(f'  n={n:>5} : puissance simulee = {rej/500:.2f}')
