# Plan du projet : Système de JDR avec IA personnalisée

## 1. Vue d'ensemble

### Objectif

Créer un système de jeu de rôle avec des personnages IA personnalisés et non censurés, capables d'évoluer, d'apprendre et d'interagir de façon cohérente dans divers univers.

### Fonctionnalités clés

- Personnages IA avec personnalités complexes et évolutives
- Mémoire à long terme permettant une progression des relations
- Univers variés (historiques, fantasy, etc.) influençant les personnages
- Interface visuelle et sonore immersive
- Flexibilité narrative sans restrictions de contenu

### Architecture

- Modèle LLM exécuté localement sur machine avec RTX 4060
- Backend optionnellement hébergé sur VM cloud légère pour accessibilité
- Interface web accessible depuis différents appareils

## 2. Configuration technique

### Prérequis matériels

- **Processeur**: Intel Core i7-13700HX (16 cœurs, 13e génération)
- **RAM**: 32 Go
- **GPU**: NVIDIA GeForce RTX 4060 Laptop GPU (8 Go VRAM)
- **Stockage**: SSD 512 Go+ recommandé
- **Connexion Internet**: Pour déploiement optionnel uniquement

### Stack technologique

- **Backend**: Python 3.8+ avec Flask/FastAPI
- **Frontend**: Vue.js ou React
- **Base de données**: SQLite (suffisant pour usage personnel)
- **Modèle LLM**: Ollama avec Llama 3/Mistral non censuré
- **Vectorisation**: sentence-transformers pour embeddings

## 3. Composants du système

### Serveur LLM local

- Ollama hébergé sur machine locale
- API REST locale exposée sur localhost/réseau local
- Modèles jusqu'à 13B optimisés pour RTX 4060
- Utilisation de modèles quantifiés pour performances optimales

### Application Backend

- API principale exécutée localement
- Gestion des personnages, univers et mémoires
- Orchestration des appels au LLM et traitement des résultats

### Base de données

- SQLite locale pour données structurées
- Stockage des embeddings pour récupération contextuelle
- Option de synchronisation cloud pour sauvegarde

### Frontend web

- Interface responsive et thématique
- Composants pour chat, gestion des personnages/univers
- Intégration visuelle et sonore adaptative

## 4. Modèles de données

### Personnages

- Profils avec personnalité, histoire et caractéristiques
- Association à des univers spécifiques
- Configuration visuelle et vocale

### Univers

- Définition du cadre (historique, fantasy, sci-fi, etc.)
- Éléments spécifiques (lieux, concepts, objets importants)
- Règles linguistiques et comportementales

### Mémoire

- Souvenirs épisodiques (conversations, événements)
- Faits extraits (connaissances sémantiques)
- Embeddings vectoriels pour récupération contextuelle

### Relations

- Évolution des sentiments entre personnages et utilisateur
- Niveaux de confiance et familiarité
- Historique d'interactions

## 5. Plan d'implémentation

### Phase 1: Configuration initiale (3-5 jours)

1. Installation d'Ollama et optimisation pour RTX 4060
2. Mise en place de l'environnement de développement
3. Création de l'API de base et tests d'intégration

### Phase 2: Système de personnages et mémoire (1-2 semaines)

1. Développement du gestionnaire de personnages
2. Implémentation du système de mémoire à long terme
3. Création de l'interface de conversation basique

### Phase 3: Univers et expérience sensorielle (2-3 semaines)

1. Développement du système d'univers
2. Améliorations visuelles et thématiques
3. Intégration de la synthèse vocale (optionnelle)

### Phase 4: Optimisations et finitions (1-2 semaines)

1. Optimisation des performances et des prompts
2. Création de la documentation et des exemples
3. Tests, débogage et améliorations finales

## 6. Considérations techniques

### Performance

- Utilisation de modèles quantifiés (GGUF q5_K_M)
- Paramètres Ollama optimisés pour RTX 4060
- Mise en cache intelligente des requêtes fréquentes
- Gestion efficace des ressources GPU/CPU

### Sécurité

- Restriction de l'accès au réseau local
- Chiffrement des communications
- Sauvegardes régulières des données

### Évolutivité

- Architecture modulaire pour ajouts futurs
- Séparation claire des composants
- Interfaces standardisées entre modules

## 7. Configuration et déploiement

### Installation locale

1. Configuration d'Ollama avec paramètres optimisés
2. Téléchargement des modèles LLM non censurés
3. Déploiement du backend et de la base de données
4. Configuration du frontend et des ressources

### Déploiement cloud (optionnel)

1. Mise en place d'une VM légère pour accessibilité externe
2. Configuration des sauvegardes et synchronisations
3. Mise en place de tunnels sécurisés pour accès distant

## 8. Ressources et références

### Modèles recommandés

- Llama 3 13B Instruct Uncensored (GGUF q5_K_M)
- Mistral 7B Instruct Uncensored (GGUF q5_K_M)
- Mixtral 8x7B Instruct (GGUF q4_K_M)
- Nous-Hermes 2 13B (GGUF q5_K_M)

### Outils de développement

- VS Code avec extensions Python/JavaScript
- GitHub Desktop ou équivalent
- DB Browser pour SQLite
- Outils de monitoring GPU/système

## 9. Structure du projet

```
jdr-ia/
├── backend/          # Application backend
│   ├── app.py        # Point d'entrée
│   ├── models/       # Modèles de données
│   ├── services/     # Services métier
│   ├── routes/       # Endpoints API
│   └── utils/        # Utilitaires
├── frontend/         # Interface utilisateur
│   ├── components/   # Composants UI
│   ├── services/     # Services frontend
│   └── assets/       # Ressources statiques
├── data/             # Stockage données
└── scripts/          # Scripts utilitaires
```

## 10. Roadmap d'évolution

### Version 1.0 (Base fonctionnelle)

- Système de conversation de base
- Mémoire simple
- Interface web minimaliste

### Version 1.5 (Expérience améliorée)

- Interface visuelle enrichie
- Système de mémoire avancé
- Synthèse vocale basique

### Version 2.0 (Fonctionnalités avancées)

- Interactions multi-personnages
- Narration guidée
- Génération visuelle
- Accessibilité à distance

## 11. Ressources et documentation

### Documentation technique

- [Documentation Ollama](https://ollama.com/docs)
- [Guide FastAPI](https://fastapi.tiangolo.com/)
- [Optimisation GPU pour modèles LLM](https://github.com/ollama/ollama/blob/main/docs/gpu.md)

### Tutoriels et guides

- Guide d'installation
- Documentation de l'API
- Exemples de personnages et univers
- Guide d'optimisation pour votre matériel
