"""Tests du correctif du 2026-09-06 — cadence sur annees denses, et le verrou
de l'amendement 2 compte sur la FENETRE.

    py -m pytest recherche/test_cadence_et_decalages.py -q

POURQUOI CES TESTS EXISTENT. Le defaut corrige le 2026-09-06 n'a produit
AUCUNE erreur pendant neuf jours : `verifier` rendait code 0, un verdict
« aucun blocage », et une date de lecture fausse de quatorze mois. Un
instrument qui se trompe en silence se distingue d'un instrument juste par
absolument rien — c'est la panne habituelle de ce projet, et la seule parade
est de faire tourner l'instrument sur des cas dont on connait la reponse.

Le verrou de `executer` est dans le meme cas : il est aujourd'hui INATTEIGNABLE
en pratique, parce que le verrou calendaire (2028-09-01) tire avant lui. Il ne
s'executera pour de vrai qu'en 2028. Le tester maintenant est la seule facon de
savoir qu'il fonctionnera ce jour-la.
"""
from __future__ import annotations

import calendar
from datetime import datetime, timezone

import numpy as np
import pytest

import lecture_h_trend as L


def _ts(annee_a_compte: dict[int, int], depart=None) -> np.ndarray:
    """Fabrique des horodatages H4 : `n` barres etalees dans chaque annee.

    `depart=(an, mois, jour)` fait demarrer la serie en cours d'annee — c'est
    ce qui distingue une annee PARTIELLE (la cotation s'ouvre en mars) d'une
    annee ECLAIRCIE (la donnee manque sur toute l'annee). Ma premiere version
    de cette fabrique etalait les barres sur l'annee entiere dans les deux cas
    et ne pouvait donc pas produire de vraie annee partielle.
    """
    out = []
    for an, n in sorted(annee_a_compte.items()):
        d0 = calendar.timegm((an, 1, 1, 0, 0, 0))
        if depart and depart[0] == an:
            d0 = calendar.timegm(tuple(depart) + (0, 0, 0))
        d1 = calendar.timegm((an + 1, 1, 1, 0, 0, 0))
        out += list(np.linspace(d0, d1 - 1, n).astype(np.int64))
    return np.array(sorted(out))


# --------------------------------------------------------------------------
# 1. Le defaut lui-meme : NVDA, reconstitue a l'identique
# --------------------------------------------------------------------------

def test_les_annees_eclaircies_ne_ralentissent_plus_la_serie():
    """LE CAS REEL. NVDA porte une archive H4 depuis 2012 dont les annees
    anciennes sont ECLAIRCIES — une barre par jour ouvre — alors que ses
    annees recentes sont pleines. Le quotient `len/span` rendait 328 barres/an
    pour une serie qui en fait ~500, et NVDA sortait « serie la plus courte »
    de l'univers alors qu'elle est dans la moyenne.
    """
    creuses = {an: 255 for an in range(2012, 2022)}
    pleines = {2022: 462, 2023: 499, 2024: 504, 2025: 496}
    ts = _ts({**creuses, **pleines})

    naif = len(ts) / ((ts.max() - ts.min()) / 86400 / 365.25)
    assert 300 < naif < 360, "le calcul naif doit bien reproduire le defaut"

    cadence, ecartees = L.cadence_denses(ts)
    assert cadence == pytest.approx(497.5, abs=1.0)
    assert all(k == "eclaircie" for an, k in ecartees.items() if an < 2021)


def test_une_annee_partielle_en_bord_de_serie_n_est_pas_une_eclaircie():
    """AMZN 2021 compte 239 barres parce que Fusion l'a cotee le 15 mars. Ce
    n'est pas un defaut de donnees, et le signaler comme tel ferait crier
    l'instrument sur une serie saine. Une alerte qui crie a tort finit par
    etre ignoree.
    """
    ts = _ts({2021: 260, 2022: 501, 2023: 499, 2024: 503, 2025: 496},
             depart=(2021, 3, 15))
    cadence, ecartees = L.cadence_denses(ts)
    assert ecartees == {2021: "partielle"}
    assert cadence == pytest.approx(499.0, abs=1.5)


def test_une_annee_de_bord_ECLAIRCIE_n_est_pas_excusee_par_son_bord():
    """LE CAS QUI A CORRIGE MA REGLE. NVDA 2012 est la premiere annee de sa
    serie ET elle est eclaircie. Une regle fondee sur la POSITION l'aurait
    classee « partielle » et aurait donc minimise le defaut — c'est-a-dire
    qu'elle se serait trompee vers le silence, la direction interdite pour une
    alarme. Le prorata la rattrape : 255 barres sur une annee couverte a 100 %
    en valent 500 attendues.
    """
    ts = _ts({2012: 255, 2024: 504, 2025: 496}, depart=(2012, 1, 2))
    _, ecartees = L.cadence_denses(ts)
    assert ecartees[2012] == "eclaircie"


def test_une_annee_creuse_au_milieu_reste_une_eclaircie():
    """Au milieu d'une serie, la couverture vaut 1 : le prorata n'excuse rien,
    et la donnee manque alors qu'elle devrait etre la."""
    ts = _ts({2021: 500, 2022: 240, 2023: 499, 2024: 503, 2025: 496})
    _, ecartees = L.cadence_denses(ts)
    assert ecartees == {2022: "eclaircie"}


def test_la_mediane_et_non_la_moyenne():
    """Une premiere annee partielle mais DENSE (au-dessus du seuil de 60 %)
    entre dans le calcul. La moyenne s'y laisse tirer vers le bas ; la mediane
    non. C'est le choix retenu, et il est verifie plutot qu'annonce."""
    ts = _ts({2021: 431, 2022: 501, 2023: 499, 2024: 501, 2025: 496})
    cadence, ecartees = L.cadence_denses(ts)
    assert ecartees == {}, "431 est au-dessus de 0,6 x 498 : l'annee est dense"
    assert cadence == pytest.approx(499.0, abs=0.5)
    assert cadence > np.mean([431, 501, 499, 501, 496])


def test_l_annee_courante_incomplete_est_toujours_ecartee():
    """2026 est partielle par construction le 2026-09-06. La compter
    ralentirait toutes les series de l'univers en meme temps."""
    an = datetime.now(timezone.utc).year
    ts = _ts({an - 3: 500, an - 2: 500, an - 1: 500, an: 120})
    _, ecartees = L.cadence_denses(ts)
    assert an not in ecartees, "l'annee courante est exclue, pas signalee"


def test_sans_annee_de_reference_l_instrument_se_tait():
    """Une serie qui ne couvre pas 2024-2025 n'a pas de densite de reference.
    L'instrument doit rendre None et laisser l'appelant refuser — jamais
    deviner un seuil."""
    cadence, _ = L.cadence_denses(_ts({2012: 260, 2013: 259}))
    assert cadence is None
    assert L.cadence_denses(np.array([], dtype=np.int64)) == (None, {})


# --------------------------------------------------------------------------
# 2. Le verrou de l'amendement 2 — compte sur la FENETRE, jamais sur l'archive
# --------------------------------------------------------------------------

def test_min_n_fenetre_ne_compte_que_les_barres_de_la_fenetre(monkeypatch):
    """C'est toute la regle ecrite le 2026-09-06 : ce qui borne l'espace des
    decalages est le nombre de barres POSTERIEURES au 2026-08-27, pas la
    taille de l'archive. Une archive de vingt ans ne rend pas un test lisible.
    """
    debut = int(L.DEBUT_FENETRE.timestamp())
    series = {
        "VIEUX": _ts({2012: 6000, 2013: 6000}),                 # 0 en fenetre
        "RICHE": np.arange(debut + 1, debut + 1 + 3000 * 14400, 14400),
    }
    monkeypatch.setattr(L, "lire_h4",
                        lambda s: (series[s], None, None, None, None))
    mn, lent = L.min_n_fenetre(["VIEUX", "RICHE"])
    assert (mn, lent) == (0, "VIEUX"), "l'archive ancienne ne compte pas"


def test_un_symbole_sans_donnees_bloque_au_lieu_de_disparaitre(monkeypatch):
    """Retirer un symbole muet serait « retirer un symbole apres coup » commis
    par arithmetique — la panne exacte qui aurait ecarte 24 des 42 symboles en
    silence (amendement 3). Il compte donc 0, et 0 fait refuser la lecture."""
    monkeypatch.setattr(L, "lire_h4", lambda s: None)
    mn, lent = L.min_n_fenetre(["AAPL", "META"])
    assert mn == 0 and lent in ("AAPL", "META")


def test_le_seuil_du_verrou_vaut_bien_99_decalages_plus_deux_minshift():
    """Le seuil n'est pas un nombre choisi : il decoule de DECALAGES_MIN et de
    MINSHIFT du fichier gele. S'il cessait d'en decouler, le verrou pourrait
    laisser passer une lecture dont le plancher de p depasse le seuil."""
    minshift = int(L.charger_appareil_gele()["MINSHIFT"])
    assert minshift == 500
    assert L.DECALAGES_MIN + 2 * minshift == 1099
    assert 1.0 / (L.DECALAGES_MIN + 1) <= L.PLANCHER_P_VISE


# --------------------------------------------------------------------------
# 3. Le controle qui aurait tout tranche tout de suite
# --------------------------------------------------------------------------

def test_la_projection_corrigee_reproduit_la_date_publiee_par_l_amendement():
    """LA LECON DE METHODE, ecrite dans le registre le 2026-08-28 : ne jamais
    recalculer une formule publiee sans d'abord REPRODUIRE le chiffre publie.

    `AMENDEMENT_TREND_H4_2026-08-28.md` §2 annonce une lecture vers 2028-11 et
    un n d'environ 1570. Avec la cadence des annees denses (~499 barres/an sur
    la serie la plus courte), la projection les retrouve. Avec le calcul naif
    (328/an) elle rendait 2030-01 : c'est ce desaccord qui a designe le defaut.
    """
    exigees = L.DECALAGES_MIN + 2 * 500
    mois = exigees / 499.0 * 12.0
    assert 25.5 < mois < 27.5, "1099 barres a ~499/an -> ~26,4 mois"
    n = int(L.CADENCE_TRADES_AN * mois / 12.0)
    assert 1500 < n < 1650, "l'amendement publie n ~ 1570"
    assert L.puissance(n, L.C_UNIVERS) >= L.PUISSANCE_MIN

    mois_naif = exigees / 328.0 * 12.0
    assert mois_naif - mois > 12, "le defaut valait plus d'un an"
