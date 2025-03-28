"""
Script de test API minimal
"""

from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel

# Modèle simple pour un personnage
class CharacterCreate(BaseModel):
    name: str
    description: str
    personality: str

app = FastAPI(title="API Test Alezia")

# Route de base
@app.get("/")
async def root():
    return {"message": "API Test fonctionne!"}

# Route pour créer un personnage
@app.post("/characters/", response_model=dict)
async def create_character(character: CharacterCreate):
    try:
        # Simulation de création
        return {"id": 1, "message": f"Personnage '{character.name}' créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("api_test:app", host="0.0.0.0", port=8000)