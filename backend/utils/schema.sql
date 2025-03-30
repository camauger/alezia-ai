-- Schéma de base de données pour le système de JDR avec IA

-- Table des personnages
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    personality TEXT NOT NULL,
    backstory TEXT,
    universe_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (universe_id) REFERENCES universes(id)
);

-- Table des univers
CREATE TABLE IF NOT EXISTS universes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    type TEXT NOT NULL,
    time_period TEXT,
    rules TEXT,
    created_at TEXT NOT NULL
);

-- Table des éléments d'univers
CREATE TABLE IF NOT EXISTS universe_elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    universe_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT NOT NULL,
    importance INTEGER DEFAULT 3,
    FOREIGN KEY (universe_id) REFERENCES universes(id) ON DELETE CASCADE
);

-- Table des mémoires
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL DEFAULT 1.0,
    metadata TEXT,
    embedding TEXT,
    created_at TEXT NOT NULL,
    last_accessed TEXT,
    access_count INTEGER DEFAULT 0,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- Table des faits
CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source_memory_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (source_memory_id) REFERENCES memories(id) ON DELETE SET NULL
);

-- Table des relations
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    target_name TEXT NOT NULL,
    sentiment REAL DEFAULT 0.0,
    trust REAL DEFAULT 0.0,
    familiarity REAL DEFAULT 0.0,
    notes TEXT,
    last_updated TEXT NOT NULL,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- Table des traits de personnalité
CREATE TABLE IF NOT EXISTS personality_traits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    value REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    volatility REAL DEFAULT 0.2,
    last_updated TEXT NOT NULL,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- Table des changements de traits (historique)
CREATE TABLE IF NOT EXISTS trait_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    trait_id INTEGER NOT NULL,
    old_value REAL NOT NULL,
    new_value REAL NOT NULL,
    change_amount REAL NOT NULL,
    reason TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (trait_id) REFERENCES personality_traits(id) ON DELETE CASCADE
);

-- Table des sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    summary TEXT,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- Table des messages
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    is_user BOOLEAN NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Index pour optimiser les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_memories_character_id ON memories(character_id);
CREATE INDEX IF NOT EXISTS idx_relationships_character_id ON relationships(character_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_facts_character_id ON facts(character_id);
CREATE INDEX IF NOT EXISTS idx_personality_traits_character_id ON personality_traits(character_id);
CREATE INDEX IF NOT EXISTS idx_trait_changes_character_id ON trait_changes(character_id);
CREATE INDEX IF NOT EXISTS idx_trait_changes_trait_id ON trait_changes(trait_id);