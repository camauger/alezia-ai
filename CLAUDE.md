# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Alezia AI — système de jeu de rôle avec personnages IA non censurés, propulsé par Ollama en local. Backend FastAPI (Python) + frontend HTML/CSS/JS statique servi par le même serveur. Mémoire à long terme par embeddings vectoriels, personnalités et relations évolutives.

## Commandes

```bash
# Lancer l'API (point d'entrée canonique — auto-détecte un port libre dans 8000-8020)
python run_api.py
python run_api.py --port 8001        # forcer un port

# Initialiser / réinitialiser la base de données (crée l'univers par défaut)
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
- Sans Ollama, le `LLMService` bascule en **mode mock** (réponses factices) — voir gotcha ci-dessous.

## Architecture

### Flux d'une requête de chat
`frontend (api.js)` → route FastAPI sous `/api/chat/...` → `chat_service` → `character_service` (profil + état) + `memory_manager` (mémoires pertinentes par similarité d'embedding) → construction du prompt → `llm_service.generate_text()` → Ollama → réponse persistée + extraction de faits/mémoires.

### Backend (`backend/`)
- `app.py` — instancie FastAPI, monte les fichiers statiques, inclut les routers **sous le préfixe `/api`**, expose `/health`.
- `routes/` — endpoints FastAPI (characters, chat, memory, system). Fins, délèguent aux services.
- `services/` — logique métier. Plusieurs services exposent une **instance globale singleton** (`llm_service`, `chat_service`, `db_manager`).
- `models/` — modèles Pydantic (API/validation) **et** modèles SQLAlchemy (ex. `MemoryModel` dans `memory.py`). Réexportés via `models/__init__.py`.
- `utils/db.py` — `DatabaseManager` (sqlite3 brut), `utils/schema.sql` — le schéma SQL.

### Frontend (`frontend/`)
HTML statique + JS vanilla dans `assets/js/` (`api.js`, `chat.js`, `main.js`, `memory-explorer.js`). Communique avec le backend via fetch.

## Pièges critiques (à connaître avant de modifier)

1. **Deux fichiers `config.py`.** L'application utilise **`backend/config.py`** (`API_CONFIG`, `SECURITY_CONFIG`, `LLM_CONFIG`, `EMBEDDING_CONFIG`, `DB_PATH`). Le `config.py` racine (basé sur `python-decouple` / `.env`) n'est **pas** importé par le code applicatif. Ne pas confondre.

2. **Deux paradigmes d'accès BD coexistent**, sur deux fichiers `.db` différents :
   - `backend/utils/db.py` → `db_manager` (sqlite3 brut), pointe par défaut sur `data/alezia.db`. Utilisé par la plupart des services et `init_db.py`.
   - `backend/database.py` → SQLAlchemy (`SessionLocal`, `Base`), pointe sur `DB_PATH = data/jdr_database.sqlite`. Utilisé par `memory_manager` (Session SQLAlchemy + `SentenceTransformer`).
   Vérifier quel paradigme cible une table avant d'écrire une requête.

3. **Mode mock par défaut.** `LLM_CONFIG` dans `backend/config.py` n'a pas les clés (`api_url`, `default_model`, `mock_mode`) que `llm_service.py` lit via `.get(...)` ; le service retombe donc sur ses défauts (`mock_mode=True`, URL `localhost:11434/api`). Conséquence : tant qu'Ollama n'est pas détecté, le chat renvoie des réponses factices. Idem pour les embeddings (vecteurs aléatoires déterministes).

4. **Préfixe `/api`.** Tous les endpoints sont sous `/api` (ex. `POST /api/chat/create`, `GET /api/characters`). Le README/cursor-rules listent des chemins **sans** `/api` — ils sont obsolètes ; se fier au code des routes.

5. **`api_port.txt`.** Au démarrage, le port choisi est écrit dans un fichier (`api_port.txt` / `frontend/api_port.txt`) pour que le frontend trouve le backend. Si on change la logique de port, garder ce mécanisme.

6. **`requirements.txt` est malformé** (contenu sur une ligne, cassé). Les vraies dépendances : `fastapi`, `uvicorn`, `sqlalchemy`, `python-decouple`, `requests`, `numpy`, `sentence-transformers`, `pytest`, `ruff`. Installer manuellement si `pip install -r` échoue.

7. **Doublons de services** : `character_manager`/`character_service`, `chat_manager`/`chat_service`. Vérifier lequel est réellement câblé via les routes (les `*_service` sont les instances importées par `routes/`).

8. **Multiples scripts de démarrage** (`start_api_*.py`, `start.ps1`, `start.bat`) sont des variantes/expérimentations. **`run_api.py` est le point d'entrée de référence.**

## Conventions de code

- Ruff : `line-length = 88`, **guillemets simples** (`quote-style = "single"`), règles `E, F, W, I, UP`, `E501`/`E731` ignorées.
- mypy ciblé sur Python 3.10, configuration volontairement lâche (types partiels tolérés).
- Docstrings en français, code/identifiants en anglais ou français selon le module existant — suivre le style du fichier modifié.
