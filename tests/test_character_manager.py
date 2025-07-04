"""
Tests unitaires pour le gestionnaire de personnages
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app import app
from backend.database import Base, get_db

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Setup the test database
SQLALCHEMY_DATABASE_URL = 'sqlite:///./test.db'
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def db_session():
    """Fixture for the database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_character(db_session):
    """Test de la création d'un personnage"""
    response = client.post(
        '/characters/',
        json={
            'name': 'Test Character',
            'description': 'A test character',
            'personality': 'Friendly',
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data['message'] == 'Character created successfully'
    assert 'id' in data


def test_get_character(db_session):
    """Test de la récupération d'un personnage"""
    response = client.post(
        '/characters/',
        json={
            'name': 'Test Character',
            'description': 'A test character',
            'personality': 'Friendly',
        },
    )
    character_id = response.json()['id']

    response = client.get(f'/characters/{character_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == 'Test Character'


if __name__ == '__main__':
    pytest.main()
