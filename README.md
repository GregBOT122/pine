# Trend Donchian H4 — réglages TradingView

Fichier : `trend_donchian_h4.pine` → coller dans Pine Editor, *Add to chart*.

## Réglages obligatoires

| Où | Valeur |
|---|---|
| Graphe | **4 heures (H4)** — le script prévient si tu es ailleurs |
| Properties → Initial capital | 50 000 |
| Properties → Order size | laisser `1 contract` (le script calcule la taille lui-même) |
| Properties → Margin long/short | 20 % (déjà dans le code) |
| Inputs → Risque par trade | 1 % pour commencer |
| Inputs → Shorts | **décoché** |

## Commission par symbole (Properties → Commission, en % *par côté*)

Le code arrive avec 0,0075 % (= XAUUSD). À changer selon le marché :

| Symbole | % par côté | Symbole | % par côté |
|---|---|---|---|
| US30 / US500 | 0,006 | XAUUSD | 0,0075 |
| USTEC | 0,007 | XAGUSD | 0,015 |
| AAPL / MSFT / NVDA | 0,010 | TSLA | 0,015 |
| AMZN / GOOGL | 0,0125 | BTC / ETH / SOL | 0,045 |

Ces chiffres sont ceux utilisés dans le pré-screen. Si ton courtier est plus cher,
mets sa valeur réelle — c'est le paramètre qui tue les stratégies rapides.

## Le panier mesuré

Le résultat solide (expR +0,388 R, IC95 [+0,279, +0,504], n=1966) est **poolé sur
les 17 symboles, perdants inclus**. Le classement par symbole ci-dessous est
post-hoc : ne l'utilise pas pour ne garder que le haut du tableau, c'est
exactement là que le sur-ajustement se cache.

Long only, H4, Donchian 40 / stop 1,5 ATR / trail 3,5 ATR :

| Symbole | n | expR | PF | R:R | IC95 |
|---|---|---|---|---|---|
| TSLA | 94 | +1,075 | 2,97 | 4,38 | [+0,40 ; +1,81] |
| NVDA | 96 | +0,822 | 2,49 | 4,75 | [+0,19 ; +1,52] |
| ETHUSDT | 104 | +0,759 | 2,30 | 4,53 | [+0,11 ; +1,50] |
| BTCUSDT | 100 | +0,751 | 2,36 | 4,39 | [+0,11 ; +1,50] |
| SOLUSDT | 110 | +0,682 | 2,25 | 3,79 | [+0,15 ; +1,31] |
| XAUUSD | 101 | +0,670 | 2,33 | 3,27 | [+0,23 ; +1,16] |
| AAPL | 105 | +0,661 | 2,25 | 2,88 | [+0,19 ; +1,16] |
| USTEC | 82 | +0,459 | 1,98 | 2,30 | [+0,08 ; +0,89] |
| USDJPY | 101 | +0,469 | 1,78 | 3,22 | [−0,05 ; +1,10] |
| XAGUSD | 93 | +0,262 | 1,41 | 2,96 | [−0,16 ; +0,76] |
| MSFT | 108 | +0,258 | 1,42 | 2,32 | [−0,14 ; +0,70] |
| AMZN | 118 | +0,245 | 1,41 | 2,45 | [−0,11 ; +0,62] |
| US500 | 244 | +0,183 | 1,33 | 2,28 | [−0,02 ; +0,41] |
| US30 | 246 | +0,145 | 1,24 | 2,48 | [−0,09 ; +0,39] |
| GOOGL | 104 | −0,047 | 0,94 | 2,42 | [−0,45 ; +0,39] |
| GBPUSD | 76 | −0,050 | 0,92 | 1,99 | [−0,38 ; +0,34] |
| EURUSD | 84 | −0,258 | 0,63 | 1,76 | [−0,53 ; +0,06] |

META exclu : split 20:1 non ajusté dans le cache (bougie à +1479 % le 2022-06-09).

## Ce qui a été écarté, et pourquoi

- **H1** : expR ≈ 0,00. Cohérent avec le plafond de friction déjà mesuré.
- **D1** : IS +0,40 R → OOS −0,05 R, symboles positifs 75 % → 12 %. Mirage de petit n.
- **Shorts** : expR −0,213, IC95 [−0,295 ; −0,128]. L'IC exclut zéro *du mauvais côté*.

## Null par decalage circulaire (2026-08-26)

**H0** : le signal Donchian ne porte aucune information ; tout vient de la derive
du marche et de la mecanique de sortie.
**Substitut** : `sig_null[i] = sig[(i+k) mod n]`, **prix inchange** — preserve le
regroupement des signaux et toute la dynamique du prix, detruit l'alignement
signal <-> mouvement futur. B = 2000, decalage >= 500 barres H4.

| Fenetre | observe | null (moy.) | p | z | edge net du signal |
|---|---|---|---|---|---|
| Periode complete | +0,3862 R | +0,2258 R | 0,0005 (plancher) | +3,85 | **+0,160 R** |
| OOS >= 2022 | +0,4016 R | +0,1819 R | 0,0005 (plancher) | +4,12 | **+0,220 R** |
| IS < 2022 | +0,3645 R | +0,2505 R | 0,0335 | +1,86 | +0,114 R |
| Decalage independant/symbole | +0,3862 R | +0,2266 R | 0,0005 | +4,65 | +0,160 R |

**Calibration** : taille a 5 % = **0,057** sur 300 repetitions sous H0
(cible 0,050, IC binomial +/-0,025). Le test tient. Les p sont legerement
conservateurs au centre (mediane 0,56 au lieu de 0,50).

**Correction multiple** : 54 configurations explorees (18 jeux de parametres x
3 timeframes). Seuil Bonferroni = 0,05/54 = 0,00093. Le plancher de p a B=2000
(0,0005) passe dessous, et z = 3,85 donne ~6e-5 en approximation normale.

### Ce que ca change concretement

**Le signal est reel, mais il ne vaut que 42 % de ce que le backtest affiche.**
Le null gagne deja +0,226 R par trade en entrant long a des dates arbitraires
sur ces memes marches avec le meme trailing ATR. Donc :

- Batis ton attente sur **+0,16 R par trade**, pas +0,39 R. Ca divise par ~2,4
  le rendement espere du backtest.
- La part beta (+0,226 R) **s'inversera en marche baissier prolonge**. La part
  signal (+0,16 R) n'a aucune raison de s'inverser — c'est elle, l'edge.
- Signe rassurant : l'edge net du signal est **plus grand en OOS (+0,220) qu'en
  IS (+0,114)**. Le beta etait plus fort en 2012-2021, pas le signal.

**Limite qui reste** : les parametres ont ete choisis apres avoir vu toutes ces
donnees. Aucune fenetre ici n'est un holdout vraiment propre. Le seul test
non-circulaire est en avant, sur des barres pas encore collectees.

## La limite a ne pas oublier

2012-2026, long only, sur tech / indices / crypto = **un seul grand marché
haussier**. Une part de l'edge est du beta, pas du trend-following. Le fait que
les shorts perdent est la même information vue à l'envers. Le test qui manque est
un marché baissier prolongé, que ces données ne contiennent pas.

Sources : `bot/xaubot/xaubot/data/cache/*.parquet` (633 Mo, H1 2012→2026).
Scripts du pré-screen dans le scratchpad de la session.
