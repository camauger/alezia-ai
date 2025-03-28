@echo off
echo ======================================================
echo             ALEZIA AI - Demarrage
echo ======================================================
echo.

REM Vérifier si Python est installé
python --version 2>NUL
if errorlevel 1 (
    echo Erreur: Python n'est pas installe ou n'est pas dans le PATH.
    echo Veuillez installer Python 3.8 ou superieur.
    pause
    exit /b
)

REM Vérifier si Ollama est installé
"C:\Users\camauger\AppData\Local\Programs\Ollama\ollama.exe" list >NUL 2>&1
if errorlevel 1 (
    echo Verification d'Ollama...
    echo Attention: Assurez-vous qu'Ollama est en cours d'execution!
    echo Voulez-vous demarrer Ollama maintenant? (O/N)
    set /p startOllama=
    if /i "%startOllama%"=="O" (
        echo Demarrage d'Ollama...
        start "" "C:\Users\camauger\AppData\Local\Programs\Ollama\ollama app.exe"
        echo Attente du demarrage d'Ollama (10 secondes)...
        timeout /t 10 /nobreak >NUL
    )
)

REM Créer l'environnement virtuel s'il n'existe pas
if not exist venv (
    echo Creation de l'environnement virtuel...
    python -m venv venv
    echo Installation des dependances...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo ======================================================
echo           DEMARRAGE DES SERVICES
echo ======================================================
echo.

REM Démarrer le backend dans une nouvelle fenêtre
echo Demarrage du backend...
start "Alezia AI - Backend" cmd /c "cd backend && python app.py"

REM Attendre un peu que le backend démarre
echo Attente du demarrage du backend (5 secondes)...
timeout /t 5 /nobreak >NUL

REM Démarrer le frontend dans une nouvelle fenêtre
echo Demarrage du frontend...
start "Alezia AI - Frontend" cmd /c "cd frontend && python -m http.server 8080"

echo.
echo ======================================================
echo           ALEZIA AI EST EN COURS D'EXECUTION
echo ======================================================
echo.
echo Application demarree! Pour l'utiliser:
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:8080
echo.
echo Ouvrez votre navigateur a l'adresse http://localhost:8080
echo.
echo Pour arreter l'application, fermez les fenetres de commandes.
echo.

REM Ouvrir le navigateur avec l'application
timeout /t 2 /nobreak >NUL
start http://localhost:8080

pause