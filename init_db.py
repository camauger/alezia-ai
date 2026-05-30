"""
Initialisation de la base de données Alezia AI (ORM SQLAlchemy).
Crée les tables et ajoute un univers par défaut si absent.
"""

import datetime

import backend.models.chat  # noqa: F401  (peuple Base.metadata avec les tables chat)

# Import des modèles pour les enregistrer dans Base.metadata
from backend import models  # noqa: F401  (peuple Base.metadata)
from backend.database import Base, SessionLocal, engine
from backend.models.universe import UniverseModel

print("Initialisation de la base de données Alezia AI...")

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    count = db.query(UniverseModel).count()
    if count == 0:
        db.add(
            UniverseModel(
                name="Monde moderne",
                description="Un univers contemporain similaire au monde réel actuel",
                type="réaliste",
                time_period="2024",
                rules="Lois de la physique standards, technologies modernes disponibles",
                created_at=datetime.datetime.now(),
            )
        )
        db.commit()
        print("Univers par défaut créé.")
    else:
        print(f"{count} univers déjà présents. Aucune action nécessaire.")
finally:
    db.close()

print("Initialisation terminée.")
