# Alignement d'Alezia AI — Design

**Date :** 2026-05-30
**Statut :** Approuvé (design), en attente de relecture spec
**Branche :** `align/alezia-sandbox`

## But

Alezia AI est un **outil personnel / bac à sable** (usage solo, jeu et expérimentation). « Mieux aligné » signifie ici : **une seule façon évidente de faire chaque chose**, pour qu'après une pause, on n'ait jamais à se demander « c'est quel fichier / quelle base / quel service ? ». On applique YAGNI sans pitié : on **collapse** les dualités existantes, on ne construit pas d'architecture nouvelle.

Frictions à éliminer (exprimées par l'utilisateur) :
1. « C'est quoi le bon fichier ? » — confusion des doublons.
2. « Ça marche pas comme attendu » — mode mock silencieux, démarrage capricieux.
3. « Trop de fichiers parasites » — scripts multiples, tests éparpillés, `requirements.txt` cassé, `.db` en double.

Hors scope (YAGNI) : nouvelle fonctionnalité, refonte produit, doc externe parfaite, architecture défendable « pour les autres ».

## Diagnostic (état réel vérifié)

La cause racine de la confusion : **`chat_service` (le service de chat câblé) écrit dans deux bases simultanément.**

- **`jdr_database.sqlite`** (SQLAlchemy, via `backend/database.py` → `DB_PATH`) : personnages, traits, mémoires, relations, univers.
- **`alezia.db`** (sqlite3 brut, via `backend/utils/db.py` → `db_manager`) : `chat_sessions`, `chat_messages`.

Une seule conversation éparpille donc les données sur deux fichiers. S'y ajoute une **duplication de schéma** : les modèles ORM SQLAlchemy (`CharacterModel`, `MemoryModel`, …) définissent les tables d'un côté ; `backend/utils/schema.sql` redéfinit des tables qui se chevauchent de l'autre.

Faits vérifiés (par lecture du code, pas supposés) :

- **Config :** le `config.py` **racine n'est importé nulle part**. Tout le code applicatif utilise `backend/config.py` (`app.py`, `run_api.py`, `llm_service`, `memory_manager`, `embedding_loader`, `database.py`).
- **Mode mock :** `backend/config.py::LLM_CONFIG` n'a pas les clés que `llm_service` lit (`api_url`, `default_model`, `mock_mode`, `temperature`, `max_tokens`). Le service retombe donc sur ses défauts (`mock_mode=True`). Le `config.py` racine, lui, **a** ces clés, pilotées par `.env` (`LLM_MOCK_MODE`, etc.).
- **Services (réachabilité depuis les routes) :**
  - Routes câblées : `routes/characters → character_manager`, `routes/chat → chat_service`, `routes/memory → memory_manager`, `routes/system → llm_service + db_manager`.
  - `character_manager` est une **façade** déléguant à `character_service`, `character_state_service`, `personality_service`, `relationship_service` → **tous vivants**.
  - `chat_service` instancie `CharacterManager` + `MemoryManager`, utilise `llm_service`.
  - **Morts** (seulement ré-exportés dans `services/__init__.py`, jamais importés par une route ni un service vivant) : **`chat_manager`**, **`universe_manager`**.

## Décisions cibles : un seul chemin par chose

| Dualité | Gagnant | Justification |
|---|---|---|
| Config | `backend/config.py`, fusionné avec le pilotage `.env` du racine | Déjà câblé partout ; greffer les définitions env-driven du racine corrige le mock du même coup. Puis **supprimer** `config.py` racine. |
| Base de données | **SQLAlchemy, fichier unique** | Tous les modèles sont déjà en ORM ; la majorité des services prennent `db: Session`. Migrer *vers* SQLAlchemy = ne réécrire que le chat. Migrer vers sqlite3 brut = réécrire mémoire + traits + relations + univers (bien plus de travail). |
| Accès chat | Modèles ORM `ChatSession` / `ChatMessage` | Porter les méthodes de `chat_service` qui utilisent `db_manager` vers l'ORM. Retirer `db_manager`, `schema.sql`, l'ancien fichier brut. |
| Services morts | Supprimer `chat_manager` + `universe_manager` | Ré-exportés mais injoignables. Mettre à jour `services/__init__.py`. **Ne pas** toucher à `character_service` & co (vivants via la façade). |
| Démarrage | `run_api.py` **unique** | Supprimer `start_api_*.py`, `start.ps1`, `start.bat`, `start_api.ps1`, `start_api.bat`, `backend_api.py`, `api_test.py`, `check_api_health.py`, `Modelfile`. (Confirmé inutilisés par l'utilisateur.) |
| Mode mock | **Bruyant** | Au démarrage, log explicite `⚠️ MODE MOCK ACTIF — réponses factices` si Ollama absent. Défaut `LLM_MOCK_MODE=False`. |
| `requirements.txt` | Réparé | Vraies deps : `fastapi`, `uvicorn`, `sqlalchemy`, `python-decouple`, `requests`, `numpy`, `sentence-transformers`, `pytest`, `ruff`. |

## Données : vérité terrain (inspection des `.db`)

Inspection réelle des deux fichiers (`PRAGMA` + `COUNT`) :

- **`data/alezia.db` (base brute `db_manager`) : quasi VIDE.** 0 personnage, 0 session, 0 message ; uniquement 1 univers par défaut + 3 `universe_elements`. → **cruft, à supprimer** (aucune migration nécessaire).
- **`data/jdr_database.sqlite` (base SQLAlchemy) : contient TOUTES les données riches.** 8 personnages, 28 `personality_traits`, 50 `trait_changes`, 7 `memories`, 8 `relationships`, 1 univers — **avec des modèles ORM correspondants**. → préservé « gratuitement » en gardant ce fichier.
- **Conversations historiques** (14 `sessions` / 19 `messages`) : dans des tables **orphelines** (`sessions`/`messages`) **sans modèle ORM** — vestiges d'une version antérieure. `chat_service` écrit, lui, dans `chat_sessions`/`chat_messages` (vides) via `db_manager`, et appelle `memory_manager.create_memory` / `get_relevant_memories` **sans l'argument `db` requis** → le chat câblé est cassé.

**Décision utilisateur : repartir à zéro sur le chat.** On garde les données riches (déjà dans la base SQLAlchemy), on abandonne les 14 conversations de test, le chat redémarre sur des tables ORM propres. **Pas de script de migration.**

## Ordre d'exécution

Chaque étape se termine par une **vérification** : l'app démarre (`python run_api.py`) et le chat répond réellement.

1. **Config (petit, sûr).** Fusionner les définitions env-driven du `config.py` racine dans `backend/config.py` (clés LLM attendues par `llm_service`, `EMBEDDING`, `MEMORY`, CORS). Supprimer le `config.py` racine. Rendre le mode mock bruyant au démarrage. Défaut `LLM_MOCK_MODE=False`.
   - *Vérif :* démarrage OK ; si Ollama présent, plus de réponses factices ; sinon avertissement visible.

2. **Base de données unique (le gros morceau).**
   1. **Sauvegarde** : copier `data/jdr_database.sqlite` en `.bak` avant toute manipulation.
   2. Redéfinir proprement les modèles ORM chat dans `backend/models/chat.py` (`ChatSessionModel` / `MessageModel`) avec le schéma dont `chat_service` a besoin (`user_id`, `character_id`, `created_at`, `updated_at`, `active`, `context` ; message : `session_id`, `sender`, `content`, `timestamp`, `message_metadata`).
   3. Réécrire `chat_service` pour utiliser `SessionLocal` / l'ORM à la place de `db_manager` (méthodes : `create_session`, `get_session`, `get_user_sessions`, `delete_session`, `get_session_messages`, `send_message`, `add_message`, `generate_response`) — en passant l'argument `db` aux appels `memory_manager.create_memory(db, …)`, `memory_manager.get_relevant_memories(db, …)`, `character_manager.update_traits_from_interaction(db, …)` (bugs latents corrigés au passage).
   4. **Pas de migration** (chat repart à zéro). Supprimer l'ancien `data/alezia.db` brut, renommer `data/jdr_database.sqlite` → `data/alezia.db`, pointer `DB_PATH` sur ce fichier unique. Retirer `db_manager` (`backend/utils/db.py`), `backend/utils/schema.sql`, et la référence dans `routes/system.py` (réécrire `check-database` via l'ORM).
   5. Adapter `init_db.py` et `run_api.py::initialize_database` (qui utilisaient `db_manager`) pour initialiser via l'ORM (`Base.metadata.create_all(bind=engine)` + univers par défaut). Créer les tables chat propres au passage.
   - *Vérif :* les 8 personnages + traits + mémoires + relations sont présents ; création d'une nouvelle session de chat + envoi d'un message fonctionne et persiste ; un seul `.db` reste.

3. **Services morts.** Supprimer `chat_manager.py` et `universe_manager.py` ; nettoyer `services/__init__.py`. (Re-vérifier l'absence de tout import avant suppression.)
   - *Vérif :* démarrage OK, routes inchangées.

4. **Parasites.** Supprimer les lanceurs/fichiers morts (tous les `start*.py` / `start*.ps1` / `start*.bat`, `backend_api.py`, `api_test.py`, `check_api_health.py`, `Modelfile` — confirmés inutilisés). Réparer `requirements.txt`. Regrouper les `backend/test_*.py` dans `tests/`. Supprimer les `.db` orphelins (`alezia-TELUQ-*.db-*`, ancien `jdr_database.sqlite` après migration).
   - *Vérif :* `pytest` passe ; un seul chemin de démarrage.

5. **Doc.** Mettre à jour `CLAUDE.md` pour refléter le chemin unique (un seul config, une seule base SQLAlchemy, services vivants). README/GEMINI/cursor-rules laissés tels quels (sandbox — priorité basse), avec une note dans CLAUDE.md signalant qu'ils sont historiques.

## Critères de succès

- Un seul `config.py`, un seul fichier `.db`, un seul paradigme d'accès (SQLAlchemy), un seul lanceur.
- Démarrage honnête : on sait immédiatement si on est en mode mock.
- `chat_manager` et `universe_manager` supprimés ; aucun import cassé.
- Données riches préservées dans la base unique (8 personnages, traits, mémoires, relations) ; chat reparti à zéro sur tables ORM propres.
- `pytest` passe ; `ruff check` propre.
- `CLAUDE.md` décrit fidèlement le projet aligné.

## Risques

- **Réécriture de `chat_service` sur l'ORM** : principal point de complexité. Mitigation : sauvegarde `.bak` de la base avant manipulation ; vérification que les données riches restent lisibles après chaque étape.
- **`Base.metadata.create_all` doit voir tous les modèles ORM** (import des modules `models/*` avant l'appel) pour créer les tables chat propres. À garantir dans `init_db.py` / `run_api.py`.
- **Tables orphelines `sessions`/`messages`** : laissées en place (inertes) ou supprimées en étape 4 ; sans impact fonctionnel puisque le chat repart sur `chat_sessions`/`chat_messages`.
