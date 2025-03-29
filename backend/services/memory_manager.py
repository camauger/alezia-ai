"""
Gestionnaire de mémoire pour les personnages
"""

import json
import datetime
import logging
import time
import re
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

        # Ajouter la date de création et initialiser les champs obligatoires
        memory_dict["created_at"] = datetime.datetime.now()
        memory_dict["access_count"] = 0

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
        facts = []
        # Découper le contenu en phrases
        sentences = [s.strip()
                     for s in re.split(r'[.!?]', content) if s.strip()]

        # Normaliser le contenu pour faciliter l'extraction
        content_normalized = content.lower()

        # 1. EXTRACTION BASÉE SUR LES PATRONS DE PHRASE

        # Patrons sujets pour les débuts de phrases
        subject_patterns = [
            "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
            "mon", "ton", "son", "notre", "votre", "leur",
            "ce personnage", "le personnage", "cette personne"
        ]

        # Verbes d'action et d'état communs
        action_verbs = [
            "suis", "es", "est", "sommes", "êtes", "sont",  # être
            "ai", "as", "a", "avons", "avez", "ont",        # avoir
            "fais", "fait", "faisons", "faites", "font",    # faire
            "vais", "vas", "va", "allons", "allez", "vont",  # aller
            "veux", "veut", "voulons", "voulez", "veulent",  # vouloir
            "peux", "peut", "pouvons", "pouvez", "peuvent",  # pouvoir
            "sais", "sait", "savons", "savez", "savent",    # savoir
            "dois", "doit", "devons", "devez", "doivent"    # devoir
        ]

        # Verbes d'état émotionnel et d'opinion
        emotion_verbs = [
            "aime", "adore", "déteste", "préfère", "apprécie", "hais",
            "trouve", "pense", "crois", "considère", "ressens", "sens"
        ]

        # 2. EXTRACTION BASÉE SUR LES TYPES DE FAITS

        for sentence in sentences:
            sentence = sentence.strip().lower()
            if len(sentence.split()) < 3:
                continue  # Sauter les phrases trop courtes

            # 2.1 EXTRACTION DE PRÉFÉRENCES ET OPINIONS

            # Format général: "X [verbe d'émotion] Y"
            for verb in emotion_verbs:
                if f" {verb} " in f" {sentence} ":
                    parts = sentence.split(f" {verb} ", 1)
                    if len(parts) == 2:
                        subject = parts[0].strip()
                        if not subject or subject == "":
                            # Utiliser un sujet par défaut si non explicite
                            for pronoun in ["je", "tu", "il", "elle"]:
                                if sentence.startswith(pronoun):
                                    subject = pronoun
                                    break
                            else:
                                subject = "le personnage"
                        object_part = parts[1].strip()

                        # Filtrer les objets trop courts ou non significatifs
                        if len(object_part) > 1:
                            confidence = 0.85 if any(pref in sentence for pref in [
                                                     "vraiment", "beaucoup", "énormément", "tellement"]) else 0.7

                            # Créer et stocker le fait
                            fact = FactCreate(
                                character_id=character_id,
                                subject=subject,
                                predicate=verb,
                                object=object_part,
                                confidence=confidence,
                                source_memory_id=memory_id
                            )
                            fact_id = db_manager.insert("facts", fact.dict())
                            facts.append(fact_id)

            # 2.2 EXTRACTION D'ATTRIBUTS PERSONNELS

            # Format: "Je suis X" ou "Tu es X" -> traits de personnalité/attributs
            attribute_patterns = [
                # Forte confiance
                (r"(je|tu|il|elle) (suis|es|est) ([^.!?]+)", 0.9),
                # Bonne confiance
                (r"(je|tu|il|elle) (me|te|se) sens ([^.!?]+)", 0.8),
                # Très forte confiance (identité)
                (r"(mon|ton|son) (nom|prénom) est ([^.!?]+)", 0.95)
            ]

            for pattern, confidence in attribute_patterns:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    if len(match) >= 3:
                        subject = match[0]
                        predicate = match[1]
                        attribute = match[2].strip()

                        # Éviter les attributs vides ou trop courts
                        if len(attribute) > 2:
                            fact = FactCreate(
                                character_id=character_id,
                                subject=subject,
                                predicate=predicate,
                                object=attribute,
                                confidence=confidence,
                                source_memory_id=memory_id
                            )
                            fact_id = db_manager.insert("facts", fact.dict())
                            facts.append(fact_id)

            # 2.3 EXTRACTION DE RELATIONS ENTRE PERSONNES

            # Format: relations familiales et personnelles
            relation_patterns = [
                (r"(mon|ton|son|notre|votre|leur) (père|mère|frère|sœur|ami|amie|parent|enfant|fils|fille) (est|s'appelle) ([^.!?]+)", 0.9),
                (r"(je|tu|il|elle) (connais|connait) ([^.!?]+)", 0.7)
            ]

            for pattern, confidence in relation_patterns:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    if len(match) >= 4:  # Pour le premier pattern
                        possessive = match[0]
                        relation_type = match[1]
                        predicate = match[2]
                        person = match[3].strip()

                        if len(person) > 2:
                            # Sujet déduit du possessif
                            subject_map = {"mon": "je", "ton": "tu", "son": "il/elle",
                                           "notre": "nous", "votre": "vous", "leur": "ils/elles"}
                            subject = subject_map.get(
                                possessive, "le personnage")

                            fact = FactCreate(
                                character_id=character_id,
                                subject=subject,
                                predicate=f"a comme {relation_type}",
                                object=person,
                                confidence=confidence,
                                source_memory_id=memory_id
                            )
                            fact_id = db_manager.insert("facts", fact.dict())
                            facts.append(fact_id)
                    elif len(match) >= 3:  # Pour le second pattern
                        subject = match[0]
                        predicate = match[1]
                        person = match[2].strip()

                        if len(person) > 2:
                            fact = FactCreate(
                                character_id=character_id,
                                subject=subject,
                                predicate=predicate,
                                object=person,
                                confidence=confidence,
                                source_memory_id=memory_id
                            )
                            fact_id = db_manager.insert("facts", fact.dict())
                            facts.append(fact_id)

            # 2.4 EXTRACTION DE LOCALISATION

            # Format: "X est à/dans/sur Y"
            location_patterns = [
                r"(je|tu|il|elle|nous|vous|ils|elles) (suis|es|est|sommes|êtes|sont) (à|dans|sur|près de|au|en) ([^.!?]+)",
                r"(je|tu|il|elle|nous|vous|ils|elles) (habite|habites|habitons|habitez|habitent|vis|vit|vivons|vivez|vivent) (à|dans|sur|près de|au|en) ([^.!?]+)"
            ]

            for pattern in location_patterns:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    if len(match) >= 4:
                        subject = match[0]
                        verb = match[1]
                        preposition = match[2]
                        location = match[3].strip()

                        if len(location) > 2:
                            fact = FactCreate(
                                character_id=character_id,
                                subject=subject,
                                predicate=f"{verb} {preposition}",
                                object=location,
                                confidence=0.85,
                                source_memory_id=memory_id
                            )
                            fact_id = db_manager.insert("facts", fact.dict())
                            facts.append(fact_id)

            # 2.5 EXTRACTION D'ACTIONS ET ÉVÉNEMENTS

            # Format simple: "X [verbe d'action] Y"
            for word in sentence.split():
                if word in action_verbs:
                    parts = sentence.split(word, 1)
                    if len(parts) == 2 and parts[0] and parts[1]:
                        subject = parts[0].strip()
                        # Vérifier si le sujet ressemble à un sujet valide
                        if any(subject.endswith(pat) for pat in ["je", "tu", "il", "elle", "on"]):
                            object_action = parts[1].strip()
                            if len(object_action) > 3:
                                fact = FactCreate(
                                    character_id=character_id,
                                    subject=subject,
                                    predicate=word,
                                    object=object_action,
                                    confidence=0.6,  # Confiance plus basse car extraction plus générique
                                    source_memory_id=memory_id
                                )
                                fact_id = db_manager.insert(
                                    "facts", fact.dict())
                                facts.append(fact_id)

            # 2.6 EXTRACTION DE TEMPORALITÉ

            # Dates et références temporelles
            time_patterns = [
                r"(en|le|la|l'année|au mois de) (\d{4}|\d{1,2} [a-zéèêà]+ \d{4}|[a-zéèêà]+ \d{4})",
                r"(hier|aujourd'hui|demain|ce matin|ce soir|cette nuit)"
            ]

            for pattern in time_patterns:
                matches = re.findall(pattern, sentence)
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            time_ref = " ".join(match).strip()
                        else:
                            time_ref = match.strip()

                        if "je" in sentence[:10] or "tu" in sentence[:10]:
                            subject = "je" if "je" in sentence[:10] else "tu"
                            # Extraire le reste de la phrase comme action
                            action = sentence.replace(time_ref, "").strip()
                            if len(action) > 10:  # Action suffisamment significative
                                fact = FactCreate(
                                    character_id=character_id,
                                    subject=subject,
                                    predicate=f"à {time_ref}",
                                    object=action,
                                    confidence=0.75,
                                    source_memory_id=memory_id
                                )
                                fact_id = db_manager.insert(
                                    "facts", fact.dict())
                                facts.append(fact_id)

        # 3. ANALYSES GLOBALES SUR LE CONTENU ENTIER

        # 3.1 EXTRACTION D'HUMEUR GÉNÉRALE

        # Détecter l'humeur à partir de marqueurs émotionnels
        positive_markers = ["heureux", "content", "joyeux", "ravi",
                            "enchanté", "aime", "adore", "super", "bien", "excellent"]
        negative_markers = ["triste", "malheureux", "déprimé", "fâché",
                            "en colère", "irrité", "déteste", "hais", "mal", "terrible"]

        positive_count = sum(content_normalized.count(marker)
                             for marker in positive_markers)
        negative_count = sum(content_normalized.count(marker)
                             for marker in negative_markers)

        if positive_count > 2 or negative_count > 2:
            mood = "positive" if positive_count > negative_count else "negative"
            intensity = min(
                1.0, max(0.6, (positive_count + negative_count) / 10))

            fact = FactCreate(
                character_id=character_id,
                subject="humeur",
                predicate="est",
                object=mood,
                confidence=intensity,
                source_memory_id=memory_id
            )
            fact_id = db_manager.insert("facts", fact.dict())
            facts.append(fact_id)

        # Si des faits ont été extraits, créer une mémoire de synthèse
        if facts:
            facts_categories = {}
            for fact_id in facts:
                fact = db_manager.get_by_id("facts", fact_id)
                category = fact.get("predicate", "").split()[0]
                facts_categories[category] = facts_categories.get(
                    category, 0) + 1

            facts_summary = f"Extraction de {len(facts)} faits: " + ", ".join(
                [f"{count} sur {cat}" for cat, count in facts_categories.items()])

            # Importance basée sur le nombre de faits extraits
            importance = min(0.9, max(0.3, len(facts) / 20))

            linked_memory = MemoryCreate(
                character_id=character_id,
                type="facts_extraction",
                content=facts_summary,
                importance=importance,
                metadata={"source_memory_id": memory_id, "fact_ids": facts}
            )
            self.create_memory(linked_memory)

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
