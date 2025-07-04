"""
Gestionnaire de base de données pour Alezia AI
Fournit une interface simplifiée pour les opérations de base de données SQLite
"""

import datetime
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class DatabaseManager:
    """Gestionnaire de base de données SQLite pour Alezia AI"""

    def __init__(self, db_path: str = None):
        """
        Initialise le gestionnaire de base de données

        Args:
            db_path: Chemin vers le fichier de base de données
        """
        if db_path is None:
            # Chemin par défaut dans le dossier data
            project_root = Path(__file__).resolve().parent.parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "alezia.db"

        self.db_path = Path(db_path)
        self.connection = None
        self._connect()

    def _connect(self):
        """Établit la connexion à la base de données"""
        try:
            self.connection = sqlite3.connect(
                str(self.db_path), check_same_thread=False, timeout=30.0
            )
            # Configuration pour des dictionnaires de résultats
            self.connection.row_factory = sqlite3.Row
            # Activer les clés étrangères
            self.connection.execute("PRAGMA foreign_keys = ON")
        except Exception as e:
            print(f"Erreur de connexion à la base de données: {e}")
            raise

    def _initialize_schema(self):
        """Initialise le schéma de la base de données"""
        try:
            schema_file = Path(__file__).parent / "schema.sql"
            if not schema_file.exists():
                print(f"Fichier de schéma non trouvé: {schema_file}")
                return False

            with open(schema_file, "r", encoding="utf-8") as f:
                schema_sql = f.read()

            # Exécuter le schéma
            self.connection.executescript(schema_sql)
            self.connection.commit()
            print("Schéma de base de données initialisé avec succès")
            return True
        except Exception as e:
            print(f"Erreur lors de l'initialisation du schéma: {e}")
            return False

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Exécute une requête SELECT et retourne les résultats

        Args:
            query: Requête SQL à exécuter
            params: Paramètres de la requête

        Returns:
            Liste de dictionnaires représentant les résultats
        """
        try:
            cursor = self.connection.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erreur lors de l'exécution de la requête: {e}")
            print(f"Requête: {query}")
            print(f"Paramètres: {params}")
            return []

    def execute(self, query: str, params: tuple = ()) -> int:
        """
        Exécute une requête INSERT/UPDATE/DELETE

        Args:
            query: Requête SQL à exécuter
            params: Paramètres de la requête

        Returns:
            ID de la dernière ligne insérée (pour INSERT)
        """
        try:
            cursor = self.connection.execute(query, params)
            return cursor.lastrowid
        except Exception as e:
            print(f"Erreur lors de l'exécution de la requête: {e}")
            print(f"Requête: {query}")
            print(f"Paramètres: {params}")
            return None

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert une nouvelle ligne dans une table

        Args:
            table: Nom de la table
            data: Dictionnaire des données à insérer

        Returns:
            ID de la ligne insérée
        """
        try:
            # Préparer les colonnes et valeurs
            columns = list(data.keys())
            placeholders = ["?" for _ in columns]
            values = [self._serialize_value(data[col]) for col in columns]

            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

            cursor = self.connection.execute(query, values)
            row_id = cursor.lastrowid

            return row_id
        except Exception as e:
            print(f"Erreur lors de l'insertion dans {table}: {e}")
            print(f"Données: {data}")
            return None

    def get_by_id(self, table: str, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une ligne par son ID

        Args:
            table: Nom de la table
            record_id: ID de la ligne

        Returns:
            Dictionnaire représentant la ligne ou None
        """
        try:
            query = f"SELECT * FROM {table} WHERE id = ?"
            cursor = self.connection.execute(query, (record_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération de {table}[{record_id}]: {e}")
            return None

    def get_all(
        self, table: str, where_clause: str = "", params: tuple = ()
    ) -> List[Dict[str, Any]]:
        """
        Récupère toutes les lignes d'une table

        Args:
            table: Nom de la table
            where_clause: Clause WHERE optionnelle
            params: Paramètres pour la clause WHERE

        Returns:
            Liste de dictionnaires représentant les lignes
        """
        try:
            query = f"SELECT * FROM {table}"
            if where_clause:
                query += f" WHERE {where_clause}"

            return self.execute_query(query, params)
        except Exception as e:
            print(f"Erreur lors de la récupération de {table}: {e}")
            return []

    def update(self, table: str, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Met à jour une ligne par son ID

        Args:
            table: Nom de la table
            record_id: ID de la ligne à mettre à jour
            data: Dictionnaire des nouvelles données

        Returns:
            True si la mise à jour a réussi
        """
        try:
            # Préparer les colonnes et valeurs
            columns = list(data.keys())
            set_clause = ", ".join([f"{col} = ?" for col in columns])
            values = [self._serialize_value(data[col]) for col in columns]
            values.append(record_id)

            query = f"UPDATE {table} SET {set_clause} WHERE id = ?"

            cursor = self.connection.execute(query, values)
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erreur lors de la mise à jour de {table}[{record_id}]: {e}")
            return False

    def delete(self, table: str, where_clause: str, params: tuple = ()) -> int:
        """
        Supprime des lignes d'une table

        Args:
            table: Nom de la table
            where_clause: Clause WHERE pour identifier les lignes à supprimer
            params: Paramètres pour la clause WHERE

        Returns:
            Nombre de lignes supprimées
        """
        try:
            query = f"DELETE FROM {table} WHERE {where_clause}"
            cursor = self.connection.execute(query, params)
            return cursor.rowcount
        except Exception as e:
            print(f"Erreur lors de la suppression dans {table}: {e}")
            return 0

    def commit(self):
        """Valide les changements en base"""
        try:
            self.connection.commit()
        except Exception as e:
            print(f"Erreur lors du commit: {e}")

    def rollback(self):
        """Annule les changements en cours"""
        try:
            self.connection.rollback()
        except Exception as e:
            print(f"Erreur lors du rollback: {e}")

    def ensure_default_universe(self) -> int:
        """
        S'assure qu'un univers par défaut existe et le retourne

        Returns:
            ID de l'univers par défaut
        """
        try:
            # Vérifier si un univers existe déjà
            universes = self.get_all("universes")
            if universes:
                return universes[0]["id"]

            # Créer un univers par défaut
            universe_data = {
                "name": "Monde moderne",
                "description": "Un univers contemporain similaire au monde réel actuel",
                "type": "réaliste",
                "time_period": "2024",
                "rules": "Lois de la physique standards, technologies modernes disponibles",
                "created_at": datetime.datetime.now().isoformat(),
            }

            universe_id = self.insert("universes", universe_data)
            self.commit()

            print(f"Univers par défaut créé avec l'ID: {universe_id}")
            return universe_id
        except Exception as e:
            print(f"Erreur lors de la création de l'univers par défaut: {e}")
            return None

    def _serialize_value(self, value: Any) -> Any:
        """
        Sérialise une valeur pour la base de données

        Args:
            value: Valeur à sérialiser

        Returns:
            Valeur sérialisée
        """
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        elif isinstance(value, bool):
            return int(value)
        else:
            return value

    def close(self):
        """Ferme la connexion à la base de données"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self):
        """Destructeur - ferme la connexion"""
        self.close()


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()

# Initialiser le schéma si la base de données est vide
try:
    tables = db_manager.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    if not tables:
        print("Base de données vide détectée, initialisation du schéma...")
        db_manager._initialize_schema()
except Exception as e:
    print(f"Erreur lors de la vérification de la base de données: {e}")
