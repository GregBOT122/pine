import sys, numpy as np, pandas as pd
sys.path.insert(0,r'C:/Users/grego/AppData/Local/Temp/claude/C--Users-grego-OneDrive-Daytrading/14097890-a20f-4bd4-aa6c-ea576741d02f/scratchpad')
import null_shift as NS      # reutilise DATA deja calcule (precompute + signaux)

DATA=NS.DATA; walk=NS.walk
B=2000; MINSH=200

# bornes temporelles par symbole
import glob
for s in list(DATA):
    d=NS.load(s); DATA[s]['ts']=d.index.values

def stat_window(shift_of, lo_frac_idx):
    """expR/PF sur une fenetre [i0, n), decalage circulaire DANS la fenetre."""
    allr=[]
    for s,D in DATA.items():
        i0=lo_frac_idx[s]; n=D['n']
        if n-i0 < 400: continue
        sig=D['sig']; sig=sig[sig>=i0]
        if len(sig)<5: continue
        L=n-i0; k=shift_of(s,L)
        idx=np.sort(((sig-i0-k)%L)+i0)
        allr.extend(walk(idx,D['KX'],D['R']))
    a=np.array(allr)
    if len(a)<50: return np.nan,np.nan,len(a)
    w=a[a>0]; ls=a[a<=0]
    return a.mean(),(w.sum()/-ls.sum() if ls.sum()<0 else np.inf),len(a)

def idx_from_date(datestr):
    out={}
    for s,D in DATA.items():
        out[s]=int(np.searchsorted(D['ts'],np.datetime64(datestr)))
    return out

for label,cut in (('OOS  >= 2022-01-01','2022-01-01'),('IS   <  2022-01-01',None)):
    if cut is None:
        i0={s:max(NS.N,NS.E,20)+1 for s in DATA}
        # borner a <2022 : on tronque en excluant les signaux apres la coupure
        cutidx=idx_from_date('2022-01-01')
        saved={s:DATA[s]['sig'].copy() for s in DATA}
        for s in DATA: DATA[s]['sig']=DATA[s]['sig'][DATA[s]['sig']<cutidx[s]]
    else:
        i0=idx_from_date(cut)
    obs=stat_window(lambda s,L:0, i0)
    rng=np.random.default_rng(7)
    ne=np.empty(B); npf=np.empty(B)
    for b in range(B):
        kk=rng.integers(MINSH,10**9)
        e,p,_=stat_window(lambda s,L,kk=kk: kk%(L-2*MINSH)+MINSH, i0)
        ne[b]=e; npf[b]=p
    pe=(1+np.sum(ne>=obs[0]))/(B+1)
    print(f'\n=== {label} ===')
    print(f'observe : expR={obs[0]:+.4f}  PF={obs[1]:.3f}  n={obs[2]}')
    print(f'null    : moyenne={np.nanmean(ne):+.4f}  sd={np.nanstd(ne):.4f}  q95={np.nanpercentile(ne,95):+.4f}')
    print(f'p={pe:.4f}   z={(obs[0]-np.nanmean(ne))/np.nanstd(ne):+.2f}   edge net du signal={obs[0]-np.nanmean(ne):+.4f} R')
    if cut is None:
        for s in DATA: DATA[s]['sig']=saved[s]

# --- sensibilite : decalage INDEPENDANT par symbole (casse la synchro inter-marches)
print('\n=== sensibilite : decalage independant par symbole, periode complete ===')
i0={s:max(NS.N,NS.E,20)+1 for s in DATA}
obs=stat_window(lambda s,L:0,i0)
rng=np.random.default_rng(99); ne=np.empty(B)
for b in range(B):
    ks={s:int(rng.integers(MINSH,10**9)) for s in DATA}
    e,_,_=stat_window(lambda s,L: ks[s]%(L-2*MINSH)+MINSH, i0)
    ne[b]=e
print(f'observe expR={obs[0]:+.4f}  |  null moyenne={ne.mean():+.4f} sd={ne.std():.4f}')
print(f'p={(1+np.sum(ne>=obs[0]))/(B+1):.4f}   z={(obs[0]-ne.mean())/ne.std():+.2f}')
