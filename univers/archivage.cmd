@echo off
REM Archivage trimestriel de l'univers H_TREND : H1 + H4.
REM Le H1 est la SOURCE DE LA LECTURE (l'appareil gele reagrege lui-meme en H4) ;
REM le H4 n'est qu'un temoin secondaire. Ajoute le 2026-08-28 par
REM AMENDEMENT_TREND_H4_2026-08-28.md.
REM Assurance contre un delisting Binance et un glissement du calendrier de
REM lecture au-dela d'aout 2029. Sert AUSSI de detecteur de delisting : tout
REM symbole muet est signale dans RAPPORT_ARCHIVAGE.md.
REM PREREQUIS : MetaTrader 5 ouvert et connecte (sinon seul Binance est archive).
REM
REM LE CODE DE LA TACHE EST CELUI DE PYTHON, depuis le 2026-10-17. Jusque-la, la
REM derniere commande etait le `copy` vers OneDrive : la tache rendait 0 meme
REM quand archivage_h4.py REFUSAIT le courtier, et c'etait l'ANCIEN rapport qui
REM partait dans OneDrive, comme si le passage avait eu lieu.
REM     0  archive faite, rien a signaler
REM     1  symbole muet ou sans H1, delisting possible -- OU plantage : le
REM        rapport neuf dit lequel, le journal aussi
REM     2  univers_resolu.json absent, rien n'est ecrit
REM     3  REFUS : courtier autre que FusionMarkets-Live, rien n'est ecrit
REM     4  Python a rendu 0, mais aucun rapport neuf n'est arrive dans OneDrive
REM Le 4 est le seul que ce .cmd fabrique : un code de sortie n'est pas une
REM preuve d'ecriture.
REM
REM UN RAPPORT NEUF SE PROUVE PAR SON EXISTENCE, PAS PAR LE CODE. Le script
REM ecrit dans RAPPORT_ARCHIVAGE.neuf.md, efface juste avant de le lancer : s'il
REM existe apres, il vient de ce passage. Le code seul ne le dirait pas, puisqu'un
REM plantage rend 1 sans rien ecrire, comme un symbole muet en ecrivant.
REM Sans rapport neuf, l'ancien part quand meme dans OneDrive, mais sous un
REM bandeau PERIME : c'est le dernier etat connu de l'archive, pas celui-ci.
REM
REM ASCII PUR ET CRLF : cmd.exe lit ce fichier dans la page de code locale, et
REM cherche ses etiquettes de travers dans un fichier en LF seul.
REM tradingbott/tests/test_archivage_cmd.py le lance contre un faux script.
setlocal
cd /d "%~dp0"
set "PY=C:\Users\grego\dev\Daytrading\bot\xaubot\.venv\Scripts\python.exe"
set "DEST=C:\Users\grego\OneDrive\collect_donne_trading\RAPPORT_ARCHIVAGE.md"
set "NEUF=RAPPORT_ARCHIVAGE.neuf.md"
set DEPOSE=non

if exist "%NEUF%" del /f /q "%NEUF%"
"%PY%" -u archivage_h4.py --sortie "%NEUF%" >> archivage.log 2>&1
set CODE=%ERRORLEVEL%
>> archivage.log echo [%DATE% %TIME%] archivage_h4.py a rendu %CODE%
if not exist "%NEUF%" goto perime

REM La copie vers OneDrive AVANT le deplacement local : si le `move` echouait,
REM c'est quand meme le rapport neuf qui partirait, jamais l'ancien.
set DEPOSE=oui
copy /y "%NEUF%" "%DEST%" >nul 2>&1 || set DEPOSE=non
move /y "%NEUF%" RAPPORT_ARCHIVAGE.md >nul
if "%DEPOSE%"=="oui" goto fin
>> archivage.log echo [%DATE% %TIME%] rapport NON depose : %DEST%
goto fin

:perime
>> archivage.log echo [%DATE% %TIME%] AUCUN rapport neuf : l'ancien part dans OneDrive sous un bandeau PERIME
> "%DEST%" echo # RAPPORT PERIME -- passage du %DATE% %TIME%, aucun rapport neuf
>> "%DEST%" echo.
>> "%DEST%" echo **archivage_h4.py a rendu %CODE% sans ecrire de rapport.** Ce qui suit est le
>> "%DEST%" echo rapport du passage PRECEDENT : le dernier etat connu de l'archive, rien sur
>> "%DEST%" echo celui-ci.
>> "%DEST%" echo.
>> "%DEST%" echo Codes : 1 = plantage ; 2 = univers_resolu.json absent ; 3 = REFUS du courtier,
>> "%DEST%" echo autre que FusionMarkets-Live, rien n'est ecrit ; 0 = sorti sans erreur ET sans
>> "%DEST%" echo rapport, ce qui ne devrait pas arriver. Detail : `pine\univers\archivage.log`.
>> "%DEST%" echo.
>> "%DEST%" echo ---
>> "%DEST%" echo.
if exist RAPPORT_ARCHIVAGE.md type RAPPORT_ARCHIVAGE.md >> "%DEST%"

:fin
if "%DEPOSE%"=="non" if "%CODE%"=="0" set CODE=4
exit /b %CODE%
