# 🚀 Guide de démarrage rapide - Alezia AI

Ce guide vous permet de démarrer Alezia AI en quelques minutes.

## Prérequis rapides

- ✅ Python 3.8+ installé
- ✅ Ollama installé et fonctionnel
- ✅ 8 Go de RAM minimum
- ✅ Connexion internet (pour télécharger les modèles)

## Installation express

### 1. Télécharger et configurer

```bash
# Cloner le projet
git clone https://github.com/votre-repo/alezia-ai.git
cd alezia-ai

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
# Sur Windows :
venv\Scripts\activate
# Sur Linux/macOS :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configurer Ollama

Assurez-vous qu'Ollama est démarré, puis installez un modèle :

```bash
# Modèle léger et rapide (recommandé pour débuter)
ollama pull gemma:2b

# OU modèle plus puissant (si vous avez 16+ Go RAM)
ollama pull llama3
```

### 3. Initialiser la base de données

```bash
python init_db.py
```

### 4. Démarrer l'application

```bash
python run_api.py
```

L'application trouvera automatiquement un port disponible et vous indiquera l'URL à utiliser.

## Première utilisation

1. **Ouvrez votre navigateur** à l'adresse indiquée (ex: http://localhost:8000)

2. **Créez votre premier personnage** :
   - Cliquez sur "Nouveau personnage"
   - Donnez-lui un nom et une description
   - Définissez sa personnalité
   - Cliquez sur "Créer"

3. **Commencez à discuter** :
   - Sélectionnez le personnage créé
   - Tapez votre premier message
   - Le personnage vous répondra selon sa personnalité !

## Scripts automatiques (Windows)

Si vous êtes sur Windows, utilisez ces scripts pour encore plus de simplicité :

```powershell
# Installer automatiquement un modèle compatible
.\install_models.ps1

# Démarrer l'API
.\start_api.ps1
```

## Résolution rapide des problèmes

### ❌ "Modèle AI non chargé"
```bash
# Vérifiez qu'Ollama fonctionne
ollama list

# Si aucun modèle, installez-en un
ollama pull gemma:2b
```

### ❌ "Port déjà utilisé"
Le script `run_api.py` trouve automatiquement un port libre. Regardez le message dans la console pour connaître le bon port.

### ❌ "Erreur de dépendances"
```bash
# Réinstallez les dépendances
pip install -r requirements.txt --force-reinstall
```

## Structure rapide du projet

```
alezia-ai/
├── run_api.py          # 🚀 Fichier principal à exécuter
├── init_db.py          # 🗄️ Initialisation de la base de données
├── frontend/           # 🌐 Interface web
├── backend/            # ⚙️ API et logique métier
└── data/               # 💾 Données et cache
```

## Commandes utiles

| Action | Commande |
|--------|----------|
| Démarrer l'app | `python run_api.py` |
| Réinitialiser la DB | `python init_db.py` |
| Voir les modèles Ollama | `ollama list` |
| Tester l'API | `python backend/check_api.py` |

---

**🎯 Objectif atteint !** Vous devriez maintenant avoir Alezia AI qui fonctionne et pouvoir créer vos premiers personnages IA.

Pour plus de détails, consultez le [README.md](README.md) complet.