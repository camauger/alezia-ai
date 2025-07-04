import logging
import time

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import EMBEDDING_CONFIG

logger = logging.getLogger(__name__)

_embedding_model = None


class MockEmbeddingModel:
    """Modèle d'embeddings factice pour les tests"""

    def __init__(self, dimensions: int = 384):
        """Initialise le modèle factice"""
        self.dimensions = dimensions

    def encode(self, text: str) -> np.ndarray:
        """Génère un embedding aléatoire pour le texte"""
        np.random.seed(hash(text) % 2**32)
        embedding = np.random.normal(0, 1, self.dimensions)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            model_name = EMBEDDING_CONFIG["model_name"]
            cache_dir = EMBEDDING_CONFIG["cache_dir"]
            use_gpu = EMBEDDING_CONFIG.get("use_gpu", False)

            logger.info(f"Chargement du modèle d'embeddings {model_name}...")
            start_time = time.time()

            _embedding_model = SentenceTransformer(
                model_name,
                cache_folder=str(cache_dir),
                device="cuda" if use_gpu else "cpu",
            )

            logger.info(
                f"Modèle d'embeddings chargé en {time.time() - start_time:.2f} secondes"
            )
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle d'embeddings: {e}")
            # Création d'un modèle factice pour les tests
            _embedding_model = MockEmbeddingModel(EMBEDDING_CONFIG["dimensions"])
            logger.warning("Utilisation d'un modèle d'embeddings factice")
    return _embedding_model
