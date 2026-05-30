"""
Smoke tests for /api/memory/* routes.

Uses FastAPI TestClient with an isolated temp SQLite DB via dependency override,
mirroring the pattern used in backend/routes/characters.py tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app import app
from backend.database import Base, get_db
from backend.models.character import CharacterModel  # noqa: F401 – registers table


@pytest.fixture
def client(tmp_path):
    # Import all model modules so every table is registered on Base.metadata
    import backend.models.chat  # noqa: F401
    import backend.models.memory  # noqa: F401
    import backend.models.relationship  # noqa: F401
    import backend.models.universe  # noqa: F401

    db_url = f"sqlite:///{tmp_path / 't.db'}"
    engine = create_engine(db_url, connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    # Seed a character (universe_id nullable, no universe needed)
    seed = TestSession()
    seed.add(
        CharacterModel(
            id=999,
            name='Testeur',
            description='Une description suffisamment longue',
            personality='Personnalité de test',
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


def test_create_then_list_memories(client):
    """POST creates a memory, GET returns it with the right memory_type."""
    payload = {
        'character_id': 999,
        'memory_type': 'conversation',
        'content': 'Une mémoire de test pour le personnage Testeur.',
        'importance': 1.0,
    }
    r = client.post('/api/memory/character/999/memories', json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['success'] is True
    assert isinstance(data['id'], int)

    # List memories
    r2 = client.get('/api/memory/character/999/memories')
    assert r2.status_code == 200, r2.text
    memories = r2.json()
    assert len(memories) >= 1
    assert memories[0]['memory_type'] == 'conversation'
    assert memories[0]['content'] == payload['content']


def test_get_single_memory(client):
    """POST then GET /api/memory/memories/{id} returns the memory."""
    payload = {
        'character_id': 999,
        'memory_type': 'event',
        'content': 'Un événement important est arrivé.',
        'importance': 5.0,
    }
    r = client.post('/api/memory/character/999/memories', json=payload)
    assert r.status_code == 200, r.text
    memory_id = r.json()['id']

    r2 = client.get(f'/api/memory/memories/{memory_id}')
    assert r2.status_code == 200, r2.text
    mem = r2.json()
    assert mem['id'] == memory_id
    assert mem['memory_type'] == 'event'


def test_get_memory_not_found(client):
    """GET on a non-existent memory_id returns 404."""
    r = client.get('/api/memory/memories/99999')
    assert r.status_code == 404


def test_update_importance(client):
    """PUT /importance updates importance and returns success."""
    payload = {
        'character_id': 999,
        'memory_type': 'observation',
        'content': 'Observation banale.',
        'importance': 1.0,
    }
    r = client.post('/api/memory/character/999/memories', json=payload)
    assert r.status_code == 200, r.text
    memory_id = r.json()['id']

    r2 = client.put(
        f'/api/memory/memories/{memory_id}/importance',
        json={'importance': 7.5},
    )
    assert r2.status_code == 200, r2.text
    result = r2.json()
    assert result['success'] is True
    assert result['importance'] == 7.5


def test_delete_memory(client):
    """DELETE removes a memory; subsequent GET returns 404."""
    payload = {
        'character_id': 999,
        'memory_type': 'conversation',
        'content': 'Mémoire à supprimer.',
        'importance': 1.0,
    }
    r = client.post('/api/memory/character/999/memories', json=payload)
    assert r.status_code == 200, r.text
    memory_id = r.json()['id']

    r2 = client.delete(f'/api/memory/memories/{memory_id}')
    assert r2.status_code == 200, r2.text
    assert r2.json()['success'] is True

    r3 = client.get(f'/api/memory/memories/{memory_id}')
    assert r3.status_code == 404


def test_get_facts(client):
    """GET /facts returns a list (possibly empty) without error."""
    r = client.get('/api/memory/character/999/facts')
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_maintenance_cycle(client):
    """POST /maintenance returns success + statistics dict."""
    r = client.post('/api/memory/character/999/maintenance')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['success'] is True
    assert 'statistics' in data


def test_character_id_mismatch(client):
    """POST with mismatched character_id returns 400."""
    payload = {
        'character_id': 1,  # does not match URL character_id=999
        'memory_type': 'conversation',
        'content': 'Test mismatch.',
        'importance': 1.0,
    }
    r = client.post('/api/memory/character/999/memories', json=payload)
    assert r.status_code == 400
