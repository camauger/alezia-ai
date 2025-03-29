"""
Gestionnaire de base de données SQLite pour l'application
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from time import sleep

import logging

# Utilisation d'un import absolu au lieu d'un import relatif
from config import DB_PATH

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestionnaire de base de données pour l'application"""

    def __init__(self, db_path: Path = DB_PATH):
        """Initialise le gestionnaire de base de données"""
        self.db_path = db_path
        self._ensure_db_exists()
        self._initialize_schema()

    def _ensure_db_exists(self):
        """Vérifie que la base de données existe"""
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _initialize_schema(self):
        """Initialise le schéma de la base de données"""
        try:
            # Charger le schéma SQL depuis le fichier
            schema_path = Path(__file__).resolve().parent / "schema.sql"
            if not schema_path.exists():
                logger.error(f"Fichier de schéma introuvable: {schema_path}")
                return

            with open(schema_path, "r") as f:
                schema = f.read()

            # Exécuter le script SQL
            conn = self._get_connection()
            conn.executescript(schema)
            conn.commit()
            conn.close()
            logger.info("Schéma de base de données initialisé avec succès")

            # Assurer la présence d'un univers par défaut
            self.ensure_default_universe()
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du schéma: {e}")

    def _get_connection(self) -> sqlite3.Connection:
        """Obtient une connexion à la base de données"""
        try:
            # Configurer les timeouts et le mode d'isolation pour éviter les problèmes de verrouillage
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,  # Augmenter le timeout d'attente pour le verrou
                isolation_level=None  # Permet de contrôler les transactions manuellement
            )

            conn.row_factory = sqlite3.Row

            # Activer l'extension JSON1 pour les opérations JSON
            conn.enable_load_extension(True)
            try:
                conn.load_extension("json1")
            except sqlite3.OperationalError:
                logger.warning(
                    "Impossible de charger l'extension JSON1, certaines fonctionnalités peuvent être limitées")
            conn.enable_load_extension(False)

            # Permettre la conversion automatique des objets datetime
            conn.execute("PRAGMA foreign_keys = ON")

            # Configuration pour réduire les problèmes de verrouillage
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            # Moins synchro avec le disque
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA busy_timeout = 5000")  # 5 secondes d'attente

            return conn
        except Exception as e:
            logger.error(
                f"Erreur lors de la connexion à la base de données: {e}")
            raise

    def _dict_to_db_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convertit un dictionnaire Python en format compatible avec SQLite"""
        result = {}
        for key, value in data.items():
            if isinstance(value, dict) or isinstance(value, list):
                result[key] = json.dumps(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convertit une ligne SQLite en dictionnaire Python"""
        if row is None:
            return None
        result = dict(row)
        # Convertir les chaînes JSON en objets Python
        for key, value in result.items():
            if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    pass
            # Convertir les dates ISO en objets datetime
            elif isinstance(value, str) and 'T' in value and value.count('-') == 2:
                try:
                    result[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
        return result

    def execute_query(self, query: str, params: Tuple = (), fetchall: bool = True) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """Exécute une requête SQL et retourne les résultats"""
        max_retries = 3
        retry_count = 0
        result = None
        conn = None

        while retry_count < max_retries:
            try:
                conn = self._get_connection()

                # Utiliser un bloc explicite de transaction pour les requêtes d'écriture
                if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                    conn.execute("BEGIN IMMEDIATE")

                cursor = conn.cursor()
                cursor.execute(query, params)

                if query.strip().upper().startswith("SELECT"):
                    if fetchall:
                        rows = cursor.fetchall()
                        result = [self._row_to_dict(row) for row in rows]
                    else:
                        row = cursor.fetchone()
                        result = self._row_to_dict(row) if row else None
                else:
                    conn.commit()
                    result = {"rowcount": cursor.rowcount,
                              "lastrowid": cursor.lastrowid}

                # Requête réussie, sortir de la boucle
                break
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry_count < max_retries - 1:
                    # Base de données verrouillée, attendre et réessayer
                    retry_count += 1
                    wait_time = retry_count * 1.5  # Backoff exponentiel
                    logger.warning(
                        f"Base de données verrouillée, nouvel essai dans {wait_time}s (essai {retry_count}/{max_retries})")
                    sleep(wait_time)
                else:
                    logger.error(
                        f"Erreur SQL: {e}, Query: {query}, Params: {params}")
                    raise
            except Exception as e:
                logger.error(
                    f"Erreur SQL: {e}, Query: {query}, Params: {params}")
                raise
            finally:
                if conn:
                    conn.close()

        return result

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insère des données dans une table et retourne l'ID de la ligne insérée"""
        data = self._dict_to_db_format(data)
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())

        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        result = self.execute_query(query, values)
        return result["lastrowid"]

    def update(self, table: str, data: Dict[str, Any], condition: str, params: Tuple) -> int:
        """Met à jour des données dans une table et retourne le nombre de lignes affectées"""
        data = self._dict_to_db_format(data)
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = tuple(data.values()) + params

        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        result = self.execute_query(query, values)
        return result["rowcount"]

    def delete(self, table: str, condition: str, params: Tuple) -> int:
        """Supprime des lignes d'une table et retourne le nombre de lignes affectées"""
        query = f"DELETE FROM {table} WHERE {condition}"
        result = self.execute_query(query, params)
        return result["rowcount"]

    def get_by_id(self, table: str, id_value: int) -> Optional[Dict[str, Any]]:
        """Récupère une ligne d'une table par son ID"""
        query = f"SELECT * FROM {table} WHERE id = ?"
        return self.execute_query(query, (id_value,), fetchall=False)

    def get_all(self, table: str, order_by: str = "id", limit: int = None) -> List[Dict[str, Any]]:
        """Récupère toutes les lignes d'une table"""
        query = f"SELECT * FROM {table} ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        return self.execute_query(query)

    def ensure_default_universe(self):
        """Vérifie qu'un univers par défaut existe et le crée si nécessaire"""
        try:
            # Vérifier si au moins un univers existe
            universes = self.get_all("universes")

            if not universes:
                logger.info(
                    "Aucun univers trouvé, création de l'univers par défaut 'Taliria'")
                default_universe = {
                    "name": "Taliria",
                    "description": "Un monde médiéval-fantastique où magie et créatures mythiques coexistent avec des civilisations humanoïdes.",
                    "type": "fantasy",
                    "time_period": "Médiéval",
                    "rules": "Magie élémentaire, royaumes en conflit, diverses races intelligentes",
                    "created_at": datetime.now().isoformat()
                }

                universe_id = self.insert("universes", default_universe)
                logger.info(
                    f"Univers par défaut 'Taliria' créé avec l'ID {universe_id}")

                # Créer quelques éléments d'univers
                elements = [
                    {
                        "universe_id": universe_id,
                        "name": "Le Royaume de Miridian",
                        "type": "location",
                        "description": "Royaume central de Taliria, connu pour ses bibliothèques et académies de magie",
                        "importance": 5
                    },
                    {
                        "universe_id": universe_id,
                        "name": "La Confrérie de l'Aube",
                        "type": "faction",
                        "description": "Groupe de magiciens et érudits cherchant à préserver les anciennes connaissances",
                        "importance": 4
                    },
                    {
                        "universe_id": universe_id,
                        "name": "Les Marais Brumeux",
                        "type": "location",
                        "description": "Région dangereuse et mystérieuse, repaire de créatures étranges",
                        "importance": 3
                    }
                ]

                for element in elements:
                    self.insert("universe_elements", element)

                logger.info(f"Éléments d'univers ajoutés pour 'Taliria'")
                return universe_id
            return universes[0]["id"]
        except Exception as e:
            logger.error(
                f"Erreur lors de la création de l'univers par défaut: {e}")
            return None


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()
