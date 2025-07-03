"""
Service d'accès aux modèles de langage (LLM)
"""

import logging
import random
import time
from typing import List, Optional

import requests

from backend.config import LLM_CONFIG

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
                    logger.info(
                        f"Modèle {self.default_model} disponible sur Ollama.")
                    self.mock_mode = False
                    return True
                else:
                    logger.warning(
                        f"Modèle {self.default_model} non disponible sur Ollama. Modèles disponibles: {available_models}")
                    logger.warning("Passage en mode simulation (mock mode).")
                    self.mock_mode = True
                    return False
            else:
                logger.error(
                    f"Erreur lors de la vérification des modèles disponibles: {response.status_code}")
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
                logger.error(
                    f"Erreur lors de la génération de texte: {response.status_code} - {response.text}")
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
        # Extract character name from the prompt if available
        character_name = "Character"
        if "# CHARACTER PROFILE:" in prompt:
            try:
                character_name_line = prompt.split("# CHARACTER PROFILE:")[1].split("\n")[0].strip()
                character_name = character_name_line
            except IndexError:
                pass

        # Determine if the prompt contains a question
        is_question = "?" in prompt.split("\n")[-2]

        # Basic simulation of a response based on context
        responses = [
            f"Hello, I am {character_name}. How can I help you today?",
            f"That's an interesting question. As {character_name}, I would say it depends on the context.",
            "I understand your point of view. Allow me to give you my opinion on the matter.",
            "I'm not sure I understand. Could you please clarify your thought?",
            "This is a topic I hold dear. I would be delighted to discuss it further.",
            "From my experience, I think you are right on this point.",
            "Thank you for sharing that with me. It's very interesting."
        ]

        # Pseudo-random selection of a response
        seed = sum(ord(c) for c in prompt[-50:])
        random.seed(seed)

        selected_response = random.choice(responses)

        # Add a small variation with a simulated "thinking" time
        time.sleep(0.5)

        return selected_response

    def get_embedding(self, text: str) -> list[float]:
        """
        Gets the embedding of a text

        Args:
            text: Text to encode

        Returns:
            Embedding vector
        """
        if self.mock_mode:
            # In mock mode, generate a random but deterministic vector
            random.seed(hash(text))
            return [random.uniform(-1, 1) for _ in range(384)]

        try:
            payload = {
                "model": self.default_model,
                "prompt": text
            }

            response = requests.post(
                f"{self.api_url}/embeddings", json=payload)

            if response.status_code == 200:
                return response.json().get("embedding", [])
            else:
                logger.error(
                    f"Error generating embedding: {response.status_code} - {response.text}")
                # Fallback to mock mode
                random.seed(hash(text))
                return [random.uniform(-1, 1) for _ in range(384)]
        except Exception as e:
            logger.error(f"Exception during embedding generation: {e}")
            # Fallback to mock mode
            random.seed(hash(text))
            return [random.uniform(-1, 1) for _ in range(384)]


# Global instance of the LLM service
llm_service = LLMService()
