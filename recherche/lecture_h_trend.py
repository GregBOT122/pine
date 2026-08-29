"""Lecture du test pre-enregistre H_TREND — ecrite le 2026-08-28, lue en 2028.

    py lecture_h_trend.py --verifier     # tourne AUJOURD'HUI, ne lit rien
    py lecture_h_trend.py --executer     # refuse avant le seuil

────────────────────────────────────────────────────────────────────────────────
POURQUOI CE FICHIER EXISTE DEUX ANS AVANT SA LECTURE
────────────────────────────────────────────────────────────────────────────────
H_L2 et H1 ont chacun leur script de lecture, ecrits avant leurs donnees
(`lecture_h_l2.py` 34 jours avant, `lecture_h1.py` avant le seuil). H_TREND
n'en avait aucun, et sa lecture est le 2028-09-01.

Un script de lecture ecrit APRES avoir vu les donnees tranche ses ambiguites en
connaissant le paysage — et une pre-inscription en laisse toujours. Les trancher
dans le noir est la seule facon de ne pas les trancher sur le resultat.

Ce fichier n'est PAS dans l'empreinte gelee (`trend_donchian_h4.pine` +
`null_shift.py`). Il ne peut donc pas l'invalider, et il la VERIFIE avant tout.
Il ne retape aucune ligne de la regle : il execute les definitions du fichier
gele, verbatim.

────────────────────────────────────────────────────────────────────────────────
LES TROIS BLOCAGES, ET LEUR AMENDEMENT DU 2026-08-28
────────────────────────────────────────────────────────────────────────────────
Trouves par ce script le jour de son ecriture, et tranches le meme jour par
`AMENDEMENT_TREND_H4_2026-08-28.md`, avant qu'aucune statistique de la fenetre
n'existe. Les trois resolutions ont en commun de ne toucher NI le `.pine` NI
`null_shift.py` : ce qui est gele est la REGLE, pas les couts, pas la politique
de decalage, pas l'emplacement des donnees.

1. FRICTION -> la table du test est celle de `univers_resolu.json` (42/42
   mesures, regle 11, quatre sessions), au p90 plus commission, et NON le dict
   `FRICTION` de la calibration (17 symboles). `precompute(d, fric)` prend le
   cout en argument : rien a modifier dans le fichier gele.
2. DECALAGE -> MINSHIFT reste 500, parce que MAXB=400 : un decalage de 300
   ferait retomber un signal DANS la fenetre de son propre trade. La prose
   « >= 300 » est amendee, pas contournee. Et la lecture exige desormais 99
   decalages distincts, pour que le plancher reel de p (0,010) soit un
   cinquieme du seuil.
3. DONNEES -> l'archivage doit stocker du H1 dans le cache, parce que c'est ce
   que `load()` reagrege. Les CSV H4 du broker ne sont PAS les memes barres.

Ce qui suit reste ouvert et doit se voir a chaque execution :

────────────────────────────────────────────────────────────────────────────────
CE QUE LA VERIFICATION CONTROLE ENCORE
────────────────────────────────────────────────────────────────────────────────
Ecrit ici parce que c'est le genre de chose qu'on decouvre le jour de la lecture,
quand il est trop tard pour la corriger sans choisir sur le resultat.

1. **L'appareil gele ne connait que 17 des 42 symboles de l'univers.** Le
   dictionnaire `FRICTION` de `null_shift.py` a ete ecrit pour la calibration
   historique ; l'univers a ete fige a 42 symboles le lendemain. Les 25 autres
   n'ont pas de cout d'aller-retour. En 2028 il faudrait soit leur en inventer un
   — un parametre choisi apres coup — soit les retirer, ce que la
   pre-inscription interdit explicitement (« retirer un symbole apres coup »).

2. **L'espace des decalages est vide au seuil de lecture.** Le decalage est
   COMMUN a tous les symboles, donc borne par la serie la plus COURTE. Les
   actions US produisent ~501 barres H4/an ; a n=1200 trades (~20 mois) elles en
   auront ~835 dans la fenetre. Avec `MINSHIFT=500` du fichier gele, l'intervalle
   [500, 835-500] est VIDE : aucune permutation n'est tirable, le null n'existe
   pas. La pre-inscription ecrit « decalage commun >= 300 » ; 500 satisfait cette
   borne, donc c'est 500 qui gouverne — et 500 ne marche pas.

3. **La source de donnees du fichier gele ne contiendra pas la fenetre.**
   `load()` lit `{CACHE}/{symbole}_H1_*.parquet` et reechantillonne en H4.
   L'archivage trimestriel, lui, ecrit `donnees-h4/{SYMBOLE}_H4.csv`. Ce sont
   deux endroits differents : l'assurance ne remplit pas le magasin que
   l'appareil vient ouvrir.

Aucun de ces trois points n'est tranche ici. Les trancher serait modifier le
test ; ce script les MESURE et REFUSE de lire tant qu'ils tiennent.

────────────────────────────────────────────────────────────────────────────────
LES AMBIGUITES DE LA PRE-INSCRIPTION, TRANCHEES DANS LE NOIR
────────────────────────────────────────────────────────────────────────────────
- **`MINSHIFT` : 300 (document) ou 500 (fichier gele) ?** Le fichier gele
  gouverne, parce que la pre-inscription definit la configuration par l'empreinte
  de DEUX FICHIERS, pas par sa propre prose ; et 500 satisfait « >= 300 ».
- **Plancher de p.** Ce n'est pas 1/(B+1). Avec un decalage commun entier, le
  nombre de nulls DISTINCTS possibles vaut `min_n - 2*MINSHIFT + 1`. Si B le
  depasse, on retire des doublons et le plancher reel est
  `1/(decalages_distincts + 1)`. C'est ce plancher-la qui est rapporte.
- **« n >= 1200 trades longs clotures ».** Clotures = sortie effective dans la
  fenetre. Une position encore ouverte au moment de la lecture ne compte pas et
  n'est pas fermee de force au dernier prix : ce serait fabriquer un resultat.
- **Bornes de la fenetre.** Barres STRICTEMENT posterieures au 2026-08-27
  00:00 UTC. Une barre a cheval n'est pas incluse.
- **Puissance.** Calculee des deux facons (forme fermee et simulation) et les
  deux sont imprimees a cote de la table de la pre-inscription. Un ecart doit se
  voir, pas se choisir.

────────────────────────────────────────────────────────────────────────────────
CE QUE CE SCRIPT NE FAIT PAS
────────────────────────────────────────────────────────────────────────────────
`--verifier` ne calcule AUCUNE statistique de la relation testee : ni expR
observe, ni p, ni edge net. Il ne lit que des tailles, des dates et des
couvertures. Il peut donc tourner autant de fois qu'on veut, aujourd'hui compris.
`--executer` ne tourne qu'une fois, et seulement si tous les verrous cedent.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parent.parent          # .../pine
GELE_PINE = RACINE / "trend_donchian_h4.pine"
GELE_NULL = RACINE / "recherche" / "null_shift.py"
UNIVERS = RACINE / "univers" / "univers_resolu.json"
ARCHIVE = Path(r"C:\Users\grego\dev\Daytrading\donnees-h4")

# --- LA SOURCE DE LA LECTURE (amendement 3). `null_shift.CACHE` pointe sur
#     `bot/xaubot/xaubot/data/cache`, qui (a) ne couvre que 18 des 42 symboles
#     et (b) vit DANS un depot git : y deplacer le code deplacerait les
#     donnees, la panne qui a coute deux jours de collecte L2. L'archive H1 vit
#     donc hors depot, a cote de `donnees-h4` et `donnees-l2`.
#
#     On ne modifie PAS le fichier gele : `load()` lit `CACHE` dans son propre
#     espace de noms, et cet espace est celui qu'on a cree en l'executant. Lui
#     assigner une autre valeur AVANT d'appeler `load` suffit, et l'empreinte
#     reste intacte. L'emplacement des donnees n'a jamais fait partie de la regle.
CACHE_H1 = Path(r"C:\Users\grego\dev\Daytrading\donnees-h1")

# --- Constantes recopiees de PREINSCRIPTION_TREND_H4_2026-08-26.md ------------
# Ce ne sont pas des reglages. Les changer changerait le test.
EMPREINTE = "1f5318dc5bbaad7c93315dde947fb17a4fd58709134786e475b7cd72d4e32c2c"
SHA_UNIVERS = "b09836abe7c035df4467f53c79297a54ceafee7969e1691c7dfb6b729b8ba962"
DEBUT_FENETRE = datetime(2026, 8, 27, 0, 0, 0, tzinfo=timezone.utc)
CIBLE_N = 1200               # trades longs clotures
ALPHA = 0.05                 # unilateral
EDGE_NET_MIN = 0.08          # R ; un p significatif en dessous = reel mais nul
EFFET_A_DETECTER = 0.16      # R ; l'edge net attendu, cf. §Audit de puissance
SD_PAR_TRADE = 2.605         # R ; mesure a la pre-inscription
PUISSANCE_MIN = 0.80
CONTROLE_CALENDAIRE = datetime(2028, 9, 1, tzinfo=timezone.utc)
# Table de la pre-inscription, pour confronter le calcul a ce qui fut annonce.
PUISSANCE_ANNONCEE = {600: 0.71, 1000: 0.84, 1200: 0.88}

# --- AMENDEMENT_TREND_H4_2026-08-28 ------------------------------------------
# Decalages distincts exiges en plus de n>=1200. Le plancher REEL de p vaut
# 1/(distincts+1), jamais 1/(B+1) : B tire avec remise dans un ensemble fini.
# 99 -> plancher 0,010, un cinquieme du seuil de 0,05 : c'est le seuil qui
# decide, pas la resolution de l'instrument.
DECALAGES_MIN = 99
PLANCHER_P_VISE = 0.01
# Le p90 et non la mediane : une confirmation doit survivre aux mauvais jours.
QUANTILE_SPREAD = "p90"

# --- `c` : TROIS VALEURS, ET IL FAUT LES TROIS -------------------------------
# 1,72 est la valeur qu'emploie la table de la pre-inscription.
# 2,125 est celle que le script gele MESURE lui-meme : rejeu du 2026-08-28,
#       ecart-type du null 0,0417 a n observe 1 968, donc
#       c = 0,0417 x sqrt(1,32 x 1968) = 2,125. Le rejeu reproduit par ailleurs
#       tout le reste a la virgule pres (null +0,2258, edge net +0,1604,
#       p = 0,0005), donc ce n'est pas un rejeu qui aurait derive.
# 2,42 est le bloc crypto homogene, la degradation que la pre-inscription
#       redoute explicitement pour le nouvel univers.
C_ANNONCE, C_MESURE, C_CRYPTO = 1.72, 2.125, 2.42

# --- `c` RECALCULE SUR L'UNIVERS REEL, le 2026-08-29 -------------------------
# `calibrer_c_42.py`, rapport `CALIBRATION_C_42_2026-08-29.md`. Fenetre bornee
# au 2026-08-26 : aucune barre du test n'y entre. 42 symboles, friction de
# l'amendement 1, graine et MINSHIFT du fichier gele.
#
#     fenetre 2024-2026   c = 2,396      (premiere mesure, archive d'alors)
#     fenetre 2022-2026   c = 2,674      <- RETENU, la plus longue VALIDE
#                         FX 1,890  indices 1,797  matieres 2,041
#                         crypto 3,631            actions 2,326
#
# POURQUOI PAS PLUS LONG. L'archive a ete approfondie a 2012 le 2026-08-29, mais
# **MT5 sert de l'historique ancien ECLAIRCI** : EURUSD rend 260 barres H1/an en
# 2012 contre 6 229 en 2024 — du journalier etiquete H1. Reagrege en H4, ca
# produit des trades qui ne sont pas ceux de la strategie, sans lever d'erreur.
# La fenetre 2012-2026 rend 2,606 ; elle est simplement invalide, pas
# conservatrice. Les 42 ne sont tous denses qu'a partir de **2022**.
# `calibrer_c_42.py` REFUSE desormais (code 7) toute fenetre contenant des
# annees creuses et nomme la bonne borne.
#
# Le bloc crypto est a 3,631 la ou la pre-inscription redoutait 2,42 : sa
# crainte etait juste dans le principe et sous-estimee de 50 %.
C_UNIVERS = 2.674

# Rapport n_null/n_obs MESURE sur les 42 : 1,259, la ou la formule fige 1,32.
# Le 1,32 vient des 17 symboles d'origine (ou il valait 1,318). L'ecart est
# absorbe par la convention `c = sd x racine(1,32 n_obs)`, qui rend la formule
# exacte au point de calibration quel que soit le rapport reel.
RATIO_MESURE_42 = 1.259

# Codes de sortie, distincts pour qu'un refus ne passe pas pour un resultat.
OK, BLOQUE, EMPREINTE_CASSEE, TROP_TOT, SOUS_PUISSANT = 0, 3, 4, 5, 6


def empreinte_gelee() -> str:
    a = hashlib.sha256(GELE_PINE.read_bytes()).hexdigest()
    b = hashlib.sha256(GELE_NULL.read_bytes()).hexdigest()
    return hashlib.sha256((a + b).encode()).hexdigest()


def charger_appareil_gele() -> dict:
    """Executer les DEFINITIONS du fichier gele, sans declencher son backtest.

    `null_shift.py` calcule tout au niveau module : l'importer lancerait 2 000
    permutations sur l'historique. On execute donc son prefixe — jusqu'a la
    ligne `DATA={}` ou commence l'execution — plus la seule fonction `stat`,
    definie plus bas.

    On ne RETAPE rien. Une regle recopiee a la main est une regle qui diverge,
    et c'est precisement ce que l'empreinte cherche a empecher.
    """
    src = GELE_NULL.read_text(encoding="utf-8")
    i = src.index("DATA={}")
    prefixe = src[:i]

    j = src.index("def stat(")
    k = src.index("obs_e,obs_pf,obs_n=", j)
    bloc_stat = src[j:k]

    ns: dict = {}
    exec(compile(prefixe + bloc_stat, str(GELE_NULL), "exec"), ns)
    # Amendement 3 : la source des barres, et rien d'autre, est redirigee.
    ns["CACHE"] = str(CACHE_H1)
    return ns


def lire_h4(symbole: str):
    """L'archive trimestrielle : ts epoch, OHLC. Rien d'autre n'est lu."""
    f = ARCHIVE / ("%s_H4.csv" % symbole)
    if not f.exists():
        return None
    ts, o, h, l, c = [], [], [], [], []
    with f.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                ts.append(int(r["ts"])); o.append(float(r["open"]))
                h.append(float(r["high"])); l.append(float(r["low"]))
                c.append(float(r["close"]))
            except (KeyError, ValueError, TypeError):
                continue
    if not ts:
        return None
    a = np.argsort(ts)
    return (np.array(ts)[a], np.array(o)[a], np.array(h)[a],
            np.array(l)[a], np.array(c)[a])


def puissance(n: int, c_null: float) -> float:
    """Formule de la pre-inscription, §Garde-fou de puissance :

        puissance = Phi( (0,16 - 1,645 c / sqrt(1,32 n)) / (sd_trade / sqrt(n)) )

    ATTENTION : LE DOCUMENT DONNE L'ECART-TYPE DU NULL DEUX FOIS.
        §4          « Ecart-type du null : 1,72/sqrt(n) »   <- sans le 1,32
        §Garde-fou  la formule ci-dessus                    <- avec
    La table publiee est calculee avec la SECONDE. Ma premiere version de ce
    fichier a employe la premiere — celle qui est imprimee juste au-dessus de la
    table — et en a conclu que le document etait haut de 0,04. C'etait faux, et
    l'accord entre ma forme fermee et ma simulation ne prouvait rien : elles
    partageaient la meme hypothese. Le §Garde-fou fait foi, son facteur etant
    mesure ; le §4 doit se lire `1,72/sqrt(1,32 n)`.

    D'ou vient le 1,32 : un decalage circulaire produit PLUS de trades que la
    serie observee, parce que les signaux deplaces se heurtent moins au blocage
    « pas de nouvelle entree tant qu'on est en position ». Rejeu de la
    calibration gelee le 2026-08-28 : n observe 1 968, n du null 2 593, soit un
    rapport de **1,318**. La distribution nulle est donc la moyenne de 32 % de
    trades en plus, et son ecart-type retrecit d'autant.
    """
    from math import erf, sqrt
    z95 = 1.6448536269514722
    seuil = z95 * c_null / sqrt(1.32 * n)
    z = (EFFET_A_DETECTER - seuil) / (SD_PAR_TRADE / sqrt(n))
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def n_pour_puissance(c_null: float, cible: float = PUISSANCE_MIN) -> int:
    """Le n qui ramene la puissance au-dessus de `cible`, pour un `c` donne.
    C'est le chiffre utile quand le garde-fou refuse : il dit de combien
    prolonger, au lieu de dire seulement « pas assez »."""
    lo, hi = 100.0, 100000.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if puissance(mid, c_null) < cible:
            lo = mid
        else:
            hi = mid
    return int(hi) + 1


def verifier(a) -> int:
    maintenant = datetime.now(timezone.utc)
    L = []
    blocages = []

    L += ["# Verification de l'appareil H_TREND — %s UTC"
          % maintenant.strftime("%Y-%m-%d %H:%M"), "",
          "Ce mode ne calcule AUCUNE statistique de la relation testee.", ""]

    # --- VERROU 0 : l'empreinte. La pre-inscription est explicite : si elle ne
    #     se recalcule pas a l'identique, le test est nul. C'est le premier
    #     controle, pas le dernier.
    emp = empreinte_gelee()
    intacte = emp == EMPREINTE
    L += ["## Empreinte de la configuration figee",
          "  calculee : %s" % emp,
          "  attendue : %s" % EMPREINTE,
          "  -> %s" % ("INTACTE" if intacte else
                       "CASSEE — le test est nul par sa propre regle"), ""]
    if not intacte:
        print("\n".join(L))
        return EMPREINTE_CASSEE

    # --- L'univers, et son empreinte propre.
    uni = json.loads(UNIVERS.read_text(encoding="utf-8"))
    resolus = uni["resolus"]
    sha_u = uni.get("sha256_univers", "")
    L += ["## Univers",
          "  symboles resolus : %d" % len(resolus),
          "  sha256 : %s" % ("conforme" if sha_u == SHA_UNIVERS
                             else "DIFFERENT (%s)" % sha_u[:16]), ""]
    if sha_u != SHA_UNIVERS:
        blocages.append("l'empreinte de l'univers a change depuis le 2026-08-27")

    ns = charger_appareil_gele()

    # --- AMENDEMENT 1 : la friction vient de l'univers, pas de la calibration.
    #     Le dict FRICTION du fichier gele couvre 17 symboles sur 42 ; il a ete
    #     ecrit pour la calibration historique, la veille du gel de l'univers.
    #     `precompute(d, fric)` prend le cout en ARGUMENT, donc rien n'a besoin
    #     d'etre modifie dans le fichier gele pour lui en passer un autre.
    spreads = uni.get("spreads", {})
    frais_crypto = float(uni.get("frais_crypto_rt_pct", 0.0))
    table, sans = {}, []
    for sym in sorted(resolus):
        m = spreads.get(sym)
        if not m or QUANTILE_SPREAD not in m:
            sans.append(sym); continue
        # crypto = paires ...USDT, les seules a payer une commission taker.
        com = frais_crypto if sym.endswith("USDT") else 0.0
        table[sym] = float(m[QUANTILE_SPREAD]) + com

    L += ["## Friction A/R — table de l'univers (amendement 1)",
          "  regle : %s du spread mesure + commission (%.2f %% crypto, 0 sinon)"
          % (QUANTILE_SPREAD, frais_crypto),
          "  couverts : %d / %d symboles" % (len(table), len(resolus))]
    if table:
        pire = sorted(table.items(), key=lambda kv: -kv[1])[:3]
        moins = sorted(table.items(), key=lambda kv: kv[1])[:3]
        L += ["  plus cher : " + ", ".join("%s %.4f%%" % kv for kv in pire),
              "  moins cher: " + ", ".join("%s %.4f%%" % kv for kv in moins)]
    L += ["  Pour memoire, le dict FRICTION du fichier gele n'en couvre que "
          "%d et n'est PAS utilise." % len(ns["FRICTION"])]
    if sans:
        L += ["  SANS SPREAD MESURE : %d -> %s" % (len(sans), ", ".join(sans))]
        blocages.append(
            "%d symboles n'ont pas de spread mesure dans univers_resolu.json. "
            "La table de friction de l'amendement 1 ne peut pas etre construite "
            "pour eux." % len(sans))
    L += ["  La valeur definitive sera RECALCULEE a la lecture sur les spreads",
          "  de la fenetre ; celle-ci est l'instantane de reference.", ""]

    # --- AMENDEMENT 3 : l'archivage doit stocker du H1 dans le cache, parce
    #     que c'est ce que `load()` reagrege. Les CSV H4 du broker ne sont pas
    #     les memes barres : choisir entre les deux en 2028 serait choisir une
    #     construction de barres en connaissant le paysage.
    cache = Path(ns["CACHE"])
    h4_csv = [s for s in resolus if (ARCHIVE / ("%s_H4.csv" % s)).exists()]
    # Presence d'un H1 quelconque : sans lui, `load()` rend None et la boucle
    # de calibration ecarte le symbole par `continue`, SANS ERREUR.
    h1_frais = [s for s in resolus
                if list(cache.glob("%s_H1_*.parquet" % s))]

    L += ["## Donnees de la fenetre (amendement 3)",
          "  source de la lecture : %s" % cache,
          "     -> parquet H1, reagrege en H4 par `load()` du fichier gele",
          "  H1 couvrant la fenetre : %d / %d symboles"
          % (len(h1_frais), len(resolus)),
          "  temoin secondaire : %d / %d CSV H4 (PAS la source de la lecture)"
          % (len(h4_csv), len(resolus))]
    if len(h1_frais) < len(resolus):
        absents = sorted(set(resolus) - set(h1_frais))
        L += ["  SANS AUCUN H1 : %d -> %s" % (len(absents), ", ".join(absents)),
              "  -> `load()` rend None pour eux et la boucle fait `continue` :",
              "     ils sortiraient de l'univers SANS QU'UNE ERREUR SOIT LEVEE."]
        blocages.append(
            "%d des %d symboles n'ont aucun parquet H1 dans l'archive. "
            "`load()` les ecarterait EN SILENCE — « retirer un symbole apres "
            "coup » commis par omission."
            % (len(absents), len(resolus)))
    L += [""]

    # --- Ce que la fenetre contient AUJOURD'HUI, et sa projection.
    #     On ne compte que des barres. Aucun signal n'est evalue ici.
    debut_ts = int(DEBUT_FENETRE.timestamp())
    dans_fenetre, par_an = {}, {}
    for s in sorted(resolus):
        d = lire_h4(s)
        if d is None:
            continue
        ts = d[0]
        dans_fenetre[s] = int((ts > debut_ts).sum())
        span = (ts.max() - ts.min()) / 86400 / 365.25
        if span > 0:
            par_an[s] = len(ts) / span

    if par_an:
        lent = min(par_an, key=par_an.get)
        # A n=1200 trades, la pre-inscription projette ~20 mois de fenetre.
        mois = 20.0
        min_n_projete = int(par_an[lent] * mois / 12.0)
        minshift = int(ns["MINSHIFT"])
        maxb = int(ns["MAXB"])
        # numpy integers(low, high) exclut high -> distincts = min_n - 2*MINSHIFT
        distincts = min_n_projete - 2 * minshift
        L += ["## Espace des decalages (amendement 2)",
              "  MINSHIFT = %d, MAXB = %d  ->  %s"
              % (minshift, maxb,
                 "OK, un decalage ne peut pas retomber dans le trade qu'il "
                 "deplace" if minshift > maxb else
                 "CONTAMINE : le decalage est plus court qu'un trade"),
              "  (c'est pourquoi le « >= 300 » du document est amende : 300 < "
              "MAXB.)",
              "  serie la plus courte : %s, %.0f barres H4/an" % (lent, par_an[lent]),
              "  fenetre projetee a n=%d trades : ~%.0f mois -> %d barres"
              % (CIBLE_N, mois, min_n_projete),
              "  decalages distincts tirables : %d  (exiges : %d)"
              % (max(0, distincts), DECALAGES_MIN)]
        if minshift <= maxb:
            blocages.append(
                "MINSHIFT=%d n'excede pas MAXB=%d : un signal decale retombe "
                "dans la fenetre de son propre trade et le null garde une part "
                "de l'alignement qu'il doit detruire." % (minshift, maxb))
        if distincts > 0:
            plancher = 1.0 / (min(int(ns["B"]), distincts) + 1)
            L += ["  plancher REEL de p : %.4f  (et non 1/(B+1) = %.4f)"
                  % (plancher, 1.0 / (int(ns["B"]) + 1))]
        if distincts < DECALAGES_MIN:
            manque = DECALAGES_MIN + 2 * minshift - min_n_projete
            L += ["  -> PAS ENCORE LISIBLE a n=%d : il manque %d barres sur %s."
                  % (CIBLE_N, manque, lent),
                  "     ~%.1f mois de plus que le seuil en trades."
                  % (manque / par_an[lent] * 12)]
            L += ["     Ce n'est pas un blocage : c'est la condition de lecture",
                  "     ajoutee par l'amendement 2, mecanique et independante du",
                  "     resultat. Elle se verifiera d'elle-meme le moment venu."]
        L += [""]

    # --- Ou en est l'accumulation, en BARRES. Pas en trades : compter les
    #     trades demanderait d'evaluer le signal, donc d'ouvrir la relation.
    total = sum(dans_fenetre.values())
    L += ["## Accumulation dans la fenetre (barres, pas trades)",
          "  depuis %s : %d barres H4 sur %d symboles"
          % (DEBUT_FENETRE.strftime("%Y-%m-%d"), total, len(dans_fenetre)),
          "  Le nombre de trades ne peut pas etre compte sans evaluer le",
          "  signal ; il ne l'est donc pas ici.", ""]

    # --- Puissance. La formule est celle du document, facteur 1,32 compris.
    #     Ce qui est confronte n'est plus « ma methode contre la sienne » —
    #     elles coincident — mais les trois valeurs possibles de `c`.
    L += ["## Puissance projetee (formule de la pre-inscription, 1,32 n compris)",
          "  %-7s %-13s %-15s %-16s" % ("n", "c=1,72 (doc)", "c=2,125 (17 sym.)",
                                        "c=2,674 (42 sym.)")]
    for n in (1000, 1200, 1500, 1800):
        L += ["  %-7d %-13.3f %-15.3f %-16.3f"
              % (n, puissance(n, C_ANNONCE), puissance(n, C_MESURE),
                 puissance(n, C_UNIVERS))]
    L += ["",
          "  n pour atteindre le plancher de %.2f :" % PUISSANCE_MIN,
          "    c=1,72 -> %d      c=2,125 -> %d      c=2,674 -> %d"
          % (n_pour_puissance(C_ANNONCE), n_pour_puissance(C_MESURE),
             n_pour_puissance(C_UNIVERS)),
          ""]
    L += ["  LE SEUIL PRE-ENREGISTRE n=1200 NE SUFFIT PAS. Recalcule sur les 42",
          "  symboles reels sur 2022-2026, `c` vaut 2,674 et non 1,72 : la",
          "  puissance a n=1200 tombe a %.3f, SOUS le plancher de %.2f. Il en"
          % (puissance(1200, C_UNIVERS), PUISSANCE_MIN),
          "  faut %d." % n_pour_puissance(C_UNIVERS),
          "",
          "  MAIS L'AMENDEMENT 2 A DEJA ABSORBE CE MANQUE, sans l'avoir cherche.",
          "  Il exige %d decalages distincts, donc ~%d barres sur la serie la"
          % (DECALAGES_MIN, 2 * 500 + DECALAGES_MIN),
          "  plus courte : la lecture ne peut pas avoir lieu avant ~2028-11, ou",
          "  la cadence projetee (714 trades/an) donne n ~ 1570 — soit une",
          "  puissance de %.3f. Le garde-fou ne mordra donc pas."
          % puissance(1570, C_UNIVERS),
          "",
          "  Le bloc crypto seul est mesure a 3,631, la ou la pre-inscription",
          "  redoutait 2,42 : sa crainte etait juste, et sous-estimee de 50 %.",
          "",
          "  Le 2,674 reste une PROJECTION : mesure sur 2022-2026, pas sur la",
          "  fenetre du test. La pre-inscription impose de recalculer `c` sur",
          "  les donnees du test et de ne pas lire sous 0,80 — c'est ce",
          "  garde-fou qui tranchera, pas ce chiffre.",
          ""]

    # --- Verdict.
    L += ["## VERDICT"]
    if blocages:
        L += ["  %d BLOCAGE(S) — la lecture echouerait en l'etat :" % len(blocages)]
        for i, b in enumerate(blocages, 1):
            L += ["    %d. %s" % (i, b)]
        L += ["",
              "  Un blocage n'est PAS « le seuil n'est pas atteint ». C'est",
              "  l'appareil qui ne peut pas rendre de reponse, quel que soit le",
              "  nombre de trades accumules."]
    else:
        L += ["  Aucun blocage d'appareil.",
              "  La lecture attend ses deux conditions : n >= %d ET %d decalages"
              % (CIBLE_N, DECALAGES_MIN),
              "  distincts. Les deux sont mecaniques et se verifient sans jamais",
              "  regarder la relation testee."]
    L += [""]

    print("\n".join(L))
    if a.sortie:
        Path(a.sortie).write_text("\n".join(L), encoding="utf-8")
    return BLOQUE if blocages else OK


def executer(a) -> int:
    """Refuse tant qu'un verrou tient. Aucune statistique n'est calculee avant
    que TOUS aient cede — l'ordre est le garde-fou."""
    maintenant = datetime.now(timezone.utc)

    if empreinte_gelee() != EMPREINTE:
        print("REFUS : l'empreinte de la configuration figee ne se recalcule "
              "pas. Le test est nul par sa propre regle.")
        return EMPREINTE_CASSEE

    if maintenant < CONTROLE_CALENDAIRE:
        print("REFUS : point de controle calendaire au %s. Nous sommes le %s."
              % (CONTROLE_CALENDAIRE.strftime("%Y-%m-%d"),
                 maintenant.strftime("%Y-%m-%d")))
        print("  Lire avant le seuil transforme un seuil de 5 % en davantage.")
        return TROP_TOT

    code = verifier(a)
    if code != OK:
        print("\nREFUS : la verification rend %d. La lecture n'a pas lieu." % code)
        return code

    print("Les verrous ont cede. La suite reste a ecrire : elle demande les "
          "donnees de la fenetre, qui n'existent pas encore.")
    return OK


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--verifier", action="store_true",
                   help="controler l'appareil sans rien lire (defaut)")
    g.add_argument("--executer", action="store_true",
                   help="lire le test — refuse avant le 2028-09-01")
    p.add_argument("--sortie", default=None)
    a = p.parse_args()
    return executer(a) if a.executer else verifier(a)


if __name__ == "__main__":
    raise SystemExit(main())
