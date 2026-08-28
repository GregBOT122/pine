@echo off
REM Echantillonnage de spreads a heure fixe, pour la regle 11.
REM
REM POURQUOI UNE TACHE ET PAS UN LANCEMENT A LA MAIN.
REM Un spread mesure a une seule heure ne vaut rien : il double ou triple hors
REM session, et il explose au rollover. Or les trois moments qui manquent sont
REM 01h00, 07h00 et 21h00 UTC — soit 21h, 03h et 17h locales. Personne ne va
REM lancer ca a 3h du matin trois jours de suite, donc ca ne se fera jamais a la
REM main, et la marge de friction restera une supposition.
REM
REM Appelle le .py DIRECTEMENT et non RESOUDRE_UNIVERS.bat : celui-ci finit par
REM `pause`, qui bloquerait une tache planifiee jusqu'a son delai d'expiration.
REM
REM Fenetre courte (12 min) exprès : le scanner H1 accumule sur le meme terminal
REM MT5, et une session d'echantillonnage longue lui disputerait le flux.
setlocal
set PY=C:\Users\grego\dev\Daytrading\bot\xaubot\.venv\Scripts\python.exe
cd /d "%~dp0"

REM Le CSV est APPENDE, jamais ecrase : chaque passage resserre les statistiques.
"%PY%" -u resoudre_univers.py --minutes 12 >> echantillonnage.log 2>&1

endlocal
