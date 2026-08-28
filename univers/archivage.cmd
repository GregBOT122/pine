@echo off
REM Archivage trimestriel de l'univers H_TREND : H1 + H4.
REM Le H1 est la SOURCE DE LA LECTURE (l'appareil gele reagrege lui-meme en H4) ;
REM le H4 n'est qu'un temoin secondaire. Ajoute le 2026-08-28 par
REM AMENDEMENT_TREND_H4_2026-08-28.md.
REM Assurance contre un delisting Binance et un glissement du calendrier de
REM lecture au-dela d'aout 2029. Sert AUSSI de detecteur de delisting : tout
REM symbole muet est signale dans RAPPORT_ARCHIVAGE.md.
REM PREREQUIS : MetaTrader 5 ouvert et connecte (sinon seul Binance est archive).
cd /d "%~dp0"
"C:\Users\grego\dev\Daytrading\bot\xaubot\.venv\Scripts\python.exe" -u archivage_h4.py >> archivage.log 2>&1
copy /Y RAPPORT_ARCHIVAGE.md "C:\Users\grego\OneDrive\collect_donne_trading\RAPPORT_ARCHIVAGE.md" >nul
