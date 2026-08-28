# Amendement à la pré-inscription H_TREND — 2026-08-28

> **Écrit avant que la moindre statistique de la fenêtre existe.** La fenêtre a
> deux jours, l'accumulation vaut 318 barres H4, et aucun `expR`, aucun `p`,
> aucun edge net n'a été calculé sur elle — ni par moi, ni par personne. C'est
> l'horodatage du commit qui donne sa valeur à ce document, exactement comme
> pour la pré-inscription qu'il amende.

Il répond aux trois blocages de `NOTE_APPAREIL_H_TREND_2026-08-28.md`, trouvés
en écrivant `recherche/lecture_h_trend.py` deux ans avant la lecture.

---

## Ce qui NE change PAS

- **H_TREND**, mot pour mot : sur des barres H4 postérieures au 2026-08-27, la
  cassure Donchian 40 + filtre EMA200, long only, a une `expR` strictement
  supérieure au même signal décalé circulairement sur les mêmes prix.
- **Le seuil `n ≥ 1200`** trades longs clôturés.
- **La double condition** : `p < 0,05` unilatéral **et** edge net `≥ +0,08 R`.
- **Le garde-fou de puissance** : `c` recalculé sur les données du test, et si la
  puissance atteinte est sous 0,80, **le test n'est pas lu**.
- **L'univers de 42 symboles**, SHA256 `b09836ac…9ba962`. Aucun symbole n'entre,
  aucun ne sort.
- **La règle elle-même** : `N=40, K=1.5, M=3.5, E=200, MAXB=400`, et les
  fonctions `signals`, `precompute`, `walk`, `stat` du fichier gelé.
- **L'empreinte `1f5318dc…e32c2c`** des deux fichiers gelés. Elle est **intacte**
  et le reste : aucun des trois amendements ci-dessous ne touche à
  `trend_donchian_h4.pine` ni à `recherche/null_shift.py`.

Ce dernier point est le fil conducteur. **Ce qui est gelé est la RÈGLE.** Les
coûts, la politique de décalage et l'emplacement des données ne sont pas la
règle et ne l'ont jamais été — ils vivent dans des constantes de module que la
lecture n'exécute pas. Cette interprétation est faite dans le noir ; elle est
écrite ici pour pouvoir être jugée, pas pour passer inaperçue.

---

## Amendement 1 — la table de friction est celle de l'univers, pas celle de la calibration

### Le problème

`null_shift.py` porte un dict `FRICTION` de **17 symboles**, écrit le 2026-08-26
pour la calibration historique. L'univers a été figé à **42 symboles** le
lendemain, par un autre document. 25 symboles n'ont donc pas de coût.

### La décision

**Le coût d'aller-retour du test forward est celui de `univers_resolu.json`, pas
celui de `null_shift.py`.**

    friction_A/R(symbole) = p90 du spread mesuré sur la fenêtre
                          + frais de commission A/R  (0,20 % crypto, 0 sinon)

`univers_resolu.json` porte déjà `spreads[symbole] = {med, p90, n}` pour les
**42/42**, mesurés sous la règle 11 sur quatre sessions (Londres, New York, nuit
asiatique, rollover), et `frais_crypto_rt_pct = 0,20`. La table existe ; elle
n'était simplement pas branchée sur la lecture.

**Aucun changement d'empreinte.** `precompute(d, fric)` reçoit le coût en
**argument**. Le dict `FRICTION` n'est lu que dans la boucle de niveau module —
celle qui lance la calibration historique — et la lecture ne l'exécute pas.

### Les trois choix à l'intérieur, tranchés maintenant

1. **p90 et non médiane.** Le p90 est le choix conservateur : une confirmation
   doit survivre aux mauvais jours, pas seulement au jour médian. Le rapport
   d'univers affiche les deux ; la lecture retiendra le p90. Sur les actions US
   l'écart médiane→p90 vaut jusqu'à +32 % (MSFT 0,1049 → 0,1382 %).
2. **Calculé à la lecture, sur les spreads de la fenêtre.** La règle est fixée
   aujourd'hui, la valeur vient plus tard — même construction que `c`, qui sera
   recalculé sur les données du test. Un spread n'est pas la relation testée :
   la tâche `spreads-sessions` l'échantillonne quatre fois par jour sans jamais
   toucher au signal. Le mesurer sur 2026-2028 est donc à la fois aveugle et
   plus représentatif qu'un instantané de deux jours.
3. **Instantané de référence enregistré aujourd'hui**, pour que la dérive soit
   visible plutôt que supposée : `univers_resolu.json`, 238 mesures par symbole
   au 2026-08-28. Si la friction 2028 s'écarte fortement de celle-ci, l'écart
   sera rapporté avec le résultat.

### Ce que ça coûte, dit franchement

La marge de friction des 12 crypto est déjà **SERRÉE** (1,5x à 2,9x) sur la
médiane. Au p90 elle se resserre encore. Ce n'est pas un motif pour les retirer
— ce serait le repêchage interdit — mais une confirmation portée par la jambe
crypto devra être lue en sachant que sa marge de coût est au point mort.

---

## Amendement 2 — `MINSHIFT` reste 500, et la lecture attend l'espace de décalage

### Le problème

Le décalage est **commun** à tous les symboles ; il est donc borné par la série
la plus **courte**. Les actions US produisent ~500 barres H4/an. À `n = 1200`
(~20 mois) elles en auront ~833, et l'intervalle `[500, 333]` est **vide** :
aucune permutation tirable, donc pas de null, donc pas de `p`.

### Pourquoi on ne descend PAS à 300

La pré-inscription écrit « décalage commun ≥ 300 barres ». **Cette borne est
insuffisante, et il faut le dire plutôt que s'en servir.**

`MAXB = 400` : un trade peut durer jusqu'à 400 barres. Un signal décalé de 300
barres retombe donc **à l'intérieur de la fenêtre de son propre trade**. Le
« null » garderait une partie de l'alignement qu'il est censé détruire, et
rendrait des `p` trop petites — le même mécanisme, sous une autre forme, que
celui qui a fait annuler la campagne contexte empilée le 2026-08-25.

**La contrainte réelle est `MINSHIFT > MAXB`.** 500 la satisfait, 300 non. Le
`500` du fichier gelé n'est donc pas un détail d'implémentation qui l'emporte
sur la prose : c'est la seule des deux valeurs qui soit valide. La prose est
amendée, pas contournée.

### La décision

`MINSHIFT = 500`, inchangé. **Et une condition de lecture est ajoutée :**

> La lecture exige, en plus de `n ≥ 1200`, qu'au moins **99 décalages communs
> distincts** soient tirables — c'est-à-dire `min_n ≥ 1099` barres H4 sur la
> série la plus courte de l'univers.

**Pourquoi 99.** Le plancher réel de `p` vaut `1/(décalages distincts + 1)`, et
**jamais `1/(B+1)`** : `B = 2000` tirages piochent avec remise dans un ensemble
d'au plus `min_n − 2·MINSHIFT` valeurs. À 99 distincts le plancher vaut `0,010`,
soit un cinquième du seuil de 0,05. C'est le seuil qui décide, pas la résolution
de l'instrument. À 19 distincts le plancher vaudrait 0,05 : le test ne pourrait
littéralement pas rejeter.

    années de fenêtre   min_n   distincts   plancher réel de p
    2,0                 1000    0           VIDE — pas de null
    2,2                 1083    83          0,0119
    2,3                 1166    166         0,0060
    2,5                 1250    250         0,0040

**Le plancher réel sera rapporté avec le résultat**, quel qu'il soit.

### Conséquence sur la date, et pourquoi ce n'est pas de l'arrêt optionnel

Le point de contrôle passe du **2028-09-01** au premier moment où les **deux**
conditions tiennent. Projeté sur la cadence mesurée : **~2028-11-06**, environ
deux mois plus tard.

Ce déplacement est décidé **maintenant, sans donnée**, et il dépend d'un critère
**mécanique** — un nombre de barres sur la série la plus courte — qui ne peut
pas être influencé par le résultat, ni même le connaître. C'est exactement la
construction retenue pour H_L2, dont la prolongation dépend de la couverture et
non du signe. Un critère d'arrêt lisible sur l'appareil n'est pas de l'arrêt
optionnel ; un critère lisible sur la relation en serait.

La puissance ne peut qu'y gagner : `n` sera plus grand qu'à 1200.

---

## Amendement 3 — l'archivage doit stocker ce que l'appareil consomme

### Le problème

    load() du fichier gelé   ->  {CACHE}/{symbole}_H1_*.parquet, RÉAGRÉGÉ en H4
    archivage trimestriel    ->  donnees-h4/{SYMBOLE}_H4.csv, H4 pris tel quel

`archivage_h4.py` demande `TIMEFRAME_H4` à MT5. L'apparat gelé, lui, demande du
H1 et le réagrège avec `resample('4h')`. **Ce ne sont pas les mêmes barres** :
les bornes des sessions ne tombent pas au même endroit. L'assurance a été
souscrite contre la purge d'historique de Fusion — elle fonctionne, 42/42 — mais
elle remplit un magasin que l'apparat n'ouvre pas.

### La décision

**L'archivage trimestriel stocke désormais le H1**, au format et au schéma que
`load()` attend (index `DatetimeIndex` nommé `time`, colonnes
open/high/low/close/tick_volume, un fichier `{symbole}_H1_{début}_{fin}.parquet`
par passage). Les CSV H4 existants sont conservés comme **témoin secondaire ;
ils ne sont pas la source de la lecture.**

**Destination : `dev\Daytrading\donnees-h1`, hors dépôt** — et non le cache de
`xaubot`. Celui-ci est gitignoré, mais il vit *à l'intérieur* d'un dépôt :
déplacer le code y déplacerait les données. C'est la panne exacte qui a coûté
deux jours de collecte L2 les 25 et 26 août, et la règle posée depuis par
`tradingbott/chemins.py` — un chemin absolu déclaré, jamais dérivé de l'endroit
d'où l'on lance.

`load()` n'est pas modifié pour autant. Il lit `CACHE` dans **son propre espace
de noms**, et cet espace est celui que le script de lecture crée en exécutant le
fichier gelé : lui assigner une autre valeur avant l'appel suffit. **L'empreinte
reste intacte** ; l'emplacement des données n'a jamais fait partie de la règle.

**Pourquoi pas l'inverse** — c'est-à-dire lire les CSV H4 déjà là, ce qui serait
plus court : parce que choisir en 2028 entre « H4 du broker » et « H1 réagrégé »
serait choisir une construction de barres en connaissant le paysage. La
pré-inscription fige un apparat qui réagrège du H1 ; l'assurance doit s'y plier,
pas l'inverse.

**Aucun changement d'empreinte** : c'est de la plomberie, `load()` n'est pas
touché.

### L'urgence — mais pas celle que j'ai d'abord écrite

**Correction, faite avant de committer ce document.** J'avais justifié l'urgence
par « Fusion ne garde que ~4 ans d'H1 sur les actions, l'historique 2026-2027
aura disparu ». C'est l'argument du 2026-08-27, et `archivage_h4.py` le
**réfute dans son propre en-tête**, mesures à l'appui le 2026-08-28 : AAPL
démarre au 2021-03-08 et son compte de barres *augmente* d'un jour sur l'autre
(9 645 → 9 648). Ces dates sont celles où le courtier a ajouté les titres, pas
le bord d'une purge. J'ai repris une affirmation que le dépôt avait déjà
corrigée le même jour.

Ce qui est réellement mesuré, et qui justifie quand même l'archivage H1 :

1. **Rien n'alimente le cache.** Les parquets H1 du cache s'arrêtent à
   l'historique ; aucune tâche n'y écrit la fenêtre 2026-2028. En 2028 il
   faudrait re-télécharger — c'est-à-dire dépendre, le jour de la lecture, d'une
   API et d'un courtier qui répondent. Une assurance qui suppose que tout
   fonctionne le jour J n'est pas une assurance.
2. **La fenêtre Binance glisse sur 3 ans**, mesuré : 26 280 barres H1 = 3 × 8 760,
   et sa date de début a avancé d'un jour entre le 27 et le 28 août. Elle
   couvrira 2025-09 → 2028-09 au contrôle initial : les données du test sont
   dedans. **Mais l'amendement 2 repousse la lecture d'environ 6 mois**, à
   ~2028-11. La marge avant que la fenêtre glissante ne morde sur le début du
   test (août 2029) passe de ~15 mois à ~9. Elle reste confortable ; elle n'est
   plus intacte, et c'est cet amendement qui l'a consommée.
3. **Le delisting**, seul risque qui détruit vraiment. Sur 12 altcoins et deux
   ans, un retrait de paire n'est pas une hypothèse d'école — et un symbole
   perdu est un symbole retiré de l'univers après coup, ce que la
   pré-inscription interdit.

### Et le vrai motif, découvert en écrivant ce paragraphe

**Le cache ne contenait que 18 symboles** — AAPL, AMZN, BTCUSDT, ETHUSDT,
EURUSD, GBPUSD, GOOGL, META, MSFT, NVDA, SOLUSDT, TSLA, US30, US500, USDJPY,
USTEC, XAGUSD, XAUUSD, plus VIXY qui n'est pas de l'univers. C'est **l'ancien
panier**, pas les 42 symboles figés le 2026-08-27.

Les 24 autres — ADAUSDT, AUDJPY, DE40, NATGAS, WTI, NFLX, UK100, JP225… —
n'avaient **aucun parquet H1, même historique**. Or `load()` rend `None` quand
il ne trouve rien, et la boucle appelante fait `continue`. En 2028, **24 des 42
symboles auraient été écartés en silence, sans qu'une seule erreur soit levée.**

C'est « retirer un symbole après coup », commis par omission, et découvert par
accident en vérifiant autre chose. L'archivage H1 le corrige à la racine : il
peuple les 42, depuis le 2024-01-01, avec l'amorce nécessaire à l'EMA200 et à
l'ATR. **Exécuté le 2026-08-28 : 42/42, 21 Mo.** Et le rapport d'archivage
signale désormais bruyamment tout symbole sans H1 — c'est le seul endroit où on
peut encore l'apprendre avant la lecture.

---

## Ce que cet amendement n'autorise pas

- **Retirer un symbole.** Les 12 crypto restent, marge serrée comprise. Les
  actions US restent, alors qu'elles seules imposent le report de deux mois.
- **Toucher `N, K, M, E, MAXB`**, ni aucune ligne des deux fichiers gelés.
- **Lire avant que les deux conditions tiennent**, ni « jeter un œil » à un
  sous-ensemble qui serait, lui, déjà prêt.
- **Repêcher un sous-groupe** si l'ensemble échoue.
- **Refaire la lecture** avec un autre null, un autre seuil ou une autre table
  de friction. Test unique.

## Un détail à ignorer, écrit pour qu'il n'inquiète pas en 2028

`recherche/friction.py` imprime en fin d'exécution un SHA256 « de la
configuration figée » calculé sur **tous les `.py` du dossier** plus le `.pine`.
C'est la formule que la pré-inscription a explicitement rejetée, précisément
parce qu'elle change dès qu'on ajoute un script d'analyse — et l'ajout de
`lecture_h_trend.py` vient de la faire changer. **Cette ligne est périmée et ne
vaut rien.** L'empreinte qui compte est celle de deux fichiers nommés,
`1f5318dc…e32c2c`, et elle est intacte.
