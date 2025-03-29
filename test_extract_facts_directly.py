"""
Script de test pour l'extraction de faits directement depuis le gestionnaire de mémoire
"""

from backend.services.memory_manager import memory_manager
from backend.models.memory import MemoryCreate
import sys
import os

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_extract_facts_directly():
    """
    Teste directement la fonction d'extraction de faits sans passer par l'API
    """
    print("Test d'extraction de faits directement depuis le gestionnaire de mémoire")

    # Créer une mémoire test avec différents types d'informations
    test_content = """
    Bonjour ! Je m'appelle Marc et j'ai 28 ans. Je vis actuellement à Montréal, mais j'ai grandi à Québec.
    Mon père s'appelle Jean et ma mère s'appelle Sophie. J'ai une sœur qui s'appelle Émilie.
    J'adore vraiment le cinéma et les jeux vidéo, mais je déteste faire le ménage.
    Je suis développeur informatique et je travaille sur des projets passionnants.
    Hier soir, je suis allé au restaurant avec des amis. Demain, j'ai prévu d'aller au parc.
    Je me sens très heureux aujourd'hui, car j'ai reçu une bonne nouvelle.
    J'aime beaucoup le chocolat et le café, mais je n'aime pas les épinards.
    """

    print("\nContenu de test:")
    print(test_content)

    # Créer une mémoire temporaire pour le test
    test_memory = MemoryCreate(
        character_id=1,  # ID du personnage de test
        type="conversation",
        content=test_content,
        importance=1.0
    )

    # Créer la mémoire dans la base de données
    memory_id = memory_manager.create_memory(test_memory)
    print(f"Mémoire créée avec l'ID: {memory_id}")

    # Récupérer les faits extraits
    from backend.utils.db import db_manager
    facts = db_manager.execute_query(
        "SELECT * FROM facts WHERE source_memory_id = ?", (memory_id,))

    if not facts:
        print("Aucun fait n'a été extrait")
        return

    # Afficher les faits extraits
    print(f"\n{len(facts)} faits extraits:")

    # Organiser les faits par prédicat
    facts_by_predicate = {}
    for fact in facts:
        predicate = fact["predicate"].split()[0]
        if predicate not in facts_by_predicate:
            facts_by_predicate[predicate] = []
        facts_by_predicate[predicate].append(fact)

    # Afficher les faits par catégorie
    for predicate, predicate_facts in facts_by_predicate.items():
        print(f"\n--- Catégorie: {predicate} ---")
        for fact in predicate_facts:
            confidence = fact.get("confidence", 0.0)
            confidence_stars = "*" * int(confidence * 5)
            print(
                f"  [{confidence_stars}] {fact['subject']} {fact['predicate']} {fact['object']}")


if __name__ == "__main__":
    test_extract_facts_directly()
