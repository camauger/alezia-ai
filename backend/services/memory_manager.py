"""
Gestionnaire de mémoire pour les personnages
"""

import json
import datetime
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

from utils.db import db_manager
from models.memory import Memory, MemoryCreate, RetrievedMemory, Fact, FactCreate
from config import EMBEDDING_CONFIG

logger = logging.getLogger(__name__)


class MemoryManager:
    """Gestionnaire de mémoire pour les personnages"""

    def __init__(self):
        """Initialise le gestionnaire de mémoire"""
        self.embedding_model = None
        self.embedding_dimensions = EMBEDDING_CONFIG["dimensions"]
        self._load_embedding_model()

    def _load_embedding_model(self):
        """Charge le modèle d'embeddings"""
        try:
            model_name = EMBEDDING_CONFIG["model_name"]
            cache_dir = EMBEDDING_CONFIG["cache_dir"]
            use_gpu = EMBEDDING_CONFIG.get("use_gpu", False)

            logger.info(f"Chargement du modèle d'embeddings {model_name}...")
            start_time = time.time()

            self.embedding_model = SentenceTransformer(
                model_name,
                cache_folder=str(cache_dir),
                device="cuda" if use_gpu else "cpu"
            )

            logger.info(
                f"Modèle d'embeddings chargé en {time.time() - start_time:.2f} secondes")
        except Exception as e:
            logger.error(
                f"Erreur lors du chargement du modèle d'embeddings: {e}")
            # Création d'un modèle factice pour les tests
            self.embedding_model = MockEmbeddingModel(
                self.embedding_dimensions)
            logger.warning("Utilisation d'un modèle d'embeddings factice")

    def create_memory(self, memory: MemoryCreate) -> int:
        """Crée une nouvelle mémoire pour un personnage"""
        memory_dict = memory.dict()

        # Générer l'embedding pour le contenu de la mémoire
        if self.embedding_model:
            embedding = self.embedding_model.encode(memory.content).tolist()
            memory_dict["embedding"] = embedding

        # Ajouter la mémoire à la base de données
        memory_id = db_manager.insert("memories", memory_dict)

        # Extraire et stocker les faits si nécessaire
        if memory.type in ["conversation", "event", "observation"]:
            self._extract_facts(memory_id, memory.character_id, memory.content)

        return memory_id

    def _extract_facts(self, memory_id: int, character_id: int, content: str) -> List[int]:
        """Extrait des faits à partir du contenu d'une mémoire et les stocke"""
        # Cette fonction pourrait utiliser un LLM pour extraire des faits
        # Pour l'instant, nous utilisons une implémentation fictive

        # Exemple simple: extraire des phrases qui commencent par "Je" ou "Tu"
        facts = []
        for sentence in content.split('.'):
            sentence = sentence.strip()
            if sentence.startswith("Je ") or sentence.startswith("Tu "):
                parts = sentence.split(' ', 2)
                if len(parts) >= 3:
                    subject = parts[0]
                    predicate = parts[1]
                    object_part = parts[2] if len(parts) > 2 else ""

                    fact = FactCreate(
                        character_id=character_id,
                        subject=subject,
                        predicate=predicate,
                        object=object_part,
                        confidence=0.8,
                        source_memory_id=memory_id
                    )

                    fact_id = db_manager.insert("facts", fact.dict())
                    facts.append(fact_id)

        return facts

    def get_memories(self, character_id: int, limit: int = 100) -> List[Memory]:
        """Récupère les mémoires d'un personnage"""
        query = "SELECT * FROM memories WHERE character_id = ? ORDER BY created_at DESC LIMIT ?"
        memories = db_manager.execute_query(query, (character_id, limit))
        return [Memory(**memory) for memory in memories]

    def get_memory(self, memory_id: int) -> Optional[Memory]:
        """Récupère une mémoire spécifique"""
        memory = db_manager.get_by_id("memories", memory_id)
        if memory:
            # Mettre à jour le compteur d'accès et la date de dernier accès
            update_data = {
                "last_accessed": datetime.datetime.now(),
                "access_count": memory["access_count"] + 1
            }
            db_manager.update("memories", update_data, "id = ?", (memory_id,))
            return Memory(**memory)
        return None

    def get_relevant_memories(
        self,
        character_id: int,
        query: str,
        limit: int = 5,
        recency_weight: float = 0.3
    ) -> List[RetrievedMemory]:
        """Récupère les mémoires les plus pertinentes pour une requête"""
        if not self.embedding_model:
            logger.warning(
                "Modèle d'embeddings non disponible, impossible de rechercher des mémoires pertinentes")
            return []

        # Générer l'embedding pour la requête
        query_embedding = self.embedding_model.encode(query).tolist()

        # Récupérer toutes les mémoires du personnage
        memories = self.get_memories(character_id, limit=100)

        if not memories:
            return []

        # Calculer la pertinence (similarité cosinus) et la récence pour chaque mémoire
        results = []

        for memory in memories:
            if not memory.embedding:
                continue

            # Calculer la similarité cosinus
            similarity = self._cosine_similarity(
                query_embedding, memory.embedding)

            # Calculer le score de récence (plus récent = plus élevé)
            age_in_days = (datetime.datetime.now() - memory.created_at).days
            recency_score = max(0, 1 - (age_in_days / 365)
                                )  # Normaliser sur un an

            # Score combiné
            combined_score = (1 - recency_weight) * \
                similarity + recency_weight * recency_score

            results.append({
                **memory.dict(),
                "relevance": similarity,
                "recency": recency_score,
                "combined_score": combined_score
            })

        # Trier par score combiné et prendre les top N
        results.sort(key=lambda x: x["combined_score"], reverse=True)
        top_results = results[:limit]

        # Mettre à jour le compteur d'accès pour ces mémoires
        for result in top_results:
            update_data = {
                "last_accessed": datetime.datetime.now(),
                "access_count": result["access_count"] + 1
            }
            db_manager.update("memories", update_data,
                              "id = ?", (result["id"],))

        return [RetrievedMemory(**result) for result in top_results]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs"""
        if not a or not b:
            return 0.0

        a_array = np.array(a)
        b_array = np.array(b)

        dot_product = np.dot(a_array, b_array)
        norm_a = np.linalg.norm(a_array)
        norm_b = np.linalg.norm(b_array)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def get_facts(self, character_id: int, subject: Optional[str] = None) -> List[Fact]:
        """Récupère les faits associés à un personnage"""
        if subject:
            query = "SELECT * FROM facts WHERE character_id = ? AND subject = ? ORDER BY created_at DESC"
            facts = db_manager.execute_query(query, (character_id, subject))
        else:
            query = "SELECT * FROM facts WHERE character_id = ? ORDER BY created_at DESC"
            facts = db_manager.execute_query(query, (character_id,))

        return [Fact(**fact) for fact in facts]

    def delete_memory(self, memory_id: int) -> bool:
        """Supprime une mémoire"""
        # Supprimer d'abord les faits associés
        db_manager.delete("facts", "source_memory_id = ?", (memory_id,))
        # Puis supprimer la mémoire
        rows_deleted = db_manager.delete("memories", "id = ?", (memory_id,))
        return rows_deleted > 0

    def update_memory_importance(self, memory_id: int, importance: float) -> bool:
        """Met à jour l'importance d'une mémoire"""
        update_data = {"importance": max(
            0.0, min(10.0, importance))}  # Limiter entre 0 et 10
        rows_updated = db_manager.update(
            "memories", update_data, "id = ?", (memory_id,))
        return rows_updated > 0


class MockEmbeddingModel:
    """Modèle d'embeddings factice pour les tests"""

    def __init__(self, dimensions: int = 384):
        """Initialise le modèle factice"""
        self.dimensions = dimensions

    def encode(self, text: str) -> np.ndarray:
        """Génère un embedding aléatoire pour le texte"""
        # Utiliser le texte comme graine pour que le même texte produise le même embedding
        np.random.seed(hash(text) % 2**32)
        embedding = np.random.normal(0, 1, self.dimensions)
        # Normaliser
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding


# Instance globale du gestionnaire de mémoire
memory_manager = MemoryManager()
