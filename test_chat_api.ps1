#!/usr/bin/env pwsh
# Script de test pour les fonctionnalités de chat de l'API Alezia

$ApiBaseUrl = "http://localhost:8001"

# Fonction pour faire des requêtes à l'API
function Invoke-AleziaApiRequest {
    param(
        [string]$Method = "GET",
        [string]$Endpoint,
        [object]$Body = $null
    )

    $Uri = "$ApiBaseUrl$Endpoint"
    $Headers = @{"Content-Type" = "application/json"}

    if ($Body) {
        $JsonBody = $Body | ConvertTo-Json
        $Response = Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body $JsonBody -ErrorAction Stop
    } else {
        $Response = Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -ErrorAction Stop
    }

    return $Response
}

Write-Host "=== Test de l'API de chat ===" -ForegroundColor Cyan

# Vérifier que l'API est en ligne
try {
    $HealthResponse = Invoke-AleziaApiRequest -Endpoint "/health"
    Write-Host "API en ligne: $($HealthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "Erreur: API inaccessible. Assurez-vous que le serveur est en cours d'exécution." -ForegroundColor Red
    exit 1
}

# Récupérer un personnage pour les tests
try {
    $Characters = Invoke-AleziaApiRequest -Endpoint "/characters"

    if ($Characters.Count -eq 0) {
        Write-Host "Erreur: Aucun personnage disponible pour les tests. Créez-en un d'abord." -ForegroundColor Red
        exit 1
    }

    $TestCharacter = $Characters[0]
    Write-Host "Personnage de test: $($TestCharacter.name) (ID: $($TestCharacter.id))" -ForegroundColor Green
} catch {
    Write-Host "Erreur lors de la récupération des personnages: $_" -ForegroundColor Red
    exit 1
}

# 1. Créer une session
try {
    Write-Host "`nCréation d'une session de chat..." -ForegroundColor Yellow
    $SessionBody = @{
        character_id = $TestCharacter.id
    }
    $Session = Invoke-AleziaApiRequest -Method "POST" -Endpoint "/chat/session" -Body $SessionBody
    Write-Host "Session créée avec ID: $($Session.id)" -ForegroundColor Green
} catch {
    Write-Host "Erreur lors de la création de la session: $_" -ForegroundColor Red
    exit 1
}

# 2. Envoyer un message
try {
    Write-Host "`nEnvoi d'un message de test..." -ForegroundColor Yellow
    $MessageBody = @{
        content = "Bonjour, comment vas-tu aujourd'hui?"
    }
    $Response = Invoke-AleziaApiRequest -Method "POST" -Endpoint "/chat/$($Session.id)/message" -Body $MessageBody
    Write-Host "Message envoyé avec succès." -ForegroundColor Green
    Write-Host "Réponse du personnage: $($Response.content)" -ForegroundColor Cyan
} catch {
    Write-Host "Erreur lors de l'envoi du message: $_" -ForegroundColor Red
}

# 3. Récupérer l'historique de la session
try {
    Write-Host "`nRécupération de l'historique de la session..." -ForegroundColor Yellow
    $History = Invoke-AleziaApiRequest -Endpoint "/chat/$($Session.id)/history"
    Write-Host "Historique récupéré: $($History.messages.Count) messages" -ForegroundColor Green

    # Afficher les messages
    foreach ($message in $History.messages) {
        $Sender = if ($message.is_user) {"Utilisateur"} else {"Personnage"}
        Write-Host "$Sender : $($message.content)" -ForegroundColor $(if ($message.is_user) {"White"} else {"Cyan"})
    }
} catch {
    Write-Host "Erreur lors de la récupération de l'historique: $_" -ForegroundColor Red
}

# 4. Terminer la session
try {
    Write-Host "`nFin de la session..." -ForegroundColor Yellow
    $EndResponse = Invoke-AleziaApiRequest -Method "POST" -Endpoint "/chat/$($Session.id)/end"
    Write-Host "Session terminée avec succès: $($EndResponse.success)" -ForegroundColor Green
} catch {
    Write-Host "Erreur lors de la fin de la session: $_" -ForegroundColor Red
}

Write-Host "`n=== Tests terminés ===" -ForegroundColor Cyan