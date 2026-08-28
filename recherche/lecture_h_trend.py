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
CE QUE LA VERIFICATION A TROUVE LE 2026-08-28, ET QUI BLOQUE LA LECTURE
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


def puissance_forme_fermee(n: int, c_null: float) -> float:
    """P(observe > q95 du null) sous un vrai effet de EFFET_A_DETECTER."""
    from math import erf, sqrt
    z95 = 1.6448536269514722
    seuil = z95 * c_null / sqrt(n)
    z = (EFFET_A_DETECTER - seuil) / (SD_PAR_TRADE / sqrt(n))
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def puissance_simulee(n: int, c_null: float, tirages: int = 20000,
                      graine: int = 20260828) -> float:
    """La meme chose sans approximation normale. Les deux sont imprimees."""
    from math import sqrt
    rng = np.random.default_rng(graine)
    seuil = 1.6448536269514722 * c_null / sqrt(n)
    obs = rng.normal(EFFET_A_DETECTER, SD_PAR_TRADE / sqrt(n), tirages)
    return float((obs > seuil).mean())


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

    # --- BLOCAGE 1 : la friction ne couvre pas l'univers.
    fric = ns["FRICTION"]
    sans = sorted(set(resolus) - set(fric))
    L += ["## Frictions connues de l'appareil gele",
          "  couverts : %d / %d symboles" % (len(resolus) - len(sans), len(resolus))]
    if sans:
        L += ["  SANS COUT D'ALLER-RETOUR : %d" % len(sans),
              "    " + ", ".join(sans)]
        blocages.append(
            "%d des %d symboles de l'univers n'ont pas de friction dans "
            "l'appareil gele. Leur en donner une en 2028 serait un parametre "
            "choisi apres coup ; les retirer est explicitement interdit."
            % (len(sans), len(resolus)))
    L += [""]

    # --- BLOCAGE 2 : la source de donnees.
    presents = [s for s in resolus if (ARCHIVE / ("%s_H4.csv" % s)).exists()]
    L += ["## Donnees de la fenetre",
          "  source de l'appareil gele : %s" % ns["CACHE"],
          "     -> parquet H1 reechantillonne en H4",
          "  source de l'archivage     : %s" % ARCHIVE,
          "     -> CSV H4 deja agreges, %d / %d symboles presents"
          % (len(presents), len(resolus))]
    L += ["  Les deux ne sont pas le meme magasin. `load()` du fichier gele ne",
          "  trouvera pas la fenetre 2026-2028 dans le cache parquet si rien ne",
          "  l'y ecrit — l'archivage trimestriel ecrit ailleurs.", ""]
    blocages.append(
        "le `load()` gele lit le cache parquet H1 ; l'archivage trimestriel "
        "ecrit des CSV H4 dans un autre dossier. La source de la lecture n'est "
        "pas celle que l'assurance remplit.")

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
        distincts = min_n_projete - 2 * minshift + 1
        L += ["## Espace des decalages au seuil de lecture",
              "  serie la plus courte : %s, %.0f barres H4/an" % (lent, par_an[lent]),
              "  fenetre projetee a n=%d trades : ~%.0f mois -> %d barres"
              % (CIBLE_N, mois, min_n_projete),
              "  MINSHIFT du fichier gele : %d" % minshift,
              "  decalages distincts tirables : %d" % max(0, distincts)]
        if distincts <= 0:
            L += ["  -> VIDE. Aucune permutation n'est tirable : le null "
                  "n'existe pas."]
            blocages.append(
                "l'intervalle de decalage [%d, %d] est vide sur la serie la "
                "plus courte (%s). Le decalage etant COMMUN, il est borne par "
                "elle. Avec MINSHIFT=%d le null ne peut pas etre calcule."
                % (minshift, min_n_projete - minshift, lent, minshift))
        else:
            plancher = 1.0 / (min(int(ns["B"]), distincts) + 1)
            L += ["  plancher REEL de p : %.4f  (et non 1/(B+1) = %.4f)"
                  % (plancher, 1.0 / (int(ns["B"]) + 1))]
            if plancher >= ALPHA:
                blocages.append(
                    "le plancher reel de p (%.4f) atteint le seuil %.2f : le "
                    "test ne peut pas rejeter." % (plancher, ALPHA))
        L += [""]

    # --- Ou en est l'accumulation, en BARRES. Pas en trades : compter les
    #     trades demanderait d'evaluer le signal, donc d'ouvrir la relation.
    total = sum(dans_fenetre.values())
    L += ["## Accumulation dans la fenetre (barres, pas trades)",
          "  depuis %s : %d barres H4 sur %d symboles"
          % (DEBUT_FENETRE.strftime("%Y-%m-%d"), total, len(dans_fenetre)),
          "  Le nombre de trades ne peut pas etre compte sans evaluer le",
          "  signal ; il ne l'est donc pas ici.", ""]

    # --- Puissance, aux deux facons, confrontee a ce qui fut annonce.
    c_null = 1.72     # ecart-type du null x sqrt(n), pre-inscription
    L += ["## Puissance projetee (c = %.2f de la pre-inscription)" % c_null,
          "  %-8s %-14s %-14s %s" % ("n", "forme fermee", "simulee", "annoncee")]
    for n in (600, 1000, 1200, 1500):
        L += ["  %-8d %-14.3f %-14.3f %s"
              % (n, puissance_forme_fermee(n, c_null),
                 puissance_simulee(n, c_null),
                 "%.2f" % PUISSANCE_ANNONCEE[n] if n in PUISSANCE_ANNONCEE else "-")]
    L += ["  `c` sera RECALCULE sur les donnees du test avant toute lecture ;",
          "  ces valeurs sont une projection, pas la puissance atteinte."]

    # --- L'ECART AVEC LA TABLE ANNONCEE DOIT SE VOIR, PAS S'EYEBALLER.
    #     Les deux methodes s'accordent entre elles a 0,005 pres et sont TOUTES
    #     DEUX sous la table de la pre-inscription, d'environ 0,04. L'ecart est
    #     donc dans le chiffre annonce, pas dans la methode — et il compte :
    #     a n=1000 le 0,84 annonce devient 0,80, c'est-a-dire EXACTEMENT le
    #     plancher sous lequel la pre-inscription interdit de lire.
    ecarts = [(n, PUISSANCE_ANNONCEE[n] - puissance_forme_fermee(n, c_null))
              for n in sorted(PUISSANCE_ANNONCEE)]
    pire = max(ecarts, key=lambda x: abs(x[1]))
    if abs(pire[1]) > 0.02:
        L += ["",
              "  ATTENTION : les deux methodes s'accordent entre elles mais",
              "  tombent sous la table de la pre-inscription (ecart max %+.3f a"
              % pire[1],
              "  n=%d). L'ecart est donc dans le chiffre annonce. Consequence :"
              % pire[0],
              "  la marge au-dessus du plancher de %.2f est plus mince que le"
              % PUISSANCE_MIN,
              "  document ne le laisse croire — a n=1000 elle est nulle."]
    L += [""]

    # --- Verdict.
    L += ["## VERDICT"]
    if blocages:
        L += ["  %d BLOCAGE(S) — la lecture de 2028 echouerait en l'etat :" % len(blocages)]
        for i, b in enumerate(blocages, 1):
            L += ["    %d. %s" % (i, b)]
        L += ["",
              "  Aucun n'est tranche ici : les trancher serait modifier le test.",
              "  Ils demandent un AMENDEMENT ecrit et horodate, comme celui du",
              "  2026-08-27 pour H_L2 — avant de voir la moindre donnee."]
    else:
        L += ["  Aucun blocage. L'appareil pourra etre lu quand n atteindra %d."
              % CIBLE_N]
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
