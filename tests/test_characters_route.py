"""Smoke test de la route /api/characters (sérialisation ORM -> CharacterSummary).

Régression : un personnage rattaché à un univers faisait échouer la liste
(`CharacterSummary.universe` recevait l'objet ORM UniverseModel au lieu d'un nom).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app import app
from backend.database import Base, get_db
from backend.models.character import CharacterModel
from backend.models.universe import UniverseModel


@pytest.fixture
def client(tmp_path):
    import backend.models.chat  # noqa: F401
    from backend import models  # noqa: F401  (enregistre toutes les tables)

    engine = create_engine(
        f"sqlite:///{tmp_path/'t.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    seed = TestSession()
    univers = UniverseModel(
        name="Monde de test",
        description="Un univers de test",
        type="réaliste",
    )
    seed.add(univers)
    seed.flush()  # pour obtenir univers.id
    seed.add(
        CharacterModel(
            id=1,
            name="Perso avec univers",
            description="Une description suffisamment longue",
            personality="Une personnalité décrite",
            universe_id=univers.id,
        )
    )
    seed.add(
        CharacterModel(
            id=2,
            name="Perso sans univers",
            description="Autre description longue",
            personality="Autre personnalité",
            universe_id=None,
        )
    )
    # Données courtes (legacy) : doivent rester lisibles via le modèle de lecture
    seed.add(
        CharacterModel(
            id=3,
            name="Legacy",
            description="test",
            personality="test",
            universe_id=None,
        )
    )
    seed.commit()
    seed.close()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_characters_serializes_universe_as_name(client):
    r = client.get("/api/characters/")
    assert r.status_code == 200, r.text
    data = r.json()
    by_id = {c["id"]: c for c in data}
    assert len(data) == 3
    # Le personnage rattaché à un univers expose le NOM de l'univers (str), pas l'objet ORM
    assert by_id[1]["universe"] == "Monde de test"
    # Le personnage sans univers expose None
    assert by_id[2]["universe"] is None


def test_get_character_detail_allows_short_legacy_data(client):
    # Le modèle de lecture ne doit pas rejeter une description/personnalité courte
    r = client.get("/api/characters/3")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == 3
    assert body["description"] == "test"
