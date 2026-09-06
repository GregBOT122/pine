# Note d'appareil — la cadence était comptée sur des années éclaircies, et la date de lecture était fausse de quatorze mois

> **Ceci n'est pas un amendement.** Aucune hypothèse, aucun seuil, aucun null,
> aucune issue ne bouge. L'empreinte gelée `1f5318dc…e32c2c` est intacte et a
> été revérifiée après chaque manipulation. Ce qui est corrigé est un
> **instrument de rapport** — le calcul de cadence de `lecture_h_trend.py` — et
> ce qui est ajouté est la **mise en exécution d'une règle déjà décidée** par
> l'amendement 2 du 2026-08-28.
>
> Écrit et commité le 2026-09-06, avant qu'aucune statistique de la fenêtre
> n'existe : 463 barres H4 accumulées, aucun `expR`, aucun `p`, aucun edge net
> calculé sur elles — ni par moi, ni par personne.

---

## 0. Ce qui a mené ici, et il faut le dire en premier

Le point de départ était **faux**. J'ai lu `null_shift.py`, vu que son dict
`FRICTION` ne porte que 17 symboles pour un univers de 42, et conclu que le
blocage 1 de `NOTE_APPAREIL_H_TREND_2026-08-28.md` était toujours ouvert. J'ai
recommandé d'écrire l'amendement qui le tranche.

**Il était déjà tranché**, le 2026-08-28, par l'amendement 1 — qui explique
précisément que ce dict n'est **pas utilisé** à la lecture, `precompute(d, fric)`
recevant le coût en argument. Le script le dit lui-même à chaque exécution :

    Pour memoire, le dict FRICTION du fichier gele n'en couvre que 17
    et n'est PAS utilise.

J'ai relu le code au lieu de lancer l'instrument. C'est exactement la panne que
`DECISIONS.md` documente aux 2026-09-03/04 — *« un appareil de mesure se vérifie
en faisant tourner ses outils l'un contre l'autre, et la relecture ne trouve pas
ce que la confrontation trouve »* — commise par celui qui venait de la lire.

**C'est en lançant l'instrument pour vérifier ma propre affirmation que le vrai
défaut est sorti.** Il est consigné ci-dessous. Sans l'erreur de départ, la
commande n'aurait pas été tapée.

---

## 1. Le défaut

`verifier()` calculait la cadence de chaque série par un quotient :

```python
span = (ts.max() - ts.min()) / 86400 / 365.25
par_an[s] = len(ts) / span
```

Le dénominateur est l'étendue **totale de l'archive**. Or l'archive H4 de
**NVDA remonte au 2012-01-03**, quand les sept autres actions US démarrent en
2021 — et ses années anciennes sont **éclaircies** :

```
NVDA   2012-2019 ~255/an   2020:253   2021:252   2022:462   2023:499   2024:504   2025:496
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ une barre par jour ouvré
```

C'est le piège que l'amendement 4 ter a déjà nommé et mesuré : **MT5 sert de
l'historique ancien éclairci, étiqueté H1 sans l'être.** `calibrer_c_42.py` a été
durci contre lui le 2026-08-29 (code 7, refus des fenêtres à années creuses).
`lecture_h_trend.py`, écrit la veille, le reproduit.

**Le quotient rendait donc 328 barres/an pour une série qui en fait 498.**

---

## 2. Ce que ça faussait

Le décalage du null est **commun**, donc borné par la série la plus courte.
L'amendement 2 exige 99 décalages distincts, soit `99 + 2×500 = 1099` barres sur
cette série. Avec la mauvaise cadence, c'est NVDA qui portait la contrainte :

| | série la plus courte | barres/an | 1 099 barres en | lecture projetée |
|---|---|---|---|---|
| calcul par quotient *(avant)* | **NVDA** | 328 | 40,2 mois | **~2030-01** |
| années denses *(après)* | **NVDA** | 498 | 26,5 mois | **~2028-11** |

**La prose des amendements était juste ; c'est l'instrument qui l'implémente qui
était faux.** L'amendement 2 publie « ~2028-11 » et l'amendement 4 bis « n ≈ 1 570,
puissance 0,832 ». Après correction, l'instrument calcule **2028-11, n ≈ 1 577,
puissance 0,834**. Il reproduit les chiffres publiés, ce qu'il ne faisait plus.

### Le contrôle qui aurait tranché tout de suite

Reproduire la valeur publiée avant de croire son propre calcul. C'est la leçon
de méthode écrite dans l'amendement 4 le 2026-08-28 — *« ne jamais recalculer une
formule publiée sans d'abord REPRODUIRE le tableau publié »* — et c'est
littéralement le désaccord 2030-01 / 2028-11 qui a désigné le défaut. Le
document et l'instrument se contredisaient de quatorze mois, et rien ne le
signalait.

### La direction de l'erreur, et c'est ce qui compte le plus

**Vers l'ATTENTE.** Une cadence sous-estimée éloigne la date de lecture ; elle ne
peut pas la rapprocher. Ce défaut **ne pouvait pas provoquer une lecture
prématurée** — la seule faute qui aurait été irréparable. Il corrompait une
projection, pas une décision.

Et il n'a produit **aucune erreur** pendant neuf jours : code de sortie 0,
verdict « aucun blocage d'appareil », une date fausse. Un instrument qui se
trompe en silence a exactement la même signature qu'un instrument juste.

---

## 3. Le correctif

### 3.1 La cadence se mesure sur les années denses

`cadence_denses()` reprend **la règle et le seuil de
`calibrer_c_42.premiere_annee_dense`** — année sous 60 % de la densité des années
de référence (2024-2025) — plutôt que d'en écrire une seconde. Deux instruments
qui calculent la même grandeur de deux façons sont précisément ce que
`tradingbott/confrontation.py` cherche.

**La médiane et non la moyenne.** La première année d'une cotation est dense mais
incomplète (META 2021 : 431 barres depuis le 25 février). La moyenne s'y laisse
tirer vers le bas ; la médiane non.

**L'année courante est toujours écartée.** 2026 est partielle par construction ;
la compter ralentirait les 42 séries en même temps.

### 3.2 Partielle ≠ éclaircie, et ma première règle se trompait vers le silence

Deux raisons d'écarter une année, qui ne disent pas la même chose : la série n'a
vécu qu'une partie de l'année (**partielle**, normal), ou la donnée manque alors
qu'elle devrait être là (**éclaircie**, défaut).

Ma première version classait « partielle » toute année de **bord**. Elle
étiquetait ainsi NVDA 2012 — qui est éclaircie *et* en bord. **Une règle de
position minimise le défaut quand les deux causes coïncident**, c'est-à-dire
qu'elle se trompe vers le silence : la direction interdite pour une alarme. Un
test l'a fait tomber.

La règle retenue est le **prorata** : l'année de bord est comparée à ce que sa
fraction d'année réellement couverte laisse attendre.

### 3.3 La règle de l'amendement 2, rendue exécutable

L'amendement 2 exige 99 décalages distincts mais ne disait **pas comment `min_n`
se compte** — et la différence décide. `min_n_fenetre()` tranche, aujourd'hui,
dans le noir :

> **À la lecture, `min_n` est le nombre de barres H4 de la FENÊTRE sur la série
> la plus courte de l'univers.** Jamais l'étendue de l'archive, jamais une
> cadence, jamais une date. Une cadence est une projection ; ceci est un
> comptage.

Le décalage circulaire s'applique aux séries du test, pas à l'archive : une
archive de vingt ans ne rend pas un test lisible.

Le verrou est posé dans `executer()`, **avant toute statistique** — l'ordre des
verrous est le garde-fou, pas la bonne volonté de celui qui lit — et rend le
code **8**. Un symbole sans données compte **0** et fait refuser, plutôt que de
disparaître : l'écarter serait « retirer un symbole après coup » commis par
arithmétique, la panne exacte qui aurait éliminé 24 des 42 symboles en silence
(amendement 3).

### 3.4 Les chiffres en dur sont calculés

`« ~2028-11 »`, `« n ~ 1570 »` et `« 2 × 500 »` étaient écrits en dur dans le
rapport. Ils sont restés justes tant que la cadence l'était, et faux dès qu'elle
a dérivé. **Un chiffre en dur ne signale jamais qu'il a cessé d'être vrai.**

### 3.5 Onze tests

`recherche/test_cadence_et_decalages.py`. Le verrou de `executer()` est
aujourd'hui **inatteignable** — le verrou calendaire (2028-09-01) tire avant lui
— donc il ne s'exécutera pour de vrai qu'en 2028. Le tester maintenant est la
seule façon de savoir qu'il fonctionnera ce jour-là.

---

## 4. Ce que le correctif a trouvé en passant : AMZN a un trou en 2021

Le prorata devait excuser les premières années de cotation. Il en excuse sept sur
huit, et refuse la huitième :

| symbole | 1ʳᵉ barre | 2021 observé | attendu au prorata | ratio |
|---|---|---|---|---|
| AAPL | 2021-03-08 | 421 | 409 | 1,03 |
| MSFT | 2021-02-19 | 443 | 432 | 1,03 |
| TSLA | 2021-03-08 | 411 | 409 | 1,01 |
| META | 2021-02-25 | 431 | 422 | 1,02 |
| NFLX | 2021-03-03 | 425 | 415 | 1,02 |
| GOOGL | 2021-04-15 | 344 | 356 | 0,97 |
| **AMZN** | **2021-03-15** | **239** | **399** | **0,60** |
| **NVDA** | **2012-01-03** | **252** | **500** | **0,50** |

**Sept séries tombent entre 0,97 et 1,03 : le prorata est calibré.** AMZN manque
40 % de ses barres 2021 par rapport à sa propre date de début. Ce n'est pas un
effet de seuil.

**Ça ne touche pas le test.** 2021 est hors de la fenêtre (postérieure au
2026-08-27) et hors de la fenêtre de calibration de `c` (2022-2026). C'est un
fait sur l'archive, consigné pour ne pas être redécouvert.

---

## 5. Ce que cette note ne fait pas

- **Elle ne change aucune date de décision.** Le point de contrôle calendaire
  reste le 2028-09-01 ; les conditions de lecture restent `n ≥ 1200` **et** 99
  décalages distincts. La projection ~2028-11 de l'amendement 2 est **restaurée**,
  pas déplacée.
- **Elle ne touche ni `trend_donchian_h4.pine` ni `null_shift.py`.** Empreinte
  vérifiée intacte avant et après.
- **Elle ne rend pas la lecture plus proche.** Elle rend l'instrument capable de
  dire *quand* elle est, ce qu'il ne faisait plus.
- **Elle ne dit rien de H_TREND.** Aucune statistique de la relation testée n'a
  été calculée, et `--verifier` reste incapable d'en calculer une.

## 6. Ce qu'elle ne prouve pas

**Que le reste de l'instrument est sain.** Ce défaut est sorti de la première
commande tapée pour vérifier une affirmation — la mienne, et elle était fausse.
Rien n'indique que la deuxième ne trouverait rien. `lecture_h_trend.py` n'a
jamais été confronté à `calibrer_c_42.py` ni à `RAPPORT_UNIVERS.md` par
`confrontation.py` ; il l'est désormais sur la règle de densité, et sur rien
d'autre.

## 7. Un dernier écart, signalé et non corrigé

Le docstring de `lecture_h_trend.py` porte encore, sous le titre **« CE QUE LA
VERIFICATION CONTROLE ENCORE »**, les trois blocages décrits comme ouverts —
alors que la section qui la précède immédiatement les déclare amendés le
2026-08-28. **C'est cette prose périmée qui m'a induit en erreur au §0.**

Elle n'est pas réécrite ici : la corriger dans la même passe que le défaut
mêlerait deux choses, et ce fichier est celui que quelqu'un lira en 2028 pour
savoir ce qui était su à quelle date. L'écart est nommé, daté, et laissé à une
passe qui ne fera que ça.
