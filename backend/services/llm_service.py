"""
Service d'accès aux modèles de langage (LLM)
"""

import logging
import random
import time
import requests
from typing import Dict, Any, List, Optional

from config import LLM_CONFIG

logger = logging.getLogger(__name__)


class LLMService:
    """Service pour interagir avec les modèles de langage"""

    def __init__(self):
        """Initialise le service LLM"""
        self.config = LLM_CONFIG
        self.api_url = self.config.get("api_url", "http://localhost:11434/api")
        self.default_model = self.config.get("default_model", "llama3")
        self.mock_mode = self.config.get("mock_mode", True)
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 1024)

        # Vérifier la disponibilité du modèle
        if not self.mock_mode:
            self.check_model_availability()

    def check_model_availability(self) -> bool:
        """
        Vérifie si le modèle spécifié est disponible sur l'API Ollama

        Returns:
            True si le modèle est disponible, False sinon
        """
        try:
            # Récupérer la liste des modèles disponibles
            response = requests.get(f"{self.api_url}/tags")

            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model.get("name") for model in models]

                if self.default_model in available_models:
                    logger.info(f"Modèle {self.default_model} disponible sur Ollama.")
                    self.mock_mode = False
                    return True
                else:
                    logger.warning(f"Modèle {self.default_model} non disponible sur Ollama. Modèles disponibles: {available_models}")
                    logger.warning("Passage en mode simulation (mock mode).")
                    self.mock_mode = True
                    return False
            else:
                logger.error(f"Erreur lors de la vérification des modèles disponibles: {response.status_code}")
                logger.warning("Passage en mode simulation (mock mode).")
                self.mock_mode = True
                return False

        except Exception as e:
            logger.error(f"Exception lors de la vérification du modèle: {e}")
            logger.warning("Passage en mode simulation (mock mode).")
            self.mock_mode = True
            return False

    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Génère du texte à partir d'un prompt en utilisant le modèle configuré

        Args:
            prompt: Texte de prompt
            model: Modèle à utiliser (facultatif, utilise default_model si non spécifié)
            temperature: Température pour la génération (contrôle la créativité)
            max_tokens: Nombre maximum de tokens à générer
            system_prompt: Prompt système pour définir le comportement global du modèle

        Returns:
            Texte généré par le modèle
        """
        if self.mock_mode:
            return self._generate_mock_response(prompt)

        model = model or self.default_model
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens

        # Préparer les paramètres pour l'API Ollama
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(f"{self.api_url}/generate", json=payload)

            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logger.error(f"Erreur lors de la génération de texte: {response.status_code} - {response.text}")
                return self._generate_mock_response(prompt)
        except Exception as e:
            logger.error(f"Exception lors de la génération de texte: {e}")
            return self._generate_mock_response(prompt)

    def _generate_mock_response(self, prompt: str) -> str:
        """
        Génère une réponse simulée en mode mock

        Args:
            prompt: Texte de prompt

        Returns:
            Réponse simulée
        """
        # Extraire le nom du personnage du prompt si disponible
        character_name = "Personnage"
        if "# PROFIL DE PERSONNAGE:" in prompt:
            try:
                character_name_line = prompt.split("# PROFIL DE PERSONNAGE:")[1].split("\n")[0].strip()
                character_name = character_name_line
            except:
                pass

        # Déterminer si le prompt contient une question
        is_question = "?" in prompt.split("\n")[-2]

        # Simulation basique d'une réponse en fonction du contexte
        responses = [
            f"Bonjour, je suis {character_name}. Comment puis-je vous aider aujourd'hui ?",
            f"C'est une question intéressante. En tant que {character_name}, je dirais que cela dépend du contexte.",
            f"Je comprends votre point de vue. Permettez-moi de vous donner mon avis sur la question.",
            f"Je ne suis pas sûr de comprendre. Pourriez-vous préciser votre pensée ?",
            f"C'est un sujet qui me tient à cœur. Je serais ravi d'en discuter davantage.",
            f"D'après mon expérience, je pense que vous avez raison sur ce point.",
            f"Je vous remercie de partager cela avec moi. C'est très intéressant."
        ]

        # Sélection pseudo-aléatoire d'une réponse
        seed = sum(ord(c) for c in prompt[-50:])
        random.seed(seed)

        selected_response = random.choice(responses)

        # Ajouter une petite variation avec un temps de "réflexion" simulé
        time.sleep(0.5)

        return selected_response

    def get_embedding(self, text: str) -> List[float]:
        """
        Obtient l'embedding d'un texte

        Args:
            text: Texte à encoder

        Returns:
            Vecteur d'embedding
        """
        if self.mock_mode:
            # En mode mock, générer un vecteur aléatoire mais déterministe
            random.seed(hash(text))
            return [random.uniform(-1, 1) for _ in range(384)]

        try:
            payload = {
                "model": self.default_model,
                "prompt": text
            }

            response = requests.post(f"{self.api_url}/embeddings", json=payload)

            if response.status_code == 200:
                return response.json().get("embedding", [])
            else:
                logger.error(f"Erreur lors de la génération d'embedding: {response.status_code} - {response.text}")
                # Fallback en mode mock
                random.seed(hash(text))
                return [random.uniform(-1, 1) for _ in range(384)]
        except Exception as e:
            logger.error(f"Exception lors de la génération d'embedding: {e}")
            # Fallback en mode mock
            random.seed(hash(text))
            return [random.uniform(-1, 1) for _ in range(384)]


# Instance globale du service LLM
llm_service = LLMService()
