"""
Service d'interface avec les LLM via Ollama
"""

import logging
import json
import aiohttp
import asyncio
import time
import re
import random
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import requests

# Remplacer les imports relatifs par des imports absolus
from config import LLM_CONFIG
from models.character import CharacterState

logger = logging.getLogger(__name__)


class LLMService:
    """Service de gestion des interactions avec les modèles de langage"""

    def __init__(self):
        """Initialise le service LLM"""
        self.llm_loaded = False
        self.mock_mode = False
        self.model_name = LLM_CONFIG["model_name"]
        self.max_tokens = LLM_CONFIG["max_tokens"]
        self.temperature = LLM_CONFIG["temperature"]
        self.ollama_base_url = LLM_CONFIG["ollama_base_url"]

        # Tenter de charger le modèle
        self._load_model()

        # Si le modèle n'est pas chargé, utiliser le mode simulé
        if not self.llm_loaded:
            logger.warning("LLM non chargé, utilisation du mode simulé")
            self.mock_mode = True

    async def check_status(self) -> Dict[str, Any]:
        """Vérifie que le serveur Ollama est disponible et le modèle est chargé"""
        try:
            # Vérifier si le serveur est accessible
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{self.ollama_base_url}/api/tags", timeout=2) as response:
                        if response.status != 200:
                            logger.warning("Serveur Ollama inaccessible")
                            self.mock_mode = True
                            return {"status": "warning", "loaded": True, "message": "Mode simulation activé - Ollama non détecté", "mock": True}

                        models = await response.json()

                        # Vérifier si le modèle par défaut est chargé
                        for model in models.get("models", []):
                            if model.get("name") == self.model_name:
                                self.llm_loaded = True
                                return {"status": "ok", "loaded": True, "model": self.model_name}

                        # Vérifier si le modèle de secours est disponible
                        if LLM_CONFIG.get("fallback_model"):
                            for model in models.get("models", []):
                                if model.get("name") == LLM_CONFIG["fallback_model"]:
                                    self.llm_loaded = True
                                    return {"status": "ok", "loaded": True, "model": LLM_CONFIG["fallback_model"], "fallback": True}

                        # Aucun modèle trouvé, mais Ollama est accessible, activer mode mock
                        logger.warning(
                            "Ollama accessible mais aucun modèle chargé - activation du mode simulation")
                        self.mock_mode = True
                        return {"status": "warning", "loaded": True, "message": "Mode simulation activé - Aucun modèle compatible", "mock": True}
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    # Erreur de connexion à Ollama
                    logger.warning(
                        "Erreur de connexion à Ollama - activation du mode simulation")
                    self.mock_mode = True
                    return {"status": "warning", "loaded": True, "message": "Mode simulation activé - Ollama non accessible", "mock": True}
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut LLM: {e}")
            # En cas d'erreur, activer quand même le mode mock
            self.mock_mode = True
            return {"status": "warning", "loaded": True, "message": f"Mode simulation activé - Erreur: {str(e)}", "mock": True}

    async def generate_text(self, prompt, system_prompt=None, character_state=None, max_tokens=500):
        """Génère une réponse en utilisant le modèle LLM"""
        return await self.generate_response(prompt, system_prompt, character_state, max_tokens)

    async def generate_response(self, prompt, system_prompt=None, character_state=None, max_tokens=500):
        """Génère une réponse en utilisant le modèle LLM"""
        start_time = time.time()

        try:
            if self.llm_loaded:
                # Utiliser Ollama pour la génération de réponse
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": max_tokens
                    }
                }

                if system_prompt:
                    payload["system"] = system_prompt

                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.ollama_base_url}/api/generate", json=payload) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            return {
                                "content": response_data["response"],
                                "model": self.model_name,
                                "generation_time": time.time() - start_time,
                                "tokens_used": response_data.get("eval_count", 0)
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"Erreur Ollama: {error_text}")
                            return await self._generate_mock_response(prompt, system_prompt, character_state, start_time)
            else:
                return await self._generate_mock_response(prompt, system_prompt, character_state, start_time)

        except Exception as e:
            logger.error(f"Erreur lors de la génération de réponse: {e}")
            return await self._generate_mock_response(prompt, system_prompt, character_state, start_time)

    async def _generate_mock_response(self, prompt, system_prompt=None, character_state=None, start_time=None):
        """Génère une réponse en mode simulé"""
        if start_time is None:
            start_time = time.time()

        # Extraire le nom du personnage depuis le prompt
        character_name = "le personnage"
        if ":" in prompt:
            parts = prompt.split(":")
            if len(parts) > 1:
                character_name_match = re.search(r'([A-Za-z]+):', parts[-2])
                if character_name_match:
                    character_name = character_name_match.group(1)

        # Générer une réponse simple basée sur le dernier message de l'utilisateur
        last_user_message = "votre message"
        if "User:" in prompt:
            user_messages = re.findall(r'User:(.*?)(?=\n|$)', prompt)
            if user_messages:
                last_user_message = user_messages[-1].strip()

        # Générer des réponses variées
        responses = [
            f"Je comprends ce que vous dites à propos de '{last_user_message}'. Pouvez-vous m'en dire plus?",
            f"C'est intéressant ce que vous dites sur '{last_user_message}'. J'aimerais en savoir davantage.",
            f"Je suis d'accord avec votre point sur '{last_user_message}'. Que pensez-vous que nous devrions faire ensuite?",
            f"Votre commentaire sur '{last_user_message}' me fait réfléchir. Comment en êtes-vous arrivé à cette conclusion?",
            f"Merci de partager votre pensée sur '{last_user_message}'. Cela me donne une nouvelle perspective."
        ]

        # Ajouter des réponses basées sur l'humeur si disponible
        if character_state and hasattr(character_state, "mood"):
            mood = character_state.mood

            if mood == "cheerful":
                responses.extend([
                    f"Haha! J'adore ce que vous dites sur '{last_user_message}'! C'est vraiment génial!",
                    f"Oh, c'est formidable! '{last_user_message}' me rend tellement joyeux!"
                ])
            elif mood == "angry":
                responses.extend([
                    f"Je n'apprécie pas du tout ce commentaire sur '{last_user_message}'! C'est frustrant!",
                    f"Honnêtement, je trouve votre remarque sur '{last_user_message}' assez agaçante."
                ])

        # Choisir une réponse aléatoire
        response = random.choice(responses)

        # Ajouter un délai aléatoire pour simuler un temps de réflexion
        await asyncio.sleep(random.uniform(0.5, 1.5))

        return {
            "content": response,
            "model": "mock_model",
            "generation_time": time.time() - start_time,
            "tokens_used": len(response.split())
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
            if self.mock_mode:
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

                    async with session.post(f"{self.ollama_base_url}/api/embeddings", json=data) as response:
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
        system_prompt = f"""Tu es {character_name}, un personnage IA dans un jeu de rôle.

Description: {character_description}

Personnalité: {character_personality}"""

        if backstory:
            system_prompt += f"\n\nHistoire personnelle: {backstory}"

        if universe_description:
            system_prompt += f"\n\nUnivers: {universe_description}"

        system_prompt += """

Instructions:
1. Reste toujours dans le personnage.
2. Réponds comme le ferait ce personnage selon sa personnalité et son histoire.
3. N'utilise pas de formules comme "en tant que [personnage]" ou "je suis [personnage]".
4. Adapte ton langage, ton ton et ton vocabulaire à la personnalité du personnage.
5. Utilise les mémoires partagées pour maintenir la cohérence des conversations précédentes."""

        return system_prompt

    def _load_model(self):
        """Tente de charger le modèle LLM"""
        try:
            # Vérifier si Ollama est accessible
            response = requests.get(
                f"{self.ollama_base_url}/api/tags", timeout=3)

            if response.status_code == 200:
                models = response.json()

                # Vérifier si le modèle est chargé
                for model in models.get("models", []):
                    if model.get("name") == self.model_name:
                        self.llm_loaded = True
                        logger.info(
                            f"Modèle {self.model_name} chargé avec succès")
                        return

                # Si le modèle n'est pas chargé, tenter de le charger
                logger.warning(
                    f"Modèle {self.model_name} non trouvé, tentative de chargement...")
                self.llm_loaded = False
            else:
                logger.warning("Serveur Ollama inaccessible")
                self.llm_loaded = False
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle: {e}")
            self.llm_loaded = False


# Instance globale du service LLM
llm_service = LLMService()
