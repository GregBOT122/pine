"""Archivage trimestriel des barres H4 de l'univers H_TREND.

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

# Le test porte sur les barres POSTERIEURES au 2026-08-27. On archive a partir
# d'un peu avant, pour que le calcul d'ATR et d'EMA200 ait son amorce.
DEPUIS = datetime(2024, 1, 1, tzinfo=timezone.utc)


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


def binance_h4(sym: str) -> list[tuple]:
    out, debut = [], int(DEPUIS.timestamp() * 1000)
    while True:
        url = (f"https://api.binance.com/api/v3/klines?symbol={sym}"
               f"&interval=4h&startTime={debut}&limit=1000")
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


def mt5_h4(mt5, nom: str) -> list[tuple]:
    mt5.symbol_select(nom, True)
    r = mt5.copy_rates_range(nom, mt5.TIMEFRAME_H4, DEPUIS,
                             datetime.now(timezone.utc))
    if r is None:
        return []
    return [(int(x["time"]), x["open"], x["high"], x["low"], x["close"],
             x["tick_volume"]) for x in r]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sortie", type=Path, default=None,
                    help="rapport markdown (defaut : RAPPORT_ARCHIVAGE.md ici)")
    a = ap.parse_args()

    _verifier_emplacement()
    if not UNIVERS.exists():
        print("univers_resolu.json absent — lancer RESOUDRE_UNIVERS.bat d'abord.")
        return 2
    d = json.loads(UNIVERS.read_text(encoding="utf-8"))
    resolus = d["resolus"]

    lignes, vides = [], []
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
        lignes.append((cible, nom, total, neuves))
        print(f"  {cible:10s} {total:6d} barres (+{neuves})")

    if ok_mt5:
        mt5.shutdown()

    horo = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    r = [f"# Archivage H4 de l'univers H_TREND — {horo}", "",
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
    r += ["## Archivé", "", "| Cible | Nom broker | Barres H4 | Nouvelles |",
          "|---|---|---|---|"]
    r += [f"| `{c}` | `{n}` | {t} | +{v} |" for c, n, t, v in sorted(lignes)]
    sortie = a.sortie or ICI / "RAPPORT_ARCHIVAGE.md"
    sortie.write_text("\n".join(r) + "\n", encoding="utf-8")
    print(f"\nrapport : {sortie}")
    return 1 if vides else 0


if __name__ == "__main__":
    raise SystemExit(main())
