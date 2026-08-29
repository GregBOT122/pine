"""Archivage trimestriel de l'univers H_TREND : H1 (source de la lecture) + H4.

LE H1 A ETE AJOUTE LE 2026-08-28 (AMENDEMENT_TREND_H4_2026-08-28). Ce script
n'archivait que du H4 ; or l'appareil gele demande du H1 et le reagrege
lui-meme. Il remplissait donc un magasin que la lecture n'ouvre pas. Voir le
commentaire de CACHE_H1 ci-dessous, et les 24 symboles qui auraient ete
ecartes en silence.

POURQUOI, ET SURTOUT POURQUOI PAS POUR LA RAISON QU'ON CROIT.

Première version de l'argument, le 2026-08-27 : « Fusion ne garde que ~4 ans
d'H1 sur les actions, l'historique 2026-2027 aura disparu en 2028 ».
**C'était faux.** Mesuré le 2026-08-28 : AAPL démarre au 2021-03-08 et son
compte de barres AUGMENTE d'un jour sur l'autre (9 645 -> 9 648). Ces dates sont
celles où le courtier a ajouté les titres, pas le bord d'une purge.

Ce qui est réel, et mesuré :

    12 crypto Binance   26 280 barres H1 = 3 x 8 760, debut 2023-08-29
                        La date de debut a AVANCE d'un jour entre le 27 et le 28
                        aout. C'est une fenetre GLISSANTE de 3 ans, exactement.
    actions US          dates de debut fixes (fev-avr 2021), serie qui grandit
    FX / indices        historiques longs et fixes

Au point de contrôle du 2028-09-01, la fenêtre crypto couvrira ~2025-09 ->
2028-09 : les données du test (à partir du 2026-08-27) sont dedans. **Rien n'est
perdu au calendrier prévu.**

LES DEUX RISQUES QUI JUSTIFIENT QUAND MEME CET ARCHIVAGE :

1. **Delisting.** Si Binance retire une paire, son historique ne glisse pas :
   il disparaît. Sur 12 altcoins et deux ans, ce n'est pas une hypothèse
   d'école. Un symbole perdu, c'est un symbole retiré de l'univers après coup —
   ce que la pré-inscription interdit.
2. **Glissement du calendrier.** La pré-inscription autorise à prolonger si
   n < 1 200. Si la lecture glissait au-delà d'**août 2029**, la fenêtre
   glissante commencerait à mordre sur les premières données du test.

Ce script est donc une assurance, pas une urgence. Trimestriel suffit.

IL SERT AUSSI DE DETECTEUR DE DELISTING : tout symbole qui rend zéro barre est
signalé bruyamment. C'est le seul moment où on l'apprendrait avant 2028.

N'ENVOIE AUCUN ORDRE. Lecture seule.
"""
from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ICI = Path(__file__).resolve().parent
UNIVERS = ICI / "univers_resolu.json"

# Hors depot, comme les journaux L2 : une archive qui grossit n'a rien a faire
# sous controle de version. Meme principe que `tradingbott/chemins.py`.
ARCHIVE = Path(r"C:\Users\grego\dev\Daytrading\donnees-h4")

# --- ARCHIVE H1, ajoutee le 2026-08-28 par AMENDEMENT_TREND_H4_2026-08-28 -----
#
# POURQUOI DU H1 ALORS QU ON ARCHIVE DEJA DU H4. Ce ne sont pas les memes
# barres. L appareil gele (`null_shift.load`) demande du H1 et le reagrege avec
# `resample('4h')` ; ce script demandait `TIMEFRAME_H4` a MT5, dont les bornes
# de seance ne tombent pas au meme endroit. Archiver du H4 laissait donc la
# lecture sans sa source.
#
# ET LE CACHE NE COUVRE QUE 18 SYMBOLES — l ancien panier, pas l univers fige a
# 42. Mesure le 2026-08-28 : ADAUSDT, AUDJPY, DE40, NATGAS, WTI et 19 autres
# n ont AUCUN parquet H1, meme historique. Or `load()` rend `None` quand il ne
# trouve rien, et la boucle de calibration fait `continue` : en 2028, 24 des 42
# symboles auraient ete ECARTES EN SILENCE, sans une erreur. C est « retirer un
# symbole apres coup », commis par omission.
#
# HORS DEPOT, comme `donnees-h4` et `donnees-l2`. Le cache de xaubot est
# gitignore, mais il vit DANS un depot : deplacer le code y deplacerait les
# donnees — la panne exacte qui a coute deux jours de collecte L2 les 25 et 26
# aout. La regle du depot est un chemin absolu declare, jamais derive.
CACHE_H1 = Path(r"C:\Users\grego\dev\Daytrading\donnees-h1")

# Le test porte sur les barres POSTERIEURES au 2026-08-27. On archive a partir
# d'un peu avant, pour que le calcul d'ATR et d'EMA200 ait son amorce.
DEPUIS = datetime(2024, 1, 1, tzinfo=timezone.utc)

# --- `--depuis` ajoute le 2026-08-29 ------------------------------------------
# L'archivage trimestriel n'a besoin que de protéger la fenêtre du test, d'où
# le 2024-01-01 : remonter plus loin à chaque passage alourdirait la tâche sans
# rien protéger de plus. Mais la CALIBRATION de `c`, elle, gagne à voir le plus
# d'historique possible. `--depuis` permet un approfondissement ponctuel sans
# changer ce que fait la tâche planifiée.
#
# Plafond réel par source : Binance ne sert qu'une fenêtre GLISSANTE de 3 ans
# (mesurée : 26 280 barres H1, début qui avance d'un jour par jour), donc
# demander 2015 pour une paire crypto rendra quand même ~2023-08. MT5 remonte
# beaucoup plus loin (EURUSD 1997). L'archive deviendra donc déséquilibrée —
# et c'est une propriété à connaître, pas un défaut à cacher.
_DEPUIS_DEFAUT = DEPUIS


def _verifier_emplacement() -> None:
    for parent in [ARCHIVE, *ARCHIVE.parents]:
        if (parent / ".git").exists():
            raise RuntimeError(f"ARCHIVE ({ARCHIVE}) est dans le depot git {parent}.")
    if "OneDrive" in str(ARCHIVE):
        raise RuntimeError(f"ARCHIVE ({ARCHIVE}) est sous OneDrive.")


def fusionner(chemin: Path, barres: list[tuple]) -> tuple[int, int]:
    """Fusionne par horodatage. Rend (total, ajoutees).

    APPEND-ONLY EN ESPRIT : on ne reecrit jamais une barre deja archivee, meme
    si le courtier en rend une version differente. Ce qui a ete vu est garde.
    """
    connues: dict[int, tuple] = {}
    if chemin.exists():
        with chemin.open(encoding="utf-8", newline="") as f:
            for r in csv.reader(f):
                if r and r[0].isdigit():
                    connues[int(r[0])] = tuple(r)
    avant = len(connues)
    for b in barres:
        if int(b[0]) not in connues:
            connues[int(b[0])] = tuple(str(x) for x in b)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tmp = chemin.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "open", "high", "low", "close", "volume"])
        for t in sorted(connues):
            w.writerow(connues[t])
    tmp.replace(chemin)
    return len(connues), len(connues) - avant


def binance_h4(sym: str, interval: str = "4h") -> list[tuple]:
    out, debut = [], int(DEPUIS.timestamp() * 1000)
    while True:
        url = (f"https://api.binance.com/api/v3/klines?symbol={sym}"
               f"&interval={interval}&startTime={debut}&limit=1000")
        req = urllib.request.Request(url, headers={"User-Agent": "archivage/1"})
        with urllib.request.urlopen(req, timeout=20) as r:
            lot = json.load(r)
        if not lot:
            break
        out += [(k[0] // 1000, k[1], k[2], k[3], k[4], k[5]) for k in lot]
        if len(lot) < 1000:
            break
        debut = lot[-1][0] + 1
    return out


def mt5_h4(mt5, nom: str, tf=None) -> list[tuple]:
    """MT5, DÉCOUPÉ PAR ANNÉE — sinon les longues plages rendent zéro barre.

    Mesuré le 2026-08-29 : avec `--depuis 2012-01-01`, `copy_rates_range` en H1
    rend **0 barre** sur AAPL et AMZN alors que la même plage en H4 en rend des
    milliers. Le terminal plafonne le nombre de barres qu'il sert d'un coup, et
    ce plafond mord d'autant plus vite que le pas de temps est fin. Il ne lève
    pas d'erreur : il rend `None`, ce qui devenait une liste vide, ce qui
    devenait « symbole sans H1 ».

    Le cache d'origine de xaubot portait déjà la réponse dans ses noms de
    fichiers — `AAPL_H1_20120101_20130101.parquet` : découpé par année. On fait
    pareil. Une requête vide sur une année donnée (titre pas encore listé) est
    normale et n'interrompt rien.
    """
    mt5.symbol_select(nom, True)
    tf = tf if tf is not None else mt5.TIMEFRAME_H4
    fin = datetime.now(timezone.utc)
    out: list[tuple] = []
    borne = DEPUIS
    while borne < fin:
        suivant = min(borne.replace(year=borne.year + 1), fin)
        r = mt5.copy_rates_range(nom, tf, borne, suivant)
        if r is not None:
            out += [(int(x["time"]), x["open"], x["high"], x["low"], x["close"],
                     x["tick_volume"]) for x in r]
        borne = suivant
    # Les tranches se recouvrent d'une barre a leur jointure ; `fusionner` et
    # `archiver_h1` dedupliquent par horodatage, mais on le fait deja ici pour
    # que le compte imprime soit le vrai.
    vus = set()
    unique = []
    for b in out:
        if b[0] not in vus:
            vus.add(b[0])
            unique.append(b)
    return unique


def archiver_h1(cible: str, barres: list[tuple]) -> tuple[int, int]:
    """Ecrit les barres H1 en parquet, au schema que `null_shift.load` attend.

    SCHEMA IMPOSE, releve sur les parquets existants du cache : index
    `DatetimeIndex` nomme `time`, colonnes open/high/low/close/tick_volume.
    `load()` fait `pd.read_parquet(f)` puis `d[['open','high','low','close']]`
    et `.resample('4h')` — un index qui ne serait pas temporel casserait tout,
    et une colonne manquante aussi.

    UN FICHIER PAR PASSAGE, nomme par la plage couverte. `load()` fait
    `sorted(glob(...))` puis `~index.duplicated()` (keep='first') : le fichier
    le PLUS ANCIEN gagne sur les doublons. Ecrire un fichier neuf est donc
    append-only en esprit — ce qui a ete vu une fois est garde, meme si le
    courtier en rend plus tard une version differente. Meme regle que
    `fusionner()` pour le H4.
    """
    import pandas as pd

    if not barres:
        return 0, 0
    d = pd.DataFrame(barres, columns=["ts", "open", "high", "low", "close",
                                      "tick_volume"])
    d = d.astype({"open": float, "high": float, "low": float, "close": float,
                  "tick_volume": float})
    d.index = pd.to_datetime(d.pop("ts"), unit="s")
    d.index.name = "time"
    d = d[~d.index.duplicated(keep="first")].sort_index()

    CACHE_H1.mkdir(parents=True, exist_ok=True)
    total = len(d)

    # --- N'ECRIRE QUE CE QUI EST NEUF. Corrige le 2026-08-29.
    #
    #     Le nom de fichier porte la plage couverte, donc sa date de FIN change
    #     a chaque passage — et un fichier neuf etait ecrit meme quand le
    #     contenu etait deja archive. Mesure : 84 fichiers H1 avant un passage
    #     a blanc, 90 apres, sans une seule barre nouvelle. A quatre passages
    #     par an sur 42 symboles, l'archive doublait pour rien, et `load()`
    #     concatene TOUS les fichiers avant de dedupliquer.
    #
    #     On compare donc aux horodatages deja archives et on n'ecrit que le
    #     complement. Rien n'est jamais reecrit : c'est toujours du append-only,
    #     simplement sans le doublon.
    #     `columns=["close"]` ET NON `columns=[]` : avec une liste vide, pandas
    #     rend un cadre sans index temporel (un RangeIndex 0..n-1), et la
    #     comparaison portait alors sur des entiers sans rapport. Le test du
    #     2026-08-29 l'a attrape : au 3e passage, 20 barres neuves etaient
    #     declarees « deja connues », le nom de fichier retombait sur celui du
    #     1er passage, et les 20 barres etaient PERDUES en silence. Lire une
    #     vraie colonne coute une colonne et garde l'index.
    #     ET NORMALISER LA RESOLUTION AVANT DE COMPARER. Mesure du 2026-08-29 :
    #     `pd.to_datetime(ts, unit="s")` rend un index **datetime64[s]**, mais
    #     l'aller-retour parquet le rend **datetime64[ms]**. `astype("int64")`
    #     donnait donc des secondes d'un cote et des millisecondes de l'autre —
    #     un facteur 1000, aucune correspondance, et la deduplication ne mordait
    #     jamais. Le premier test le voyait comme « rien n'est jamais connu ».
    def _secondes(idx):
        return idx.astype("datetime64[s]").astype("int64")

    connus: set[int] = set()
    for f in CACHE_H1.glob("%s_H1_*.parquet" % cible):
        try:
            idx = pd.read_parquet(f, columns=["close"]).index
            connus.update(_secondes(idx).tolist())
        except Exception:                                    # noqa: BLE001
            continue

    neuves = d[~_secondes(d.index).isin(connus)]
    if neuves.empty:
        return total, 0

    base = "%s_H1_%s_%s" % (cible, neuves.index[0].strftime("%Y%m%d"),
                            neuves.index[-1].strftime("%Y%m%d"))
    chemin = CACHE_H1 / (base + ".parquet")
    # Une collision de nom ne doit JAMAIS faire abandonner des barres neuves :
    # deux lots differents peuvent couvrir le meme jour. On suffixe.
    suffixe = 0
    while chemin.exists():
        suffixe += 1
        chemin = CACHE_H1 / ("%s_%02d.parquet" % (base, suffixe))
    tmp = chemin.with_suffix(".tmp")
    neuves.to_parquet(tmp)
    tmp.replace(chemin)
    return total, len(neuves)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sortie", type=Path, default=None,
                    help="rapport markdown (defaut : RAPPORT_ARCHIVAGE.md ici)")
    ap.add_argument("--depuis", default=None,
                    help="AAAA-MM-JJ : remonter plus loin que le defaut "
                         "(approfondissement ponctuel, cf. commentaire DEPUIS)")
    a = ap.parse_args()

    if a.depuis:
        global DEPUIS
        DEPUIS = datetime.strptime(a.depuis, "%Y-%m-%d").replace(
            tzinfo=timezone.utc)
        print("Approfondissement ponctuel : depuis %s (defaut %s)"
              % (DEPUIS.date(), _DEPUIS_DEFAUT.date()))

    _verifier_emplacement()
    if not UNIVERS.exists():
        print("univers_resolu.json absent — lancer RESOUDRE_UNIVERS.bat d'abord.")
        return 2
    d = json.loads(UNIVERS.read_text(encoding="utf-8"))
    resolus = d["resolus"]

    lignes, vides, sans_h1 = [], [], []
    try:
        import MetaTrader5 as mt5
        ok_mt5 = mt5.initialize()
    except ImportError:
        mt5, ok_mt5 = None, False
    if not ok_mt5:
        print("! MetaTrader5 indisponible — seules les paires Binance seront archivees.")

    for cible in sorted(resolus):
        nom = resolus[cible]
        crypto = cible.endswith("USDT")
        try:
            barres = binance_h4(nom) if crypto else (mt5_h4(mt5, nom) if ok_mt5 else [])
        except Exception as ex:                              # noqa: BLE001
            print(f"  {cible:10s} ECHEC {type(ex).__name__}")
            vides.append((cible, nom, type(ex).__name__))
            continue
        if not barres:
            # C'est le signal qui compte : un symbole muet est peut-etre delisté.
            if crypto or ok_mt5:
                vides.append((cible, nom, "aucune barre"))
                print(f"  {cible:10s} AUCUNE BARRE — delisté ?")
            continue
        total, neuves = fusionner(ARCHIVE / f"{cible}_H4.csv", barres)

        # --- H1, la source REELLE de la lecture (amendement 3). Le H4
        #     ci-dessus reste un temoin secondaire : ce ne sont pas les memes
        #     barres, et c'est le H1 que `load()` reagrege.
        try:
            b1 = (binance_h4(nom, "1h") if crypto
                  else (mt5_h4(mt5, nom, mt5.TIMEFRAME_H1) if ok_mt5 else []))
            n1, f1 = archiver_h1(cible, b1)
        except Exception as ex:                              # noqa: BLE001
            n1, f1 = 0, 0
            print(f"  {cible:10s} H1 ECHEC {type(ex).__name__}")
        if not n1:
            sans_h1.append(cible)

        lignes.append((cible, nom, total, neuves, n1))
        print(f"  {cible:10s} {total:6d} barres H4 (+{neuves})   "
              f"{n1:6d} H1 (+{f1})")

    if ok_mt5:
        mt5.shutdown()

    horo = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    r = [f"# Archivage H1 + H4 de l'univers H_TREND — {horo}", "",
         f"**{len(lignes)} / {len(resolus)} symboles archivés.** "
         f"Destination : `{ARCHIVE}`", ""]
    if vides:
        r += ["## ⚠ SYMBOLES MUETS — À VÉRIFIER", "",
              "Un symbole qui ne rend aucune barre est peut-être **delisté**. "
              "C'est le seul moment où on l'apprendrait avant 2028, et un symbole "
              "perdu est un symbole retiré de l'univers après coup — ce que la "
              "pré-inscription interdit.", "",
              "| Cible | Nom broker | Cause |", "|---|---|---|"]
        r += [f"| `{c}` | `{n}` | {m} |" for c, n, m in vides]
        r.append("")
    if sans_h1:
        # Un symbole sans H1 est un symbole que `load()` rendra `None` et que
        # la boucle de calibration ecartera par `continue`, SANS ERREUR. C est
        # « retirer un symbole apres coup » commis en silence : il faut donc
        # que ce soit bruyant ici, seul endroit ou on peut encore l apprendre.
        r += ["## ⚠ SYMBOLES SANS H1 — LA LECTURE LES ÉCARTERAIT EN SILENCE", "",
              "`load()` rend `None` quand aucun parquet H1 n existe, et la "
              "boucle de calibration fait `continue`. Ces symboles sortiraient "
              "de l univers sans qu aucune erreur ne soit levée — ce que la "
              "pré-inscription interdit.", "",
              "    " + ", ".join(sorted(sans_h1)), ""]

    r += ["## Archivé", "",
          f"H4 (témoin secondaire) : `{ARCHIVE}`", "",
          f"**H1 (source de la lecture) : `{CACHE_H1}`**", "",
          "| Cible | Nom broker | Barres H4 | Nouvelles | Barres H1 |",
          "|---|---|---|---|---|"]
    r += [f"| `{c}` | `{n}` | {t} | +{v} | {h} |"
          for c, n, t, v, h in sorted(lignes)]
    sortie = a.sortie or ICI / "RAPPORT_ARCHIVAGE.md"
    sortie.write_text("\n".join(r) + "\n", encoding="utf-8")
    print(f"\nrapport : {sortie}")
    if sans_h1:
        print("! %d symboles SANS H1 — la lecture les ecarterait en silence : %s"
              % (len(sans_h1), ", ".join(sorted(sans_h1))))
    return 1 if (vides or sans_h1) else 0


if __name__ == "__main__":
    raise SystemExit(main())
