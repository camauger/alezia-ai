Write-Host "Installation des modèles Ollama pour Alezia AI..." -ForegroundColor Green

# Vérifier si Ollama est en cours d'exécution
$ollamaRunning = $false
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -Method Get -ErrorAction SilentlyContinue
    if ($response) {
        $ollamaRunning = $true
        Write-Host "Ollama détecté: version $($response.version)" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "Ollama n'est pas en cours d'exécution. Veuillez démarrer Ollama d'abord." -ForegroundColor Red
    Write-Host "Téléchargez Ollama depuis: https://ollama.com/download" -ForegroundColor Yellow
    exit 1
}

# Vérifier les modèles disponibles
Write-Host "Vérification des modèles disponibles..." -ForegroundColor Cyan
$models = @()
try {
    $tagsResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get
    $models = $tagsResponse.models | ForEach-Object { $_.name }

    if ($models.Count -eq 0) {
        Write-Host "Aucun modèle trouvé dans Ollama." -ForegroundColor Yellow
    }
    else {
        Write-Host "Modèles déjà installés: $($models -join ', ')" -ForegroundColor Green
    }
}
catch {
    Write-Host "Impossible de récupérer la liste des modèles." -ForegroundColor Red
}

# Installer un modèle compatible
$targetModel = ""
if ($models -contains "llama3") {
    $targetModel = "llama3"
    Write-Host "Le modèle 'llama3' est déjà installé." -ForegroundColor Green
}
elseif ($models -contains "llama3:8b") {
    $targetModel = "llama3:8b"
    Write-Host "Le modèle 'llama3:8b' est déjà installé." -ForegroundColor Green
}
elseif ($models -contains "llama2") {
    $targetModel = "llama2"
    Write-Host "Le modèle 'llama2' est déjà installé." -ForegroundColor Green
}
elseif ($models -contains "gemma:7b") {
    $targetModel = "gemma:7b"
    Write-Host "Le modèle 'gemma:7b' est déjà installé." -ForegroundColor Green
}
elseif ($models -contains "gemma:2b") {
    $targetModel = "gemma:2b"
    Write-Host "Le modèle 'gemma:2b' est déjà installé." -ForegroundColor Green
}
else {
    # Installer un modèle léger par défaut
    $targetModel = "gemma:2b"
    Write-Host "Installation du modèle 'gemma:2b'..." -ForegroundColor Yellow
    Write-Host "Cela peut prendre plusieurs minutes pour le téléchargement initial." -ForegroundColor Yellow

    try {
        Invoke-RestMethod -Uri "http://localhost:11434/api/pull" -Method Post -Body (@{
            name = "gemma:2b"
        } | ConvertTo-Json) -ContentType "application/json"
        Write-Host "Modèle 'gemma:2b' installé avec succès." -ForegroundColor Green
    }
    catch {
        Write-Host "Erreur lors de l'installation du modèle: $_" -ForegroundColor Red
        exit 1
    }
}

# Mettre à jour le fichier de configuration
Write-Host "Mise à jour de la configuration pour utiliser le modèle '$targetModel'..." -ForegroundColor Cyan
$configFile = Join-Path $PSScriptRoot "backend\config.py"

if (Test-Path $configFile) {
    $config = Get-Content $configFile -Raw

    # Remplacer les modèles dans la configuration
    $config = $config -replace '"default_model": "roleplay-uncensored"', "`"default_model`": `"$targetModel`""
    $config = $config -replace '"fallback_model": "llama3:8b-instruct-uncensored"', "`"fallback_model`": `"$targetModel`""

    # Sauvegarder la configuration
    $config | Set-Content $configFile -Encoding UTF8
    Write-Host "Configuration mise à jour avec succès." -ForegroundColor Green
}
else {
    Write-Host "Fichier de configuration non trouvé: $configFile" -ForegroundColor Red
    exit 1
}

Write-Host "Installation terminée. Vous pouvez maintenant démarrer l'API avec 'python run_api.py'." -ForegroundColor Green