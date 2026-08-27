# Résolution de l'univers H_TREND — à lancer sur la station

## Ce que ça fait

1. **Résout** les 42 symboles de la pré-inscription contre le broker réel.
2. **Mesure le spread réel** par symbole, échantillonné dans le temps (règle 11).
3. **Compare** au seuil de rentabilité : `0,2406 × ATR%` = la friction
   aller-retour qui annule l'edge net de +0,1604 R sur un stop de 1,5 ATR.

N'envoie aucun ordre. Lecture seule sur MT5.

## Installation

Copier `resoudre_univers.py` et `RESOUDRE_UNIVERS.bat` **dans le dossier
`station-scanner` de la station** (à côté de `lancer_scanner.bat`), pour que
`python.cfg` soit trouvé. Le `.bat` cherche `python.cfg` à côté de lui puis dans
le dossier parent.

## Usage

```
RESOUDRE_UNIVERS.bat          30 min d'échantillonnage de spreads
RESOUDRE_UNIVERS.bat 0        résolution seule, un passage
RESOUDRE_UNIVERS.bat 120      2 h
```

**Prérequis : MetaTrader5 ouvert ET connecté.** Sinon `mt5.initialize()` échoue
et le script s'arrête proprement, sans rien écrire de faux.

**Relancer à des heures différentes.** Le CSV des spreads est appendé, pas
écrasé : ouverture de Londres, ouverture de New York, nuit asiatique. Un spread
mesuré à une seule heure ne vaut rien — c'est tout l'objet de la règle 11.

## Sorties

| Fichier | Contenu |
|---|---|
| `univers_resolu.json` | la liste résolue + specs + SHA256 de l'univers |
| `spreads_mesures.csv` | un échantillon par ligne, accumulé sur tous les runs |
| `RAPPORT_UNIVERS.md` | le rapport lisible, verdict par symbole |

`RAPPORT_UNIVERS.md` est aussi copié dans `OneDrive\collect_donne_trading\`,
comme `RAPPORT_H1.md`, pour être lu depuis l'autre PC.

## Ce qu'il faut faire du résultat

1. **Trancher chaque manquant.** Soit le remplacer par un nom valide proposé,
   soit le retirer explicitement de la pré-inscription. Le laisser tomber en
   silence changerait l'univers après coup — c'est exactement le trou que ce
   script existe pour boucher.
2. **Trancher chaque `ECHEC` de friction.** Les garder en le sachant, ou les
   retirer en le notant.
3. **Coller la liste résolue dans la pré-inscription**, puis démarrer l'horloge.
   Pas avant.

## Deux garde-fous dans le code

**La résolution automatique est stricte.** Nom exact, alias écrit à la main, ou
même ticker simplement décoré (`XAUUSD.raw`, `#AAPL`, `US30Cash`). Le
rapprochement flou ne résout rien : testé contre un broker fictif, il donnait
`XAGUSD` (argent) → `XNGUSD` (gaz naturel) et `AUDUSD` → `XAUUSD` (or), à un
caractère d'écart. Substituer silencieusement un instrument par un autre est
pire que de le déclarer manquant. Le flou ne sert qu'à suggérer.

**La valeur du point est mesurée**, via `order_calc_profit` — la fonction que le
broker utilise vraiment pour le P&L. `trade_tick_value` et `trade_contract_size`
peuvent se contredire sur le même symbole (cas avéré sur XAUUSD/MetaQuotes-Demo,
facteur 10).

## Ce que la partie Binance a déjà dit (testée le 2026-08-26)

12/12 symboles en TRADING. Mais la friction crypto est dominée par **les frais,
pas le spread** — les spreads de carnet vont de 0,0000 % à 0,115 %, les frais
taker standard font 0,200 % aller-retour à eux seuls.

| Tier de frais | Verdict sur les 12 |
|---|---|
| 0,200 % A/R (taker standard) | **12 SERRE**, marge 1,5× à 2,9× |
| 0,075 % A/R (VIP/BNB ou maker) | **11 OK**, 1 SERRE (DOTUSDT) |

Le backtest supposait 0,090 % : entre les deux. Optimiste pour un compte
standard, à peu près juste pour un compte remisé. **À trancher avant de démarrer :
le tier de frais réel décide si la jambe crypto tient.**

Second constat : sur les 12, l'ATR% des 42 derniers jours est **~40 % sous** la
médiane 3 ans (BTC 0,841 contre 1,283). Régime de basse volatilité en cours. Le
seuil de friction étant proportionnel à l'ATR%, la marge crypto est actuellement
plus serrée que le tableau 3 ans ne le montre.
