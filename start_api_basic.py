"""
Script basique pour vérifier le fonctionnement de l'API FastAPI
"""

from fastapi import FastAPI
import uvicorn

# Créer une application FastAPI simplifiée
app = FastAPI(
    title="Alezia AI - API Test",
    description="Version minimale pour tester le démarrage de l'API",
    version="0.1.0"
)

# Route de base


@app.get("/")
async def root():
    return {"message": "API Alezia AI - Version de test"}

# Route health check


@app.get("/health")
async def health_check():
    return {"status": "healthy", "api": "online"}

# Point d'entrée
if __name__ == "__main__":
    port = 8007
    host = "127.0.0.1"  # Utiliser localhost au lieu de 0.0.0.0
    print(f"Démarrage de l'API simplifiée sur http://{host}:{port}/")

    # Ecrire le port dans un fichier pour le frontend
    with open("api_port.txt", "w") as f:
        f.write(str(port))

    # Démarrer l'API
    uvicorn.run(
        "start_api_basic:app",
        host=host,
        port=port,
        reload=False
    )
