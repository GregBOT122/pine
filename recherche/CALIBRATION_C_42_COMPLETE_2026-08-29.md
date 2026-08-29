# Recalcul de `c` sur l'univers figé — 2026-08-29 15:51 UTC

Fenêtre bornée au **2026-08-26 inclus** ; les barres du test (2026-08-27 et au-delà) n'y entrent pas.
L'expR observé n'est ni calculé ni rapporté : `c` ne dépend que de la dispersion du null.

| Bloc | k | n obs. | part | n null | ratio mesuré | sd du null | **c** |
|---|---|---|---|---|---|---|---|
| TOUT (42) | 42 | 5552 | — | 6873 | 1.238 | 0.03044 | **2.606** |
| FX | 11 | 1563 | 28.2 % | 1958 | 1.253 | 0.04261 | **1.935** |
| indices | 7 | 1153 | 20.8 % | 1549 | 1.343 | 0.04334 | **1.691** |
| matieres | 4 | 546 | 9.8 % | 692 | 1.267 | 0.06879 | **1.847** |
| crypto | 12 | 1983 | 35.7 % | 2278 | 1.149 | 0.05908 | **3.023** |
| actions | 8 | 307 | 5.5 % | 409 | 1.332 | 0.11295 | **2.274** |

**La colonne `part` est celle qui décide de la représentativité.** Une fenêtre longue ne vaut pas mieux si elle change la composition du panier : les séries n'ont pas le même point de départ chez le courtier, donc allonger la fenêtre dilue les symboles récents. Or le test, lui, aura les 42 actifs simultanément, avec la crypto en tête du volume de barres (2 192 H4/an contre 500 pour une action US). La fenêtre à retenir est celle dont la composition ressemble à celle du test, pas la plus longue.

`c = sd_null x racine(1,32 n_obs)`, la convention de la formule du document. Le **ratio mesuré** est le vrai `n_null / n_obs` : la formule le fige à 1,32, valeur relevée sur les 17 symboles de la calibration d'origine.

## Puissance avec ce `c`

| n | c=1,72 (table du doc) | c=2,125 (17 symboles) | **c=2.606 (42 symboles)** |
|---|---|---|---|
| 1000 | 0.841 | 0.781 | **0.695** |
| 1200 | 0.881 | 0.831 | **0.757** |
| 1500 | 0.924 | 0.887 | **0.828** |
| 1800 | 0.952 | 0.925 | **0.880** |
| 2100 | 0.969 | 0.950 | **0.917** |
| 2400 | 0.980 | 0.967 | **0.943** |

`n` pour atteindre le plancher de 0,80 : **1371** (contre 847 annoncé avec c=1,72).

