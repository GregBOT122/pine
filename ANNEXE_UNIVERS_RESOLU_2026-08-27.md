# Annexe à PREINSCRIPTION_TREND_H4_2026-08-26 — univers résolu

**CONFIRME le 2026-08-27.** `GOOGL` -> `Alphabet-A` tranche et accepte (voir §3).

Résolution faite le **2026-08-27 16:36 UTC** contre le broker réel.

    broker      Fusion Markets Pty Ltd
    compte      470599  —  FusionMarkets-Live  —  REEL
    offerts     250 symboles
    resolus     42 / 42        manquants : 0
    SHA256      b09836abe7c035df4467f53c79297a54ceafee7969e1691c7dfb6b729b8ba962

Ce SHA256 fige la liste résolue. S'il ne se recalcule pas à l'identique, l'univers
a changé et le test est nul — même règle que l'empreinte des deux fichiers de
configuration.

---

## 1. Pourquoi cette annexe existe

La pré-inscription exigeait, au titre des « deux vraies actions » :

> résoudre les noms de symboles contre le broker et **figer la liste résolue** —
> `LiveMT5Feed.resolve` filtre silencieusement les absents, et un symbole qui
> disparaît sans bruit change l'univers après coup.

C'est fait. Et le risque n'était pas théorique : **au premier passage, 7 des 8
actions US sont ressorties « MANQUANT »** alors qu'elles sont toutes offertes.

---

## 2. Correspondances retenues

Fusion Markets nomme ses actions par la **société**, pas par le ticker. Le
résolveur strict (nom exact, alias écrit à la main, ticker simplement décoré) ne
pouvait pas les voir.

| Pré-inscription | Nom broker | | Pré-inscription | Nom broker |
|---|---|---|---|---|
| `AAPL` | `Apple` | | `WTI` | `XTIUSD` |
| `AMZN` | `Amazon` | | `NATGAS` | `XNGUSD` |
| `GOOGL` | `Alphabet-A` | | `DE40` | `GER40` |
| `MSFT` | `Microsoft` | | `USTEC` | `NAS100` |
| `NFLX` | `Netflix` | | `JP225` | `JPN225` |
| `NVDA` | `NVIDIA` | | | |
| `TSLA` | `Tesla` | | | |
| `META` | `Meta` | | | |

Les 12 symboles Binance et les 22 autres MT5 se résolvent par leur nom exact.

**Ces alias sont inscrits dans `resoudre_univers.py`**, pas appliqués à la main :
une correction manuelle du JSON ne serait pas reproductible, et son empreinte ne
vaudrait rien.

---

## 3. LE SEUL CHOIX AMBIGU — TRANCHE

Le broker offre **`Alphabet-A` et `Alphabet-C`**. `GOOGL` désigne les actions de
**classe A** ; `Alphabet-C` correspond à `GOOG`, qui est un **autre titre**.

**TRANCHE le 2026-08-27 : `GOOGL` -> `Alphabet-A`.** Classe A, conformement au
ticker inscrit dans la pre-inscription.

Si `Alphabet-A` disparaissait un jour, **ne pas basculer sur `Alphabet-C` en
silence** — ce serait changer l'univers après coup.

## 3 bis. Le rapprochement flou n'a rien tranché, et c'est voulu

Ce qu'il proposait avant que les alias soient écrits :

    AAPL -> ADP        AMZN -> AMD        TSLA -> TSMC
    NVDA -> NVIDIA, NZDCAD                GOOGL, MSFT, NFLX -> aucun

Trois faux à un caractère près, un seul juste. **Le flou suggère, un humain
tranche** — la règle tient.

---

## 4. RÈGLE 11 : les frictions ne sont plus supposées

La pré-inscription annonçait « marge 4,1x au plus serré (BTCUSDT) à 25x au plus
large (NVDA) », en précisant que ces frictions étaient **supposées**. Mesurées :

| Groupe | Marge mesurée | Verdict |
|---|---|---|
| Indices | 10x à 66x | OK |
| FX | 6,1x à 15,5x | OK |
| Métaux, WTI | 6,3x à 33x | OK |
| Actions US | 4,5x (NFLX) à 24x (NVDA) | OK |
| **NATGAS** | **2,3x** | **SERRE** |
| **Les 12 crypto** | **1,5x (BTCUSDT) à 2,9x** | **SERRE** |

Bilan : **29 OK, 13 SERRE, 0 ECHEC.**

**La marge la plus serrée n'est pas 4,1x mais 1,5x**, et la cause est
identifiable : le backtest supposait 0,090 % aller-retour — **le chiffre
d'Hyperliquid** — alors que le taker standard Binance est 0,200 %. Ce n'est pas
une erreur de mesure, c'est une hypothèse héritée du mauvais marché.

### Et le régime actuel resserre encore

Le seuil de friction est **proportionnel à l'ATR%**. Or l'ATR% récent des crypto
est très en dessous du structurel :

    SOLUSDT  -50 %    DOGEUSDT -47 %    BNBUSDT  -43 %    XRPUSDT -42 %
    LINKUSDT -41 %    LTCUSDT  -35 %    AVAXUSDT -34 %    DOTUSDT -33 %
    ETHUSDT  -31 %    BTCUSDT  -30 %    ATOMUSDT -30 %

À volatilité d'aujourd'hui, la marge de `BTCUSDT` tombe autour de **1,05x** — le
point mort.

**Ce que ça ne change PAS.** Aucun symbole n'est retiré. La pré-inscription
interdit d'en ôter un après coup, et le faire parce que la friction déplaît
serait exactement le repêchage qu'elle proscrit.

**Ce que ça change.** Ce qu'une confirmation voudrait dire. Sur la jambe crypto,
et dans le régime actuel, l'edge net serait mangé par les frais. C'est
précisément ce que la règle 11 existe pour révéler avant le test plutôt qu'après.

---

## 5. Ce qui reste à faire

1. **Ré-échantillonner les spreads à d'autres heures.** Un seul échantillon par
   symbole pour l'instant, pris à 16h30 UTC. `spreads_mesures.csv` s'accumule :
   relancer à l'ouverture de Londres, à celle de New York, et en nuit asiatique.
   **Un spread mesuré à une seule heure ne vaut rien.**
2. **Archivage trimestriel**, et c'est plus urgent qu'annoncé : Fusion ne garde
   qu'environ **4 ans d'H1 sur les actions** (AAPL 9 645 barres depuis 2021-03,
   contre 48 714 pour EURUSD depuis 1997). L'historique 2026-2027 aura disparu
   au moment de lire si personne ne l'archive.
3. ~~Confirmer `GOOGL`~~ — fait le 2026-08-27.
4. **Verser ce dossier dans un depot.** `pine\` n'est pas versionne : la
   pre-inscription H_TREND et cette annexe reposent sur des dates de fichier,
   pas sur des commits. C'est plus faible que H_L2 et H1, dont l'engagement est
   horodate par un commit pousse.

---

## 6. Le dossier est devenu un dépôt (2026-08-27)

`pine\` vivait sous OneDrive et n'était pas versionné : la pré-inscription et
cette annexe reposaient sur des **dates de fichier**, pas sur des commits.

**Nouvel emplacement : `C:\Users\grego\dev\Daytrading\pine`**, dépôt git, branche
`main`. Un dépôt ne va jamais sous OneDrive — écritures atomiques de git en
échec, fichiers « en ligne uniquement » absents du disque, et deux systèmes de
version qui se marchent dessus. Vérifié avant de déplacer : 0 fichier hors ligne
sur 26.

### L'empreinte, vérifiée trois fois

    avant le déplacement    1f5318dc...e32c2c   identique
    après le déplacement    1f5318dc...e32c2c   identique
    dans un CLONE FRAIS     1f5318dc...e32c2c   reproduite

Le troisième contrôle n'est pas du zèle. **Git convertit LF -> CRLF à la sortie
par défaut sous Windows** : sans précaution, un clone aurait rendu d'autres
octets, l'empreinte ne se serait plus recalculée, et le test se serait déclaré
nul **par sa propre règle**, sans que personne ait touché une ligne de code.
Les avertissements « LF will be replaced by CRLF » à l'ajout portaient
précisément sur les deux fichiers empreintés.

`.gitattributes` pose donc `* -text` : aucune conversion, les octets sortent
comme ils sont entrés.

### Le chemin dans la pré-inscription est périmé, et c'est voulu

La commande de vérification du §Empreinte de
`PREINSCRIPTION_TREND_H4_2026-08-26.md` commence par
`cd /c/Users/grego/OneDrive/Daytrading/pine`. **Ce document n'est pas modifié** :
c'est l'engagement gelé, et le corriger après coup serait précisément ce qu'une
pré-inscription interdit. Lire `dev\Daytrading\pine` à la place — le reste de la
commande est inchangé et rend bien `1f5318dc...e32c2c`.
