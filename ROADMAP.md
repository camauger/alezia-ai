# Alezia AI Development Roadmap

This roadmap outlines the plan to implement the improvements suggested in `IMPROVEMENTS.md`. The tasks are organized into milestones, starting with the highest priority items to deliver the most impact early on.

## Milestone 1: Foundational Backend Improvements (High Priority)

This milestone focuses on critical backend refactoring and security improvements that will provide a solid foundation for future development.

### Task 1.1: Secure Configuration with Environment Variables
- **Goal:** Avoid hardcoding sensitive information and improve configuration flexibility across different environments.
- **Actions:**
    1.  Create a `.env.example` file in the root directory to document all required environment variables (e.g., `CORS_ORIGINS`, `DB_PATH`, `LLM_API_URL`).
    2.  Add `python-decouple` to the `requirements.txt` file.
    3.  Modify `config.py` to load `CORS_ORIGINS` and other configurations from environment variables using `decouple`.
- **Reference:** `IMPROVEMENTS.md` - "Avoid Hardcoding CORS Origins"

### Task 1.2: Refactor `CharacterManager`
- **Goal:** Improve code structure, testability, and maintainability by breaking down the `CharacterManager` god object.
- **Actions:**
    1.  Create a new `backend/services` directory structure with the following files: `character_service.py`, `relationship_service.py`, `personality_service.py`, `character_state_service.py`.
    2.  Carefully move the relevant methods and logic from `character_manager.py` into the new, more focused service files.
    3.  Update the API routes in `backend/routes/characters.py` to import and use the new services.
    4.  Initially, `character_manager.py` can be kept as a facade that delegates calls to the new services to minimize breaking changes, with the goal of eventually phasing it out.
- **Reference:** `IMPROVEMENTS.md` - "Refactor `CharacterManager` into Smaller, Focused Services"

## Milestone 2: Database and API Enhancements (Medium Priority)

This milestone focuses on improving database interactions for better performance and maintainability.

### Task 2.1: Integrate SQLAlchemy ORM
- **Goal:** Replace raw SQL queries with a more robust, secure, and maintainable ORM.
- **Actions:**
    1.  Add `SQLAlchemy` to `requirements.txt`.
    2.  Create a `backend/database.py` file to manage the SQLAlchemy engine and session.
    3.  Define SQLAlchemy models for `Character`, `Universe`, `Relationship`, `Trait`, etc., in the `backend/models/` directory.
    4.  Refactor the new services (from Milestone 1) to use SQLAlchemy for all database operations.
    5.  Remove the old `db_manager` and raw SQL queries.
- **Reference:** `IMPROVEMENTS.md` - "Use an ORM for Database Interactions"

### Task 2.2: Optimize Database Queries
- **Goal:** Improve API performance by reducing the number of database queries.
- **Actions:**
    1.  Once SQLAlchemy is integrated, refactor the `get_characters` method (now in `CharacterService`) to use a `joinedload` or `selectinload` to fetch characters and their associated universes in a single, efficient query.
- **Reference:** `IMPROVEMENTS.md` - "Optimize `get_characters` Method"

## Milestone 3: Frontend Overhaul (High Priority)

This milestone focuses on modernizing the frontend for better maintainability, scalability, and user experience.

### Task 3.1: Set Up a Modern JavaScript Framework
- **Goal:** Replace the vanilla JavaScript frontend with a modern framework like React or Vue for a more structured and maintainable codebase.
- **Actions:**
    1.  Choose a framework (e.g., React with Vite for fast setup and development).
    2.  Set up a new frontend project structure within the `frontend` directory.
    3.  Re-create the main UI components (`CharacterList`, `ChatWindow`, `CharacterCreationModal`) in the new framework.
- **Reference:** `IMPROVEMENTS.md` - "Refactor Frontend to Use a Modern JavaScript Framework"

### Task 3.2: Refactor API Client
- **Goal:** Clean up and consolidate the frontend API client to make it more robust and easier to use.
- **Actions:**
    1.  Create a new `api.js` (or `api.ts` if using TypeScript) in the new frontend structure.
    2.  Implement a single, generic `fetchAPI` function that handles all requests, including setting headers, handling responses, and managing errors.
    3.  Create specific API functions (e.g., `getCharacters`, `createCharacter`) that use the generic `fetchAPI` function.
- **Reference:** `IMPROVEMENTS.md` - "Consolidate API Calls in `api.js`"

## Milestone 4: Polishing and Final Touches (Low Priority)

This milestone includes lower-priority tasks that will improve the overall quality and user experience of the application.

### Task 4.1: Standardize API Error Handling
- **Goal:** Make API error responses consistent, predictable, and more informative for the frontend.
- **Actions:**
    1.  Create a set of custom exception classes in `backend/utils/errors.py` (e.g., `CharacterNotFound`, `InvalidTraitValue`).
    2.  Update the services to raise these custom exceptions when appropriate.
    3.  Modify the FastAPI exception handlers in `backend/app.py` to catch these custom exceptions and return standardized JSON error responses.
- **Reference:** `IMPROVEMENTS.md` - "Improve Consistency in API Error Handling"

### Task 4.2: Implement a User-Friendly Notification System
- **Goal:** Replace disruptive `alert()` calls with a more modern and user-friendly notification system.
- **Actions:**
    1.  Choose a notification library for the new frontend framework (e.g., `react-toastify` for React).
    2.  Integrate the library into the main application component.
    3.  Replace all `alert()` calls in the frontend code with calls to the new notification system for displaying success messages, errors, and other information.
- **Reference:** `IMPROVEMENTS.md` - "Replace `alert()` with a More User-Friendly Notification System"
