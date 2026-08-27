import sys, numpy as np, pandas as pd, hashlib, glob
sys.path.insert(0,r'C:/Users/grego/AppData/Local/Temp/claude/C--Users-grego-OneDrive-Daytrading/14097890-a20f-4bd4-aa6c-ea576741d02f/scratchpad')
import null_shift as NS

# --- friction a l'equilibre : quel aller-retour annule l'edge NET de +0.16 R ?
EDGE=0.1604
print('=== FRICTION A L EQUILIBRE (edge net du signal = +0,1604 R, stop = 1,5 ATR) ===')
print('  seuil = edge_net x 1,5 x ATR%,  a comparer au spread REEL aller-retour\n')
print(f"{'symbole':<9}{'ATR% H4 med':>13}{'friction eq.':>14}{'friction test':>15}{'marge':>9}")
rows=[]
for s in NS.FRICTION:
    d=NS.load(s)
    if d is None: continue
    a=(NS.atr(d)/d.close*100).median()
    be=EDGE*1.5*a
    used=NS.FRICTION[s]
    rows.append((s,a,be,used,be/used))
    print(f'{s:<9}{a:>13.3f}{be:>13.4f}%{used:>14.4f}%{be/used:>8.1f}x')

# --- cadence par symbole : combien de symboles pour lire en 24 mois ?
print('\n=== CADENCE : trades longs par symbole et par an (2022-2026) ===')
im={s:int(np.searchsorted(NS.load(s).index.values,np.datetime64('2022-01-01'))) for s in NS.DATA}
tot=0
for s,D in NS.DATA.items():
    sig=D['sig']; sig=sig[sig>=im[s]]
    r=NS.walk(np.sort(sig),D['KX'],D['R']); tot+=len(r)
yrs=4.62
print(f'  17 symboles -> {tot} trades / {yrs:.2f} ans = {tot/yrs:.0f}/an, soit {tot/yrs/17:.1f} par symbole et par an')
for target,months in ((1200,18),(1200,24),(1200,36)):
    need=target/(months/12)/(tot/yrs/17)
    print(f'  n={target} en {months} mois -> {need:.0f} symboles necessaires')

# --- empreinte de la configuration figee
h=hashlib.sha256()
for f in sorted(glob.glob(r'C:/Users/grego/OneDrive/Daytrading/pine/recherche/*.py'))+[r'C:/Users/grego/OneDrive/Daytrading/pine/trend_donchian_h4.pine']:
    h.update(open(f,'rb').read())
print(f'\nSHA256 de la configuration figee (6 scripts + le .pine) : {h.hexdigest()}')
