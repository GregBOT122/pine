# Quarantaine — lignes retirées de `spreads_mesures.csv`

Rien n'est effacé : une ligne qui sort d'un fichier de mesure arrive ici, avec sa raison.

## `passe_demo_2026-10-16.csv` — 1 554 lignes

La passe `spreads-sessions` de 03 h (New York) le 2026-10-16, de 07:24:51 à 07:36:51 UTC.
`mt5.initialize()` sans chemin s'était rattaché au terminal **MetaQuotes-Demo** du bot P2 :
1 110 lignes MT5 venues d'un autre courtier, avec 12 noms de symboles différents
(`AAPL` au lieu de `Apple`, `NG` au lieu de `XNGUSD`...). Les 444 lignes Binance de la
même passe sont justes, mais la passe a été retirée entière.

Ces lignes ne sont pas des mesures de l'univers gelé (`ANNEXE_UNIVERS_RESOLU_2026-08-27`,
FusionMarkets-Live). Ne pas les reverser.

Depuis, `resoudre_univers.py` et `archivage_h4.py` se rattachent au terminal Fusion par
son chemin et refusent tout autre serveur. Récit complet : `tradingbott/DECISIONS.md`,
entrée du 2026-10-16/17 (univers H_TREND).
