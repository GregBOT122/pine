@echo off
REM Archivage trimestriel des barres H4 de l'univers H_TREND.
REM Assurance contre un delisting Binance et un glissement du calendrier de
REM lecture au-dela d'aout 2029. Sert AUSSI de detecteur de delisting : tout
REM symbole muet est signale dans RAPPORT_ARCHIVAGE.md.
REM PREREQUIS : MetaTrader 5 ouvert et connecte (sinon seul Binance est archive).
cd /d "%~dp0"
"C:\Users\grego\dev\Daytrading\bot\xaubot\.venv\Scripts\python.exe" -u archivage_h4.py >> archivage.log 2>&1
copy /Y RAPPORT_ARCHIVAGE.md "C:\Users\grego\OneDrive\collect_donne_trading\RAPPORT_ARCHIVAGE.md" >nul
