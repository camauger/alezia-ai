# Code Improvement Suggestions

This document provides a prioritized list of suggestions to improve the codebase's quality, performance, security, and maintainability.

## Code Quality and Readability

*   **Priority:** Medium
*   **Title:** Use `Enum` for Memory and Trait Types
*   **File & Lines:** `backend/models/memory.py:29-35`, `backend/models/character.py:70-76`
*   **Description:** The `memory_type` in `MemoryCreate` and `category` in `CharacterTrait` are validated against a hardcoded list of strings. This is error-prone and makes it difficult to manage the allowed types.
*   **Suggested Improvement:** Use Python's `Enum` to define the allowed types. This provides better type safety, autocompletion, and a single source of truth for the allowed values.

    **Before:**
    ```python
    class MemoryCreate(MemoryBase):
        # ...
        @validator("memory_type")
        def check_memory_type(cls, v):
            allowed_types = ["conversation", "event", "observation", "reflection"]
            if v not in allowed_types:
                raise ValueError(f"Memory type must be one of the following: {', '.join(allowed_types)}")
            return v
    ```

    **After:**
    ```python
    from enum import Enum

    class MemoryType(str, Enum):
        CONVERSATION = "conversation"
        EVENT = "event"
        OBSERVATION = "observation"
        REFLECTION = "reflection"
        USER_MESSAGE = "user_message"
        CHARACTER_MESSAGE = "character_message"
        FACTS_EXTRACTION = "facts_extraction"

    class MemoryCreate(MemoryBase):
        memory_type: MemoryType = MemoryType.CONVERSATION
        # ...
    ```

*   **Priority:** Low
*   **Title:** Consolidate API Client Classes
*   **File & Lines:** `frontend/assets/js/api.js`, `frontend/assets/js/memory-api.js`
*   **Description:** There are two separate API client classes, `AleziaAPI` and `MemoryAPI`, with overlapping functionality (e.g., fetching data from the API). This can lead to code duplication and inconsistencies.
*   **Suggested Improvement:** Consolidate all API calls into a single `AleziaAPI` class. This will create a single source of truth for all API interactions and make the code easier to maintain.

    **Before:**
    ```javascript
    // frontend/assets/js/api.js
    class AleziaAPI {
        // ... methods for characters, chat, etc.
    }

    // frontend/assets/js/memory-api.js
    class MemoryAPI {
        // ... methods for memories
    }
    ```

    **After:**
    ```javascript
    // frontend/assets/js/api.js
    class AleziaAPI {
        // ... methods for characters, chat, etc.

        // Methods from MemoryAPI integrated here
        async getCharacterMemories(characterId, limit = 100) {
            // ...
        }

        async getCharacterFacts(characterId, subject = null) {
            // ...
        }
        // ... and so on
    }
    ```

## Performance Optimization

*   **Priority:** High
*   **Title:** Use Asynchronous Database Operations
*   **File & Lines:** `backend/utils/db.py` (and all files that use `db_manager`)
*   **Description:** The current database operations are synchronous, which can block the event loop and limit the application's concurrency, especially under load.
*   **Suggested Improvement:** Use an asynchronous database driver like `asyncpg` (for PostgreSQL) or `aiosqlite` (for SQLite) and make all database operations `async`. This will significantly improve the application's performance and scalability.

    **Before:**
    ```python
    # backend/utils/db.py
    # Synchronous operations
    def execute_query(self, query, params=None, fetchall=True):
        # ...
    ```

    **After:**
    ```python
    # backend/utils/db.py
    # Asynchronous operations
    async def execute_query(self, query, params=None, fetchall=True):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                if fetchall:
                    return await cursor.fetchall()
                else:
                    return await cursor.fetchone()
    ```

*   **Priority:** Medium
*   **Title:** Optimize Embedding Loading
*   **File & Lines:** `backend/services/memory_manager.py:29-46`
*   **Description:** The embedding model is loaded every time a `MemoryManager` is instantiated. This can be slow and inefficient, especially if multiple `MemoryManager` instances are created.
*   **Suggested Improvement:** Load the embedding model once as a singleton and reuse the same instance across the application. This will significantly reduce the application's startup time and memory usage.

    **Before:**
    ```python
    class MemoryManager:
        def __init__(self):
            self.embedding_model = None
            self._load_embedding_model()

        def _load_embedding_model(self):
            # ... loads the model
    ```

    **After:**
    ```python
    # In a separate module, e.g., backend/utils/embedding_loader.py
    from sentence_transformers import SentenceTransformer

    def get_embedding_model():
        # ... logic to load the model once
        if not hasattr(get_embedding_model, "model"):
            get_embedding_model.model = SentenceTransformer(...)
        return get_embedding_model.model

    # backend/services/memory_manager.py
    class MemoryManager:
        def __init__(self):
            self.embedding_model = get_embedding_model()
    ```

## Security

*   **Priority:** High
*   **Title:** Use Parameterized Queries to Prevent SQL Injection
*   **File & Lines:** `backend/utils/db.py` (and all files that use `db_manager`)
*   **Description:** The current database queries are constructed using f-strings, which makes them vulnerable to SQL injection attacks.
*   **Suggested Improvement:** Use parameterized queries to safely pass data to the database. This is a critical security measure that should be implemented immediately.

    **Before:**
    ```python
    # Vulnerable to SQL injection
    count_query = f"SELECT count(*) as record_count FROM {table['name']}"
    ```

    **After:**
    ```python
    # Safe from SQL injection
    count_query = "SELECT count(*) as record_count FROM ?"
    db_manager.execute_query(count_query, (table['name'],))
    ```

*   **Priority:** High
*   **Title:** Avoid Hardcoding Secrets
*   **File & Lines:** `backend/config.py`
*   **Description:** The `SECURITY_CONFIG` dictionary contains a hardcoded `hash_algorithm`. While not a secret in itself, it's a good practice to manage all security-related configurations in a consistent and secure manner.
*   **Suggested Improvement:** Use environment variables to manage all security-related configurations. This makes the application more secure and easier to configure for different environments.

    **Before:**
    ```python
    SECURITY_CONFIG = {
        "token_expiration": 24 * 60 * 60,
        "hash_algorithm": "HS256",
        # ...
    }
    ```

    **After:**
    ```python
    # Using python-decouple or os.environ
    from decouple import config

    SECURITY_CONFIG = {
        "token_expiration": config("TOKEN_EXPIRATION", default=24 * 60 * 60, cast=int),
        "hash_algorithm": config("HASH_ALGORITHM", default="HS256"),
        # ...
    }
    ```

## Maintainability and Best Practices

*   **Priority:** High
*   **Title:** Implement a Proper Database Management System
*   **File & Lines:** `backend/utils/db.py`
*   **Description:** The current `db_manager` is a custom implementation that directly interacts with the database. This can be difficult to maintain and scale.
*   **Suggested Improvement:** Use a well-established Object-Relational Mapper (ORM) like SQLAlchemy. This will provide a more robust and maintainable way to interact with the database, with features like data validation, migrations, and connection pooling. The project already uses SQLAlchemy for its models, so it should be used for all database interactions.

*   **Priority:** Medium
*   **Title:** Add Unit and Integration Tests
*   **File & Lines:** `tests/`
*   **Description:** The project has a very limited test suite. This makes it difficult to ensure the code's correctness and prevent regressions.
*   **Suggested Improvement:** Add a comprehensive test suite with unit tests for individual functions and integration tests for the API endpoints. This will significantly improve the code's quality and make it easier to refactor and add new features.

*   **Priority:** Low
*   **Title:** Use a Linter and Formatter
*   **Description:** The codebase has some inconsistencies in code style and formatting.
*   **Suggested Improvement:** Use a linter like `ruff` or `pylint` and a formatter like `black` or `autopep8` to enforce a consistent code style across the project. This will make the code easier to read and maintain.
