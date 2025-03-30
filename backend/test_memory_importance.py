"""
Script de test pour le système de pondération des mémoires
"""

from backend.utils.db import db_manager
from backend.services.memory_manager import memory_manager
from backend.models.memory import MemoryCreate
import sys
import os
import json
import datetime
from pprint import pprint

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_memory_importance():
    """Teste les fonctionnalités de pondération des mémoires"""
    print("\n=== TEST DU SYSTÈME DE PONDÉRATION DES MÉMOIRES ===\n")

    # Créer un personnage de test s'il n'existe pas
    character_id = get_or_create_test_character()

    # 1. Tester le calcul d'importance sur différents types de mémoires
    test_importance_calculation(character_id)

    # 2. Tester la réévaluation de l'importance lors de la récupération
    test_importance_reevaluation(character_id)

    # 3. Tester la dégradation des mémoires anciennes
    test_memory_decay(character_id)

    # 4. Tester la consolidation des mémoires similaires
    test_memory_consolidation(character_id)

    print("\n=== FIN DES TESTS DE PONDÉRATION ===\n")


def get_or_create_test_character():
    """Récupère ou crée un personnage de test pour les expériences"""
    query = "SELECT id FROM characters WHERE name = 'Personnage de Test'"
    characters = db_manager.execute_query(query)

    if characters:
        character_id = characters[0]["id"]
        print(
            f"Utilisation du personnage de test existant (ID: {character_id})")
    else:
        # Créer un personnage de test
        character_data = {
            "name": "Personnage de Test",
            "description": "Personnage utilisé pour tester le système de mémoire",
            "personality": "Curieux et analytique",
            "backstory": "Créé spécifiquement pour des tests automatisés",
            "universe_id": 1
        }
        character_id = db_manager.insert("characters", character_data)
        print(f"Personnage de test créé avec l'ID: {character_id}")

    return character_id


def test_importance_calculation(character_id):
    """Teste le calcul d'importance initial des mémoires"""
    print("\n--- Test du calcul d'importance ---")

    # Exemples de mémoires avec différents contenus et types
    test_memories = [
        {
            "type": "conversation",
            "content": "Salut, comment vas-tu ?",
            "expected_range": (0.5, 2.0)
        },
        {
            "type": "event",
            "content": "Je suis allé au cinéma hier soir avec mes amis. J'ai adoré le film !",
            "expected_range": (2.0, 4.0)
        },
        {
            "type": "observation",
            "content": "Il pleut dehors.",
            "expected_range": (0.2, 1.5)
        },
        {
            "type": "user_message",
            "content": "Mon nom est Pierre et j'habite à Paris. J'ai 34 ans et je travaille comme ingénieur.",
            "expected_range": (3.0, 5.0)
        },
        {
            "type": "user_message",
            "content": "Je suis très heureux aujourd'hui car j'ai reçu une excellente nouvelle ! C'est vraiment important pour moi.",
            "expected_range": (3.0, 6.0)
        }
    ]

    for i, memory_data in enumerate(test_memories):
        # Créer la mémoire
        memory = MemoryCreate(
            character_id=character_id,
            type=memory_data["type"],
            content=memory_data["content"],
            importance=1.0  # Valeur par défaut, sera recalculée
        )

        # Calculer l'importance manuellement pour comparaison
        calculated_importance = memory_manager._calculate_memory_importance(
            memory_data["content"],
            memory_data["type"]
        )

        # Créer la mémoire en base de données
        memory_id = memory_manager.create_memory(memory)

        # Récupérer la mémoire créée
        created_memory = db_manager.get_by_id("memories", memory_id)

        print(f"\nMémoire {i+1}:")
        print(f"Type: {memory_data['type']}")
        print(f"Contenu: {memory_data['content'][:50]}..." if len(
            memory_data["content"]) > 50 else f"Contenu: {memory_data['content']}")
        print(
            f"Importance attendue: entre {memory_data['expected_range'][0]} et {memory_data['expected_range'][1]}")
        print(f"Importance calculée: {calculated_importance:.2f}")
        print(f"Importance stockée: {created_memory['importance']:.2f}")

        # Vérifier que l'importance est dans la plage attendue
        min_expected, max_expected = memory_data["expected_range"]
        if min_expected <= created_memory["importance"] <= max_expected:
            print("✅ L'importance est dans la plage attendue")
        else:
            print("❌ L'importance n'est PAS dans la plage attendue")


def test_importance_reevaluation(character_id):
    """Teste la réévaluation de l'importance lors de l'accès aux mémoires"""
    print("\n--- Test de la réévaluation d'importance ---")

    # Créer une mémoire pour le test
    memory = MemoryCreate(
        character_id=character_id,
        type="conversation",
        content="Ceci est un message important que je vais consulter plusieurs fois.",
        importance=2.0
    )

    memory_id = memory_manager.create_memory(memory)
    print(f"Mémoire créée avec ID: {memory_id}")

    # Simuler des accès répétés
    print("\nSimulation de 10 accès à la mémoire...")
    initial_memory = db_manager.get_by_id("memories", memory_id)
    initial_importance = initial_memory["importance"]

    for i in range(10):
        # Simuler un accès
        memory_manager.get_memory(memory_id)

        # Vérifier après certains accès
        if i in [0, 4, 9]:
            current_memory = db_manager.get_by_id("memories", memory_id)
            print(f"Après {i+1} accès - Importance: {current_memory['importance']:.2f}, "
                  f"Compteur d'accès: {current_memory['access_count']}")

    # Vérifier l'augmentation d'importance
    final_memory = db_manager.get_by_id("memories", memory_id)
    print(f"\nImportance initiale: {initial_importance:.2f}")
    print(f"Importance finale: {final_memory['importance']:.2f}")

    if final_memory["importance"] > initial_importance:
        print("✅ L'importance a augmenté avec les accès répétés")
    else:
        print("❌ L'importance n'a PAS augmenté comme prévu")


def test_memory_decay(character_id):
    """Teste la dégradation des mémoires anciennes"""
    print("\n--- Test de la dégradation des mémoires anciennes ---")

    # 1. Créer des mémoires avec différentes dates
    # Mémoire récente (ne devrait pas être dégradée)
    recent_memory = MemoryCreate(
        character_id=character_id,
        type="observation",
        content="Ceci est une mémoire récente qui ne devrait pas être dégradée.",
        importance=3.0
    )
    recent_id = memory_manager.create_memory(recent_memory)

    # Mémoire ancienne de faible importance
    old_memory_low = MemoryCreate(
        character_id=character_id,
        type="conversation",
        content="Ceci est une vieille mémoire de faible importance qui devrait être dégradée.",
        importance=2.0
    )
    old_low_id = memory_manager.create_memory(old_memory_low)

    # Mémoire ancienne de haute importance
    old_memory_high = MemoryCreate(
        character_id=character_id,
        type="event",
        content="Ceci est une vieille mémoire de haute importance qui ne devrait pas être dégradée beaucoup.",
        importance=7.5
    )
    old_high_id = memory_manager.create_memory(old_memory_high)

    # Modifier manuellement les dates de création pour simuler des mémoires anciennes
    db_manager.execute_query(
        "UPDATE memories SET created_at = ? WHERE id = ?",
        (datetime.datetime.now() - datetime.timedelta(days=180), old_low_id)
    )
    db_manager.execute_query(
        "UPDATE memories SET created_at = ? WHERE id = ?",
        (datetime.datetime.now() - datetime.timedelta(days=200), old_high_id)
    )

    print("\nMémoires créées pour le test de dégradation:")
    print(f"- Récente (ID: {recent_id}): ne devrait pas être dégradée")
    print(
        f"- Ancienne de faible importance (ID: {old_low_id}): devrait être fortement dégradée")
    print(
        f"- Ancienne de haute importance (ID: {old_high_id}): devrait être légèrement dégradée")

    # Enregistrer les importances initiales
    initial_importances = {
        "recent": db_manager.get_by_id("memories", recent_id)["importance"],
        "old_low": db_manager.get_by_id("memories", old_low_id)["importance"],
        "old_high": db_manager.get_by_id("memories", old_high_id)["importance"]
    }

    # Appliquer la dégradation avec un seuil bas pour tester
    print("\nApplication de la dégradation des mémoires (seuil: 30 jours)...")
    update_count = memory_manager.decay_old_memories(
        character_id, days_threshold=30)
    print(f"Nombre de mémoires dégradées: {update_count}")

    # Vérifier les nouvelles importances
    final_importances = {
        "recent": db_manager.get_by_id("memories", recent_id)["importance"],
        "old_low": db_manager.get_by_id("memories", old_low_id)["importance"],
        "old_high": db_manager.get_by_id("memories", old_high_id)["importance"]
    }

    print("\nRésultats de la dégradation:")
    print(
        f"- Récente: {initial_importances['recent']:.2f} -> {final_importances['recent']:.2f}")
    print(
        f"- Ancienne (faible): {initial_importances['old_low']:.2f} -> {final_importances['old_low']:.2f}")
    print(
        f"- Ancienne (haute): {initial_importances['old_high']:.2f} -> {final_importances['old_high']:.2f}")

    # Vérifier que la dégradation a fonctionné comme prévu
    if final_importances['recent'] == initial_importances['recent']:
        print("✅ La mémoire récente n'a pas été dégradée (correct)")
    else:
        print("❌ La mémoire récente a été dégradée (incorrect)")

    if final_importances['old_low'] < initial_importances['old_low']:
        print("✅ La mémoire ancienne de faible importance a été dégradée (correct)")
    else:
        print("❌ La mémoire ancienne de faible importance n'a pas été dégradée (incorrect)")

    if final_importances['old_high'] <= initial_importances['old_high']:
        if final_importances['old_high'] == initial_importances['old_high']:
            print("✅ La mémoire ancienne de haute importance n'a pas été dégradée en raison de son importance élevée")
        else:
            print("✅ La mémoire ancienne de haute importance a été légèrement dégradée")
    else:
        print("❌ La mémoire ancienne de haute importance a été augmentée (incorrect)")


def test_memory_consolidation(character_id):
    """Teste la consolidation des mémoires similaires"""
    print("\n--- Test de la consolidation des mémoires ---")

    # Créer des mémoires similaires
    similar_content1 = "J'aime vraiment beaucoup la musique classique, surtout les œuvres de Mozart."
    similar_content2 = "J'adore énormément la musique classique, particulièrement les compositions de Mozart."

    memory1 = MemoryCreate(
        character_id=character_id,
        type="observation",
        content=similar_content1,
        importance=2.5
    )

    memory2 = MemoryCreate(
        character_id=character_id,
        type="observation",
        content=similar_content2,
        importance=2.0
    )

    # Créer une mémoire différente
    different_memory = MemoryCreate(
        character_id=character_id,
        type="observation",
        content="Je préfère la cuisine italienne à la cuisine française.",
        importance=2.2
    )

    # Créer les mémoires
    id1 = memory_manager.create_memory(memory1)
    id2 = memory_manager.create_memory(memory2)
    id3 = memory_manager.create_memory(different_memory)

    print("\nMémoires créées pour le test de consolidation:")
    print(f"- Mémoire 1 (ID: {id1}): \"{similar_content1}\"")
    print(f"- Mémoire 2 (ID: {id2}): \"{similar_content2}\"")
    print(f"- Mémoire 3 (ID: {id3}): \"{different_memory.content}\"")

    # Exécuter la consolidation
    print("\nExécution de la consolidation...")
    consolidated_count = memory_manager.consolidate_memories(
        character_id, similarity_threshold=0.8)

    print(f"Nombre de mémoires consolidées: {consolidated_count}")

    # Vérifier quelles mémoires existent encore
    memories_after = db_manager.execute_query(
        "SELECT id, importance FROM memories WHERE id IN (?, ?, ?)",
        (id1, id2, id3)
    )

    remaining_ids = [mem["id"] for mem in memories_after]
    print("\nMémoires restantes après consolidation:", remaining_ids)

    # Vérifier que la mémoire conservée a une importance accrue
    for mem in memories_after:
        if mem["id"] in [id1, id2]:
            print(
                f"Mémoire similaire conservée: ID {mem['id']}, Importance: {mem['importance']:.2f}")
            if mem["importance"] > max(2.5, 2.0):
                print("✅ L'importance de la mémoire conservée a été augmentée")
            else:
                print("❌ L'importance de la mémoire conservée n'a PAS été augmentée")

    # Vérifier que la mémoire différente existe toujours
    if id3 in remaining_ids:
        print("✅ La mémoire différente n'a pas été consolidée (correct)")
    else:
        print("❌ La mémoire différente a été consolidée (incorrect)")

    # Vérifier qu'une des mémoires similaires a été supprimée
    if id1 in remaining_ids and id2 in remaining_ids:
        print("❌ Les deux mémoires similaires existent encore (incorrect)")
    elif id1 not in remaining_ids and id2 not in remaining_ids:
        print("❌ Les deux mémoires similaires ont été supprimées (incorrect)")
    else:
        print("✅ Une des mémoires similaires a été consolidée dans l'autre (correct)")


if __name__ == "__main__":
    test_memory_importance()
