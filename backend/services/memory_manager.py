"""
Gestionnaire de mémoire pour les personnages
"""

import datetime
import logging
import re
import time
from typing import Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import EMBEDDING_CONFIG
from backend.models.memory import (
    Fact,
    FactCreate,
    Memory,
    MemoryCreate,
    RetrievedMemory,
)
from backend.utils.db import db_manager

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

        # Calculer l'importance si elle n'est pas explicitement définie
        if memory.importance == 1.0:  # Valeur par défaut
            memory_dict["importance"] = self._calculate_memory_importance(
                memory.content, memory.type)

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

    def _calculate_memory_importance(self, content: str, memory_type: str) -> float:
        """Calcule l'importance d'une mémoire en analysant son contenu

        Retourne une valeur entre 0.2 (peu important) et 9.0 (très important)
        """
        content_lower = content.lower()
        base_importance = 1.0  # Importance par défaut

        # 1. Ajustement selon le type de mémoire
        type_weights = {
            "conversation": 1.0,
            "event": 1.5,         # Les événements sont généralement plus importants
            "observation": 0.8,   # Les observations sont souvent moins importantes
            "thought": 0.9,       # Les pensées sont modérément importantes
            "facts_extraction": 1.2,  # Les faits extraits ont une importance accrue
            "user_message": 1.3,   # Les messages de l'utilisateur sont plus importants
            "character_message": 1.0  # Les réponses du personnage ont une importance standard
        }

        importance_multiplier = type_weights.get(memory_type, 1.0)

        # 2. Analyse du contenu pour indicateurs d'importance

        # Mots-clés indiquant une information importante
        important_markers = [
            "important", "crucial", "essentiel", "clé", "vital", "critique",
            "toujours", "jamais", "adore", "déteste", "aime", "hais",
            "secret", "confidential", "promesse", "jure", "avoue",
            "révèle", "découvre", "explique", "comprend", "réalise",
            "première fois", "dernier", "meilleur", "pire"
        ]

        # Expressions temporelles dénotant l'importance
        temporal_markers = [
            "hier", "aujourd'hui", "demain", "maintenant", "immédiatement",
            "plus jamais", "toujours", "tous les jours"
        ]

        # Indicateurs émotionnels forts
        emotion_markers = [
            "heureux", "triste", "furieux", "effrayé", "excité", "nerveux",
            "angoissé", "terrifié", "ravi", "extatique", "traumatisé",
            "choqué", "surpris", "ému", "frustré", "énervé", "déçu",
            "fier", "honteux", "coupable", "embarrassé"
        ]

        # Informations personnelles ou identitaires
        identity_markers = [
            "mon nom", "je m'appelle", "je suis", "ma ville", "mon âge",
            "mon adresse", "mon travail", "ma famille", "mes enfants",
            "mon père", "ma mère", "mon frère", "ma sœur", "ma date de naissance"
        ]

        # Calculer les scores en fonction du nombre d'occurrences
        important_score = sum(content_lower.count(marker)
                              for marker in important_markers) * 0.5
        temporal_score = sum(content_lower.count(marker)
                             for marker in temporal_markers) * 0.3
        emotion_score = sum(content_lower.count(marker)
                            for marker in emotion_markers) * 0.4
        identity_score = sum(content_lower.count(marker)
                             for marker in identity_markers) * 0.7

        # 3. Analyse des structures grammaticales
        # Compter les questions (suggérant une demande d'information importante)
        question_count = content.count('?') * 0.4

        # Compter les exclamations (suggérant une émotion forte)
        exclamation_count = content.count('!') * 0.3

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

            # Ajuster l'importance en fonction du nombre d'accès
            # Les mémoires fréquemment consultées gagnent en importance
            if memory["access_count"] > 5:
                current_importance = memory["importance"]
                # Augmenter progressivement l'importance, sans dépasser 9.0
                new_importance = min(
                    9.0, current_importance * (1 + 0.05 * (memory["access_count"] // 5)))
                update_data["importance"] = new_importance

            db_manager.update("memories", update_data, "id = ?", (memory_id,))
            return Memory(**memory)
        return None

    def get_relevant_memories(
        self,
        character_id: int,
        query: str,
        limit: int = 5,
        recency_weight: float = 0.3,
        importance_weight: float = 0.4
    ) -> List[RetrievedMemory]:
        """Récupère les mémoires les plus pertinentes pour une requête

        Args:
            character_id: ID du personnage
            query: Texte de la requête pour trouver des mémoires similaires
            limit: Nombre maximum de mémoires à retourner
            recency_weight: Poids accordé à la récence (0.0 - 1.0)
            importance_weight: Poids accordé à l'importance (0.0 - 1.0)

        Returns:
            Liste de mémoires pertinentes avec leur score de pertinence
        """
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

        # Calculer les métriques pour chaque mémoire
        results = []
        now = datetime.datetime.now()

        for memory in memories:
            if not memory.embedding:
                continue

            # 1. Similarité sémantique (similarité cosinus)
            similarity = self._cosine_similarity(
                query_embedding, memory.embedding)

            # 2. Récence (valeur normalisée)
            age_in_days = (now - memory.created_at).days
            max_age = 365  # Normaliser sur un an
            recency_score = max(0, 1 - (age_in_days / max_age))

            # 3. Importance de la mémoire (normalisée sur 0-1)
            importance_score = memory.importance / 10.0

            # 4. Fréquence d'accès (bonus pour les mémoires consultées)
            access_factor = min(1.0, memory.access_count / 20.0) * 0.2

            # Calculer le score combiné avec les différents facteurs pondérés
            # Le poids de la similarité est calculé pour que tous les poids = 1.0
            similarity_weight = 1.0 - recency_weight - importance_weight

            combined_score = (
                similarity_weight * similarity +      # Pertinence sémantique
                recency_weight * recency_score +      # Récence de la mémoire
                importance_weight * importance_score  # Importance intrinsèque
            ) * (1 + access_factor)                   # Bonus pour accès fréquent

            # Stocker les résultats avec tous les scores individuels
            results.append({
                **memory.dict(),
                "relevance": similarity,
                "recency": recency_score,
                "importance_score": importance_score,
                "access_factor": access_factor,
                "combined_score": combined_score
            })

        # Trier par score combiné et prendre les top N
        results.sort(key=lambda x: x["combined_score"], reverse=True)
        top_results = results[:limit]

        # Mettre à jour le compteur d'accès et éventuellement réévaluer l'importance
        for result in top_results:
            memory_id = result["id"]

            # Incrémenter le compteur d'accès
            new_access_count = result["access_count"] + 1

            # Mettre à jour la date de dernier accès et le compteur
            update_data = {
                "last_accessed": now,
                "access_count": new_access_count
            }

            # Périodiquement, réévaluer l'importance des mémoires fréquemment accédées
            if new_access_count % 10 == 0:  # Toutes les 10 consultations
                try:
                    # Réévaluer l'importance en fonction du contenu
                    recalculated_importance = self._calculate_memory_importance(
                        result["content"], result["type"]
                    )

                    # Moyenner avec l'importance actuelle pour éviter les changements brusques
                    current_importance = result["importance"]
                    adjusted_importance = (
                        current_importance + recalculated_importance) / 2

                    # Ajouter un bonus pour les mémoires fréquemment consultées
                    access_bonus = min(1.5, new_access_count / 20)

                    # Mettre à jour l'importance finale
                    update_data["importance"] = min(
                        9.0, adjusted_importance * (1 + access_bonus * 0.1))

                    logger.info(f"Réévaluation de l'importance de la mémoire {memory_id}: "
                                f"{current_importance} -> {update_data['importance']}")
                except Exception as e:
                    logger.error(
                        f"Erreur lors de la réévaluation de l'importance: {e}")

            db_manager.update("memories", update_data, "id = ?", (memory_id,))

        # Construire les objets RetrievedMemory à partir des résultats
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

    def decay_old_memories(self, character_id: int, days_threshold: int = 90) -> int:
        """Diminue progressivement l'importance des mémoires anciennes

        Les mémoires plus anciennes qu'un certain seuil voient leur importance diminuer,
        sauf si elles sont particulièrement importantes ou fréquemment consultées.

        Args:
            character_id: ID du personnage dont les mémoires seront dégradées
            days_threshold: Âge en jours à partir duquel les mémoires commencent à être dégradées

        Returns:
            Le nombre de mémoires dont l'importance a été mise à jour
        """
        now = datetime.datetime.now()
        cutoff_date = now - datetime.timedelta(days=days_threshold)

        # Récupérer les mémoires anciennes peu consultées
        query = """
            SELECT * FROM memories
            WHERE character_id = ?
            AND created_at < ?
            AND (last_accessed IS NULL OR last_accessed < ?)
            AND access_count < 5
        """
        old_memories = db_manager.execute_query(
            query,
            (character_id, cutoff_date, cutoff_date)
        )

        updated_count = 0

        for memory in old_memories:
            # Ne pas dégrader les mémoires très importantes (>7.0)
            if memory["importance"] > 7.0:
                continue

            # Calculer le facteur de dégradation basé sur l'âge
            age_in_days = (now - memory["created_at"]).days
            decay_factor = 1.0 - min(0.5, (age_in_days - days_threshold) / 365)

            # Appliquer une dégradation plus forte pour les mémoires jamais consultées
            if memory["access_count"] == 0:
                decay_factor *= 0.8

            # Calculer la nouvelle importance
            # Plus l'importance actuelle est élevée, plus la dégradation est lente
            current_importance = memory["importance"]
            importance_resistance = min(0.8, current_importance / 10.0)
            new_importance = max(0.1, current_importance *
                                 (decay_factor + importance_resistance) / 2)

            # Ne mettre à jour que si la différence est significative
            if abs(new_importance - current_importance) > 0.2:
                update_data = {"importance": new_importance}
                db_manager.update("memories", update_data,
                                  "id = ?", (memory["id"],))
                updated_count += 1

                logger.debug(
                    f"Dégradation de mémoire {memory['id']}: {current_importance:.2f} -> {new_importance:.2f}")

        if updated_count > 0:
            logger.info(
                f"Dégradation de {updated_count} mémoires anciennes pour le personnage {character_id}")

        return updated_count

    def consolidate_memories(self, character_id: int, similarity_threshold: float = 0.85) -> int:
        """Consolide les mémoires similaires pour éviter la redondance

        Recherche des mémoires sémantiquement similaires et les fusionne en conservant
        la plus importante, tout en augmentant son importance pour refléter la répétition.

        Args:
            character_id: ID du personnage dont les mémoires seront consolidées
            similarity_threshold: Seuil de similarité au-delà duquel les mémoires sont considérées comme similaires

        Returns:
            Le nombre de mémoires consolidées (supprimées car redondantes)
        """
        if not self.embedding_model:
            logger.warning(
                "Modèle d'embeddings non disponible, impossible de consolider les mémoires")
            return 0

        # Récupérer toutes les mémoires du personnage
        memories = self.get_memories(character_id, limit=500)

        if len(memories) < 5:  # Pas assez de mémoires pour justifier une consolidation
            return 0

        consolidated_count = 0
        processed_ids = set()

        # Comparer chaque paire de mémoires
        for i, memory1 in enumerate(memories):
            if memory1.id in processed_ids:
                continue

            # Passer aux mémoires suivantes
            for j in range(i+1, len(memories)):
                memory2 = memories[j]

                if memory2.id in processed_ids:
                    continue

                # Vérifier si les deux mémoires sont du même type
                if memory1.type != memory2.type:
                    continue

                # Calculer la similarité sémantique
                if memory1.embedding and memory2.embedding:
                    similarity = self._cosine_similarity(
                        memory1.embedding, memory2.embedding)

                    # Si les mémoires sont très similaires
                    if similarity > similarity_threshold:
                        # Déterminer quelle mémoire conserver (la plus importante ou la plus récente)
                        keep_memory, discard_memory = (
                            (memory1, memory2) if memory1.importance > memory2.importance or
                            (memory1.importance ==
                             memory2.importance and memory1.created_at > memory2.created_at)
                            else (memory2, memory1)
                        )

                        # Augmenter l'importance de la mémoire conservée
                        new_importance = min(9.0, keep_memory.importance * 1.2)

                        # Mettre à jour la mémoire conservée
                        update_data = {
                            "importance": new_importance,
                            "metadata": {
                                **keep_memory.metadata,
                                "consolidated_with": discard_memory.id,
                                "consolidation_date": datetime.datetime.now().isoformat(),
                                "similarity_score": similarity
                            }
                        }

                        db_manager.update(
                            "memories", update_data, "id = ?", (keep_memory.id,))

                        # Supprimer la mémoire redondante
                        self.delete_memory(discard_memory.id)

                        processed_ids.add(discard_memory.id)
                        consolidated_count += 1

                        logger.info(f"Mémoires consolidées: {discard_memory.id} fusionnée dans {keep_memory.id} "
                                    f"(similarité: {similarity:.2f})")

        if consolidated_count > 0:
            logger.info(
                f"Consolidation terminée: {consolidated_count} mémoires fusionnées pour le personnage {character_id}")

        return consolidated_count

    def maintenance_cycle(self, character_id: int) -> Dict[str, int]:
        """Exécute un cycle complet de maintenance sur les mémoires d'un personnage

        Combine la dégradation des mémoires anciennes et la consolidation des mémoires similaires.
        Cette méthode est conçue pour être exécutée périodiquement (par exemple, une fois par jour).

        Args:
            character_id: ID du personnage dont les mémoires doivent être maintenues

        Returns:
            Dictionnaire contenant les statistiques du cycle de maintenance
        """
        stats = {}

        try:
            # 1. Dégradation des mémoires anciennes
            decay_count = self.decay_old_memories(character_id)
            stats["decayed_memories"] = decay_count

            # 2. Consolidation des mémoires similaires
            if decay_count > 0:  # Ne consolider que s'il y a des mémoires à maintenir
                consolidation_count = self.consolidate_memories(character_id)
                stats["consolidated_memories"] = consolidation_count
            else:
                stats["consolidated_memories"] = 0

            # 3. Nettoyage des mémoires de très faible importance (optionnel)
            query = "SELECT COUNT(*) as count FROM memories WHERE character_id = ? AND importance < 0.3"
            low_importance = db_manager.execute_query(
                query, (character_id,))[0]["count"]
            stats["low_importance_memories"] = low_importance

            logger.info(f"Cycle de maintenance terminé pour le personnage {character_id}: "
                        f"{decay_count} dégradées, {stats['consolidated_memories']} consolidées, "
                        f"{low_importance} de faible importance")

        except Exception as e:
            logger.error(
                f"Erreur lors du cycle de maintenance pour le personnage {character_id}: {e}")
            stats["error"] = str(e)

        return stats


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
