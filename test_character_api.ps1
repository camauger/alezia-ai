Write-Host "Test de création de personnage..." -ForegroundColor Green

# Demander le port à utiliser ou prendre la valeur par défaut
$port = Read-Host "Entrez le port de l'API (laissez vide pour 8000)"
if ([string]::IsNullOrWhiteSpace($port)) {
    $port = 8000
}

$characterData = @{
    name = "Test Character"
    description = "Un personnage de test pour vérifier l'API"
    personality = "Amical et serviable"
}

$jsonBody = $characterData | ConvertTo-Json

Write-Host "Envoi de la requête à http://localhost:$port/characters/..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:$port/characters/" -Method Post -Body $jsonBody -ContentType "application/json"

    Write-Host "Personnage créé avec succès!" -ForegroundColor Green
    Write-Host "ID du personnage: $($response.id)" -ForegroundColor Green
    Write-Host "Message: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "Erreur lors de la création du personnage:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.Exception.Response) {
        $responseBody = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($responseBody)
        $responseContent = $reader.ReadToEnd()
        Write-Host "Détails de l'erreur: $responseContent" -ForegroundColor Red
    }
}