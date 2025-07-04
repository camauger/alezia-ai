"""
Script pour optimiser Ollama pour NVIDIA RTX 4060 Laptop GPU (8 Go VRAM)
Ce script crée un fichier de configuration et un Modelfile optimisés
"""

import json
import os
import sys
from pathlib import Path

# Répertoire actuel
script_dir = Path(__file__).resolve().parent


def create_config_directory():
    """Crée le répertoire de configuration Ollama si nécessaire"""
    home_dir = Path.home()
    config_dir = home_dir / '.ollama'

    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        print(f'Répertoire de configuration créé: {config_dir}')

    return config_dir


def create_ollama_config(config_dir):
    """Crée le fichier de configuration Ollama optimisé pour RTX 4060"""
    config_file = config_dir / 'config.json'

    config = {
        'gpu_layers': 35,  # Optimisé pour 8 Go VRAM
        'compute': 'cuda',  # Utiliser CUDA pour le GPU NVIDIA
        'numa': False,  # Désactiver NUMA pour les ordinateurs portables
        'tensorSplit': [0, 0, 1],  # Tout sur GPU pour de meilleures performances
    }

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f'Configuration Ollama optimisée créée: {config_file}')
    print('Paramètres optimisés pour RTX 4060 Laptop GPU (8 Go VRAM)')


def create_modelfile():
    """Crée un Modelfile pour un modèle RP non censuré"""
    modelfile_path = script_dir / 'Modelfile'

    modelfile_content = """
FROM mistral
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

    with open(modelfile_path, 'w') as f:
        f.write(modelfile_content.strip())

    print(f'Modelfile créé: {modelfile_path}')
    return modelfile_path


def print_manual_instructions():
    """Affiche les instructions manuelles pour terminer l'optimisation"""
    print("\n=== Instructions manuelles pour terminer l'optimisation ===")
    print("\n1. Assurez-vous que le service Ollama est en cours d'exécution")
    print("   - Exécutez l'application 'Ollama App' depuis le menu Démarrer")

    print('\n2. Téléchargez le modèle de base')
    print('   - Ouvrez un terminal PowerShell ou Command Prompt')
    print(
        '   - Exécutez: & "C:\\Users\\camauger\\AppData\\Local\\Programs\\Ollama\\ollama.exe" "pull" "mistral"'
    )

    print('\n3. Créez votre modèle personnalisé à partir du Modelfile')
    print('   - Dans le même terminal, naviguez vers le répertoire du projet:')
    print('   - cd', script_dir)
    print(
        '   - Exécutez: & "C:\\Users\\camauger\\AppData\\Local\\Programs\\Ollama\\ollama.exe" "create" "roleplay-uncensored" "-f" "Modelfile"'
    )

    print("\n4. Lancez l'API backend")
    print('   - Dans un terminal, naviguez vers le répertoire backend:')
    print('   - cd', script_dir / 'backend')
    print('   - Exécutez: python app.py')


def main():
    """Fonction principale"""
    print("=== Optimisation d'Ollama pour RTX 4060 Laptop GPU ===")

    # Vérifier le chemin de l'exécutable Ollama
    ollama_path = r'C:\Users\camauger\AppData\Local\Programs\Ollama\ollama.exe'
    if not os.path.exists(ollama_path):
        print(
            f"ATTENTION: Ollama n'a pas été trouvé à l'emplacement attendu: {ollama_path}"
        )
        print(
            "L'optimisation continuera, mais vous devrez peut-être ajuster les commandes manuelles"
        )
    else:
        print(f'Ollama trouvé à: {ollama_path}')

    # Créer le répertoire de configuration
    config_dir = create_config_directory()

    # Créer le fichier de configuration
    create_ollama_config(config_dir)

    # Créer le Modelfile
    create_modelfile()

    # Afficher les instructions manuelles
    print_manual_instructions()

    print('\n=== Optimisation terminée avec succès ===')
    print(
        "Les fichiers de configuration ont été créés. Suivez les instructions ci-dessus pour terminer l'installation."
    )

    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
