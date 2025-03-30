#!/usr/bin/env python3

"""
Script de test pour démontrer l'évolution des traits de personnalité
en simulant des interactions directes.
"""

from models.character import CharacterCreate
from services.character_manager import CharacterManager
import sys
import logging
import time
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au chemin Python pour permettre les imports absolus
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importation des services nécessaires


def display_traits(traits):
    """Affiche les traits de personnalité avec une visualisation"""
    print("\n=== TRAITS ACTUELS ===")

    for trait in traits.traits:
        # Créer une barre de visualisation pour le trait (-1.0 à 1.0)
        bar_length = 30
        middle = bar_length // 2
        position = int(middle + (trait.value * middle))

        bar = ["•"] * bar_length
        bar[middle] = "│"  # Marque le 0
        bar[position] = "▓"  # Position actuelle

        # Ajouter des couleurs
        if trait.value > 0:
            bar_str = "".join(bar[:middle]) + "\033[32m" + \
                "".join(bar[middle:]) + "\033[0m"
        else:
            bar_str = "\033[31m" + \
                "".join(bar[:middle]) + "\033[0m" + "".join(bar[middle:])

        print(
            f"{trait.name:20} [{bar_str}] {trait.value:+.2f} ({trait.category})")


def test_trait_evolution(character_id, character_manager, messages):
    """Test l'évolution des traits de personnalité avec des interactions directes"""
    # Afficher les traits initiaux
    print("\n--- TRAITS DE PERSONNALITÉ INITIAUX ---")
    initial_traits = character_manager.get_personality_traits(character_id)
    display_traits(initial_traits)

    # Simuler des interactions avec différents messages
    for i, message in enumerate(messages):
        print(f"\n[Message {i+1}/{len(messages)}] Interaction: \"{message}\"")

        # Traits avant l'interaction
        traits_before = character_manager.get_personality_traits(character_id)

        # Simuler une interaction directe avec ce message
        changes = character_manager.update_traits_from_interaction(
            character_id,
            message,
            intensity=1.0  # Intensité maximale pour mieux voir les changements
        )

        # Si des changements ont été détectés, les afficher
        if changes:
            print("\n--- CHANGEMENTS DE TRAITS ---")
            for change in changes:
                direction = "↑" if change["change"] > 0 else "↓"
                print(
                    f"{change['trait_name']}: {change['old_value']:.2f} → {change['new_value']:.2f} {direction} ({change['change']:+.2f})")
                print(f"  Raison: {change['reason']}")
        else:
            print("\nAucun changement détecté pour cette interaction.")

        time.sleep(0.5)  # Pause pour mieux voir les changements

    # Afficher les traits finaux
    print("\n--- TRAITS DE PERSONNALITÉ FINAUX ---")
    final_traits = character_manager.get_personality_traits(character_id)
    display_traits(final_traits)

    # Comparer avec les traits initiaux
    print("\n--- ÉVOLUTION TOTALE ---")
    for initial_trait in initial_traits.traits:
        final_trait = next(
            (t for t in final_traits.traits if t.name == initial_trait.name), None)
        if final_trait:
            total_change = final_trait.value - initial_trait.value
            direction = "↑" if total_change > 0 else (
                "↓" if total_change < 0 else "→")
            print(f"{initial_trait.name}: {initial_trait.value:.2f} → {final_trait.value:.2f} {direction} ({total_change:+.2f})")


def create_test_character():
    """Crée un personnage de test"""
    character_manager = CharacterManager()

    # Définir les traits initiaux
    initial_traits = [
        {
            "name": "extraversion",
            "value": 0.0,
            "category": "social",
            "description": "Tendance à rechercher la stimulation dans le monde extérieur",
            "volatility": 0.3
        },
        {
            "name": "agréabilité",
            "value": 0.2,
            "category": "social",
            "description": "Tendance à être compatissant et coopératif envers les autres",
            "volatility": 0.3
        },
        {
            "name": "conscienciosité",
            "value": 0.1,
            "category": "comportemental",
            "description": "Tendance à être organisé et à penser aux conséquences",
            "volatility": 0.2
        },
        {
            "name": "stabilité émotionnelle",
            "value": 0.0,
            "category": "émotionnel",
            "description": "Tendance à rester calme face au stress",
            "volatility": 0.4
        },
        {
            "name": "ouverture",
            "value": 0.3,
            "category": "cognitif",
            "description": "Tendance à être ouvert aux nouvelles expériences",
            "volatility": 0.3
        },
        {
            "name": "curiosité",
            "value": 0.4,
            "category": "cognitif",
            "description": "Tendance à vouloir explorer et apprendre",
            "volatility": 0.4
        },
        {
            "name": "impulsivité",
            "value": -0.2,
            "category": "comportemental",
            "description": "Tendance à agir sans réfléchir",
            "volatility": 0.5
        }
    ]

    # Créer le personnage
    character = CharacterCreate(
        name="Emma (Test)",
        description="Une femme de 28 ans, professeure d'histoire passionnée par les voyages",
        personality="Intelligente, curieuse et sociable, Emma apprécie les conversations enrichissantes. Elle peut parfois être analytique et réservée.",
        backstory="Originaire d'une petite ville, Emma a toujours rêvé de découvrir le monde. Après ses études, elle est devenue professeure d'histoire, ce qui lui permet de partager sa passion et de voyager pendant les vacances.",
        universe_id=1,
        initial_traits=initial_traits
    )

    character_id = character_manager.create_character(character)
    logger.info(f"Personnage de test créé avec l'ID: {character_id}")

    return character_id


def main():
    """Fonction principale"""
    logger.info("Démarrage du test d'évolution des traits de personnalité")

    # Créer un personnage de test
    character_id = create_test_character()

    # Initialiser le gestionnaire de personnages
    character_manager = CharacterManager()

    # Série de messages pour tester différents aspects de la personnalité
    messages = [
        # Messages pour tester l'extraversion (social vs introspectif)
        "J'aimerais organiser une grande fête avec tous nos amis ce week-end. On pourrait inviter beaucoup de monde et faire un grand rassemblement!",
        "Je préfère parfois rester seul pour réfléchir et méditer dans un environnement calme et tranquille.",

        # Messages pour tester l'agréabilité (empathie vs antagonisme)
        "Je comprends vraiment ton point de vue et j'apprécie ton aide. Merci beaucoup pour ton soutien et ta gentillesse.",
        "Je suis vraiment frustré et en colère contre cette situation stupide. Tout m'énerve aujourd'hui.",

        # Messages pour tester la curiosité
        "Pourquoi les civilisations anciennes ont-elles disparu? J'ai découvert un nouveau livre fascinant sur les dernières découvertes archéologiques et je me pose beaucoup de questions.",
        "Je ne vois pas l'intérêt d'apprendre toutes ces choses. À quoi ça sert de se poser des questions sur des choses qu'on ne peut pas changer?",

        # Messages pour tester l'impulsivité
        "Je vais faire ça tout de suite sans réfléchir! Agissons maintenant, spontanément, et on verra bien ce qui se passe!",
        "Je pense qu'il faut attendre, réfléchir et planifier soigneusement avant de prendre une décision aussi importante."
    ]

    # Lancer le test
    test_trait_evolution(character_id, character_manager, messages)

    # Afficher l'historique des changements
    print("\n=== HISTORIQUE DES CHANGEMENTS ===")
    history = character_manager.get_trait_history(character_id)
    for entry in history:
        change_symbol = "↑" if entry.change_amount > 0 else (
            "↓" if entry.change_amount < 0 else "→")
        print(f"{entry.timestamp.strftime('%H:%M:%S')} - {entry.trait_name}: {entry.old_value:.2f} → {entry.new_value:.2f} {change_symbol} ({entry.change_amount:+.2f})")
        print(f"  Raison: {entry.reason}")

    logger.info("Test d'évolution des traits terminé")


if __name__ == "__main__":
    main()
