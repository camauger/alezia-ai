# Alignement d'Alezia AI — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapser les dualités d'Alezia AI (config, base de données, services morts, fichiers parasites) vers un chemin unique, en préservant les données riches et en réparant le chat cassé.

**Architecture:** Une seule config (`backend/config.py` pilotée par `.env`), une seule base SQLAlchemy (`data/alezia.db`), un seul paradigme d'accès (ORM, `db_manager`/`schema.sql` supprimés), un seul lanceur (`run_api.py`). Le chat repart à zéro sur des modèles ORM propres.

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy, SQLite, python-decouple, pytest, ruff.

**Branche :** `align/alezia-sandbox`. **Spec :** `docs/superpowers/specs/2026-05-30-alignement-alezia-design.md`.

**Prérequis exécution :** travailler depuis la racine du projet, environnement virtuel activé. Lancer les vérifications d'app avec `python run_api.py` (Ctrl+C pour arrêter).

---

## Task 1 : Config unique + mode mock bruyant

Fusionner le pilotage `.env` du `config.py` racine dans `backend/config.py` pour que `llm_service` trouve les clés qu'il lit (`api_url`, `default_model`, `mock_mode`, `temperature`, `max_tokens`), rendre le mode mock visible, et supprimer le `config.py` racine mort.

**Files:**
- Modify: `backend/config.py`
- Delete: `config.py` (racine)
- Test: `tests/test_config_alignment.py`

- [ ] **Step 1 : Écrire le test qui échoue**

Créer `tests/test_config_alignment.py` :

```python
"""Vérifie que la config unique expose les clés attendues par llm_service."""

from backend import config


def test_llm_config_has_keys_read_by_llm_service():
    # llm_service lit ces clés via LLM_CONFIG.get(...)
    for key in ("api_url", "default_model", "mock_mode", "temperature", "max_tokens"):
        assert key in config.LLM_CONFIG, f"Clé manquante dans LLM_CONFIG: {key}"


def test_llm_mock_mode_defaults_to_false():
    # Honnêteté : par défaut on tente le vrai LLM, pas le mock silencieux.
    assert config.LLM_CONFIG["mock_mode"] is False


def test_root_config_is_gone():
    import importlib.util
    from pathlib import Path

    root_config = Path(__file__).resolve().parent.parent / "config.py"
    assert not root_config.exists(), "Le config.py racine doit être supprimé"
```

- [ ] **Step 2 : Lancer le test pour vérifier l'échec**

Run: `pytest tests/test_config_alignment.py -v`
Expected: FAIL — `test_llm_config_has_keys_read_by_llm_service` échoue (LLM_CONFIG actuel a `model_name`/`ollama_base_url`, pas `api_url`/`mock_mode`).

- [ ] **Step 3 : Réécrire `LLM_CONFIG` et `EMBEDDING_CONFIG` dans `backend/config.py`**

Dans `backend/config.py`, remplacer le bloc `LLM_CONFIG = {...}` (les clés `model_name`/`fallback_model`/`gpu_settings`/etc.) par une version pilotée par `.env`, et compléter `EMBEDDING_CONFIG` avec `mock_mode` :

```python
# Ollama configuration (clés lues par backend/services/llm_service.py)
LLM_CONFIG = {
    'api_url': config('LLM_API_URL', default='http://localhost:11434/api'),
    'default_model': config('LLM_DEFAULT_MODEL', default='llama3'),
    'mock_mode': config('LLM_MOCK_MODE', default=False, cast=bool),
    'temperature': config('LLM_TEMPERATURE', default=0.7, cast=float),
    'max_tokens': config('LLM_MAX_TOKENS', default=1024, cast=int),
}
```

Et remplacer `EMBEDDING_CONFIG = {...}` par :

```python
# Embeddings configuration
EMBEDDING_CONFIG = {
    'model_name': config('EMBEDDING_MODEL', default='all-MiniLM-L6-v2'),
    'cache_dir': DATA_DIR / 'embeddings',
    'dimensions': config('EMBEDDING_DIMENSIONS', default=384, cast=int),
    'use_gpu': config('EMBEDDING_USE_GPU', default=False, cast=bool),
    'mock_mode': config('EMBEDDING_MOCK_MODE', default=True, cast=bool),
}
```

> Note : `from decouple import config, Csv` est déjà importé en tête de `backend/config.py`. Laisser `API_CONFIG`, `SECURITY_CONFIG`, `SYSTEM_LIMITS` inchangés.

- [ ] **Step 4 : Supprimer le `config.py` racine (mort)**

Run: `git rm config.py`

- [ ] **Step 5 : Rendre le mode mock bruyant au démarrage**

Dans `backend/app.py`, juste après la création du logger (après `configure_http_logging()`), ajouter :

```python
from backend.services.llm_service import llm_service

if llm_service.mock_mode:
    logger.warning(
        "⚠️  MODE MOCK ACTIF — les réponses du LLM sont factices. "
        "Démarrez Ollama et installez un modèle pour des réponses réelles."
    )
else:
    logger.info("LLM réel actif (mode mock désactivé).")
```

- [ ] **Step 6 : Lancer les tests pour vérifier le succès**

Run: `pytest tests/test_config_alignment.py -v`
Expected: PASS (3 tests).

- [ ] **Step 7 : Vérifier que l'app démarre**

Run: `python run_api.py` (puis Ctrl+C)
Expected: démarrage sans erreur d'import ; si Ollama absent, le log `⚠️ MODE MOCK ACTIF` apparaît.

- [ ] **Step 8 : Commit**

```bash
git add backend/config.py backend/app.py tests/test_config_alignment.py
git commit -m "refactor: config unique pilotée par .env + mode mock bruyant"
```

---

## Task 2 : Modèles ORM chat propres

Redéfinir `ChatSessionModel` / `MessageModel` dans `backend/models/chat.py` avec le schéma dont `chat_service` a besoin (id UUID en `String`, `context`/`active`/`sender`/`metadata`), pour préserver le contrat d'API basé sur des `session_id: str`.

**Files:**
- Modify: `backend/models/chat.py:111-159` (bloc SQLAlchemy + alias)
- Test: `tests/test_chat_models.py`

- [ ] **Step 1 : Écrire le test qui échoue**

Créer `tests/test_chat_models.py` :

```python
"""Round-trip ORM des modèles de chat sur une base SQLite en mémoire."""

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models.chat import ChatSessionModel, MessageModel


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_chat_session_uses_string_uuid_id():
    db = _session()
    sid = str(uuid.uuid4())
    db.add(ChatSessionModel(id=sid, user_id="u1", character_id=1, active=True))
    db.commit()
    row = db.query(ChatSessionModel).filter_by(id=sid).first()
    assert row is not None
    assert row.id == sid
    assert row.active is True


def test_message_links_to_session():
    db = _session()
    sid = str(uuid.uuid4())
    mid = str(uuid.uuid4())
    db.add(ChatSessionModel(id=sid, user_id="u1", character_id=1))
    db.add(MessageModel(id=mid, session_id=sid, sender="user", content="bonjour"))
    db.commit()
    msg = db.query(MessageModel).filter_by(id=mid).first()
    assert msg.session_id == sid
    assert msg.sender == "user"
    assert msg.content == "bonjour"
```

- [ ] **Step 2 : Lancer le test pour vérifier l'échec**

Run: `pytest tests/test_chat_models.py -v`
Expected: FAIL — le `ChatSessionModel` actuel a `id` Integer (pas de `active`/`context`), `MessageModel` a `is_user` (pas `sender`).

- [ ] **Step 3 : Remplacer le bloc SQLAlchemy de `backend/models/chat.py`**

Remplacer les classes `ChatSessionModel` et `MessageModel` (lignes ~116-150) par :

```python
class ChatSessionModel(Base):
    """Modèle SQLAlchemy pour les sessions de chat (id UUID en String)."""

    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, nullable=False, default="default_user")
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    context = Column(Text, nullable=True)  # JSON sérialisé

    character = relationship("CharacterModel")
    messages = relationship(
        "MessageModel", back_populates="session", cascade="all, delete-orphan"
    )


class MessageModel(Base):
    """Modèle SQLAlchemy pour les messages de chat (id UUID en String)."""

    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True)  # UUID
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    sender = Column(String, nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    character_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    message_metadata = Column(Text, nullable=True)  # JSON sérialisé

    session = relationship("ChatSessionModel", back_populates="messages")
```

> Les imports en tête de `chat.py` incluent déjà `Boolean, Column, DateTime, ForeignKey, Integer, String, Text` et `relationship`. Conserver l'alias `Message = ChatMessage` en fin de fichier.

- [ ] **Step 4 : Lancer les tests pour vérifier le succès**

Run: `pytest tests/test_chat_models.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5 : Commit**

```bash
git add backend/models/chat.py tests/test_chat_models.py
git commit -m "refactor: modèles ORM chat propres (id UUID, sender, context, active)"
```

---

## Task 3 : Réécriture de `chat_service` sur l'ORM

Remplacer entièrement `backend/services/chat_service.py` par une implémentation ORM qui préserve la surface publique utilisée par les routes (`create_session`, `get_session`, `get_user_sessions`, `send_message`, `get_session_messages`, `delete_session`) et passe correctement `db` à `memory_manager` et `character_manager` (corrige les bugs latents). Les méthodes inutilisées `add_message` / `generate_response` sont supprimées (YAGNI).

**Files:**
- Replace: `backend/services/chat_service.py`
- Test: `tests/test_chat_service.py`

- [ ] **Step 1 : Écrire le test qui échoue**

Créer `tests/test_chat_service.py`. Le test s'exécute sur une **base temporaire isolée** (monkeypatch de `SessionLocal`) pour ne pas polluer `data/alezia.db` :

```python
"""Round-trip du service de chat sur une base temporaire isolée."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models.character import CharacterModel


@pytest.fixture
def chat_service_isolated(tmp_path, monkeypatch):
    # Importer chat_service AVANT create_all : son import enregistre les
    # modèles ORM du chat (chat_sessions/chat_messages) dans Base.metadata.
    import backend.services.chat_service as cs
    from backend import models  # noqa: F401  (enregistre les autres tables)

    db_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    test_sessionmaker = sessionmaker(bind=engine)

    seed = test_sessionmaker()
    seed.add(
        CharacterModel(id=999, name="Testeur", description="d", personality="p")
    )
    seed.commit()
    seed.close()

    # Router toutes les sessions de chat_service vers la base temporaire.
    monkeypatch.setattr(cs, "SessionLocal", test_sessionmaker)
    return cs.chat_service


def test_create_session_and_send_message_roundtrip(chat_service_isolated):
    chat = chat_service_isolated

    session = chat.create_session(user_id="u1", character_id=999, context=None)
    assert isinstance(session["id"], str)

    response = chat.send_message(
        session_id=session["id"], user_input="Bonjour", metadata=None
    )
    assert response["sender"] == "assistant"
    assert response["content"]

    messages = chat.get_session_messages(session["id"])
    senders = [m["sender"] for m in messages]
    assert "user" in senders and "assistant" in senders
```

- [ ] **Step 2 : Lancer le test pour vérifier l'échec**

Run: `pytest tests/test_chat_service.py -v`
Expected: FAIL — `chat_service` actuel utilise `db_manager` et appelle `memory_manager` sans `db` (erreur).

- [ ] **Step 3 : Remplacer intégralement `backend/services/chat_service.py`**

```python
"""
Service de gestion des sessions de chat et intégration LLM (ORM SQLAlchemy).
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Optional

from backend.database import SessionLocal
from backend.models.chat import ChatSessionModel, MessageModel
from backend.models.memory import MemoryCreate
from backend.services.character_manager import CharacterManager
from backend.services.llm_service import llm_service
from backend.services.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ChatService:
    """Gère les sessions de chat et la génération de réponses via le LLM."""

    def __init__(self):
        self.character_manager = CharacterManager()
        self.memory_manager = MemoryManager()

    @staticmethod
    def _session_to_dict(s: ChatSessionModel) -> dict[str, Any]:
        return {
            "id": s.id,
            "user_id": s.user_id,
            "character_id": s.character_id,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "active": s.active,
            "context": json.loads(s.context) if s.context else {},
        }

    @staticmethod
    def _message_to_dict(m: MessageModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "session_id": m.session_id,
            "sender": m.sender,
            "content": m.content,
            "character_id": m.character_id,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "metadata": json.loads(m.message_metadata) if m.message_metadata else None,
        }

    def create_session(
        self, user_id: str, character_id: int, context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        db = SessionLocal()
        try:
            character = self.character_manager.get_character(db, character_id)
            if not character:
                raise ValueError(f"Character {character_id} not found")

            session = ChatSessionModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                character_id=character_id,
                active=True,
                context=json.dumps(context or {}),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return self._session_to_dict(session)
        finally:
            db.close()

    def get_session(self, session_id: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            session = (
                db.query(ChatSessionModel).filter_by(id=session_id).first()
            )
            if not session:
                raise ValueError(f"Session {session_id} not found")
            return self._session_to_dict(session)
        finally:
            db.close()

    def get_user_sessions(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            sessions = (
                db.query(ChatSessionModel)
                .filter_by(user_id=user_id)
                .order_by(ChatSessionModel.updated_at.desc())
                .limit(limit)
                .all()
            )
            return [self._session_to_dict(s) for s in sessions]
        finally:
            db.close()

    def get_session_messages(
        self, session_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        db = SessionLocal()
        try:
            messages = (
                db.query(MessageModel)
                .filter_by(session_id=session_id)
                .order_by(MessageModel.timestamp.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [self._message_to_dict(m) for m in messages]
        finally:
            db.close()

    def delete_session(self, session_id: str) -> bool:
        db = SessionLocal()
        try:
            session = db.query(ChatSessionModel).filter_by(id=session_id).first()
            if not session:
                return False
            db.delete(session)  # cascade supprime les messages
            db.commit()
            return True
        finally:
            db.close()

    def _build_prompt(
        self, db, session_dict: dict[str, Any], character_id: int, user_input: str
    ) -> str:
        context = session_dict.get("context", {}) or {}
        character_profile = context.get("character_profile", "")

        recent = self.get_session_messages(session_dict["id"], limit=10)
        prompt = f"# CHARACTER PROFILE:\n{character_profile}\n\n# CONVERSATION:\n"
        for msg in recent:
            sender = "User" if msg["sender"] == "user" else "Assistant"
            prompt += f"{sender}: {msg['content']}\n"
        prompt += f"User: {user_input}\nAssistant: "
        return prompt

    def send_message(
        self,
        session_id: str,
        user_input: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        db = SessionLocal()
        try:
            session = db.query(ChatSessionModel).filter_by(id=session_id).first()
            if not session:
                raise ValueError(f"Session {session_id} not found")
            character_id = session.character_id

            # Message utilisateur
            db.add(
                MessageModel(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    sender="user",
                    content=user_input,
                    character_id=character_id,
                    message_metadata=json.dumps(metadata) if metadata else None,
                )
            )
            session.updated_at = datetime.now()
            db.commit()

            # Contexte mémoire (db passé correctement — corrige le bug latent)
            relevant = self.memory_manager.get_relevant_memories(
                db, character_id, user_input
            )
            session_dict = self._session_to_dict(session)
            session_dict.setdefault("context", {})["relevant_memories"] = [
                m.dict() for m in relevant
            ]

            prompt = self._build_prompt(db, session_dict, character_id, user_input)
            system_prompt = session_dict["context"].get(
                "system_instructions", "You are a conversational AI assistant."
            )

            start = time.time()
            response_text = llm_service.generate_text(
                prompt=prompt, system_prompt=system_prompt
            )
            generation_time = time.time() - start

            assistant_meta = {
                "generation_time": generation_time,
                "model": llm_service.default_model,
            }
            assistant_id = str(uuid.uuid4())
            db.add(
                MessageModel(
                    id=assistant_id,
                    session_id=session_id,
                    sender="assistant",
                    content=response_text,
                    character_id=character_id,
                    message_metadata=json.dumps(assistant_meta),
                )
            )
            session.updated_at = datetime.now()
            db.commit()

            # Mémoire de la conversation (db passé correctement)
            self.memory_manager.create_memory(
                db,
                MemoryCreate(
                    character_id=character_id,
                    content=f"User: {user_input}\n{response_text}",
                    memory_type="conversation",
                    importance=1.0,
                ),
            )

            # Évolution des traits à partir de l'échange utilisateur
            try:
                self.character_manager.update_traits_from_interaction(
                    db, character_id, user_input, intensity=1.0
                )
            except Exception as e:
                logger.error(f"Erreur évolution des traits: {e}")

            return {
                "id": assistant_id,
                "session_id": session_id,
                "character_id": character_id,
                "content": response_text,
                "sender": "assistant",
                "timestamp": datetime.now().isoformat(),
                "metadata": assistant_meta,
            }
        finally:
            db.close()


# Instance globale du service de chat
chat_service = ChatService()
```

- [ ] **Step 4 : Lancer le test pour vérifier le succès**

Run: `pytest tests/test_chat_service.py -v`
Expected: PASS. (Le LLM est en mock si Ollama absent — le test n'exige qu'un contenu non vide.)

> Si `MemoryCreate` n'accepte pas `memory_type`/`importance` tels quels, lire `backend/models/memory.py` et ajuster les noms de champs — ne pas inventer.

- [ ] **Step 5 : Commit**

```bash
git add backend/services/chat_service.py tests/test_chat_service.py
git commit -m "refactor: chat_service sur ORM SQLAlchemy + correction des appels db manquants"
```

---

## Task 4 : Base unique + suppression de `db_manager`

Basculer toute la persistance sur la base SQLAlchemy unique `data/alezia.db`, initialiser via l'ORM, et retirer `db_manager` / `schema.sql`.

**Files:**
- Modify: `backend/config.py` (DB_PATH)
- Modify: `init_db.py` (réécriture ORM)
- Modify: `run_api.py:59-85` (initialize_database via ORM)
- Modify: `backend/routes/system.py` (check-database via ORM)
- Delete: `backend/utils/db.py`, `backend/utils/schema.sql`
- Test: vérification manuelle (smoke) — pas de test unitaire dédié

- [ ] **Step 1 : Sauvegarder la base riche**

```bash
cp "data/jdr_database.sqlite" "data/jdr_database.sqlite.bak"
```

- [ ] **Step 2 : Réécrire `init_db.py` pour l'ORM**

Remplacer intégralement `init_db.py` :

```python
"""
Initialisation de la base de données Alezia AI (ORM SQLAlchemy).
Crée les tables et ajoute un univers par défaut si absent.
"""

import datetime

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
```

> Vérifier les champs réels de `UniverseModel` dans `backend/models/universe.py` (notamment que `created_at` est bien un `DateTime`) et ajuster si nécessaire — ne pas inventer de colonnes.

- [ ] **Step 3 : Réécrire `initialize_database()` dans `run_api.py`**

Remplacer la fonction `initialize_database()` (lignes ~59-85) par :

```python
def initialize_database():
    """Initialise la base de données via l'ORM et un univers par défaut."""
    try:
        import datetime

        from backend import models  # noqa: F401  (peuple Base.metadata)
        from backend.database import Base, SessionLocal, engine
        from backend.models.universe import UniverseModel

        Base.metadata.create_all(bind=engine)

        db = SessionLocal()
        try:
            if db.query(UniverseModel).count() == 0:
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
                print("Univers par défaut initialisé.")
            from backend.models.character import CharacterModel

            print(f"Personnages en base: {db.query(CharacterModel).count()}")
        finally:
            db.close()
        return True
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False
```

- [ ] **Step 4 : Réécrire `check-database` dans `backend/routes/system.py`**

Remplacer le contenu de `backend/routes/system.py` par :

```python
"""
Routes for system functions
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import inspect

from backend.database import engine
from backend.services.llm_service import llm_service

router = APIRouter(prefix='/system', tags=['system'])


@router.get('/check-database', response_model=dict[str, Any])
async def check_database():
    """Checks the database status via SQLAlchemy."""
    try:
        tables = inspect(engine).get_table_names()
        return {'status': 'ok', 'tables': tables, 'database_path': str(engine.url)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Database error: {str(e)}')


@router.get('/check-llm', response_model=dict[str, Any])
async def check_llm():
    """Checks the LLM service status"""
    try:
        status = llm_service.check_model_availability()
        return {'status': 'ok' if status else 'error'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'LLM service error: {str(e)}')
```

- [ ] **Step 5 : Basculer le fichier de base et pointer `DB_PATH`**

Renommer la base riche en `alezia.db` et supprimer l'ancienne base brute vide :

```bash
rm -f data/alezia.db data/alezia.db-shm data/alezia.db-wal
mv "data/jdr_database.sqlite" "data/alezia.db"
```

Dans `backend/config.py`, changer la ligne `DB_PATH` :

```python
DB_PATH = DATA_DIR / 'alezia.db'
```

- [ ] **Step 6 : Supprimer `db_manager` et `schema.sql`**

```bash
git rm backend/utils/db.py backend/utils/schema.sql
```

- [ ] **Step 7 : Vérifier qu'aucun import résiduel ne référence `db_manager`**

Run: `grep -rn "utils.db\|db_manager\|schema.sql" backend run_api.py init_db.py`
Expected: aucune occurrence (hors fichiers `backend/test_*.py` qui seront déplacés/nettoyés en Task 6). Si une occurrence vivante reste, la corriger avant de continuer.

- [ ] **Step 8 : Vérification smoke — données préservées + chat fonctionnel**

Run: `python run_api.py` puis dans un autre terminal :
```bash
curl http://localhost:8000/api/characters
curl http://localhost:8000/api/system/check-database
```
Expected: la liste des 8 personnages s'affiche ; `check-database` liste les tables (dont `chat_sessions`, `chat_messages`, `characters`). Arrêter avec Ctrl+C.

- [ ] **Step 9 : Commit**

```bash
git add backend/config.py init_db.py run_api.py backend/routes/system.py
git commit -m "refactor: base unique alezia.db via ORM, suppression de db_manager/schema.sql"
```

---

## Task 5 : Supprimer les services morts

Retirer `chat_manager` et `universe_manager` (seulement ré-exportés, jamais utilisés par une route ni un service vivant).

**Files:**
- Delete: `backend/services/chat_manager.py`, `backend/services/universe_manager.py`
- Modify: `backend/services/__init__.py`

- [ ] **Step 1 : Re-confirmer l'absence d'usage vivant**

Run: `grep -rn "chat_manager\|universe_manager" backend run_api.py init_db.py | grep -v "services/__init__.py\|services/chat_manager.py\|services/universe_manager.py"`
Expected: aucune occurrence. Si une occurrence vivante apparaît, NE PAS supprimer — traiter d'abord cette dépendance.

- [ ] **Step 2 : Supprimer les deux fichiers**

```bash
git rm backend/services/chat_manager.py backend/services/universe_manager.py
```

- [ ] **Step 3 : Nettoyer `backend/services/__init__.py`**

Remplacer le contenu par :

```python
"""
Package des services pour l'application Alezia AI
"""

from .character_manager import character_manager
from .llm_service import llm_service
from .memory_manager import memory_manager

__all__ = [
    'character_manager',
    'memory_manager',
    'llm_service',
]
```

- [ ] **Step 4 : Vérifier l'import du package services**

Run: `python -c "import backend.services; print(backend.services.__all__)"`
Expected: `['character_manager', 'memory_manager', 'llm_service']` sans erreur d'import.

- [ ] **Step 5 : Commit**

```bash
git add backend/services/__init__.py
git commit -m "refactor: suppression des services morts chat_manager et universe_manager"
```

---

## Task 6 : Nettoyage des parasites + requirements

Supprimer les lanceurs/fichiers morts, réparer `requirements.txt`, regrouper les tests éparpillés, supprimer les `.db` orphelins.

**Files:**
- Delete: `start.bat`, `start.ps1`, `start_api.bat`, `start_api.ps1`, `start_api_basic.py`, `start_api_noreload.py`, `start_api_simple.py`, `start_api_verbose.py`, `backend_api.py`, `api_test.py`, `check_api_health.py`, `Modelfile`
- Modify: `requirements.txt`
- Move: `backend/test_*.py` → `tests/`
- Delete: `.db` orphelins (`data/alezia-TELUQ-*`, `data/jdr_database.sqlite.bak` après validation finale)

- [ ] **Step 1 : Supprimer les lanceurs et fichiers morts (confirmés inutilisés)**

```bash
git rm start.bat start.ps1 start_api.bat start_api.ps1 \
  start_api_basic.py start_api_noreload.py start_api_simple.py start_api_verbose.py \
  backend_api.py api_test.py check_api_health.py Modelfile
```

- [ ] **Step 2 : Réparer `requirements.txt`**

Remplacer le contenu de `requirements.txt` par :

```
fastapi
uvicorn
sqlalchemy
python-decouple
requests
numpy
sentence-transformers
pytest
ruff
```

- [ ] **Step 3 : Regrouper les tests du backend dans `tests/`**

Déplacer les scripts de test éparpillés (qui référençaient `db_manager`) vers `tests/`, en les renommant pour éviter les collisions :

```bash
git mv backend/test_api.py tests/test_api.py
git mv backend/test_db_connection.py tests/test_db_connection.py
git mv backend/test_memory_importance.py tests/test_memory_importance.py
git mv backend/test_trait_evolution.py tests/test_trait_evolution.py
```

> Ces fichiers peuvent référencer `backend.utils.db` (supprimé). À ce stade ce sont des scripts manuels, pas des tests pytest valides. Si l'un casse la collecte pytest, ajouter `pytest.importorskip` ou le marquer obsolète en tête — ne pas le réparer en profondeur (hors scope). L'objectif ici est le rangement, pas la réhabilitation.

- [ ] **Step 4 : Supprimer les `.db` orphelins**

```bash
rm -f data/alezia-TELUQ-*.db-shm data/alezia-TELUQ-*.db-wal data/alezia-TELUQ-*.db
```

- [ ] **Step 5 : Vérifier la collecte pytest et le lint**

Run: `pytest -q` puis `ruff check backend tests`
Expected: les tests d'alignement (config, chat_models, chat_service) passent ; `ruff check` sans erreur bloquante. Corriger tout import cassé restant signalé par la collecte.

- [ ] **Step 6 : Vérifier le démarrage final**

Run: `python run_api.py` (puis Ctrl+C)
Expected: démarrage propre, un seul chemin, données présentes.

- [ ] **Step 7 : Commit**

```bash
git add -A
git commit -m "chore: suppression des parasites, requirements réparé, tests regroupés"
```

---

## Task 7 : Mettre à jour `CLAUDE.md`

Refléter le projet aligné : une seule config, une seule base SQLAlchemy, services vivants, chat ORM.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1 : Mettre à jour la section « Pièges critiques »**

Dans `CLAUDE.md`, remplacer les pièges désormais obsolètes (deux config.py, deux paradigmes BD, mode mock silencieux, doublons de services) par l'état aligné :

```markdown
## Architecture (état aligné)

- **Config unique** : `backend/config.py`, pilotée par `.env` (python-decouple). Le `config.py` racine a été supprimé.
- **Base unique** : `data/alezia.db`, accès exclusivement via SQLAlchemy (`backend/database.py` → `SessionLocal`/`Base`). `db_manager` (sqlite3 brut) et `schema.sql` ont été supprimés. Initialisation via `Base.metadata.create_all`.
- **Mode mock LLM bruyant** : défaut `LLM_MOCK_MODE=False` ; un avertissement explicite est loggé au démarrage si Ollama est absent.
- **Services** : routes → `character_manager` (façade sur `character_service`, `character_state_service`, `personality_service`, `relationship_service`), `chat_service`, `memory_manager`, `llm_service`. `chat_manager` et `universe_manager` ont été supprimés.
- **Chat** : modèles ORM `ChatSessionModel`/`MessageModel` (`backend/models/chat.py`, id UUID en String). L'historique de chat antérieur (tables legacy `sessions`/`messages`) n'est pas utilisé.
- **Lanceur unique** : `python run_api.py`.

> Note : `README.md`, `GEMINI.md` et `.cursor/rules/` sont historiques et peuvent décrire l'ancien état (chemins sans `/api`, flake8/black, deux bases). Se fier au code et à ce fichier.
```

- [ ] **Step 2 : Vérifier la cohérence**

Relire `CLAUDE.md` : aucune mention restante de « deux config.py », « jdr_database.sqlite » comme base active, ou des services supprimés comme vivants.

- [ ] **Step 3 : Commit**

```bash
git add CLAUDE.md
git commit -m "docs: CLAUDE.md reflète le projet aligné"
```

---

## Vérification finale (après toutes les tâches)

- [ ] `pytest -q` : les tests d'alignement passent.
- [ ] `ruff check backend tests` : propre.
- [ ] `python run_api.py` : démarre, 8 personnages présents (`/api/characters`), création de session + envoi de message persistent (`/api/chat/create` puis `/api/chat/message`).
- [ ] Un seul `config.py`, un seul `.db` actif (`data/alezia.db`), un seul lanceur (`run_api.py`).
- [ ] Après validation : supprimer la sauvegarde `data/jdr_database.sqlite.bak`.
