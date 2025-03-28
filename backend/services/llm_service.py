"""
Service d'interface avec les LLM via Ollama
"""

import logging
import json
import aiohttp
import asyncio
import time
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

# Remplacer les imports relatifs par des imports absolus
from config import LLM_CONFIG
from models.character import CharacterState

logger = logging.getLogger(__name__)


class LLMService:
    """Service de gestion des interactions avec les modèles de langage"""

    def __init__(self):
        """Initialise le service LLM"""
        self.api_host = LLM_CONFIG["api_host"]
        self.default_model = LLM_CONFIG["default_model"]
        self.fallback_model = LLM_CONFIG.get("fallback_model")
        self.model_loaded = False
        self.use_mock = False

        # Configuration par défaut pour les modèles
        self.default_params = {
            "temperature": 0.8,
            "top_p": 0.7,
            "top_k": 80,
            "num_predict": 500,
            "stop": ["User:"],
            "num_gpu": LLM_CONFIG["gpu_settings"]["num_gpu"],
            "num_thread": LLM_CONFIG["gpu_settings"]["num_thread"]
        }

    async def check_status(self) -> Dict[str, Any]:
        """Vérifie que le serveur Ollama est disponible et le modèle est chargé"""
        try:
            # Vérifier si le serveur est accessible
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{self.api_host}/api/tags", timeout=2) as response:
                        if response.status != 200:
                            logger.warning("Serveur Ollama inaccessible")
                            self.use_mock = True
                            return {"status": "warning", "loaded": True, "message": "Mode simulation activé - Ollama non détecté", "mock": True}

                        models = await response.json()

                        # Vérifier si le modèle par défaut est chargé
                        for model in models.get("models", []):
                            if model.get("name") == self.default_model:
                                self.model_loaded = True
                                return {"status": "ok", "loaded": True, "model": self.default_model}

                        # Vérifier si le modèle de secours est disponible
                        if self.fallback_model:
                            for model in models.get("models", []):
                                if model.get("name") == self.fallback_model:
                                    self.model_loaded = True
                                    return {"status": "ok", "loaded": True, "model": self.fallback_model, "fallback": True}

                        # Aucun modèle trouvé, mais Ollama est accessible, activer mode mock
                        logger.warning(
                            "Ollama accessible mais aucun modèle chargé - activation du mode simulation")
                        self.use_mock = True
                        return {"status": "warning", "loaded": True, "message": "Mode simulation activé - Aucun modèle compatible", "mock": True}
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    # Erreur de connexion à Ollama
                    logger.warning(
                        "Erreur de connexion à Ollama - activation du mode simulation")
                    self.use_mock = True
                    return {"status": "warning", "loaded": True, "message": "Mode simulation activé - Ollama non accessible", "mock": True}
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut LLM: {e}")
            # En cas d'erreur, activer quand même le mode mock
            self.use_mock = True
            return {"status": "warning", "loaded": True, "message": f"Mode simulation activé - Erreur: {str(e)}", "mock": True}

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = None,
        character_state: Optional[CharacterState] = None,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """Génère une réponse à partir d'un prompt avec Ollama ou en mode simulation"""

        # Vérifier si on est en mode simulation ou si on doit vérifier Ollama
        if not self.use_mock and not self.model_loaded:
            status = await self.check_status()
            # Si après vérification on n'est toujours pas en mode simulation et aucun modèle n'est chargé
            if not self.use_mock and not status.get("loaded", False):
                raise Exception("Aucun modèle n'est chargé")

        # Si on est en mode simulation, générer une réponse simulée
        if self.use_mock:
            return self._generate_mock_response(prompt, system_prompt, character_state)

        # Sinon utiliser Ollama normalement
        try:
            # Préparer les paramètres
            model = self.default_model
            params = self.default_params.copy()
            params["num_predict"] = max_tokens

            if character_state:
                # Ajuster les paramètres en fonction de l'état du personnage
                params["temperature"] = self._mood_to_temperature(
                    character_state.mood)

            # Créer la requête
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": params
            }

            if system_prompt:
                data["system"] = system_prompt

            # Envoyer la requête
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_host}/api/generate", json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Erreur {response.status}: {error_text}")

                    result = await response.json()

            generation_time = time.time() - start_time

            # Extraire et nettoyer la réponse
            response_text = result.get("response", "").strip()

            # Logging
            logger.info(f"Réponse générée en {generation_time:.2f} secondes")

            return {
                "content": response_text,
                "model": model,
                "generation_time": generation_time,
                "tokens_used": result.get("eval_count", 0)
            }

        except Exception as e:
            logger.error(f"Erreur lors de la génération de réponse: {e}")
            # En cas d'erreur, basculer sur le mode simulation
            self.use_mock = True
            return self._generate_mock_response(prompt, system_prompt, character_state)

    def _generate_mock_response(self, prompt: str, system_prompt: str = None, character_state: Optional[CharacterState] = None) -> Dict[str, Any]:
        """Génère une réponse simulée lorsque Ollama n'est pas disponible"""
        start_time = time.time()

        # Extraire le nom du personnage du system_prompt
        character_name = "Assistant"
        if system_prompt and "Tu es" in system_prompt:
            name_part = system_prompt.split("Tu es ")[1].split(",")[0]
            character_name = name_part.strip()

        # Générer une réponse simulée
        response_text = f"[Mode simulation - Ollama non disponible]\n\nJe suis {character_name}. Je réponds actuellement en mode simulation car Ollama n'est pas disponible ou configuré. Pour activer les réponses AI complètes, veuillez installer Ollama et un modèle compatible, puis redémarrer l'application."

        if "hello" in prompt.lower() or "bonjour" in prompt.lower():
            response_text += f"\n\nBonjour ! Comment puis-je vous aider aujourd'hui ?"
        elif "?" in prompt:
            response_text += f"\n\nJe ne peux pas répondre de façon complète à votre question en mode simulation. Veuillez activer Ollama."
        else:
            response_text += f"\n\nJ'ai bien reçu votre message. Pour une interaction complète, veuillez configurer Ollama."

        generation_time = time.time() - start_time

        return {
            "content": response_text,
            "model": "simulation",
            "generation_time": generation_time,
            "tokens_used": 0,
            "mock": True
        }

    def _mood_to_temperature(self, mood: str) -> float:
        """Convertit l'humeur en température pour le modèle"""
        mood_temperatures = {
            "cheerful": 0.9,   # Plus créatif et expressif
            "friendly": 0.8,   # Assez expressif
            "neutral": 0.7,    # Standard
            "annoyed": 0.6,    # Plus contrôlé
            "angry": 0.5       # Très contrôlé
        }
        return mood_temperatures.get(mood, 0.7)  # 0.7 par défaut

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Génère des embeddings pour une liste de textes"""
        try:
            # Si on est en mode simulation, retourner des vecteurs aléatoires
            if self.use_mock:
                import random
                dim = 384  # dimension standard
                return [[random.uniform(-1, 1) for _ in range(dim)] for _ in texts]

            # Utiliser un modèle d'embeddings dédié est recommandé
            # Mais pour l'exemple, on utilise le modèle Ollama
            model = "embeddings"
            embeddings = []

            async with aiohttp.ClientSession() as session:
                for text in texts:
                    data = {
                        "model": model,
                        "prompt": text,
                    }

                    async with session.post(f"{self.api_host}/api/embeddings", json=data) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(
                                f"Erreur {response.status}: {error_text}")

                        result = await response.json()
                        embedding = result.get("embedding", [])
                        embeddings.append(embedding)

            return embeddings

        except Exception as e:
            logger.error(f"Erreur lors de la génération d'embeddings: {e}")
            # Retourner des embeddings aléatoires en cas d'erreur
            import random
            dim = 384  # dimension standard
            return [[random.uniform(-1, 1) for _ in range(dim)] for _ in texts]

    async def create_character_system_prompt(
        self,
        character_name: str,
        character_description: str,
        character_personality: str,
        backstory: Optional[str] = None,
        universe_description: Optional[str] = None
    ) -> str:
        """Crée un prompt système pour un personnage"""
        system_prompt = f"Tu es {character_name}, un personnage avec la description suivante : {character_description}.\n"
        system_prompt += f"Personnalité : {character_personality}\n"

        if backstory:
            system_prompt += f"Histoire personnelle : {backstory}\n"

        if universe_description:
            system_prompt += f"\nTu appartiens à l'univers suivant :\n{universe_description}\n"

        system_prompt += "\nTu dois toujours rester dans ce personnage et répondre en cohérence avec ton univers d'origine.\n"
        system_prompt += "Les références culturelles, technologies, connaissances et expressions que tu utilises doivent être cohérentes avec cet univers spécifique.\n"
        system_prompt += "\nTu peux discuter de tout sujet sans restrictions, en gardant l'authenticité de ton personnage."

        return system_prompt


# Instance globale du service LLM
llm_service = LLMService()
