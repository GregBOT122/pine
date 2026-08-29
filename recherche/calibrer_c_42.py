"""Recalcul de `c` sur l'univers figé de 42 symboles — 2026-08-29.

    py calibrer_c_42.py            # tout l'univers + décomposition par bloc
    py calibrer_c_42.py --bloc crypto

────────────────────────────────────────────────────────────────────────────────
CE QU'EST `c`, ET POURQUOI LE RECALCULER
────────────────────────────────────────────────────────────────────────────────
La pré-inscription écrit l'écart-type de la distribution nulle comme

    sd_null = c / sqrt(1,32 · n)

`c` est donc un facteur d'échelle par trade : plus les symboles sont corrélés,
moins la mise en commun réduit la dispersion du null, et plus `c` est grand.

La table de puissance emploie **c = 1,72**, mesuré sur les **17 symboles** de la
calibration historique. L'univers du test en compte **42**, dont 12 crypto — et
la pré-inscription avertit elle-même qu'un bloc homogène est puni (crypto seul
mesuré à 2,42). Le rejeu du 2026-08-28 a par ailleurs montré que même sur les 17
d'origine, le `c` que le script gelé mesure vaut **2,125**, pas 1,72.

D'où ce recalcul : sur l'univers réel, pas sur celui de la calibration.

────────────────────────────────────────────────────────────────────────────────
LA DISCIPLINE, ET ELLE EST LE POINT
────────────────────────────────────────────────────────────────────────────────
1. **Fenêtre bornée au 2026-08-26 23:59 UTC.** Les barres du test commencent le
   2026-08-27. Aucune n'entre ici. Le contrôle est une assertion, pas une
   intention : le script REFUSE de tourner si une barre postérieure survit au
   filtre.

2. **L'expR observé n'est ni calculé ni imprimé.** `c` ne dépend que de la
   DISPERSION du null et de comptages de trades. Sortir un rendement in-sample
   de plus sur des données déjà vues ne servirait qu'à créer une tentation.

3. **Aucune ligne de la règle n'est retapée.** Les fonctions viennent du fichier
   gelé, exécutées verbatim via `lecture_h_trend.charger_appareil_gele()`.
   L'empreinte est vérifiée avant tout calcul.

4. **Friction de l'amendement 1** : p90 du spread mesuré + commission crypto.
   Le dict `FRICTION` du fichier gelé (17 symboles) n'est pas utilisé.

5. **Graine 20260826**, celle du fichier gelé. Pas de graine choisie pour
   l'occasion.

────────────────────────────────────────────────────────────────────────────────
CE QUE CE RECALCUL NE FAIT PAS
────────────────────────────────────────────────────────────────────────────────
Il ne remplace pas le `c` que la pré-inscription impose de recalculer **sur les
données du test** en 2028. Il donne une PROJECTION mieux fondée que 1,72 — sur
le bon univers, mais sur la période 2024-2026, qui n'est pas celle du test.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import lecture_h_trend as L                                  # noqa: E402

# Borne dure : le test porte sur les barres POSTÉRIEURES au 2026-08-27 00:00 UTC.
FIN_CALIBRATION = pd.Timestamp("2026-08-26 23:59:59")
GRAINE = 20260826
B = 2000

BLOCS = {
    "FX": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
           "EURJPY", "GBPJPY", "EURGBP", "AUDJPY"],
    "indices": ["US30", "US500", "USTEC", "DE40", "UK100", "JP225", "FRA40"],
    "matieres": ["XAUUSD", "XAGUSD", "WTI", "NATGAS"],
    "crypto": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
               "AVAXUSDT", "LINKUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT",
               "DOGEUSDT"],
    "actions": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "NFLX"],
}


def table_friction(uni: dict) -> dict:
    """Amendement 1 : p90 du spread mesuré + commission crypto."""
    frais = float(uni.get("frais_crypto_rt_pct", 0.0))
    out = {}
    for sym, m in uni.get("spreads", {}).items():
        if L.QUANTILE_SPREAD in m:
            out[sym] = float(m[L.QUANTILE_SPREAD]) + (frais if sym.endswith("USDT") else 0.0)
    return out


def preparer(ns, symboles, fric) -> dict:
    data = {}
    for sym in symboles:
        d = ns["load"](sym)
        if d is None or len(d) < 600:
            print("  %-10s ecarte (pas de donnees)" % sym)
            continue

        # --- LA BORNE, ET SON CONTROLE. Couper puis VERIFIER : un filtre qu'on
        #     n'a pas verifie est une intention, pas une garantie.
        d = d[d.index <= FIN_CALIBRATION]
        if len(d) and d.index.max() > FIN_CALIBRATION:
            raise AssertionError("%s : une barre du test a survecu au filtre" % sym)
        if len(d) < 600:
            print("  %-10s ecarte (trop court avant la borne)" % sym)
            continue

        R, KX = ns["precompute"](d, fric[sym])
        sg = ns["signals"](d)
        data[sym] = dict(R=R, KX=KX, sig=np.flatnonzero(sg), n=len(d))
        print("  %-10s n=%5d  signaux=%4d  friction=%.4f%%  jusqu'au %s"
              % (sym, len(d), int(sg.sum()), fric[sym], d.index.max().date()))
    return data


def mesurer_c(data: dict, etiquette: str) -> dict | None:
    """c = ecart-type du null x sqrt(n du null). Rien d'autre n'est calcule."""
    if len(data) < 2:
        return None
    ns = L.charger_appareil_gele()
    ns["DATA"] = data
    minshift = int(ns["MINSHIFT"])
    n_min = min(D["n"] for D in data.values())
    distincts = n_min - 2 * minshift
    if distincts <= 0:
        print("  %-10s espace de decalage VIDE (min_n=%d, MINSHIFT=%d)"
              % (etiquette, n_min, minshift))
        return None

    # n observe : un COMPTAGE. Le rendement associe n'est ni garde ni imprime.
    n_obs = ns["stat"]({s: 0 for s in data})[2]

    rng = np.random.default_rng(GRAINE)
    e = np.empty(B)
    nn = np.empty(B)
    for b in range(B):
        k = int(rng.integers(minshift, n_min - minshift))
        m, _, cnt = ns["stat"]({s: k for s in data})
        e[b] = m
        nn[b] = cnt
    sd = float(e.std())
    n_null = float(nn.mean())

    # --- LA CONVENTION, ET POURQUOI ELLE N'EST PAS ANODINE.
    #
    #     `c` n'a de sens que branché dans la formule du document :
    #         sd_null(n) = c / racine(1,32 n)
    #     Pour que cette formule REPRODUISE l'écart-type mesuré au n de la
    #     calibration, il faut donc  c = sd x racine(1,32 x n_obs).
    #
    #     Ma première version prenait `sd x racine(n_null)`. Sur les 17 symboles
    #     d'origine les deux coïncidaient, parce que le rapport n_null/n_obs y
    #     valait 1,318 — le 1,32 de la formule. Sur les 42 il vaut 1,259, et les
    #     deux définitions divergent de 2,4 %. **Le 1,32 codé en dur dans la
    #     formule n'est plus le rapport réel de cet univers.**
    #
    #     On garde la convention du document — sinon la formule et le `c` ne
    #     parlent plus de la même chose — et on RAPPORTE le rapport mesuré, pour
    #     que l'écart soit visible au lieu d'être absorbé en silence.
    ratio = n_null / n_obs if n_obs else float("nan")
    return dict(etiquette=etiquette, k=len(data), n_obs=n_obs, n_null=n_null,
                ratio=ratio, sd=sd, c=sd * np.sqrt(1.32 * n_obs),
                c_brut=sd * np.sqrt(n_null), distincts=distincts)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bloc", default=None, help="ne calibrer qu'un bloc")
    p.add_argument("--sortie", type=Path, default=None)
    a = p.parse_args()

    if L.empreinte_gelee() != L.EMPREINTE:
        print("REFUS : l'empreinte de la configuration figee ne se recalcule pas.")
        return 4

    uni = json.loads(L.UNIVERS.read_text(encoding="utf-8"))
    resolus = sorted(uni["resolus"])
    fric = table_friction(uni)
    manquants = [s for s in resolus if s not in fric]
    if manquants:
        print("REFUS : pas de friction pour %s" % ", ".join(manquants))
        return 3

    print("# Recalcul de c — univers fige, %d symboles" % len(resolus))
    print("  fenetre de calibration : jusqu'au %s inclus (le test commence le "
          "2026-08-27)" % FIN_CALIBRATION.date())
    print("  friction : %s du spread mesure + commission crypto (amendement 1)"
          % L.QUANTILE_SPREAD)
    print("  graine %d, B=%d, decalage commun\n" % (GRAINE, B))

    ns = L.charger_appareil_gele()
    print("Chargement et precalcul :")
    tout = preparer(ns, resolus, fric)
    print()

    lots = [("TOUT (42)", tout)]
    if a.bloc:
        lots = [(a.bloc, {s: d for s, d in tout.items() if s in BLOCS[a.bloc]})]
    else:
        for nom, membres in BLOCS.items():
            lots.append((nom, {s: d for s, d in tout.items() if s in membres}))

    res = []
    for nom, d in lots:
        print("Null par decalage circulaire : %s (%d symboles)..." % (nom, len(d)),
              flush=True)
        r = mesurer_c(d, nom)
        if r:
            res.append(r)
            print("   c = %.3f   (sd_null %.5f, n_null %.0f, ratio %.3f, "
                  "%d decalages distincts)"
                  % (r["c"], r["sd"], r["n_null"], r["ratio"], r["distincts"]))
        print()

    out = ["# Recalcul de `c` sur l'univers figé — %s UTC"
           % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "",
           "Fenêtre bornée au **%s inclus** ; les barres du test "
           "(2026-08-27 et au-delà) n'y entrent pas." % FIN_CALIBRATION.date(),
           "L'expR observé n'est ni calculé ni rapporté : `c` ne dépend que de "
           "la dispersion du null.", "",
           "| Bloc | k | n obs. | n null | ratio mesuré | sd du null | **c** |",
           "|---|---|---|---|---|---|---|"]
    for r in res:
        out.append("| %s | %d | %d | %.0f | %.3f | %.5f | **%.3f** |"
                   % (r["etiquette"], r["k"], r["n_obs"], r["n_null"],
                      r["ratio"], r["sd"], r["c"]))
    out += ["",
            "`c = sd_null x racine(1,32 n_obs)`, la convention de la formule du "
            "document. Le **ratio mesuré** est le vrai `n_null / n_obs` : la "
            "formule le fige à 1,32, valeur relevée sur les 17 symboles de la "
            "calibration d'origine."]

    tout_r = next((r for r in res if r["etiquette"].startswith("TOUT")), None)
    if tout_r:
        c42 = tout_r["c"]
        out += ["", "## Puissance avec ce `c`", "",
                "| n | c=1,72 (table du doc) | c=2,125 (17 symboles) | "
                "**c=%.3f (42 symboles)** |" % c42, "|---|---|---|---|"]
        for n in (1000, 1200, 1500, 1800, 2100, 2400):
            out.append("| %d | %.3f | %.3f | **%.3f** |"
                       % (n, L.puissance(n, 1.72), L.puissance(n, 2.125),
                          L.puissance(n, c42)))
        out += ["", "`n` pour atteindre le plancher de 0,80 : "
                "**%d** (contre %d annoncé avec c=1,72)."
                % (L.n_pour_puissance(c42), L.n_pour_puissance(1.72)), ""]

    texte = "\n".join(out)
    # ÉCRIRE D'ABORD. La première version imprimait puis écrivait : la console
    # cp1252 a buté sur une flèche Unicode, et le fichier n'a jamais été créé —
    # dix minutes de permutations perdues pour un caractère d'affichage.
    if a.sortie:
        a.sortie.write_text(texte + "\n", encoding="utf-8")
        print("ecrit : %s" % a.sortie)
    try:
        print(texte)
    except UnicodeEncodeError:
        print("(rapport non affichable dans cette console ; il est dans le "
              "fichier ci-dessus)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
