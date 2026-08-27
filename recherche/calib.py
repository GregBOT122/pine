"""Taille du test sous H0 : on fabrique des 'observes' qui sont eux-memes des
substituts (donc sans effet par construction) et on compte les rejets a 5 %."""
import sys, time, numpy as np
sys.path.insert(0,r'C:/Users/grego/AppData/Local/Temp/claude/C--Users-grego-OneDrive-Daytrading/14097890-a20f-4bd4-aa6c-ea576741d02f/scratchpad')
import null_shift as NS
DATA=NS.DATA; walk=NS.walk; MINSH=500
I0={s:max(NS.N,NS.E,20)+1 for s in DATA}

def stat(k):
    allr=[]
    for s,D in DATA.items():
        i0=I0[s]; n=D['n']; L=n-i0
        sig=D['sig']; sig=sig[sig>=i0]
        idx=np.sort(((sig-i0-(k%(L-2*MINSH)+MINSH))%L)+i0)
        allr.extend(walk(idx,D['KX'],D['R']))
    return np.mean(allr)

t0=time.time(); [stat(int(x)) for x in range(1000,1200)]; rate=200/(time.time()-t0)
print(f'debit = {rate:.0f} stat/s',flush=True)

OUT=300; IN=300
print(f'calibration : {OUT} x {IN} = {OUT*IN} appels, ~{OUT*IN/rate/60:.1f} min',flush=True)
rng=np.random.default_rng(4242)
rej05=0; rej10=0; ps=[]
for o in range(OUT):
    ko=int(rng.integers(MINSH,10**9))
    obs=stat(ko)                                   # 'observe' sans effet
    inner=np.array([stat(int(rng.integers(MINSH,10**9))) for _ in range(IN)])
    p=(1+np.sum(inner>=obs))/(IN+1)
    ps.append(p); rej05+= p<=0.05; rej10+= p<=0.10
    if (o+1)%75==0: print(f'  {o+1}/{OUT}  taille@5%={rej05/(o+1):.3f}',flush=True)
ps=np.array(ps)
print(f'\n=== TAILLE DU NULL PAR DECALAGE CIRCULAIRE ({OUT} repetitions sous H0) ===')
print(f'taille a 5 %  : {rej05/OUT:.3f}   (cible 0.050, IC binomial +/- {1.96*np.sqrt(.05*.95/OUT):.3f})')
print(f'taille a 10 % : {rej10/OUT:.3f}   (cible 0.100)')
print(f'p uniformes ? quantiles 25/50/75 = {np.percentile(ps,[25,50,75]).round(3)}  (attendu 0.25/0.50/0.75)')
