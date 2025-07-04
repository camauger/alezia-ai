# Alezia AI - Système de JDR avec IA non censurée

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Ollama](https://img.shields.io/badge/Ollama-Compatible-orange.svg)

Un système de jeu de rôle avec des personnages IA personnalisés et non censurés, capables d'évoluer, d'apprendre et d'interagir de façon cohérente dans divers univers.

## 🚀 Démarrage rapide

**Nouveau ici ?** Consultez le [**Guide de démarrage rapide (START.md)**](START.md) pour être opérationnel en quelques minutes !

Cette documentation complète contient tous les détails techniques et d'utilisation avancée.

## Table des matières

- [🚀 Démarrage rapide](#-démarrage-rapide)
- [Fonctionnalités](#fonctionnalités)
- [Architecture technique](#architecture-technique)
- [Configuration requise](#configuration-requise)
- [Installation](#installation)
- [Structure du projet](#structure-du-projet)
- [API REST](#api-rest)
- [Utilisation](#utilisation)
- [Modèle de données](#modèle-de-données)
  - [Évolution des personnages](#évolution-des-personnages)
- [Dépannage](#dépannage)
- [Développement](#développement)
- [Performances et optimisation](#performances-et-optimisation)
- [Contributing](#contributing)
- [Support et Contact](#support-et-contact)

## Fonctionnalités

- 🧠 Personnages IA avec personnalités complexes et évolutives
- 🔄 Mémoire à long terme permettant une progression des relations
- 🌍 Univers variés (historiques, fantasy, etc.) influençant les personnages
- 🎭 Flexibilité narrative sans restrictions de contenu
- 🖥️ Interface web immersive et accessible

## Architecture technique

Le projet est organisé en plusieurs composants clés :

### Backend (Python/FastAPI)

- **API REST** pour la gestion des personnages, univers et conversations
- **Système de mémoire** utilisant des embeddings vectoriels pour la pertinence contextuelle
- **Service LLM** pour interagir avec Ollama et générer des réponses IA
- **Base de données SQLite** pour persister les données

### Frontend (HTML/CSS/JavaScript)

- **Interface utilisateur** responsive et intuitive
- **Communication asynchrone** avec l'API backend
- **Gestion d'état** pour le suivi des conversations et des personnages

## Configuration requise

- **Processeur**: Intel Core i7-13700HX ou équivalent
- **RAM**: 16 Go minimum (32 Go recommandé)
- **GPU**: NVIDIA avec 8 Go VRAM minimum (RTX 4060 ou supérieur recommandé)
- **Stockage**: SSD avec 10 Go d'espace libre minimum
- **OS**: Windows 10/11, Linux, ou macOS
- **Logiciels**: Python 3.8+, Ollama

## Installation

> **💡 Pour un démarrage rapide**, consultez plutôt [START.md](START.md) qui contient une version simplifiée de ces instructions.

### 1. Prérequis

1. **Installez Python 3.8+** depuis [python.org](https://www.python.org/downloads/)
2. **Installez Ollama** depuis [ollama.com/download](https://ollama.com/download)
3. **Démarrez Ollama** et assurez-vous qu'il fonctionne avec `ollama --version`

### 2. Configuration du projet

```bash
# Cloner le dépôt
git clone https://github.com/votre-repo/alezia-ai.git
cd alezia-ai

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Installation des modèles Ollama

Avant de démarrer l'API, vous devez installer un modèle compatible avec Ollama. Utilisez le script fourni :

```powershell
# Sur Windows
.\install_models.ps1
```

Ce script va :
1. Vérifier si Ollama est en cours d'exécution
2. Vérifier les modèles déjà installés
3. Installer un modèle léger compatible si nécessaire
4. Mettre à jour la configuration pour utiliser le modèle disponible

Alternativement, vous pouvez installer manuellement n'importe quel modèle Ollama supporté :
```bash
ollama pull gemma:2b   # Un modèle léger et rapide
# ou
ollama pull llama3     # Modèle plus performant mais plus lourd
```

### 4. Initialisation de la base de données

Avant de démarrer l'application, il est recommandé d'initialiser la base de données :

```bash
# Initialiser la base de données avec un univers par défaut
python init_db.py
```

### 5. Lancement

Pour démarrer l'API backend :

```bash
# Utiliser le script Python de démarrage
python run_api.py
```

Le script trouvera automatiquement un port disponible entre 8000 et 8020 et affichera l'URL d'accès.

Ou sur Windows, vous pouvez également utiliser le script PowerShell fourni :

```powershell
# Démarrer l'API avec le script PowerShell
.\start_api.ps1
```

Accédez à l'interface frontend à l'adresse indiquée par le script de démarrage (généralement http://localhost:8000 ou autre port si 8000 est déjà utilisé).

## Structure du projet

```
alezia-ai/
├── backend/           # API et logique métier
│   ├── models/        # Modèles de données Pydantic
│   ├── services/      # Services métier (LLM, personnages, mémoire)
│   ├── routes/        # Endpoints API FastAPI
│   └── utils/         # Utilitaires (DB, logging, etc.)
├── frontend/          # Interface utilisateur
│   ├── assets/        # Ressources statiques (CSS, JS, images)
│   ├── components/    # Composants UI réutilisables
│   └── services/      # Services frontend pour l'API
├── data/              # Stockage des données
│   └── embeddings/    # Cache pour les embeddings vectoriels
├── logs/              # Fichiers de journalisation
├── scripts/           # Scripts utilitaires
├── tests/             # Tests unitaires et d'intégration
└── docs/              # Documentation
```

## API REST

L'API expose plusieurs endpoints pour interagir avec le système :

### Personnages

- `GET /characters` - Liste des personnages disponibles
- `POST /characters` - Création d'un nouveau personnage
- `GET /characters/{id}` - Détails d'un personnage spécifique
- `DELETE /characters/{id}` - Suppression d'un personnage

### Chat

- `POST /chat/session` - Créer une nouvelle session de chat avec un personnage
- `GET /chat/session/{session_id}` - Obtenir les détails d'une session spécifique
- `GET /chat/character/{character_id}/sessions` - Lister les sessions d'un personnage
- `POST /chat/{session_id}/message` - Envoyer un message et obtenir une réponse
- `GET /chat/{session_id}/history` - Récupérer l'historique d'une conversation
- `POST /chat/{session_id}/end` - Terminer une session de chat

### Système

- `GET /system/check-database` - Vérification de l'état de la BD
- `GET /system/check-llm` - Vérification de l'état du modèle LLM

## Utilisation

### Création d'un personnage

1. Accédez à la page de création de personnage
2. Remplissez les informations de base (nom, description, personnalité)
3. Sélectionnez un univers ou créez-en un nouveau
4. Personnalisez les paramètres avancés (optionnel)
5. Cliquez sur "Créer"

### Test de l'API

Pour tester la création d'un personnage via l'API, utilisez le script PowerShell fourni :

```powershell
# Tester la création de personnage
.\test_character_api.ps1

# Tester les fonctionnalités de chat
.\test_chat_api.ps1
```

Si l'API utilise un port différent de 8000, modifiez d'abord les scripts de test pour utiliser le bon port.

### Conversation avec un personnage

1. Sélectionnez un personnage dans la liste
2. Commencez à converser dans la zone de texte
3. Le personnage répondra en fonction de sa personnalité, de son univers et de vos interactions passées

## Modèle de données

### Personnage (Character)

- `id` - Identifiant unique
- `name` - Nom du personnage
- `description` - Description physique et comportementale
- `personality` - Traits de personnalité et comportement
- `backstory` - Histoire personnelle (optionnel)
- `universe_id` - ID de l'univers auquel il appartient (optionnel)

### Session (Session)

- `id` - Identifiant unique
- `character_id` - Lien vers le personnage
- `start_time` - Date et heure de début de session
- `end_time` - Date et heure de fin (si terminée)
- `summary` - Résumé automatique de la conversation (optionnel)

### Message (Message)

- `id` - Identifiant unique
- `session_id` - Lien vers la session
- `is_user` - Booléen indiquant si c'est un message utilisateur
- `content` - Contenu du message
- `timestamp` - Date et heure d'envoi
- `metadata` - Métadonnées additionnelles (JSON)

### Mémoire (Memory)

- `id` - Identifiant unique
- `character_id` - Lien vers le personnage
- `type` - Type de mémoire (conversation, observation, etc.)
- `content` - Contenu textuel de la mémoire
- `importance` - Valeur d'importance (0.0-1.0)
- `embedding` - Vecteur de représentation sémantique

### Relation (Relationship)

- `character_id` - ID du personnage
- `target_name` - Nom de la cible (autre personnage ou utilisateur)
- `sentiment` - Sentiment (-1.0 à 1.0)
- `trust` - Niveau de confiance (0.0 à 1.0)
- `familiarity` - Niveau de familiarité (0.0 à 1.0)

### Évolution des personnages

Le système d'Alezia AI comprend des mécanismes d'évolution dynamique des personnalités :

- **Évolution des traits** : Les traits de personnalité s'adaptent en fonction des interactions
- **Évolution des relations** : Les relations avec l'utilisateur évoluent au fil du temps
- **Moments décisifs** : Certaines conversations peuvent provoquer des changements significatifs
- **Mémoire contextuelle** : Les personnages se souviennent des interactions passées et s'y adaptent

## Dépannage

### Problèmes de modèle AI

Si vous voyez "Modèle AI non chargé" dans l'interface :

1. Vérifiez qu'Ollama est en cours d'exécution
2. Exécutez le script `.\install_models.ps1` pour installer un modèle compatible
3. Redémarrez l'API après l'installation du modèle

### Problèmes de port

Si vous voyez des erreurs comme "Errno 10048" ou "WinError 10013", cela signifie que le port est déjà utilisé:

- Le script run_api.py trouve automatiquement un port disponible
- Vérifiez dans la console le message indiquant le port utilisé
- Assurez-vous d'utiliser ce même port dans votre navigateur

### Autres problèmes courants

- **API ne démarre pas**: Vérifiez que toutes les dépendances sont installées avec `pip install -r requirements.txt`
- **Extension JSON1**: Le message "Impossible de charger l'extension JSON1" est normal sur Windows et n'affecte pas les fonctionnalités essentielles
- **Modèle d'embeddings**: Le message "Torch not compiled with CUDA enabled" est normal si vous n'avez pas de GPU compatible CUDA
- **Réponses lentes**: Si les réponses des personnages sont lentes, considérez utiliser un modèle plus léger comme `gemma:2b`
- **Mémoire insuffisante**: Fermez d'autres applications gourmandes en RAM ou utilisez un modèle plus petit
- **Base de données corrompue**: Supprimez le fichier `data/alezia.db` et relancez `python init_db.py`
- **Erreur "No module named 'utils.db'"**: Assurez-vous d'être dans le dossier racine du projet (alezia-ai) et que l'environnement virtuel est activé

### Commandes de diagnostic

```bash
# Vérifier l'état de l'API
python backend/check_api.py

# Vérifier la connexion à Ollama
ollama list

# Tester la base de données
python backend/test_db_connection.py

# Voir les logs d'erreur
# Consultez le dossier logs/ pour les fichiers de journalisation
```

## Développement

### Exécuter les tests

```bash
# Installer les dépendances de développement
pip install -r requirements.txt

# Exécuter les tests
pytest

# Vérifier la couverture des tests
pytest --cov=backend
```

### Conventions de code

Ce projet suit les conventions PEP 8 pour le code Python. Vous pouvez vérifier le style avec:

```bash
# Vérifier le style du code
flake8 backend tests

# Formater automatiquement le code
black backend tests
```

### Documentation API

Une documentation OpenAPI est générée automatiquement et accessible à l'URL:
```
http://localhost:8000/docs
```

## Performances et optimisation

### Conseils pour de meilleures performances

- **GPU recommandé** : Ollama fonctionne mieux avec une carte graphique compatible
- **Modèles légers** : Utilisez `gemma:2b` ou `phi:2.7b` pour des réponses plus rapides
- **RAM suffisante** : 16 Go recommandés pour les gros modèles comme `llama3`
- **SSD recommandé** : Améliore les temps de chargement des embeddings

### Optimisation des modèles

```bash
# Voir les modèles installés et leur taille
ollama list

# Supprimer un modèle inutilisé pour libérer l'espace
ollama rm nom_du_modele

# Précharger un modèle en mémoire (optionnel)
ollama run gemma:2b ""
```

## Contributing

Les contributions sont les bienvenues ! Pour contribuer :

1. **Fork** le projet
2. **Créez une branche** pour votre fonctionnalité (`git checkout -b feature/nouvelle-fonctionnalite`)
3. **Committez** vos changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. **Push** vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. **Ouvrez une Pull Request**

### Areas d'amélioration prioritaires

- Nouveaux types d'univers et personnages
- Amélioration de l'interface utilisateur
- Optimisations de performance
- Tests automatisés supplémentaires
- Documentation et tutoriels

## License

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

## Support et Contact

### 🐛 Signaler un bug
Ouvrez une [issue GitHub](https://github.com/votre-repo/alezia-ai/issues) avec :
- Description du problème
- Étapes pour reproduire
- Messages d'erreur (le cas échéant)
- Votre configuration (OS, Python, modèle Ollama)

### 💡 Suggestions d'amélioration
Les suggestions sont bienvenues via les [GitHub Issues](https://github.com/votre-repo/alezia-ai/issues) ou [Discussions](https://github.com/votre-repo/alezia-ai/discussions).

### 📚 Documentation
- **Démarrage rapide** : [START.md](START.md)
- **API complète** : http://localhost:8000/docs (quand l'app est lancée)
- **Code source** : Explorez le code dans `backend/` et `frontend/`

### 🤝 Communauté
- Partagez vos personnages créés
- Proposez de nouveaux univers
- Contribuez au code source

---

**Alezia AI** - Créé avec ❤️ pour la communauté du jeu de rôle et de l'IA.

