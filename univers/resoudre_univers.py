"""
Résolution de l'univers pré-enregistré H_TREND contre le broker réel.

À lancer SUR LA STATION, MetaTrader5 ouvert et connecté.

Trois choses, dans cet ordre d'importance :

  1. RÉSOUDRE les 42 symboles contre le broker. `LiveMT5Feed.resolve` filtre
     SILENCIEUSEMENT les absents — un symbole qui disparaît sans bruit change
     l'univers après coup et invalide la pré-inscription. Ici, tout manquant est
     signalé, jamais avalé.

     La résolution automatique est STRICTE : nom exact, table d'alias écrite à
     la main, ou même ticker simplement décoré par le broker (`XAUUSD.raw`,
     `#AAPL`, `US30Cash`). Le rapprochement flou ne résout RIEN : testé contre
     un broker fictif, il donnait `XAGUSD` (argent) -> `XNGUSD` (gaz naturel) et
     `AUDUSD` -> `XAUUSD` (or), à un caractère d'écart. Il ne sert qu'à suggérer
     dans le rapport, pour qu'un humain tranche.

  2. MESURER LE SPREAD RÉEL, par symbole, échantillonné dans le temps. C'est la
     règle 11, jamais faite. Un spread lu une seule fois ne veut rien dire : il
     double ou triple hors session. Le script APPEND dans un CSV — relancez-le à
     des heures différentes, les statistiques s'accumulent.

  3. COMPARER au seuil de rentabilité mesuré : l'edge net du signal est
     +0,1604 R et le stop vaut 1,5 ATR, donc la friction aller-retour qui
     annule l'edge est  0,1604 x 1,5 x ATR%  =  0,2406 x ATR%.

N'ENVOIE AUCUN ORDRE. Lecture seule sur MT5.

Sorties (à côté de ce script) :
    univers_resolu.json     la liste résolue + specs, avec son SHA256
    spreads_mesures.csv     un échantillon de spread par ligne (append)
    RAPPORT_UNIVERS.md      le rapport lisible, avec le verdict par symbole
"""
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ICI = Path(__file__).resolve().parent

# ---------------------------------------------------------------- l'univers --
# Figé dans PREINSCRIPTION_TREND_H4_2026-08-26.md §5 bis. Ne pas modifier sans
# invalider la pré-inscription.
MT5_FX_INDICES = [
    "XAUUSD", "XAGUSD", "WTI", "NATGAS",
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "EURGBP", "AUDJPY",
    "US30", "US500", "USTEC", "DE40", "UK100", "JP225", "FRA40",
]
MT5_ACTIONS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "NFLX"]
BINANCE = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "AVAXUSDT", "LINKUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "DOGEUSDT",
]

# Noms alternatifs courants selon le broker. Essayés dans l'ordre après le nom
# canonique. La liste est volontairement large : mieux vaut un candidat de trop
# qu'un symbole perdu en silence.
ALIAS = {
    "WTI":    ["USOIL", "XTIUSD", "WTIUSD", "CRUDOIL", "OIL", "USOUSD", "CL"],
    "NATGAS": ["XNGUSD", "NGAS", "NATGASUSD", "NG"],
    "DE40":   ["GER40", "GER30", "DAX40", "DE30", "DAX", "GERMANY40"],
    "UK100":  ["FTSE100", "GB100", "UK100Cash", "FTSE", "GBR100"],
    "JP225":  ["JPN225", "NIKKEI", "JP225Cash", "JPN225Cash", "JAPAN225"],
    "FRA40":  ["CAC40", "FR40", "FRA40Cash", "FRANCE40"],
    "US30":   ["DJ30", "WS30", "USA30", "DOW", "US30Cash", "DJIUSD"],
    "US500":  ["SPX500", "SP500", "USA500", "US500Cash", "SPXUSD"],
    "USTEC":  ["NAS100", "NDX100", "USATEC", "USTECH", "NASDAQ100", "NDXUSD"],
    "XAUUSD": ["GOLD", "XAUUSD.", "GOLDUSD"],
    "XAGUSD": ["SILVER", "SILVERUSD"],
    # --- Actions US : Fusion Markets les nomme par la SOCIETE, pas par le ticker.
    # Constate le 2026-08-27 : sur 250 symboles offerts, 7 des 8 actions de la
    # pre-inscription etaient "MANQUANT" alors qu'elles sont toutes presentes.
    # Le resolveur strict ne pouvait pas les voir, et le rapprochement flou
    # proposait ADP pour AAPL et TSMC pour TSLA — d'ou la regle : le flou
    # SUGGERE, un humain TRANCHE.
    "AAPL":   ["Apple"],
    "AMZN":   ["Amazon"],
    # GOOGL = actions de classe A. `Alphabet-C` (= GOOG) est un AUTRE titre :
    # ne pas y basculer en silence si Alphabet-A disparaissait.
    "GOOGL":  ["Alphabet-A"],
    "MSFT":   ["Microsoft"],
    "NFLX":   ["Netflix"],
    "NVDA":   ["NVIDIA"],
    "TSLA":   ["Tesla"],
    "META":   ["Meta"],
}
# Les actions portent souvent un suffixe/préfixe broker.
SUFFIXES_ACTIONS = ["", ".US", ".NAS", "_us", ".us", ".NYSE", "-USD"]
PREFIXES_ACTIONS = ["", "#"]

EDGE_NET_R = 0.1604      # edge attribuable au signal, mesuré 2026-08-26
STOP_ATR = 1.5           # stop initial de la configuration figée
SEUIL = EDGE_NET_R * STOP_ATR   # friction A/R qui annule l'edge, en unités d'ATR%


# ------------------------------------------------------------------ outils ---
def maintenant() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def atr_pct_h4(df) -> float | None:
    """ATR(14) médian sur H4, en % du prix. df = barres H1 (open/high/low/close)."""
    import pandas as pd
    if df is None or len(df) < 900:
        return None
    h4 = df.resample("4h").agg({"open": "first", "high": "max",
                                "low": "min", "close": "last"}).dropna()
    if len(h4) < 250:
        return None
    pc = h4["close"].shift(1)
    tr = pd.concat([h4["high"] - h4["low"],
                    (h4["high"] - pc).abs(),
                    (h4["low"] - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    return float((atr / h4["close"] * 100).median())


# -------------------------------------------------------------------- MT5 ----
# Décorations que les brokers collent autour d'un ticker. Tout le reste est un
# symbole DIFFÉRENT, pas une variante.
DECOR_AVANT = ("#", ".", "_")
DECOR_APRES = ("", ".US", ".NAS", ".NYSE", "_us", ".us", "-USD", ".raw", ".RAW",
               ".pro", ".PRO", ".ecn", ".ECN", ".a", ".b", ".c", ".m", ".spot",
               ".cash", "Cash", "CASH", "cash", "+", "-", "m", "c", "i", "z")


def _base(nom: str) -> str:
    """Retire les décorations broker autour d'un ticker. `#AAPL.US` -> `AAPL`."""
    n = nom
    while n and n[0] in DECOR_AVANT:
        n = n[1:]
    for s in sorted(DECOR_APRES, key=len, reverse=True):
        if s and n.endswith(s):
            n = n[: -len(s)]
            break
    return n.upper()


def candidats(cible: str, tous: list[str], actions: bool) -> list[str]:
    """Noms que l'on peut résoudre AUTOMATIQUEMENT, sans risque de confusion.

    Volontairement strict. Le rapprochement flou n'est PAS ici : testé contre un
    broker fictif, il résolvait `XAGUSD` (argent) en `XNGUSD` (gaz naturel) et
    `AUDUSD` en `XAUUSD` (or) — un caractère d'écart. Substituer silencieusement
    un instrument par un autre est pire que de le déclarer manquant. Le flou ne
    sert qu'à SUGGÉRER dans le rapport, pour qu un humain tranche.
    """
    vus, sortie = set(), []

    def ajoute(n):
        if n in tous and n not in vus:
            vus.add(n)
            sortie.append(n)

    ajoute(cible)                                   # nom exact
    for a in ALIAS.get(cible, []):                  # alias explicite, écrit à la main
        ajoute(a)
    if actions:
        for p in PREFIXES_ACTIONS:
            for s in SUFFIXES_ACTIONS:
                ajoute(f"{p}{cible}{s}")
    # même ticker, simplement décoré par le broker (XAUUSD.raw, #AAPL, US30Cash)
    haut = cible.upper()
    for n in tous:
        if n not in vus and _base(n) == haut:
            vus.add(n)
            sortie.append(n)
    return sortie


def suggestions(cible: str, tous: list[str]) -> list[str]:
    """Candidats POUR L'HUMAIN uniquement. Jamais résolus automatiquement."""
    return difflib.get_close_matches(cible, tous, n=5, cutoff=0.5)


def resoudre_mt5(mt5, verbose=True):
    tous = [s.name for s in (mt5.symbols_get() or [])]
    if verbose:
        print(f"  broker : {len(tous)} symboles offerts")
    resolus, manquants = {}, {}
    for cible in MT5_FX_INDICES + MT5_ACTIONS:
        est_action = cible in MT5_ACTIONS
        cands = candidats(cible, tous, est_action)
        trouve = None
        for c in cands:
            if mt5.symbol_info(c) is not None:
                mt5.symbol_select(c, True)   # réveille le symbole
                trouve = c
                break
        if trouve:
            resolus[cible] = trouve
        else:
            manquants[cible] = suggestions(cible, tous)
    return resolus, manquants, tous


def specs_mt5(mt5, nom: str) -> dict:
    """Specs + profondeur d'historique. `point_value` MESURÉE via order_calc_profit :
    trade_tick_value et trade_contract_size peuvent se contredire (cas avéré sur
    XAUUSD/MetaQuotes-Demo, facteur 10)."""
    import pandas as pd
    info = mt5.symbol_info(nom)
    if info is None:
        return {}
    d = {"point": info.point, "digits": info.digits,
         "spread_points_instantane": info.spread,
         "volume_min": info.volume_min, "volume_step": info.volume_step}

    # valeur du point, mesurée par la fonction que le broker utilise pour le P&L
    try:
        tick = mt5.symbol_info_tick(nom)
        if tick and tick.ask > 0:
            move = 100 * info.point
            for vol in (1.0, 0.1, 0.01):
                p = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, nom, vol,
                                          tick.ask, tick.ask + move)
                if p and p > 0:
                    d["point_value_mesuree"] = p / (100 * vol)
                    break
    except Exception:
        pass

    # historique H1 disponible aujourd'hui
    try:
        rates = mt5.copy_rates_from_pos(nom, mt5.TIMEFRAME_H1, 0, 60000)
        if rates is not None and len(rates):
            df = pd.DataFrame(rates)
            df["time"] = pd.to_datetime(df["time"], unit="s")
            df = df.set_index("time")[["open", "high", "low", "close"]]
            d["h1_barres"] = len(df)
            d["h1_depuis"] = str(df.index[0].date())
            d["h1_jusqua"] = str(df.index[-1].date())
            d["atr_pct_h4"] = atr_pct_h4(df)
    except Exception as ex:
        d["erreur_historique"] = str(ex)
    return d


# ---------------------------------------------------------------- Binance ----
def _http(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "station-univers/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def resoudre_binance(verbose=True):
    try:
        info = _http("https://api.binance.com/api/v3/exchangeInfo")
    except Exception as ex:
        print(f"  ! Binance injoignable : {ex}")
        return {}, {s: [] for s in BINANCE}
    vivants = {s["symbol"] for s in info.get("symbols", [])
               if s.get("status") == "TRADING"}
    resolus = {s: s for s in BINANCE if s in vivants}
    manquants = {s: [] for s in BINANCE if s not in vivants}
    if verbose:
        print(f"  Binance : {len(resolus)}/{len(BINANCE)} en TRADING")
    return resolus, manquants


def specs_binance(sym: str, annees: float = 3.0) -> dict:
    """Specs Binance. PAGINE l'historique : l'API plafonne à 1000 klines par
    requête, soit 42 jours en H1. Mesurer l'ATR% sur 42 jours au lieu de
    plusieurs années donne un chiffre de régime, pas un chiffre structurel — et
    le seuil de friction est PROPORTIONNEL à l'ATR%, donc l'erreur se propage
    directement au verdict.
    """
    import pandas as pd
    d = {}
    try:
        besoin = int(annees * 365 * 24)
        fin = int(time.time() * 1000)
        morceaux = []
        while besoin > 0:
            n = min(1000, besoin)
            kl = _http(f"https://api.binance.com/api/v3/klines"
                       f"?symbol={sym}&interval=1h&limit={n}&endTime={fin}")
            if not kl:
                break
            morceaux.append(kl)
            besoin -= len(kl)
            fin = int(kl[0][0]) - 1        # remonte avant la plus vieille bougie
            if len(kl) < n:
                break
            time.sleep(0.12)               # courtoisie : le poids API est limité
        if not morceaux:
            return {"erreur_historique": "aucune bougie"}
        plat = [r for m in reversed(morceaux) for r in m]
        df = pd.DataFrame(plat).iloc[:, :5]
        df.columns = ["time", "open", "high", "low", "close"]
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df = df.set_index("time").astype(float).sort_index()
        df = df[~df.index.duplicated(keep="first")]
        d["h1_barres"] = len(df)
        d["h1_depuis"] = str(df.index[0].date())
        d["h1_jusqua"] = str(df.index[-1].date())
        d["atr_pct_h4"] = atr_pct_h4(df)
        # l'ATR récent, à côté du structurel : si les deux divergent, le verdict
        # de friction dépend du régime et doit être lu comme tel
        d["atr_pct_h4_recent"] = atr_pct_h4(df.iloc[-1000:])
    except Exception as ex:
        d["erreur_historique"] = str(ex)
    return d


def spread_binance(syms: list[str]) -> dict:
    """Spread du carnet, en % du mid. NE CONTIENT PAS les frais de taker."""
    out = {}
    try:
        book = _http("https://api.binance.com/api/v3/ticker/bookTicker")
        par = {b["symbol"]: b for b in book}
        for s in syms:
            b = par.get(s)
            if not b:
                continue
            bid, ask = float(b["bidPrice"]), float(b["askPrice"])
            if bid > 0 and ask > 0:
                out[s] = (ask - bid) / ((ask + bid) / 2) * 100
    except Exception:
        pass
    return out


# ------------------------------------------------- échantillonnage spreads ---
CSV_SPREADS = ICI / "spreads_mesures.csv"


def echantillonner(mt5, resolus_mt5, resolus_bin, minutes, intervalle):
    """Boucle d'échantillonnage. Append dans le CSV — les runs s'accumulent.

    Un spread lu une fois ne mesure rien : il double ou triple hors session.
    Relancer à des heures différentes est le seul moyen d'avoir une distribution.
    """
    fin = time.time() + minutes * 60
    neuf = not CSV_SPREADS.exists()
    n = 0
    with CSV_SPREADS.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if neuf:
            w.writerow(["ts_utc", "cible", "nom_broker", "source",
                        "spread_pct", "prix"])
        while True:
            ts = maintenant()
            for cible, nom in resolus_mt5.items():
                try:
                    info = mt5.symbol_info(nom)
                    tick = mt5.symbol_info_tick(nom)
                    if not info or not tick or tick.ask <= 0:
                        continue
                    sp = (tick.ask - tick.bid) / tick.ask * 100
                    w.writerow([ts, cible, nom, "mt5", f"{sp:.6f}", tick.ask])
                    n += 1
                except Exception:
                    continue
            for s, sp in spread_binance(list(resolus_bin)).items():
                w.writerow([ts, s, s, "binance", f"{sp:.6f}", ""])
                n += 1
            f.flush()
            reste = fin - time.time()
            if reste <= 0:
                break
            print(f"    ... {n} échantillons, encore {reste/60:.1f} min",
                  flush=True)
            time.sleep(min(intervalle, max(reste, 1)))
    return n


def stats_spreads():
    """Médiane et p90 par symbole, sur TOUT l'historique du CSV."""
    if not CSV_SPREADS.exists():
        return {}
    par = {}
    with CSV_SPREADS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                par.setdefault(row["cible"], []).append(float(row["spread_pct"]))
            except (ValueError, KeyError):
                continue
    out = {}
    for k, v in par.items():
        v = sorted(v)
        if not v:
            continue
        out[k] = {"n": len(v), "med": v[len(v) // 2],
                  "p90": v[min(len(v) - 1, int(len(v) * 0.9))]}
    return out


# ----------------------------------------------------------------- rapport ---
def verdict(atr_pct, spread_pct, frais_rt=0.0):
    """Compare la friction totale au seuil de rentabilité."""
    if atr_pct is None or spread_pct is None:
        return None, None, "?"
    seuil = SEUIL * atr_pct
    friction = spread_pct + frais_rt
    if friction <= 0:
        return seuil, None, "?"
    marge = seuil / friction
    if marge >= 3:
        v = "OK"
    elif marge >= 1.5:
        v = "SERRE"
    else:
        v = "ECHEC"
    return seuil, marge, v


def ecrire_rapport(resolus, manquants, specs, sp, frais_crypto):
    L = []
    L.append("# Univers H_TREND — résolution contre le broker\n")
    L.append(f"Généré le {maintenant()} UTC.\n")
    n_ok = len(resolus)
    L.append(f"**{n_ok} / {len(MT5_FX_INDICES) + len(MT5_ACTIONS) + len(BINANCE)} "
             f"symboles résolus.**\n")

    if manquants:
        L.append("\n## Manquants — À TRANCHER AVANT DE DÉMARRER L'HORLOGE\n")
        L.append("Un symbole absent doit être soit remplacé par un nom valide "
                 "ci-dessous, soit retiré explicitement de la pré-inscription. "
                 "Le laisser tomber en silence changerait l'univers après coup.\n")
        L.append("\n| Cible | Candidats proposés par le broker |")
        L.append("|---|---|")
        for c, props in sorted(manquants.items()):
            L.append(f"| `{c}` | {', '.join(f'`{p}`' for p in props) or '_aucun_'} |")

    L.append("\n## Résolus\n")
    L.append("Seuil = friction aller-retour qui annule l'edge net "
             f"(+{EDGE_NET_R:.4f} R sur un stop de {STOP_ATR} ATR).\n")
    L.append("\n| Cible | Nom broker | ATR% H4 | Seuil A/R | Spread méd. | p90 | "
             "Friction | Marge | Verdict | H1 depuis |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    alertes = []
    for cible in MT5_FX_INDICES + MT5_ACTIONS + BINANCE:
        if cible not in resolus:
            continue
        sc = specs.get(cible, {})
        st = sp.get(cible)
        atr = sc.get("atr_pct_h4")
        frais = frais_crypto if cible in BINANCE else 0.0
        med = st["med"] if st else None
        seuil, marge, v = verdict(atr, med, frais)
        fr = (med + frais) if med is not None else None
        L.append("| {} | `{}` | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            cible, resolus[cible],
            f"{atr:.3f}" if atr else "?",
            f"{seuil:.4f}%" if seuil else "?",
            f"{med:.4f}%" if med is not None else "—",
            f"{st['p90']:.4f}%" if st else "—",
            f"{fr:.4f}%" if fr is not None else "—",
            f"{marge:.1f}x" if marge else "—",
            v,
            sc.get("h1_depuis", "?")))
        if v == "ECHEC":
            alertes.append(cible)

    if alertes:
        L.append(f"\n**ÉCHEC de friction : {', '.join(alertes)}.** "
                 "Le spread réel mange l'edge sur ces symboles. À trancher "
                 "explicitement dans la pré-inscription — les garder en sachant, "
                 "ou les retirer en le notant.\n")

    # Le seuil est PROPORTIONNEL à l'ATR% : si la volatilité récente s'écarte de
    # la structurelle, le verdict de friction dépend du régime et pas du symbole.
    regimes = []
    for cible in resolus:
        sc = specs.get(cible, {})
        a, ar = sc.get("atr_pct_h4"), sc.get("atr_pct_h4_recent")
        if a and ar and a > 0 and abs(ar / a - 1) > 0.25:
            regimes.append((cible, a, ar))
    if regimes:
        L.append("\n### Divergence de régime de volatilité\n")
        L.append("Le seuil de friction est **proportionnel à l'ATR%**. Sur ces "
                 "symboles, la volatilité récente s'écarte de plus de 25 % de la "
                 "structurelle : le verdict ci-dessus dépend du régime, pas "
                 "seulement du symbole.\n")
        L.append("\n| Symbole | ATR% structurel | ATR% récent | écart |")
        L.append("|---|---|---|---|")
        for c, a, ar in sorted(regimes, key=lambda x: x[2] / x[1]):
            L.append(f"| {c} | {a:.3f} | {ar:.3f} | {(ar/a - 1)*100:+.0f} % |")

    n_ech = sum(v["n"] for v in sp.values()) if sp else 0
    L.append(f"\n## Spreads : {n_ech} échantillons cumulés\n")
    L.append("Relancer ce script à des heures différentes (ouverture Londres, "
             "New York, nuit asiatique) : le CSV s'accumule et les statistiques "
             "se resserrent. **Un spread mesuré à une seule heure ne vaut rien.**\n")
    if any(cible in BINANCE for cible in resolus):
        L.append(f"\nPour Binance, la friction affichée = spread du carnet + "
                 f"**{frais_crypto:.3f} %** de frais aller-retour (paramètre "
                 f"`--frais-crypto`). Le backtest supposait 0,090 % : si tes frais "
                 f"réels sont ceux du taker standard (0,200 % A/R), l'écart est "
                 f"réel et la marge crypto se resserre d'autant.\n")

    L.append("\n## Profondeur d'historique\n")
    L.append("Le test lit des barres jusqu'en 2028. Un symbole dont le broker ne "
             "garde que quelques mois d'H1 doit être archivé trimestriellement, "
             "sinon son historique 2026-2027 aura disparu au moment de lire.\n")
    L.append("\n| Cible | Barres H1 | Depuis |")
    L.append("|---|---|---|")
    for cible in sorted(resolus):
        sc = specs.get(cible, {})
        L.append(f"| {cible} | {sc.get('h1_barres', '?')} | "
                 f"{sc.get('h1_depuis', '?')} |")

    return "\n".join(L) + "\n"


# -------------------------------------------------------------------- main ---
def main():
    ap = argparse.ArgumentParser(description="Résout l'univers H_TREND sur la station.")
    ap.add_argument("--minutes", type=float, default=30,
                    help="durée d'échantillonnage des spreads (0 = un seul passage)")
    ap.add_argument("--intervalle", type=float, default=20,
                    help="secondes entre deux échantillons")
    ap.add_argument("--frais-crypto", type=float, default=0.200,
                    help="frais aller-retour Binance en %% (taker standard = 0,200)")
    a = ap.parse_args()

    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("MetaTrader5 introuvable. Ce script tourne SUR LA STATION, avec le "
              "venv du paquet (voir python.cfg).")
        return 2
    try:
        import pandas  # noqa: F401
    except ImportError:
        print("pandas introuvable dans ce venv.")
        return 2

    print(f"[{maintenant()}] résolution de l'univers H_TREND\n")
    if not mt5.initialize():
        print(f"mt5.initialize a échoué : {mt5.last_error()}")
        print("Ouvrir MetaTrader5 et se connecter, puis relancer.")
        return 1

    try:
        print("1. MT5")
        r_mt5, m_mt5, tous = resoudre_mt5(mt5)
        print(f"     {len(r_mt5)}/{len(MT5_FX_INDICES) + len(MT5_ACTIONS)} résolus")
        for c, nom in sorted(r_mt5.items()):
            if nom != c:
                print(f"     {c:9s} -> {nom}")
        for c in sorted(m_mt5):
            print(f"     {c:9s} -> MANQUANT")

        print("\n2. Binance")
        r_bin, m_bin = resoudre_binance()

        print("\n3. specs + historique")
        specs = {}
        for c, nom in r_mt5.items():
            specs[c] = specs_mt5(mt5, nom)
            print(f"     {c:9s} {specs[c].get('h1_barres', '?')} barres H1, "
                  f"ATR%H4={specs[c].get('atr_pct_h4') and round(specs[c]['atr_pct_h4'], 3)}")
        for c in r_bin:
            specs[c] = specs_binance(c)
            print(f"     {c:9s} ATR%H4="
                  f"{specs[c].get('atr_pct_h4') and round(specs[c]['atr_pct_h4'], 3)}")

        print(f"\n4. spreads ({a.minutes:.0f} min, un échantillon / {a.intervalle:.0f} s)")
        if a.minutes > 0:
            n = echantillonner(mt5, r_mt5, r_bin, a.minutes, a.intervalle)
            print(f"     {n} échantillons ajoutés")
        else:
            echantillonner(mt5, r_mt5, r_bin, 0, a.intervalle)

        sp = stats_spreads()
        resolus = {**r_mt5, **r_bin}
        manquants = {**m_mt5, **m_bin}

        gel = {"genere_utc": maintenant(),
               "edge_net_r": EDGE_NET_R, "stop_atr": STOP_ATR,
               "frais_crypto_rt_pct": a.frais_crypto,
               "resolus": resolus, "manquants": manquants,
               "specs": specs, "spreads": sp}
        gel["sha256_univers"] = hashlib.sha256(
            json.dumps(resolus, sort_keys=True).encode()).hexdigest()
        (ICI / "univers_resolu.json").write_text(
            json.dumps(gel, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8")

        rap = ecrire_rapport(resolus, manquants, specs, sp, a.frais_crypto)
        (ICI / "RAPPORT_UNIVERS.md").write_text(rap, encoding="utf-8")

        # copie vers OneDrive pour la lire depuis l'autre PC, comme RAPPORT_H1
        for base in (Path.home() / "OneDrive" / "collect_donne_trading",):
            if base.exists():
                (base / "RAPPORT_UNIVERS.md").write_text(rap, encoding="utf-8")
                print(f"\n     copié vers {base / 'RAPPORT_UNIVERS.md'}")

        print(f"\n[{maintenant()}] terminé")
        print(f"  résolus   : {len(resolus)}")
        print(f"  manquants : {len(manquants)}"
              + (f"  -> {', '.join(sorted(manquants))}" if manquants else ""))
        print(f"  SHA256 de l'univers résolu : {gel['sha256_univers']}")
        print("\n  Lire RAPPORT_UNIVERS.md, trancher les manquants et les ECHEC "
              "de friction, PUIS coller la liste résolue dans la pré-inscription.")
        print("  L'horloge ne démarre qu'après.")
        return 0
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())
