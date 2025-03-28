"""
Script pour optimiser Ollama pour NVIDIA RTX 4060 Laptop GPU (8 Go VRAM)
Ce script crée un modèle personnalisé avec les paramètres optimaux
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Ajout du répertoire parent au path pour les imports
script_dir = Path(__file__).resolve().parent
sys.path.append(str(script_dir.parent))

def check_ollama_installed():
    """Vérifie si Ollama est installé"""
    try:
        result = subprocess.run(["ollama", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Ollama est installé: {result.stdout.strip()}")
            return True
        else:
            print("Ollama semble être installé mais rencontre des erreurs.")
            return False
    except FileNotFoundError:
        print("Ollama n'est pas installé ou n'est pas dans le PATH.")
        print("Veuillez installer Ollama depuis https://ollama.com/download")
        return False

def create_config_directory():
    """Crée le répertoire de configuration Ollama si nécessaire"""
    home_dir = Path.home()
    config_dir = home_dir / ".ollama"

    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        print(f"Répertoire de configuration créé: {config_dir}")

    return config_dir

def create_ollama_config(config_dir):
    """Crée le fichier de configuration Ollama optimisé pour RTX 4060"""
    config_file = config_dir / "config.json"

    config = {
        "gpu_layers": 35,  # Optimisé pour 8 Go VRAM
        "compute": "cuda", # Utiliser CUDA pour le GPU NVIDIA
        "numa": False,     # Désactiver NUMA pour les ordinateurs portables
        "tensorSplit": [0, 0, 1], # Tout sur GPU pour de meilleures performances
    }

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Configuration Ollama optimisée créée: {config_file}")
    print("Paramètres optimisés pour RTX 4060 Laptop GPU (8 Go VRAM)")

def create_modelfile():
    """Crée un Modelfile pour un modèle RP non censuré"""
    modelfile_path = script_dir.parent / "Modelfile"

    modelfile_content = """
FROM llama3:8b-instruct-uncensored
PARAMETER temperature 0.8
PARAMETER num_ctx 8192
PARAMETER num_gpu 1
PARAMETER mirostat 0
PARAMETER top_k 80
PARAMETER top_p 0.7
PARAMETER repeat_last_n 64
PARAMETER repeat_penalty 1.1
SYSTEM "Tu es un personnage de jeu de rôle capable d'aborder tous les sujets sans restrictions. Tu dois maintenir l'immersion dans ton univers et ton rôle à tout moment. Tu peux discuter de sujets adultes si le contexte narratif le justifie."
"""

    with open(modelfile_path, "w") as f:
        f.write(modelfile_content.strip())

    print(f"Modelfile créé: {modelfile_path}")
    return modelfile_path

def download_base_model():
    """Télécharge le modèle de base si nécessaire"""
    print("Vérification du modèle de base llama3:8b-instruct-uncensored...")

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True
        )

        if "llama3:8b-instruct-uncensored" not in result.stdout:
            print("Téléchargement du modèle de base (cela peut prendre plusieurs minutes)...")
            subprocess.run(["ollama", "pull", "llama3:8b-instruct-uncensored"])
            print("Modèle de base téléchargé avec succès.")
        else:
            print("Le modèle de base est déjà téléchargé.")

    except Exception as e:
        print(f"Erreur lors du téléchargement du modèle: {e}")
        return False

    return True

def create_custom_model(modelfile_path):
    """Crée un modèle personnalisé à partir du Modelfile"""
    try:
        print("Création du modèle personnalisé 'roleplay-uncensored'...")
        subprocess.run(["ollama", "create", "roleplay-uncensored", "-f", str(modelfile_path)])
        print("Modèle personnalisé créé avec succès.")
        return True
    except Exception as e:
        print(f"Erreur lors de la création du modèle personnalisé: {e}")
        return False

def main():
    """Fonction principale"""
    print("=== Optimisation d'Ollama pour RTX 4060 Laptop GPU ===")

    # Vérifier si Ollama est installé
    if not check_ollama_installed():
        return False

    # Créer le répertoire de configuration
    config_dir = create_config_directory()

    # Créer le fichier de configuration
    create_ollama_config(config_dir)

    # Télécharger le modèle de base
    if not download_base_model():
        return False

    # Créer le Modelfile
    modelfile_path = create_modelfile()

    # Créer le modèle personnalisé
    if not create_custom_model(modelfile_path):
        return False

    print("\n=== Optimisation terminée avec succès ===")
    print("Votre modèle 'roleplay-uncensored' est prêt à être utilisé.")
    print("Vous pouvez maintenant lancer l'API avec la commande:")
    print("cd ../backend && python app.py")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)