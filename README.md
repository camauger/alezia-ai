# Alezia AI - Système de JDR avec IA non censurée

Un système de jeu de rôle avec des personnages IA personnalisés et non censurés, capables d'évoluer, d'apprendre et d'interagir de façon cohérente dans divers univers.

## Fonctionnalités

- 🧠 Personnages IA avec personnalités complexes et évolutives
- 🔄 Mémoire à long terme permettant une progression des relations
- 🌍 Univers variés (historiques, fantasy, etc.) influençant les personnages
- 🎭 Flexibilité narrative sans restrictions de contenu
- 🖥️ Interface web immersive et accessible

## Configuration requise

- **Processeur**: Intel Core i7-13700HX ou équivalent
- **RAM**: 16 Go minimum (32 Go recommandé)
- **GPU**: NVIDIA avec 8 Go VRAM minimum (RTX 4060 ou supérieur recommandé)
- **Stockage**: SSD avec 10 Go d'espace libre minimum
- **OS**: Windows 10/11, Linux, ou macOS
- **Logiciels**: Python 3.8+, Ollama

## Installation

### 1. Prérequis

Installez [Ollama](https://ollama.com/download) pour votre système d'exploitation.

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

# Optimiser Ollama pour votre GPU
python scripts/optimize_ollama.py

# Initialiser la base de données
python scripts/init_db.py
```

### 3. Lancement

```bash
# Démarrer le backend
cd backend
python app.py

# Dans un nouveau terminal, lancer le frontend temporaire
cd ../frontend
python -m http.server 8080
```

Accédez à l'application à l'adresse http://localhost:8080

## Structure du projet

```
alezia-ai/
├── backend/           # API et logique métier
│   ├── models/        # Modèles de données
│   ├── services/      # Services métier
│   ├── routes/        # Endpoints API
│   └── utils/         # Utilitaires
├── frontend/          # Interface utilisateur
│   ├── assets/        # Ressources statiques
│   ├── components/    # Composants UI
│   └── services/      # Services frontend
├── data/              # Stockage des données
├── scripts/           # Scripts utilitaires
└── docs/              # Documentation
```

## Utilisation

### Création d'un personnage

1. Accédez à la page de création de personnage
2. Remplissez les informations de base (nom, description, personnalité)
3. Sélectionnez un univers ou créez-en un nouveau
4. Personnalisez les paramètres avancés (optionnel)
5. Cliquez sur "Créer"

### Conversation avec un personnage

1. Sélectionnez un personnage dans la liste
2. Commencez à converser dans la zone de texte
3. Le personnage répondra en fonction de sa personnalité, de son univers et de vos interactions passées

## Développement

Pour contribuer au développement :

1. Installez les dépendances de développement : `pip install -r requirements-dev.txt`
2. Exécutez les tests : `pytest`
3. Vérifiez le style de code : `flake8`

## Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

## Contact

Pour toute question ou suggestion, veuillez ouvrir une issue sur GitHub.

---

**Note**: Ce système est conçu pour fonctionner localement sur votre machine. Les modèles d'IA utilisés ne sont pas censurés et peuvent générer du contenu pour adultes si le contexte narratif le justifie.

## Images pour Alezia AI

Ce répertoire doit contenir les images utilisées par l'application, notamment les avatars des personnages.

### Images requises

- `placeholder-avatar.jpg` : Image utilisée comme avatar par défaut pour les personnages. Idéalement une image de 256x256 pixels.

### Comment ajouter des images

1. Téléchargez une image d'avatar générique depuis un site comme [Unsplash](https://unsplash.com/) ou créez une image avec [Stable Diffusion](https://github.com/AUTOMATIC1111/stable-diffusion-webui).
2. Redimensionnez l'image en 256x256 pixels.
3. Enregistrez l'image sous le nom `placeholder-avatar.jpg` dans ce répertoire.

### Notes

- Si l'image n'est pas présente, l'interface utilisateur affichera une icône par défaut à la place.
- Dans une version future, l'application pourra générer automatiquement des avatars pour les personnages avec des modèles de diffusion.
