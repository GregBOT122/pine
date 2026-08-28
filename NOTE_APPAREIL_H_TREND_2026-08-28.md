# Note d'appareil — H_TREND ne serait pas lisible en 2028

> **Ceci n'est pas un amendement.** Rien n'est tranché ici : l'hypothèse, le
> seuil `n ≥ 1200`, le null, la règle de décision et l'univers restent
> exactement ce qu'ils étaient le 2026-08-26. Ce document constate trois
> blocages mécaniques et expose ce que chaque issue coûterait. **Le choix
> demande un amendement écrit et horodaté, avant toute donnée** — comme
> `AMENDEMENT_L2_2026-08-27.md`.

Trouvés le 2026-08-28 en écrivant `recherche/lecture_h_trend.py`, deux ans avant
la lecture. Reproductibles : `py lecture_h_trend.py --verifier` (code 3).

L'empreinte gelée `1f5318dc…e32c2c` est **intacte** et a été revérifiée avant et
après chaque manipulation, y compris le test négatif du verrou.

---

## Pourquoi ces trois choses se découvrent maintenant et pas le jour venu

Le script de lecture de H_L2 a été écrit 34 jours avant sa date, et il avait
déjà servi à trancher dans le vide des degrés de liberté que la pré-inscription
laissait ouverts. H_TREND n'avait aucun script de lecture. Sa lecture était donc
un plan, pas un appareil — et un plan ne révèle pas qu'il ne s'exécute pas.

Les trois blocages ci-dessous auraient été découverts **le 2028-09-01**, au
moment de lire, c'est-à-dire au pire moment possible : celui où toute correction
se fait en connaissant déjà les données.

---

## Blocage 1 — l'appareil gelé ne connaît que 17 des 42 symboles

`null_shift.py` porte un dictionnaire `FRICTION` de 17 symboles. Il a été écrit
le 2026-08-26 pour la **calibration historique**. L'univers a été figé à
**42 symboles** le 2026-08-27, le lendemain, par un autre document.

Les 25 orphelins : ADAUSDT, ATOMUSDT, AUDJPY, AUDUSD, AVAXUSDT, BNBUSDT, DE40,
DOGEUSDT, DOTUSDT, EURGBP, EURJPY, FRA40, GBPJPY, JP225, LINKUSDT, LTCUSDT,
META, NATGAS, NFLX, NZDUSD, UK100, USDCAD, USDCHF, WTI, XRPUSDT.

**Les deux sorties évidentes sont toutes deux interdites :**

| sortie | ce qu'elle vaut |
|---|---|
| leur donner un coût en 2028 | un paramètre choisi **après** avoir vu le paysage |
| les retirer de l'univers | « retirer un symbole après coup », interdit nommément |

Ce qui existe déjà et pourrait fonder un amendement : `spreads_mesures.csv`
accumule des spreads réels depuis le 2026-08-27, et `univers_resolu.json` porte
`frais_crypto_rt_pct = 0,2`. La matière est là. **Ce qui manque est une règle
écrite avant de regarder** qui dise comment un spread mesuré devient un coût
d'aller-retour, pour les 42 symboles et pas seulement pour les 25.

Un amendement pris maintenant serait aveugle au résultat. Pris en 2028, non.

---

## Blocage 2 — l'espace des décalages est vide au seuil de lecture

Le décalage du null est **commun** à tous les symboles — c'est une exigence de
la pré-inscription, elle garde la synchronisation inter-symboles. Il est donc
borné par la série la plus **courte**.

    série la plus courte      META, ~500 barres H4/an (actions US)
    fenêtre à n=1200 (~20 mois)   ~833 barres
    MINSHIFT du fichier gelé      500
    intervalle tirable            [500, 333]   -> VIDE

**Aucune permutation n'est tirable. Le null n'existe pas**, et sans null il n'y
a ni p, ni edge net, ni décision.

La pré-inscription écrit « décalage commun ≥ 300 » là où le fichier gelé pose
500. Ce n'est pas une contradiction : 500 satisfait « ≥ 300 ». Et la
pré-inscription définit la configuration **par l'empreinte de deux fichiers**,
pas par sa prose — donc c'est 500 qui gouverne, et 500 ne marche pas.

À titre indicatif, si un amendement retenait 300 : l'intervalle deviendrait
[300, 533], soit **234 décalages distincts**. Le plancher réel de `p` serait
alors `1/235 = 0,0043` — et non `1/(B+1) = 0,0005` comme le laisse croire
`B = 2000`. Le test pourrait encore rejeter à 5 %, mais avec une résolution dix
fois plus grossière qu'annoncée. **Le plancher réel est gouverné par le nombre
de décalages distincts, jamais par B.**

---

## Blocage 3 — l'assurance ne remplit pas le magasin que l'appareil ouvre

    load() du fichier gelé  ->  {CACHE}/{symbole}_H1_*.parquet, réagrégé en H4
    archivage trimestriel   ->  donnees-h4/{SYMBOLE}_H4.csv

Deux endroits différents. L'archivage trimestriel a été mis en place précisément
parce que **Fusion ne garde qu'environ 4 ans d'H1 sur les actions** et que
l'historique 2026-2027 aura disparu en 2028. Il fonctionne : 42/42 symboles
archivés. Mais il écrit là où l'appareil ne regarde pas.

En l'état, `load()` ne trouvera pas la fenêtre 2026-2028 dans le cache parquet.
L'assurance est souscrite ; elle n'est pas branchée.

---

## Quatrième constat, plus discret : la table de puissance est optimiste

La pré-inscription annonce une puissance de 0,71 / 0,84 / 0,88 à n = 600 / 1000
/ 1200. Recalculée de deux façons indépendantes (forme fermée et simulation à
20 000 tirages), avec les mêmes constantes du document (`c = 1,72`,
`sd = 2,605 R`, effet `+0,16 R`, seuil unilatéral 5 %) :

| n | forme fermée | simulée | annoncée |
|---|---|---|---|
| 600 | 0,662 | 0,657 | 0,71 |
| 1000 | 0,804 | 0,798 | 0,84 |
| 1200 | 0,851 | 0,848 | **0,88** |

Les deux méthodes s'accordent entre elles à 0,005 près et tombent toutes deux
sous la table, d'environ 0,04. **L'écart est donc dans le chiffre annoncé.**

Il compte, parce que la pré-inscription pose un garde-fou : *si la puissance
atteinte est sous 0,80, le test n'est pas lu*. À n = 1000 la valeur recalculée
vaut 0,80 — **exactement le plancher, marge nulle**, là où le document laissait
croire à un confort de 0,04. Le seuil `n ≥ 1200` reste au-dessus, mais la marge
est deux fois plus mince qu'écrit.

Ça ne change aucune décision aujourd'hui : `c` sera de toute façon **recalculé
sur les données du test** avant lecture, comme prévu. Ça dit seulement que la
projection ne doit pas servir de coussin.

---

## Ce que cette note ne fait pas

Elle ne choisit pas `MINSHIFT`. Elle ne fabrique pas 25 frictions. Elle ne
rebranche pas `load()`. Chacune de ces trois choses est un changement d'appareil
qui doit être écrit, justifié et horodaté **avant** que quiconque ait vu une
statistique de la fenêtre — sans quoi le test n'aura pas la valeur pour laquelle
tout ce dispositif existe.

Et une quatrième issue reste ouverte, qu'il faut nommer pour qu'elle soit un
choix et non un défaut : **constater que H_TREND, tel qu'il a été gelé, n'est
pas exécutable, et le dire**. Ce serait un résultat sur l'appareil, pas sur le
marché — mais c'en est un.
