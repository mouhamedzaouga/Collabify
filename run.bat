@echo off
setlocal
title Collabify
cd /d "%~dp0backend" || goto :nobackend

REM --- 1. Trouver Python (lanceur "py" en priorite, sinon "python") ---
set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY (
  python --version >nul 2>nul && set "PY=python"
)
if not defined PY goto :nopython

REM --- 2. Environnement virtuel ---
if not exist ".venv\Scripts\python.exe" (
  echo Creation de l'environnement virtuel...
  %PY% -m venv .venv
  if errorlevel 1 goto :fail
)
set "VPY=.venv\Scripts\python.exe"

REM --- 3. Dependances ---
echo Installation des dependances...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

REM --- 4. Lancement (le navigateur s'ouvre apres 4 secondes) ---
echo.
echo ================================================
echo   Collabify demarre sur http://localhost:8000
echo   Appuyez sur Ctrl+C pour arreter le serveur
echo ================================================
echo.
start "" cmd /c "timeout /t 4 /nobreak >nul & start http://localhost:8000"
"%VPY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
echo.
echo Le serveur s'est arrete. Lisez les messages ci-dessus en cas d'erreur.
pause
exit /b 0

:nobackend
echo [ERREUR] Dossier "backend" introuvable.
echo Extrayez d'abord le zip completement, puis lancez run.bat depuis le dossier extrait.
pause
exit /b 1

:nopython
echo [ERREUR] Python est introuvable.
echo Installez Python 3.10 ou plus depuis https://www.python.org/downloads/
echo et cochez "Add python.exe to PATH" pendant l'installation.
pause
exit /b 1

:fail
echo.
echo [ERREUR] Une etape a echoue. Copiez le message ci-dessus pour obtenir de l'aide.
pause
exit /b 1
