import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"


def create_session(character_id=2):
    """Crée une session de chat avec un personnage"""
    response = requests.post(
        f"{BASE_URL}/chat/create", json={"character_id": character_id})
    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Erreur lors de la création de la session: {response.status_code}")
        print(response.text)
        return None


def send_message(session_id, content):
    """Envoie un message dans une session de chat"""
    response = requests.post(
        f"{BASE_URL}/chat/{session_id}/message",
        json={"content": content}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur lors de l'envoi du message: {response.status_code}")
        print(response.text)
        return None


def get_facts(character_id):
    """Récupère les faits extraits pour un personnage"""
    # Essayer plusieurs routes possibles car nous ne sommes pas sûrs de la route exacte
    possible_routes = [
        f"{BASE_URL}/characters/{character_id}/facts",
        f"{BASE_URL}/memory/facts/{character_id}",
        f"{BASE_URL}/memory/character/{character_id}/facts",
        f"{BASE_URL}/facts/character/{character_id}"
    ]

    for route in possible_routes:
        try:
            print(f"Tentative de récupération des faits via: {route}")
            response = requests.get(route)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Erreur avec la route {route}: {e}")

    print(
        f"Impossible de récupérer les faits pour le personnage {character_id}")
    return None


def test_fact_extraction():
    """Teste le système d'extraction de faits"""
    # 1. Créer une session
    print("Création d'une session de chat...")
    session = create_session()
    if not session:
        print("Impossible de créer une session de chat")
        return

    session_id = session["id"]
    character_id = session["character_id"]
    print(f"Session créée: ID={session_id}, Personnage ID={character_id}")

    # 2. Envoyer un message contenant diverses informations
    test_message = """
    Bonjour ! Je m'appelle Marc et j'ai 28 ans. Je vis actuellement à Montréal, mais j'ai grandi à Québec.
    Mon père s'appelle Jean et ma mère s'appelle Sophie. J'ai une sœur qui s'appelle Émilie.
    J'adore vraiment le cinéma et les jeux vidéo, mais je déteste faire le ménage.
    Je suis développeur informatique et je travaille sur des projets passionnants.
    Hier soir, je suis allé au restaurant avec des amis. Demain, j'ai prévu d'aller au parc.
    Je me sens très heureux aujourd'hui, car j'ai reçu une bonne nouvelle.
    J'aime beaucoup le chocolat et le café, mais je n'aime pas les épinards.
    Est-ce que tu as des hobbies particuliers ?
    """

    print("\nEnvoi du message test:")
    print(test_message)

    response = send_message(session_id, test_message)
    if not response:
        print("Échec de l'envoi du message")
        return

    print("\nRéponse reçue:")
    print(response.get("content", "Pas de contenu"))

    # 3. Récupérer les faits extraits
    print("\nRécupération des faits extraits...")
    facts = get_facts(character_id)

    if not facts:
        print("Aucun fait n'a été extrait")
        return

    # 4. Afficher les faits de manière organisée
    print(f"\n{len(facts)} faits extraits:")

    # Organiser les faits par catégorie
    facts_by_category = {}
    for fact in facts:
        predicate = fact["predicate"].split()[0]
        if predicate not in facts_by_category:
            facts_by_category[predicate] = []
        facts_by_category[predicate].append(fact)

    # Afficher les faits par catégorie
    for category, category_facts in facts_by_category.items():
        print(f"\n--- Catégorie: {category} ---")
        for fact in category_facts:
            confidence = fact.get("confidence", 0.0)
            confidence_stars = "*" * int(confidence * 5)
            print(
                f"  [{confidence_stars}] {fact['subject']} {fact['predicate']} {fact['object']}")


if __name__ == "__main__":
    test_fact_extraction()
