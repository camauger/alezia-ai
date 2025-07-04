#!/usr/bin/env python3

"""
Script to test the evolution of personality traits
by simulating direct interactions.
"""

import logging
import sys
import time
from pathlib import Path

from models.character import CharacterCreate
from services.character_manager import CharacterManager

# Add the parent directory to the Python path to allow absolute imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import necessary services


def display_traits(traits):
    """Displays personality traits with a visualization"""
    print("\n=== CURRENT TRAITS ===")

    for trait in traits.traits:
        # Create a visualization bar for the trait (-1.0 to 1.0)
        bar_length = 30
        middle = bar_length // 2
        position = int(middle + (trait.value * middle))

        bar = ["•"] * bar_length
        bar[middle] = "│"  # Mark the 0
        bar[position] = "▓"  # Current position

        # Add colors
        if trait.value > 0:
            bar_str = "".join(bar[:middle]) + "\033[32m" + \
                "".join(bar[middle:]) + "\033[0m"
        else:
            bar_str = "\033[31m" + \
                "".join(bar[:middle]) + "\033[0m" + "".join(bar[middle:])

        print(
            f"{trait.name:20} [{bar_str}] {trait.value:+.2f} ({trait.category})")


def test_trait_evolution(character_id, character_manager, messages):
    """Tests the evolution of personality traits with direct interactions"""
    # Display initial traits
    print("\n--- INITIAL PERSONALITY TRAITS ---")
    initial_traits = character_manager.get_personality_traits(character_id)
    display_traits(initial_traits)

    # Simulate interactions with different messages
    for i, message in enumerate(messages):
        print(f"\n[Message {i+1}/{len(messages)}] Interaction: \"{message}\"")

        # Simulate a direct interaction with this message
        changes = character_manager.update_traits_from_interaction(
            character_id,
            message,
            intensity=1.0  # Maximum intensity to better see the changes
        )

        # If changes were detected, display them
        if changes:
            print("\n--- TRAIT CHANGES ---")
            for change in changes:
                direction = "↑" if change["change"] > 0 else "↓"
                print(
                    f"{change['trait_name']}: {change['old_value']:.2f} → {change['new_value']:.2f} {direction} ({change['change']:+.2f})")
                print(f"  Reason: {change['reason']}")
        else:
            print("\nNo changes detected for this interaction.")

        time.sleep(0.5)  # Pause to better see the changes

    # Display final traits
    print("\n--- FINAL PERSONALITY TRAITS ---")
    final_traits = character_manager.get_personality_traits(character_id)
    display_traits(final_traits)

    # Compare with initial traits
    print("\n--- TOTAL EVOLUTION ---")
    for initial_trait in initial_traits.traits:
        final_trait = next(
            (t for t in final_traits.traits if t.name == initial_trait.name), None)
        if final_trait:
            total_change = final_trait.value - initial_trait.value
            direction = "↑" if total_change > 0 else (
                "↓" if total_change < 0 else "→")
            print(f"{initial_trait.name}: {initial_trait.value:.2f} → {final_trait.value:.2f} {direction} ({total_change:+.2f})")


def create_test_character():
    """Creates a test character"""
    character_manager = CharacterManager()

    # Define initial traits
    initial_traits = [
        {
            "name": "extraversion",
            "value": 0.0,
            "category": "social",
            "description": "Tendency to seek stimulation in the external world",
            "volatility": 0.3
        },
        {
            "name": "agreeableness",
            "value": 0.2,
            "category": "social",
            "description": "Tendency to be compassionate and cooperative towards others",
            "volatility": 0.3
        },
        {
            "name": "conscientiousness",
            "value": 0.1,
            "category": "behavioral",
            "description": "Tendency to be organized and think about consequences",
            "volatility": 0.2
        },
        {
            "name": "emotional stability",
            "value": 0.0,
            "category": "emotional",
            "description": "Tendency to remain calm under stress",
            "volatility": 0.4
        },
        {
            "name": "openness",
            "value": 0.3,
            "category": "cognitive",
            "description": "Tendency to be open to new experiences",
            "volatility": 0.3
        },
        {
            "name": "curiosity",
            "value": 0.4,
            "category": "cognitive",
            "description": "Tendency to want to explore and learn",
            "volatility": 0.4
        },
        {
            "name": "impulsiveness",
            "value": -0.2,
            "category": "behavioral",
            "description": "Tendency to act without thinking",
            "volatility": 0.5
        }
    ]

    # Create the character
    character = CharacterCreate(
        name="Emma (Test)",
        description="A 28-year-old woman, a history teacher passionate about travel",
        personality="Intelligent, curious, and sociable, Emma enjoys enriching conversations. She can sometimes be analytical and reserved.",
        backstory="Originally from a small town, Emma has always dreamed of discovering the world. After her studies, she became a history teacher, which allows her to share her passion and travel during the holidays.",
        universe_id=1,
        initial_traits=initial_traits
    )

    character_id = character_manager.create_character(character)
    logger.info(f"Test character created with ID: {character_id}")

    return character_id


def main():
    """Main function"""
    logger.info("Starting the personality trait evolution test")

    # Create a test character
    character_id = create_test_character()

    # Initialize the character manager
    character_manager = CharacterManager()

    # Series of messages to test different aspects of personality
    messages = [
        # Messages to test extraversion (social vs. introspective)
        "I would like to organize a big party with all our friends this weekend. We could invite a lot of people and have a big gathering!",
        "I sometimes prefer to be alone to think and meditate in a calm and quiet environment.",

        # Messages to test agreeableness (empathy vs. antagonism)
        "I really understand your point of view and I appreciate your help. Thank you very much for your support and kindness.",
        "I'm really frustrated and angry about this stupid situation. Everything is annoying me today.",

        # Messages to test curiosity
        "Why did ancient civilizations disappear? I discovered a fascinating new book on the latest archaeological discoveries and I have a lot of questions.",
        "I don't see the point of learning all these things. What's the use of asking questions about things we can't change?",

        # Messages to test impulsiveness
        "I'll do it right away without thinking! Let's act now, spontaneously, and we'll see what happens!",
        "I think we need to wait, think, and plan carefully before making such an important decision."
    ]

    # Run the test
    test_trait_evolution(character_id, character_manager, messages)

    # Display the change history
    print("\n=== CHANGE HISTORY ===")
    history = character_manager.get_trait_history(character_id)
    for entry in history:
        change_symbol = "↑" if entry.change_amount > 0 else (
            "↓" if entry.change_amount < 0 else "→")
        print(f"{entry.timestamp.strftime('%H:%M:%S')} - {entry.trait_name}: {entry.old_value:.2f} → {entry.new_value:.2f} {change_symbol} ({entry.change_amount:+.2f})")
        print(f"  Reason: {entry['reason']}")

    logger.info("Trait evolution test finished")


if __name__ == "__main__":
    main()
