Write-Host "Test de l'API Alezia..." -ForegroundColor Green

$apiUrl = "http://localhost:8000"

# Test de la route principale
try {
    Write-Host "Test de la route principale..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri "$apiUrl" -Method Get
    Write-Host "Réponse: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "Erreur: $_" -ForegroundColor Red
}

# Test de création de personnage
try {
    Write-Host "Test de création de personnage..." -ForegroundColor Cyan

    $character = @{
        name = "Test Character"
        description = "A test character"
        personality = "Friendly"
    }

    $jsonBody = $character | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$apiUrl/characters/" -Method Post -Body $jsonBody -ContentType "application/json"
    Write-Host "Réponse: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "Erreur: $_" -ForegroundColor Red
}

Write-Host "Tests terminés" -ForegroundColor Green