# Pré-inscription — test en avant du trend-following H4

**Déposé le 2026-08-26.** Aucune donnée postérieure au 2026-08-26 n'a été
regardée au moment d'écrire ce document.

**Empreinte de la configuration figée.** Deux fichiers, et deux seulement — ceux
qui définissent le test. Les autres scripts de `recherche/` sont de l'analyse,
pas de la configuration : les ajouter à l'empreinte la rendrait fragile.

```
365ab7b775dd14e417458c5ae47ce207de51159da92c444721bbf2ed039960b7  trend_donchian_h4.pine
b0f40f12a77955204b9914f81364e967a8751e640422bcdb9735fc7364c5ba21  recherche/null_shift.py
1f5318dc5bbaad7c93315dde947fb17a4fd58709134786e475b7cd72d4e32c2c  = empreinte globale
```

Recalcul (SHA256 de la concaténation des deux SHA256 individuels) :

```bash
cd /c/Users/grego/OneDrive/Daytrading/pine && /c/Users/grego/dev/Daytrading/bot/xaubot/.venv/Scripts/python.exe -c "import hashlib; t=hashlib.sha256(); [t.update(hashlib.sha256(open(f,'rb').read()).hexdigest().encode()) for f in ['trend_donchian_h4.pine','recherche/null_shift.py']]; print(t.hexdigest())"
```

Si cette empreinte ne se recalcule pas à l'identique au moment de la lecture, le
test est nul et non avenu — la configuration aura bougé.

---

## 1. L'hypothèse, formulée pour pouvoir être refusée

> **H_TREND.** Sur des barres H4 non encore collectées au 2026-08-26, la cassure
> Donchian 40 filtrée par EMA200 produit une espérance par trade **strictement
> supérieure à celle du même signal décalé circulairement** sur les mêmes prix.

Ce qui est testé n'est pas « la stratégie gagne ». C'est **« le signal apporte
quelque chose au-delà de la dérive du marché »**. La différence est tout le
sujet : sur 2012-2026, le signal brut gagne +0,386 R par trade, dont **+0,226 R
que le null obtient déjà** en entrant long à des dates arbitraires. L'objet du
test est le reste : **+0,160 R**.

## 2. Configuration figée — rien de tout ceci ne bougera

| Élément | Valeur |
|---|---|
| Timeframe | H4 |
| Signal | `close > plus_haut(high, 40)[1]` **et** `close > EMA200` |
| Sens | **long uniquement** |
| Stop initial | 1,5 × ATR(14) |
| Trail | Chandelier, 3,5 × ATR(14), monotone |
| Sortie forcée | 400 barres |
| Une position à la fois par symbole | oui |
| Friction | table par symbole du `README.md`, inchangée |

## 3. La statistique et le null

**Statistique** : expR poolé sur tous les symboles, longs seulement.

**Null** : décalage circulaire du signal, prix inchangé.
`sig_null[i] = sig[(i+k) mod n]`, décalage **commun** à tous les symboles,
`k ≥ 300` barres H4, **B = 2000**.

Taille du test vérifiée le 2026-08-26 : **0,057 à 5 %** sur 300 répétitions sous
H0 (cible 0,050, IC binomial ±0,025). Un `p < 0,05` en est bien un.

**p** = `(1 + #{null ≥ observé}) / (B + 1)`, unilatéral à droite.

## 4. Audit de puissance — fait AVANT, pas après

Écart-type par trade mesuré : **2,605 R**. Écart-type du null : `1,72/√n`.
Effet à détecter : **δ = +0,16 R**. Seuil 5 % unilatéral.

| n trades | puissance (analytique) | puissance (simulée) |
|---|---|---|
| 400 | 0,61 | 0,66 |
| 600 | 0,71 | 0,79 |
| 900 | — | 0,90 |
| 1000 | 0,84 | — |
| 1200 | 0,88 | 0,96 |

**Cible retenue : n = 1200 trades longs clôturés.** Au-dessus des 1000 requis
pour 80 %, la marge absorbe la corrélation supplémentaire qu'introduira
l'élargissement de l'univers.

> **RENVOI AJOUTÉ LE 2026-08-28 — cette table est optimiste. Aucun engagement
> n'est modifié ici ; seul ce renvoi est inséré, pour qu'on ne l'utilise pas
> telle quelle en 2028.**
>
> L'arithmétique est juste : la table se reconstruit exactement avec la formule
> du §Garde-fou ci-dessous, facteur `1,32·n` compris. Mais elle emploie
> `c = 1,72`, et le rejeu de `null_shift.py` du 2026-08-28 **mesure c = 2,125**
> (écart-type du null 0,0417 à n = 1 968) — 19 % de plus. Le même rejeu
> reproduit tout le reste à la virgule près.
>
> Avec le `c` mesuré : n=1200 → **0,831** et non 0,881. Le plancher de 0,80 tient
> encore, mais la marge vaut 0,031 au lieu de 0,081. Et si `c` dérive vers le
> 2,42 du bloc crypto — dégradation que ce document redoute lui-même deux
> paragraphes plus bas — n=1200 rend **0,787, sous le plancher**, et il en
> faudrait 1 251.
>
> Le garde-fou du §suivant absorbe cela sans qu'aucune décision soit à prendre :
> `c` sera recalculé sur les données du test. Il faut simplement s'attendre à ce
> qu'il morde. Table corrigée et détail :
> `AMENDEMENT_TREND_H4_2026-08-28.md`, §Amendement 4.

**Sans cet audit, ce test aurait été muet et je l'aurais cru concluant.**

## 5. Le goulot : la cadence — corrigé le 2026-08-26 après inspection de la station

**Correction n°1 — les barres n'ont pas besoin d'être collectées en continu.**
Le scanner de la station n'archive AUCUNE barre : `ScanStore` est en mémoire, et
seuls `paper_trades.csv` et le contexte sont écrits. Le cache parquet vient de
*fetchers à la demande* — `MT5DataFeed.load` (`copy_rates_range`) et l'API
publique Binance. L'historique 2026-2028 sera donc **récupérable en 2028**.
La watchlist du scanner est **sans rapport** avec ce test : elle sert à l'autre
hypothèse pré-enregistrée. Ma version précédente confondait les deux.

**Correction n°2 — la cadence dépend du marché d'un facteur 3.** Mesuré :

| Marché | barres H4/an | trades longs / symbole / an |
|---|---|---|
| Crypto 24/7 | 2192 | **20,3** |
| FX / indices | 1534 | **18,9** |
| Actions US | 501 | **6,8** |

Le « 13,9 par symbole » de ma première version était une moyenne qui cachait
cet écart. **Un univers penché sur les actions serait trois fois plus lent.**

**Pénalité de diversification, mesurée.** Dans `sd_null = c/√n` :

| Sous-univers | symboles | c |
|---|---|---|
| Crypto seul | 3 | **2,42** |
| Actions US | 7 | 1,84 |
| FX | 4 | 1,46 |
| Mélange | 6 | 1,66 |
| Tout | 17 | 1,86 |

`c` reste stable entre 1,5 et 1,9 dès que l'univers est mélangé — donc ajouter
des symboles achète bien de la puissance. Mais un **bloc homogène** est puni
(crypto seul à 2,42). Conclusion : élargir en mélangeant, pas en empilant
quinze altcoins.

## 5 bis. L'univers, figé maintenant

**42 symboles.** Il est nommé ici pour qu'il ne puisse pas être choisi plus tard
en fonction du résultat.

- **MT5 — FX, indices, matières (22)** : XAUUSD, XAGUSD, WTI, NATGAS, EURUSD,
  GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, EURGBP,
  AUDJPY, US30, US500, USTEC, DE40, UK100, JP225, FRA40
- **Binance spot (12)** : BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, ADAUSDT,
  AVAXUSDT, LINKUSDT, DOTUSDT, LTCUSDT, ATOMUSDT, DOGEUSDT
- **MT5 — actions US (8)** : AAPL, MSFT, NVDA, GOOGL, AMZN, TSLA, META, NFLX

BTCUSD / ETHUSD (CFD MT5) sont **exclus volontairement** : même sous-jacent que
les paires Binance, ils gonfleraient n sans ajouter d'information.

Cadence projetée : 22×18,9 + 12×20,3 + 8×6,8 = **714 trades/an** → n = 1200 en
**~20 mois**.

**Deux actions à faire, petites :**

1. **Résoudre les noms de symboles contre le broker réel et figer la liste
   résolue.** Les noms MT5 varient (WTI/USOIL, DE40/GER40) et `LiveMT5Feed.resolve`
   **filtre silencieusement les absents** — un symbole qui disparaît sans bruit
   change l'univers après coup. La liste résolue doit être écrite dans ce
   document avant que l'horloge démarre.
2. **Un fetch d'archivage trimestriel** dans le cache parquet, en assurance
   contre la purge d'historique du broker et contre un delisting Binance. Ce
   n'est PAS un collecteur temps réel : `MT5DataFeed.load` + le script
   `fetch_crypto_universe` suffisent, lancés 4 fois par an.

## 6. Règle de décision — arrêtée d'avance

Le test se lit **quand n ≥ 1200 trades longs clôturés**, sur des barres
**postérieures au 2026-08-27**. Point de contrôle calendaire : **2028-09-01**.

Deux conditions, toutes deux exigées :

1. **Statistique** : `p < 0,05`
2. **Économique** : edge net `(observé − moyenne du null) ≥ +0,08 R`
   (la moitié de l'estimation actuelle)

**Garde-fou de puissance, pré-spécifié ici pour ne pas être un calcul post-hoc.**
Les 88 % supposent `c = 1,72`. Le nouvel univers, plus chargé en crypto, peut
dégrader `c` (bloc homogène mesuré à 2,42). Donc **`c` sera recalculé sur les
données du test**, et la puissance atteinte avec :

```
puissance = Φ( (0,16 − 1,645·c/√(1,32·n)) / (sd_trade/√n) )
```

Si `puissance < 0,80`, **le test n'est pas lu** : on prolonge la collecte jusqu'à
ce que n la ramène au-dessus. Un `p ≥ 0,05` sous-puissant n'est pas une
réfutation, c'est un silence — et le confondre avec un résultat est exactement
l'erreur des 11 628 nuls.

| Résultat | Lecture |
|---|---|
| p < 0,05 **et** net ≥ 0,08 R | **Confirmé.** Premier edge validé en avant du projet. |
| p ≥ 0,05 **et** puissance ≥ 0,80 | **Réfuté.** Un nul est un résultat, pas un échec. |
| p ≥ 0,05 **et** puissance < 0,80 | **Muet.** Prolonger, ne rien conclure. |
| p < 0,05 **mais** net < 0,08 R | **Réel et économiquement nul.** Ne pas trader. |
| n < 1200 au 2028-09-01 | **Pas de test.** Rapporter le manque et la puissance atteinte. Ne pas lire quand même. |

**Friction à l'équilibre** (l'aller-retour qui annulerait l'edge net) : de
0,059 % (EURUSD) à 0,725 % (SOLUSDT). Marge par rapport aux frictions supposées :
4,1× au plus serré (BTCUSDT), 25× au plus large (NVDA). L'edge n'est pas fragile
aux coûts — mais **les spreads réels ne sont toujours pas mesurés (règle 11)**,
et cette marge repose sur des frictions supposées.

## 7. Ce qui est interdit

- Toucher un paramètre. Un seul changement et cette pré-inscription est morte.
- Retirer un symbole après coup parce qu'il tire le résultat vers le bas.
- Regarder avant n = 1200. Pas de lecture intermédiaire, pas de « juste un œil ».
- Refaire le test avec un autre null, un autre seuil, une autre fenêtre.
  **C'est un test unique.** Le plancher de p à B = 2000 (0,0005) ne le menace
  pas, contrairement à une campagne multiple.
- Repêcher un sous-groupe qui marche si l'ensemble échoue.

## 8. Ce que ce test ne dira pas

Il ne dira rien sur le comportement en **marché baissier prolongé**. La part
beta (+0,226 R) s'inversera dans ce régime ; la part signal n'a pas de raison de
s'inverser, mais 2026-2028 ne contiendra probablement pas la réponse. C'est une
question séparée, qui demandera ses propres données.

---

**Journal.** À remplir au moment de la lecture, et pas avant.

| Date | n atteint | expR observé | null moyen | p | edge net | verdict |
|---|---|---|---|---|---|---|
| | | | | | | |
