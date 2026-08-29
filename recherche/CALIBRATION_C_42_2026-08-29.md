# Recalcul de `c` sur l'univers figé — 2026-08-29 15:37 UTC

Fenêtre bornée au **2026-08-26 inclus** ; les barres du test (2026-08-27 et au-delà) n'y entrent pas.
L'expR observé n'est ni calculé ni rapporté : `c` ne dépend que de la dispersion du null.

| Bloc | k | n obs. | n null | ratio mesuré | sd du null | **c** |
|---|---|---|---|---|---|---|
| TOUT (42) | 42 | 1853 | 2333 | 1.259 | 0.04845 | **2.396** |
| FX | 11 | 541 | 657 | 1.215 | 0.07444 | **1.989** |
| indices | 7 | 354 | 475 | 1.341 | 0.08697 | **1.880** |
| matieres | 4 | 197 | 259 | 1.316 | 0.11753 | **1.895** |
| crypto | 12 | 639 | 766 | 1.199 | 0.12649 | **3.674** |
| actions | 8 | 122 | 166 | 1.362 | 0.17720 | **2.249** |

`c = sd_null x racine(1,32 n_obs)`, la convention de la formule du document. Le **ratio mesuré** est le vrai `n_null / n_obs` : la formule le fige à 1,32, valeur relevée sur les 17 symboles de la calibration d'origine.

## Puissance avec ce `c`

| n | c=1,72 (table du doc) | c=2,125 (17 symboles) | **c=2.396 (42 symboles)** |
|---|---|---|---|
| 1000 | 0.841 | 0.781 | **0.734** |
| 1200 | 0.881 | 0.831 | **0.791** |
| 1500 | 0.924 | 0.887 | **0.856** |
| 1800 | 0.952 | 0.925 | **0.901** |
| 2100 | 0.969 | 0.950 | **0.933** |
| 2400 | 0.980 | 0.967 | **0.955** |

`n` pour atteindre le plancher de 0,80 : **1235** (contre 847 annoncé avec c=1,72).

