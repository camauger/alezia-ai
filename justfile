# Alezia AI — raccourcis de développement (just)
# https://just.systems — lancer `just` (sans argument) pour la liste des recettes.
# Note : pas de `set dotenv-load` — l'app lit `.env` elle-même via python-decouple.

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

python := "python"

# Liste les recettes disponibles
default:
    @just --list

alias r := run
alias t := test

# Lancer l'API (auto-détecte un port libre 8000-8020). Ex : just run --port 8077
run *args:
    {{ python }} run_api.py {{ args }}

# Initialiser la base : crée les tables (ORM) + un univers par défaut (idempotent)
init-db:
    {{ python }} init_db.py

# Réinitialiser la base : SUPPRIME data/alezia.db puis ré-initialise (DONNÉES PERDUES)
[confirm("Supprimer data/alezia.db et tout réinitialiser ? Les données seront perdues.")]
reset-db:
    if (Test-Path data/alezia.db) { Remove-Item -Force -ErrorAction SilentlyContinue data/alezia.db, data/alezia.db-shm, data/alezia.db-wal }
    {{ python }} init_db.py

# Lancer les tests. Ex : just test tests/test_chat_service.py -v
test *args:
    {{ python }} -m pytest {{ args }}

# Tests avec couverture
cov:
    {{ python }} -m pytest --cov=backend

# Vérifier le style (ruff)
lint:
    ruff check backend tests run_api.py init_db.py

# Corriger automatiquement ce qui peut l'être (ruff)
lint-fix:
    ruff check --fix backend tests run_api.py init_db.py

# Formater le code (ruff)
fmt:
    ruff format backend tests run_api.py init_db.py

# Typage statique (mypy, configuration lâche)
typecheck:
    mypy backend

# Vérifs rapides avant commit : lint puis tests
check: lint test

# Lister les modèles Ollama installés (vérifie aussi qu'Ollama tourne)
ollama:
    ollama list
