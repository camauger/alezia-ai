Write-Host "Démarrage de l'API Alezia AI..." -ForegroundColor Green

# Vérification de Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python n'est pas installé ou n'est pas dans le PATH." -ForegroundColor Red
    exit 1
}

# Vérification des dépendances
Write-Host "Vérification des dépendances..." -ForegroundColor Cyan
try {
    python -c "import fastapi, uvicorn; print('OK')" > $null
}
catch {
    Write-Host "Dépendances manquantes. Installation..." -ForegroundColor Yellow
    python -m pip install fastapi uvicorn
}

# Démarrage de l'API avec le script run_api.py amélioré
Write-Host "Démarrage de l'API..." -ForegroundColor Cyan
try {
    python run_api.py
}
catch {
    Write-Host "Erreur lors du démarrage de l'API: $_" -ForegroundColor Red
    exit 1
}