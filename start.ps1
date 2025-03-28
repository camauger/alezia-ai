# Alezia AI - Script de démarrage PowerShell
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "             ALEZIA AI - Démarrage                    " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si Python est installé
try {
    $pythonVersion = python --version
    Write-Host "Python détecté: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Erreur: Python n'est pas installé ou n'est pas dans le PATH." -ForegroundColor Red
    Write-Host "Veuillez installer Python 3.8 ou supérieur." -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter"
    exit
}

# Vérifier si Ollama est installé
$ollamaPath = "C:\Users\camauger\AppData\Local\Programs\Ollama\ollama.exe"
if (Test-Path $ollamaPath) {
    Write-Host "Vérification d'Ollama..." -ForegroundColor Yellow
    try {
        & $ollamaPath list | Out-Null
    } catch {
        Write-Host "Attention: Assurez-vous qu'Ollama est en cours d'exécution!" -ForegroundColor Yellow
        $startOllama = Read-Host "Voulez-vous démarrer Ollama maintenant? (O/N)"
        if ($startOllama -eq "O" -or $startOllama -eq "o") {
            Write-Host "Démarrage d'Ollama..." -ForegroundColor Green
            Start-Process -FilePath "C:\Users\camauger\AppData\Local\Programs\Ollama\ollama app.exe"
            Write-Host "Attente du démarrage d'Ollama (10 secondes)..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
    }
} else {
    Write-Host "Attention: Ollama n'est pas trouvé à l'emplacement attendu." -ForegroundColor Yellow
    Write-Host "Veuillez installer Ollama depuis https://ollama.com/download" -ForegroundColor Yellow
}

# Créer l'environnement virtuel s'il n'existe pas
if (!(Test-Path "venv")) {
    Write-Host "Création de l'environnement virtuel..." -ForegroundColor Green
    python -m venv venv
    Write-Host "Installation des dépendances..." -ForegroundColor Green
    & .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
} else {
    & .\venv\Scripts\Activate.ps1
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "           DÉMARRAGE DES SERVICES                     " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Démarrer le backend dans une nouvelle fenêtre
Write-Host "Démarrage du backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; python app.py"

# Attendre un peu que le backend démarre
Write-Host "Attente du démarrage du backend (5 secondes)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Démarrer le frontend dans une nouvelle fenêtre
Write-Host "Démarrage du frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; python -m http.server 8080"

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "           ALEZIA AI EST EN COURS D'EXÉCUTION         " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Application démarrée! Pour l'utiliser:" -ForegroundColor Green
Write-Host "- Backend: http://localhost:8000" -ForegroundColor Yellow
Write-Host "- Frontend: http://localhost:8080" -ForegroundColor Yellow
Write-Host ""
Write-Host "Ouvrez votre navigateur à l'adresse http://localhost:8080" -ForegroundColor Green
Write-Host ""
Write-Host "Pour arrêter l'application, fermez les fenêtres PowerShell." -ForegroundColor Yellow
Write-Host ""

# Ouvrir le navigateur avec l'application
Start-Sleep -Seconds 2
Start-Process "http://localhost:8080"

# Garder la fenêtre principale ouverte
Write-Host "Appuyez sur Entrée pour quitter ce script (l'application continuera de fonctionner)"
Read-Host