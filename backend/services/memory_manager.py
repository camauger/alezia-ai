"""
Gestionnaire de mémoire pour les personnages
"""

import datetime
import logging
import re
import time
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from backend.config import EMBEDDING_CONFIG
from backend.models.memory import (
    Fact,
    FactCreate,
    FactModel,
    Memory,
    MemoryCreate,
    MemoryModel,
    RetrievedMemory,
)
from backend.utils.embedding_loader import get_embedding_model

logger = logging.getLogger(__name__)


class MemoryManager:
    """Gestionnaire de mémoire pour les personnages"""

    def __init__(self):
        """Initialise le gestionnaire de mémoire"""
        self.embedding_model = get_embedding_model()
        self.embedding_dimensions = EMBEDDING_CONFIG["dimensions"]

    def create_memory(self, db: Session, memory: MemoryCreate) -> MemoryModel:
        """Crée une nouvelle mémoire pour un personnage"""
        memory_dict = memory.model_dump()

        # Calculer l'importance si elle n'est pas explicitement définie
        if memory.importance == 1.0:  # Valeur par défaut
            memory_dict["importance"] = self._calculate_memory_importance(
                memory.content, memory.memory_type
            )

        # Générer l'embedding pour le contenu de la mémoire
        if self.embedding_model:
            embedding = self.embedding_model.encode(memory.content)
            memory_dict["embedding"] = embedding.tolist()

        db_memory = MemoryModel(**memory_dict)
        db.add(db_memory)
        db.commit()
        db.refresh(db_memory)

        # Extraire et stocker les faits si nécessaire
        if memory.memory_type in ["conversation", "event", "observation"]:
            self._extract_facts(
                db, int(db_memory.id), memory.character_id, memory.content
            )

        return db_memory

    def _calculate_memory_importance(self, content: str, memory_type: str) -> float:
        """Calcule l'importance d'une mémoire en analysant son contenu

        Retourne une valeur entre 0.2 (peu important) et 9.0 (très important)
        """
        content_lower = content.lower()
        base_importance = 1.0  # Importance par défaut

        # 1. Ajustement selon le type de mémoire
        type_weights = {
            "conversation": 1.0,
            "event": 1.5,  # Les événements sont généralement plus importants
            "observation": 0.8,  # Les observations sont souvent moins importantes
            "thought": 0.9,  # Les pensées sont modérément importantes
            "facts_extraction": 1.2,  # Les faits extraits ont une importance accrue
            "user_message": 1.3,  # Les messages de l'utilisateur sont plus importants
            "character_message": 1.0,  # Les réponses du personnage ont une importance standard
        }

        importance_multiplier = type_weights.get(memory_type, 1.0)

        # 2. Analyse du contenu pour indicateurs d'importance

        # Mots-clés indiquant une information importante
        important_markers = [
            "important",
            "crucial",
            "essentiel",
            "clé",
            "vital",
            "critique",
            "toujours",
            "jamais",
            "adore",
            "déteste",
            "aime",
            "hais",
            "secret",
            "confidential",
            "promesse",
            "jure",
            "avoue",
            "révèle",
            "découvre",
            "explique",
            "comprend",
            "réalise",
            "première fois",
            "dernier",
            "meilleur",
            "pire",
        ]

        # Expressions temporelles dénotant l'importance
        temporal_markers = [
            "hier",
            "aujourd'hui",
            "demain",
            "maintenant",
            "immédiatement",
            "plus jamais",
            "toujours",
            "tous les jours",
        ]

        # Indicateurs émotionnels forts
        emotion_markers = [
            "heureux",
            "triste",
            "furieux",
            "effrayé",
            "excité",
            "nerveux",
            "angoissé",
            "terrifié",
            "ravi",
            "extatique",
            "traumatisé",
            "choqué",
            "surpris",
            "ému",
            "frustré",
            "énervé",
            "déçu",
            "fier",
            "honteux",
            "coupable",
            "embarrassé",
        ]

        # Informations personnelles ou identitaires
        identity_markers = [
            "mon nom",
            "je m'appelle",
            "je suis",
            "ma ville",
            "mon âge",
            "mon adresse",
            "mon travail",
            "ma famille",
            "mes enfants",
            "mon père",
            "ma mère",
            "mon frère",
            "ma sœur",
            "ma date de naissance",
        ]

        # Calculer les scores en fonction du nombre d'occurrences
        important_score = (
            sum(content_lower.count(marker) for marker in important_markers) * 0.5
        )
        temporal_score = (
            sum(content_lower.count(marker) for marker in temporal_markers) * 0.3
        )
        emotion_score = (
            sum(content_lower.count(marker) for marker in emotion_markers) * 0.4
        )
        identity_score = (
            sum(content_lower.count(marker) for marker in identity_markers) * 0.7
        )

        # 3. Analyse des structures grammaticales
        # Compter les questions (suggérant une demande d'information importante)
        question_count = content.count("?") * 0.4

        # Compter les exclamations (suggérant une émotion forte)
        exclamation_count = content.count("!") * 0.3

        # 4. Complexité et détail (longueur et richesse du texte)
        word_count = len(content_lower.split())
        # Bonus pour les contenus détaillés mais pas trop longs
        complexity_score = min(1.0, word_count / 100) * 0.5

        # 5. Calculer l'importance finale
        total_score = base_importance
        total_score += important_score
        total_score += temporal_score
        total_score += emotion_score
        total_score += identity_score
        total_score += question_count
        total_score += exclamation_count
        total_score += complexity_score

        # Appliquer le multiplicateur de type
        total_score *= importance_multiplier

        # Limiter l'importance entre 0.2 et 9.0
        return min(9.0, max(0.2, total_score))

    def _extract_facts(
        self, db: Session, memory_id: int, character_id: int, content: str
    ) -> list[int]:
        """Extrait des faits à partir du contenu d'une mémoire et les stocke"""
        facts = []

        try:
            # Patterns simples pour extraire des faits de base
            fact_patterns = [
                # "Je m'appelle X" -> ("user", "s'appelle", "X")
                (r"je m'appelle ([A-Z][a-zA-Z\s-]+)", "user", "s'appelle"),
                # "Mon nom est X" -> ("user", "a pour nom", "X")
                (r"mon nom est ([A-Z][a-zA-Z\s-]+)", "user", "a pour nom"),
                # "J'ai X ans" -> ("user", "a pour âge", "X ans")
                (r"j'ai (\d+) ans?", "user", "a pour âge"),
                # "Je suis X" -> ("user", "est", "X")
                (r"je suis (un|une) ([a-zA-Z\s-]+)", "user", "est"),
                # "J'habite à X" -> ("user", "habite à", "X")
                (r"j'habite (?:à|en|au|aux) ([a-zA-Z\s-]+)", "user", "habite à"),
                # "J'aime X" -> ("user", "aime", "X")
                (r"j'aime (?:le|la|les|l') ([a-zA-Z\s-]+)", "user", "aime"),
                # "Je déteste X" -> ("user", "déteste", "X")
                (r"je déteste (?:le|la|les|l') ([a-zA-Z\s-]+)", "user", "déteste"),
                # "Mon travail est X" -> ("user", "travaille comme", "X")
                (r"mon travail est ([a-zA-Z\s-]+)", "user", "travaille comme"),
                # "Je travaille comme X" -> ("user", "travaille comme", "X")
                (r"je travaille comme ([a-zA-Z\s-]+)", "user", "travaille comme"),
                # "Ma passion est X" -> ("user", "a pour passion", "X")
                (r"ma passion est ([a-zA-Z\s-]+)", "user", "a pour passion"),
                # "Je fais X" -> ("user", "fait", "X")
                (r"je fais (?:du|de la|de l'|des) ([a-zA-Z\s-]+)", "user", "fait"),
            ]

            content_lower = content.lower()

            for pattern, subject, predicate in fact_patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        # Pour les patterns avec plusieurs groupes
                        object_value = " ".join(match).strip()
                    else:
                        object_value = match.strip()

                    if object_value and len(object_value) > 1:
                        # Vérifier si ce fait existe déjà
                        existing_fact = (
                            db.query(FactModel)
                            .filter(
                                FactModel.character_id == character_id,
                                FactModel.subject == subject,
                                FactModel.predicate == predicate,
                                FactModel.object == object_value,
                            )
                            .first()
                        )

                        if not existing_fact:
                            # Créer le nouveau fait
                            fact_data = FactCreate(
                                character_id=character_id,
                                subject=subject,
                                predicate=predicate,
                                object=object_value,
                                confidence=0.8,  # Confiance par défaut pour l'extraction automatique
                                source_memory_id=memory_id,
                            )

                            db_fact = FactModel(**fact_data.model_dump())
                            db.add(db_fact)
                            db.commit()
                            db.refresh(db_fact)
                            facts.append(db_fact.id)

                            logger.debug(
                                f"Fait extrait: {subject} {predicate} {object_value} "
                                f"(confiance: {fact_data.confidence})"
                            )
                        else:
                            # Mise à jour de la confiance si le fait existe déjà
                            existing_fact.confidence = min(
                                1.0, existing_fact.confidence + 0.1
                            )
                            existing_fact.last_confirmed = datetime.datetime.now()
                            db.commit()
                            facts.append(existing_fact.id)

            # Patterns avancés pour extraire des relations émotionnelles
            emotion_patterns = [
                # "X me rend heureux/triste/etc."
                (
                    r"([a-zA-Z\s-]+) me rend (heureux|triste|nerveux|calme|fier)",
                    "emotional_response",
                ),
                # "J'ai peur de X"
                (r"j'ai peur de ([a-zA-Z\s-]+)", "a peur de"),
            ]

            for pattern, predicate in emotion_patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) == 2:
                        subject_value = match[0].strip()
                        emotion = match[1].strip()

                        if predicate == "emotional_response":
                            predicate_value = f"rend {emotion}"
                        else:
                            predicate_value = predicate

                        if subject_value and len(subject_value) > 1:
                            existing_fact = (
                                db.query(FactModel)
                                .filter(
                                    FactModel.character_id == character_id,
                                    FactModel.subject == subject_value,
                                    FactModel.predicate == predicate_value,
                                    FactModel.object == "user",
                                )
                                .first()
                            )

                            if not existing_fact:
                                fact_data = FactCreate(
                                    character_id=character_id,
                                    subject=subject_value,
                                    predicate=predicate_value,
                                    object="user",
                                    confidence=0.7,
                                    source_memory_id=memory_id,
                                )

                                db_fact = FactModel(**fact_data.model_dump())
                                db.add(db_fact)
                                db.commit()
                                db.refresh(db_fact)
                                facts.append(db_fact.id)

            if facts:
                logger.info(
                    f"Extraction de faits terminée: {len(facts)} faits extraits de la mémoire {memory_id}"
                )

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de faits: {e}")
            # Ne pas faire échouer la création de mémoire si l'extraction de faits échoue

        return facts

    def get_memories(
        self, db: Session, character_id: int, limit: int = 100
    ) -> list[MemoryModel]:
        """Récupère les mémoires d'un personnage"""
        return (
            db.query(MemoryModel)
            .filter(MemoryModel.character_id == character_id)
            .order_by(MemoryModel.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_memory(self, db: Session, memory_id: int) -> Optional[MemoryModel]:
        """Récupère une mémoire spécifique"""
        memory = db.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
        if memory:
            # Mettre à jour le compteur d'accès et la date de dernier accès
            memory.last_accessed = datetime.datetime.now()
            memory.access_count += 1

            # Ajuster l'importance en fonction du nombre d'accès
            if memory.access_count > 5:
                current_importance = memory.importance
                new_importance = min(
                    9.0, current_importance * (1 + 0.05 * (memory.access_count // 5))
                )
                memory.importance = new_importance

            db.commit()
            db.refresh(memory)
        return memory

    def get_relevant_memories(
        self,
        db: Session,
        character_id: int,
        query: str,
        limit: int = 5,
        recency_weight: float = 0.3,
        importance_weight: float = 0.4,
    ) -> list[RetrievedMemory]:
        """Récupère les mémoires les plus pertinentes pour une requête"""
        if not self.embedding_model:
            logger.warning(
                "Modèle d'embeddings non disponible, impossible de rechercher des mémoires pertinentes"
            )
            return []

        query_embedding = self.embedding_model.encode(query)

        memories = self.get_memories(db, character_id, limit=100)

        if not memories:
            return []

        results = []
        now = datetime.datetime.now()

        for memory in memories:
            if not memory.embedding:
                continue

            similarity = self._cosine_similarity(
                query_embedding, np.array(memory.embedding)
            )

            age_in_days = (now - memory.created_at).days
            max_age = 365
            recency_score = max(0, 1 - (age_in_days / max_age))

            importance_score = memory.importance / 10.0

            access_factor = min(1.0, memory.access_count / 20.0) * 0.2

            # Le poids de la similarité est calculé pour que tous les poids = 1.0
            similarity_weight = 1.0 - recency_weight - importance_weight

            results.append(
                RetrievedMemory(
                    memory=Memory.from_orm(memory),
                    relevance_score=similarity,
                    similarity_score=similarity,
                    recency_score=recency_score,
                    importance_score=importance_score,
                )
            )

        results.sort(key=lambda x: x.relevance_score, reverse=True)
        top_results = results[:limit]

        for result in top_results:
            self.get_memory(db, result.memory.id)

        return top_results

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calcule la similarité cosinus entre deux vecteurs"""
        if a is None or b is None:
            return 0.0

        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def get_facts(
        self, db: Session, character_id: int, subject: Optional[str] = None
    ) -> list[FactModel]:
        """Récupère les faits associés à un personnage"""
        query = db.query(FactModel).filter(FactModel.character_id == character_id)
        if subject:
            query = query.filter(FactModel.subject == subject)
        return query.order_by(FactModel.created_at.desc()).all()

    def delete_memory(self, db: Session, memory_id: int) -> bool:
        """Supprime une mémoire"""
        db_memory = self.get_memory(db, memory_id)
        if db_memory:
            db.delete(db_memory)
            db.commit()
            return True
        return False

    def update_memory_importance(
        self, db: Session, memory_id: int, importance: float
    ) -> bool:
        """Met à jour l'importance d'une mémoire"""
        db_memory = self.get_memory(db, memory_id)
        if db_memory:
            db_memory.importance = max(0.0, min(10.0, importance))
            db.commit()
            return True
        return False

    def decay_old_memories(
        self, db: Session, character_id: int, days_threshold: int = 90
    ) -> int:
        """Diminue progressivement l'importance des mémoires anciennes"""
        now = datetime.datetime.now()
        cutoff_date = now - datetime.timedelta(days=days_threshold)

        old_memories = (
            db.query(MemoryModel)
            .filter(
                MemoryModel.character_id == character_id,
                MemoryModel.created_at < cutoff_date,
                (MemoryModel.last_accessed is None)
                | (MemoryModel.last_accessed < cutoff_date),
                MemoryModel.access_count < 5,
            )
            .all()
        )

        updated_count = 0
        for memory in old_memories:
            if memory.importance > 7.0:
                continue

            age_in_days = (now - memory.created_at).days
            decay_factor = 1.0 - min(0.5, (age_in_days - days_threshold) / 365)

            if memory.access_count == 0:
                decay_factor *= 0.8

            current_importance = memory.importance
            importance_resistance = min(0.8, current_importance / 10.0)
            new_importance = max(
                0.1, current_importance * (decay_factor + importance_resistance) / 2
            )

            if abs(new_importance - current_importance) > 0.2:
                memory.importance = new_importance
                updated_count += 1

        if updated_count > 0:
            db.commit()
            logger.info(
                f"Dégradation de {updated_count} mémoires anciennes pour le personnage {character_id}"
            )

        return updated_count

    def consolidate_memories(
        self, db: Session, character_id: int, similarity_threshold: float = 0.85
    ) -> int:
        """Consolide les mémoires similaires pour éviter la redondance"""
        if not self.embedding_model:
            logger.warning(
                "Modèle d'embeddings non disponible, impossible de consolider les mémoires"
            )
            return 0

        memories = self.get_memories(db, character_id, limit=500)

        if len(memories) < 5:
            return 0

        consolidated_count = 0
        processed_ids = set()

        for i, memory1 in enumerate(memories):
            if memory1.id in processed_ids:
                continue

            for j in range(i + 1, len(memories)):
                memory2 = memories[j]

                if memory2.id in processed_ids:
                    continue

                if memory1.memory_type != memory2.memory_type:
                    continue

                if memory1.embedding and memory2.embedding:
                    similarity = self._cosine_similarity(
                        np.array(memory1.embedding), np.array(memory2.embedding)
                    )

                    if similarity > similarity_threshold:
                        keep_memory, discard_memory = (
                            (memory1, memory2)
                            if memory1.importance > memory2.importance
                            or (
                                memory1.importance == memory2.importance
                                and memory1.created_at > memory2.created_at
                            )
                            else (memory2, memory1)
                        )

                        keep_memory.importance = min(9.0, keep_memory.importance * 1.2)

                        if keep_memory.memory_metadata is None:
                            keep_memory.memory_metadata = {}
                        keep_memory.memory_metadata["consolidated_with"] = (
                            discard_memory.id
                        )
                        keep_memory.memory_metadata["consolidation_date"] = (
                            datetime.datetime.now().isoformat()
                        )
                        keep_memory.memory_metadata["similarity_score"] = similarity

                        db.delete(discard_memory)
                        processed_ids.add(discard_memory.id)
                        consolidated_count += 1

        if consolidated_count > 0:
            db.commit()
            logger.info(
                f"Consolidation terminée: {consolidated_count} mémoires fusionnées pour le personnage {character_id}"
            )

        return consolidated_count

    def maintenance_cycle(self, db: Session, character_id: int) -> dict[str, int]:
        """Exécute un cycle complet de maintenance sur les mémoires d'un personnage"""
        stats = {}

        try:
            decay_count = self.decay_old_memories(db, character_id)
            stats["decayed_memories"] = decay_count

            consolidation_count = self.consolidate_memories(db, character_id)
            stats["consolidated_memories"] = consolidation_count

            low_importance = (
                db.query(MemoryModel)
                .filter(
                    MemoryModel.character_id == character_id,
                    MemoryModel.importance < 0.3,
                )
                .count()
            )
            stats["low_importance_memories"] = low_importance

            logger.info(
                f"Cycle de maintenance terminé pour le personnage {character_id}: "
                f"{decay_count} dégradées, {consolidation_count} consolidées, "
                f"{low_importance} de faible importance"
            )

        except Exception as e:
            logger.error(
                f"Erreur lors du cycle de maintenance pour le personnage {character_id}: {e}"
            )
            stats["error"] = str(e)

        return stats


# Instance globale du gestionnaire de mémoire
memory_manager = MemoryManager()
