"""
Script d'initialisation de la base de données pour Alezia AI
Crée les tables nécessaires pour le système de JDR avec IA
"""

import os
import sys
import sqlite3
from pathlib import Path

# Ajout du répertoire parent au path pour les imports
script_dir = Path(__file__).resolve().parent
sys.path.append(str(script_dir.parent))

from backend.config import DB_PATH, DATA_DIR

# Création du répertoire de données si nécessaire
os.makedirs(DATA_DIR, exist_ok=True)

# Définition du schéma de la base de données
SCHEMA = """
-- Table des univers
CREATE TABLE IF NOT EXISTS universes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    type TEXT NOT NULL,
    time_period TEXT,
    rules TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des éléments d'univers
CREATE TABLE IF NOT EXISTS universe_elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    universe_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT NOT NULL,
    importance INTEGER DEFAULT 3,
    FOREIGN KEY (universe_id) REFERENCES universes (id)
);

-- Table des personnages
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    personality TEXT NOT NULL,
    backstory TEXT,
    universe_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (universe_id) REFERENCES universes (id)
);

-- Table des mémoires
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL DEFAULT 1.0,
    embedding BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    metadata TEXT,
    FOREIGN KEY (character_id) REFERENCES characters (id)
);

-- Table des faits
CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source_memory_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters (id),
    FOREIGN KEY (source_memory_id) REFERENCES memories (id)
);

-- Table des relations
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER,
    target_name TEXT NOT NULL,
    sentiment REAL DEFAULT 0.0,
    trust REAL DEFAULT 0.0,
    familiarity REAL DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (character_id) REFERENCES characters (id)
);

-- Table des sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    summary TEXT,
    FOREIGN KEY (character_id) REFERENCES characters (id)
);

-- Table des messages
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    is_user BOOLEAN NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions (id)
);
"""

def init_database():
    """Initialise la base de données avec le schéma défini"""
    print(f"Initialisation de la base de données: {DB_PATH}")

    try:
        # Création du répertoire parent si nécessaire
        os.makedirs(DB_PATH.parent, exist_ok=True)

        # Connexion à la base de données
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Exécution du schéma
        cursor.executescript(SCHEMA)

        # Validation des changements
        conn.commit()
        print("Schéma de base de données créé avec succès.")

        # Ajout de données d'exemple (univers par défaut)
        add_default_data(conn)

        # Fermeture de la connexion
        conn.close()
        print("Base de données initialisée avec succès.")
        return True

    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False

def add_default_data(conn):
    """Ajoute des données par défaut à la base de données"""
    try:
        cursor = conn.cursor()

        # Ajout d'un univers médiéval fantasy par défaut
        cursor.execute("""
            INSERT INTO universes (name, description, type, time_period, rules)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Taliria",
            "Un monde médiéval fantastique où la magie et les créatures mythiques coexistent avec les humains.",
            "fantasy",
            "medieval",
            "Dans cet univers, la magie est omniprésente mais rare parmi les humains. Les créatures fantastiques vivent dans les forêts profondes et les montagnes."
        ))

        universe_id = cursor.lastrowid

        # Ajout de quelques éléments d'univers
        universe_elements = [
            (universe_id, "Royaume d'Aldoria", "location", "Le plus grand royaume humain, connu pour ses chevaliers et ses tournois.", 5),
            (universe_id, "La Guilde des Mages", "organization", "Une organisation secrète regroupant les utilisateurs de magie.", 4),
            (universe_id, "Les Terres Désolées", "location", "Une région corrompue par une ancienne magie noire.", 3)
        ]

        cursor.executemany("""
            INSERT INTO universe_elements (universe_id, name, type, description, importance)
            VALUES (?, ?, ?, ?, ?)
        """, universe_elements)

        # Validation des changements
        conn.commit()
        print("Données par défaut ajoutées avec succès.")

    except Exception as e:
        print(f"Erreur lors de l'ajout des données par défaut: {e}")
        conn.rollback()

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)