# Recalcul de `c` sur l'univers figé — 2026-08-29 15:52 UTC

Fenêtre bornée au **2026-08-26 inclus** ; les barres du test (2026-08-27 et au-delà) n'y entrent pas.
L'expR observé n'est ni calculé ni rapporté : `c` ne dépend que de la dispersion du null.

| Bloc | k | n obs. | part | n null | ratio mesuré | sd du null | **c** |
|---|---|---|---|---|---|---|---|
| TOUT (42) | 42 | 3285 | — | 4096 | 1.247 | 0.04061 | **2.674** |
| FX | 11 | 924 | 28.1 % | 1155 | 1.250 | 0.05412 | **1.890** |
| indices | 7 | 635 | 19.3 % | 857 | 1.349 | 0.06206 | **1.797** |
| matieres | 4 | 344 | 10.5 % | 440 | 1.279 | 0.09577 | **2.041** |
| crypto | 12 | 1142 | 34.8 % | 1318 | 1.154 | 0.09351 | **3.631** |
| actions | 8 | 240 | 7.3 % | 327 | 1.364 | 0.13070 | **2.326** |

**La colonne `part` est celle qui décide de la représentativité.** Une fenêtre longue ne vaut pas mieux si elle change la composition du panier : les séries n'ont pas le même point de départ chez le courtier, donc allonger la fenêtre dilue les symboles récents. Or le test, lui, aura les 42 actifs simultanément, avec la crypto en tête du volume de barres (2 192 H4/an contre 500 pour une action US). La fenêtre à retenir est celle dont la composition ressemble à celle du test, pas la plus longue.

`c = sd_null x racine(1,32 n_obs)`, la convention de la formule du document. Le **ratio mesuré** est le vrai `n_null / n_obs` : la formule le fige à 1,32, valeur relevée sur les 17 symboles de la calibration d'origine.

## Puissance avec ce `c`

| n | c=1,72 (table du doc) | c=2,125 (17 symboles) | **c=2.674 (42 symboles)** |
|---|---|---|---|
| 1000 | 0.841 | 0.781 | **0.682** |
| 1200 | 0.881 | 0.831 | **0.745** |
| 1500 | 0.924 | 0.887 | **0.818** |
| 1800 | 0.952 | 0.925 | **0.872** |
| 2100 | 0.969 | 0.950 | **0.911** |
| 2400 | 0.980 | 0.967 | **0.938** |

`n` pour atteindre le plancher de 0,80 : **1417** (contre 847 annoncé avec c=1,72).

