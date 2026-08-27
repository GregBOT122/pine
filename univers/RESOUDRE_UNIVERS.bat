@echo off
REM Resolution de l'univers pre-enregistre H_TREND contre le broker reel.
REM
REM PREREQUIS : MetaTrader5 ouvert ET connecte a un compte.
REM             Sans ca mt5.initialize() echoue et le script s'arrete proprement.
REM
REM Le chemin de Python vient de python.cfg, ecrit par INSTALLER.bat : ne jamais
REM le chercher dans le PATH, Windows 11 y place un leurre du Microsoft Store.
REM
REM Usage :
REM   RESOUDRE_UNIVERS.bat              30 min d'echantillonnage de spreads
REM   RESOUDRE_UNIVERS.bat 0            resolution seule, un seul passage
REM   RESOUDRE_UNIVERS.bat 120          2 h d'echantillonnage
REM
REM RELANCER A DES HEURES DIFFERENTES. Le CSV des spreads est appende, pas
REM ecrase : ouverture de Londres, ouverture de New York, nuit asiatique.
REM Un spread mesure a une seule heure ne vaut rien.
setlocal
set "RACINE=%~dp0"

set "MINUTES=%~1"
if not defined MINUTES set "MINUTES=30"

set "PY="
if exist "%RACINE%python.cfg" set /p PY=<"%RACINE%python.cfg"
if not defined PY if exist "%RACINE%..\python.cfg" set /p PY=<"%RACINE%..\python.cfg"
if not defined PY (
    echo.
    echo   python.cfg introuvable.
    echo   Placer ce dossier dans le paquet station-scanner, ou copier le
    echo   python.cfg du paquet a cote de ce .bat.
    echo.
    pause
    exit /b 1
)

echo.
echo   Python  : %PY%
echo   Duree   : %MINUTES% min d'echantillonnage de spreads
echo.

"%PY%" "%RACINE%resoudre_univers.py" --minutes %MINUTES%
set "CODE=%errorlevel%"

echo.
if "%CODE%"=="0" (
    echo   Termine. Lire RAPPORT_UNIVERS.md dans ce dossier.
) else (
    echo   Echec ^(code %CODE%^). MetaTrader5 est-il ouvert et connecte ?
)
echo.
pause
exit /b %CODE%
