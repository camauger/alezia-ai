# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Alezia AI — système de jeu de rôle avec personnages IA non censurés, propulsé par Ollama en local. Backend FastAPI (Python) + frontend HTML/CSS/JS statique servi par le même serveur. Mémoire à long terme par embeddings vectoriels, personnalités et relations évolutives.

## Commandes

```bash
# Lancer l'API (point d'entrée canonique — auto-détecte un port libre dans 8000-8020)
python run_api.py
python run_api.py --port 8001        # forcer un port

# Initialiser / réinitialiser la base de données (via SQLAlchemy ORM — Base.metadata.create_all)
python init_db.py

# Tests
pytest                               # tous les tests
pytest tests/test_character_manager.py
pytest tests/test_character_manager.py::test_nom -v   # un seul test
pytest --cov=backend                 # avec couverture

# Lint & format (ruff est l'outil configuré — pas flake8/black malgré le README)
ruff check backend tests
ruff format backend tests
mypy backend                         # typage (config lâche, voir pyproject.toml)
```

Le frontend n'a pas de build : ouvrir l'URL affichée par `run_api.py` (le serveur sert `frontend/index.html`, `chat.html`, `traits-visualizer.html` et les assets).

## Prérequis runtime

- **Ollama** doit tourner (`http://localhost:11434`) avec un modèle installé (`ollama pull gemma:2b` ou `llama3`). Voir `install_models.ps1`.
- `LLM_MOCK_MODE=False` par défaut ; si Ollama est absent au démarrage, un avertissement explicite est loggé (pas de bascule silencieuse).

## Architecture

### Flux d'une requête de chat
`frontend (api.js)` → route FastAPI sous `/api/chat/...` → `chat_service` → `character_manager` (profil + état + personnalité + relations) + `memory_manager` (mémoires pertinentes par similarité d'embedding) → construction du prompt → `llm_service.generate_text()` → Ollama → réponse persistée + extraction de faits/mémoires.

### Backend (`backend/`)
- `app.py` — instancie FastAPI, monte les fichiers statiques, inclut les routers **sous le préfixe `/api`**, expose `/health`. Appelle `Base.metadata.create_all` pour initialiser le schéma ORM.
- `routes/` — endpoints FastAPI (characters, chat, memory, system). Fins, délèguent aux services.
- `services/` — logique métier. Services actifs : `llm_service`, `chat_service`, `memory_manager`, `character_manager` (façade sur `character_service`, `character_state_service`, `personality_service`, `relationship_service`).
- `models/` — modèles Pydantic (API/validation) **et** modèles SQLAlchemy (`MemoryModel` dans `memory.py`, `ChatSessionModel`/`MessageModel` dans `chat.py`). Réexportés via `models/__init__.py`.
- `database.py` — `SessionLocal`, `Base`, `engine`, `get_db` (SQLAlchemy). Toutes les tables passent par cet ORM.

### Frontend (`frontend/`)
HTML statique + JS vanilla dans `assets/js/` (`api.js`, `chat.js`, `main.js`, `memory-explorer.js`). Communique avec le backend via fetch.

## Architecture (état aligné)

- **Config unique** : `backend/config.py`, pilotée par `.env` (python-decouple). Le `config.py` racine a été supprimé.
- **Base unique** : `data/alezia.db`, accès exclusivement via SQLAlchemy (`backend/database.py` → `SessionLocal` / `Base` / `engine` / `get_db`). `db_manager` (sqlite3 brut) et `schema.sql` ont été supprimés. Initialisation via `Base.metadata.create_all` (voir `init_db.py` et `run_api.py`).
- **Mode mock LLM bruyant** : défaut `LLM_MOCK_MODE=False` ; un avertissement explicite est loggé au démarrage si Ollama est absent.
- **Services** : routes → `character_manager` (façade sur `character_service`, `character_state_service`, `personality_service`, `relationship_service`), `chat_service`, `memory_manager`, `llm_service`. `chat_manager` et `universe_manager` ont été supprimés.
- **Chat** : modèles ORM `ChatSessionModel` / `MessageModel` (`backend/models/chat.py`, id UUID en String). L'historique de chat antérieur (tables legacy `sessions` / `messages`) n'est pas utilisé.
- **Préfixe `/api`** : tous les endpoints sont sous `/api` (ex. `POST /api/chat/create`, `GET /api/characters`). Le README/cursor-rules listent des chemins sans `/api` — ils sont obsolètes ; se fier au code des routes.
- **`api_port.txt`** : au démarrage, le port choisi est écrit dans ce fichier pour que le frontend trouve le backend. Si on change la logique de port, garder ce mécanisme.
- **Lanceur unique** : `python run_api.py`.

> Note : `README.md`, `GEMINI.md` et `.cursor/rules/` sont historiques et peuvent décrire l'ancien état (chemins sans `/api`, flake8/black, deux bases). Se fier au code et à ce fichier.

## Conventions de code

- Ruff : `line-length = 88`, **guillemets simples** (`quote-style = "single"`), règles `E, F, W, I, UP`, `E501`/`E731` ignorées.
- mypy ciblé sur Python 3.10, configuration volontairement lâche (types partiels tolérés).
- Docstrings en français, code/identifiants en anglais ou français selon le module existant — suivre le style du fichier modifié.
