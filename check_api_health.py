"""
Script pour vérifier l'état de l'API Alezia AI
"""

import sys
import requests
import time


def check_api_health(port, max_attempts=5, timeout=5):
    """Vérifie que l'API répond correctement sur le port spécifié"""
    base_url = f"http://127.0.0.1:{port}"
    health_url = f"{base_url}/health"
    print(f"Vérification de la santé de l'API à {health_url}...")

    for attempt in range(max_attempts):
        try:
            response = requests.get(health_url, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print(f"✓ API active et en bonne santé!")
                    print(f"✓ Documentation disponible sur {base_url}/docs")
                    return True
                else:
                    print(f"API active mais signale un problème: {data}")
                    return False
            else:
                print(f"Réponse non-200: {response.status_code}")
        except requests.RequestException as e:
            print(f"Tentative {attempt+1}/{max_attempts}: {e}")

        # Attendre avant la prochaine tentative
        time.sleep(1)

    print("✗ L'API ne répond pas. Vérifiez qu'elle est bien démarrée.")
    return False


if __name__ == "__main__":
    # Port explicite pour tester l'API basique
    port = 8007
    print(f"Vérification de l'API sur le port {port}...")

    if not check_api_health(port):
        print("ERREUR: L'API n'est pas disponible.")
        sys.exit(1)
    else:
        print("Succès: L'API est disponible et fonctionne correctement.")
        sys.exit(0)
