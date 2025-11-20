# Claude Development Guide for Alezia AI

This document provides guidance for working with Claude (AI assistant) on the Alezia AI project. It contains architectural insights, development workflows, and best practices specifically tailored for AI-assisted development.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture Summary](#architecture-summary)
- [Key Components](#key-components)
- [Development Workflow](#development-workflow)
- [Common Tasks](#common-tasks)
- [Code Conventions](#code-conventions)
- [Testing Strategy](#testing-strategy)
- [Debugging Tips](#debugging-tips)
- [Important Considerations](#important-considerations)

## Project Overview

**Alezia AI** is an AI-powered role-playing game system featuring:
- Uncensored AI characters with evolving personalities
- Long-term memory and contextual awareness
- Dynamic relationship tracking
- Multiple universe support
- FastAPI backend + vanilla JavaScript frontend
- Ollama integration for LLM capabilities

### Tech Stack

- **Backend**: Python 3.8+, FastAPI, SQLite
- **Frontend**: HTML, CSS, vanilla JavaScript
- **AI/ML**: Ollama (local LLM), sentence-transformers (embeddings)
- **Key Libraries**: Pydantic, SQLAlchemy, aiosqlite

## Architecture Summary

```
alezia-ai/
├── backend/
│   ├── app.py              # Main FastAPI application
│   ├── database.py         # Database connection and setup
│   ├── models/             # Pydantic models and data structures
│   │   ├── character.py    # Character model
│   │   ├── chat.py         # Chat/session/message models
│   │   ├── memory.py       # Memory model
│   │   ├── relationship.py # Relationship model
│   │   └── universe.py     # Universe model
│   ├── routes/             # API endpoints
│   │   ├── characters.py   # Character CRUD operations
│   │   ├── chat.py         # Chat/conversation endpoints
│   │   ├── memory.py       # Memory operations
│   │   └── system.py       # System health checks
│   ├── services/           # Business logic
│   │   ├── llm_service.py         # Ollama LLM integration
│   │   ├── character_service.py   # Character management
│   │   ├── chat_service.py        # Chat session handling
│   │   ├── memory_manager.py      # Memory storage and retrieval
│   │   ├── relationship_service.py # Relationship tracking
│   │   └── personality_service.py  # Personality evolution
│   └── utils/              # Utilities
│       ├── db.py           # Database helpers
│       ├── errors.py       # Custom exceptions
│       ├── logging_config.py # Logging setup
│       └── embedding_loader.py # Embedding model loader
├── frontend/
│   ├── index.html          # Main UI
│   ├── assets/             # Static resources
│   └── components/         # UI components
├── data/                   # Database and embeddings storage
├── tests/                  # Test files
└── config.py               # Configuration management
```

## Key Components

### 1. LLM Service (`backend/services/llm_service.py`)

The core interface to Ollama for generating AI responses. Key functions:
- `generate_response()`: Main method for character responses
- Model configuration and prompt engineering
- Handles streaming and non-streaming responses

**When modifying**: Be cautious with prompt templates as they define character behavior.

### 2. Character Service (`backend/services/character_service.py`)

Manages character creation, retrieval, and updates. Handles:
- Character validation
- Personality trait management
- Integration with universe context

**When modifying**: Ensure character schema changes are reflected in database.

### 3. Memory Manager (`backend/services/memory_manager.py`)

Implements semantic memory system using vector embeddings:
- Stores conversation history
- Retrieves relevant memories based on context
- Calculates memory importance scores

**When modifying**: Memory retrieval logic affects character consistency.

### 4. Relationship Service (`backend/services/relationship_service.py`)

Tracks evolving relationships between characters and users:
- Sentiment analysis
- Trust and familiarity tracking
- Relationship history

**When modifying**: Changes here affect character emotional responses.

### 5. Personality Service (`backend/services/personality_service.py`)

Handles dynamic personality evolution:
- Trait modification based on interactions
- Decisive moment detection
- Personality consistency checks

**When modifying**: Evolution logic impacts long-term character development.

## Development Workflow

### Setting Up Development Environment

```bash
# Ensure you're in the project root
cd /home/user/alezia-ai

# Activate virtual environment (if exists)
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py
```

### Running the Application

```bash
# Start the API (finds available port automatically)
python run_api.py

# Or use specific port
uvicorn backend.app:app --reload --port 8000
```

### Checking System Health

```bash
# Check API health
python check_api_health.py

# Test database connection
python backend/test_db_connection.py

# Test specific features
python backend/test_memory_importance.py
python backend/test_trait_evolution.py
```

## Common Tasks

### Adding a New API Endpoint

1. **Create route in appropriate file** (`backend/routes/`)
2. **Implement service logic** (`backend/services/`)
3. **Add data models if needed** (`backend/models/`)
4. **Update database schema** if new tables required
5. **Test the endpoint** using FastAPI docs or API tests

Example structure:
```python
# In backend/routes/your_route.py
from fastapi import APIRouter, HTTPException
from backend.models.your_model import YourModel
from backend.services.your_service import YourService

router = APIRouter(prefix="/your-endpoint", tags=["your-tag"])

@router.post("/")
async def create_something(data: YourModel):
    result = await YourService.create(data)
    return result
```

### Adding a New Character Trait

1. **Update character model** (`backend/models/character.py`)
2. **Modify character service** (`backend/services/character_service.py`)
3. **Update personality service** if trait should evolve
4. **Update LLM prompts** to incorporate new trait
5. **Test with character creation**

### Modifying Memory Retrieval

1. **Edit memory manager** (`backend/services/memory_manager.py`)
2. **Adjust importance calculation** if needed
3. **Test memory retrieval accuracy**
4. **Consider embedding model changes** if semantic matching is affected

### Adding a New Model to Ollama Support

1. **Update config.py** to include model name
2. **Test model with** `ollama pull model_name`
3. **Update documentation** (README.md, START.md)
4. **Test response quality** with various prompts

## Code Conventions

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for function parameters and returns
- Prefer **async/await** for I/O operations
- Use **Pydantic models** for data validation

```python
# Good example
async def get_character(character_id: int) -> Optional[Character]:
    """Retrieve a character by ID."""
    async with get_db() as db:
        result = await db.fetch_one(query, {"id": character_id})
        return Character(**result) if result else None
```

### Error Handling

- Use **custom exceptions** from `backend/utils/errors.py`
- Provide **meaningful error messages**
- Log errors appropriately
- Return proper HTTP status codes

```python
# Good example
if not character:
    logger.error(f"Character {character_id} not found")
    raise HTTPException(status_code=404, detail="Character not found")
```

### Database Operations

- Use **async database operations**
- Always use **parameterized queries** (prevent SQL injection)
- Handle **connection errors gracefully**
- Close connections properly

### Logging

- Use the configured logger from `backend/utils/logging_config.py`
- Log levels: DEBUG (development), INFO (key operations), WARNING (issues), ERROR (failures)
- Include context in log messages

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Creating character: {character.name}")
logger.error(f"Failed to connect to LLM: {error}", exc_info=True)
```

## Testing Strategy

### Unit Tests

Located in `tests/` directory. Test individual components:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test file
pytest tests/test_character_manager.py
```

### Integration Tests

Test API endpoints:

```bash
# Test character creation
python backend/test_api.py

# Test chat functionality
python api_test.py
```

### Manual Testing

1. **Start the API**: `python run_api.py`
2. **Access Swagger UI**: http://localhost:8000/docs
3. **Test endpoints** interactively
4. **Check frontend**: Open http://localhost:8000

### What to Test

- **Character CRUD operations**
- **Chat session management**
- **Memory retrieval accuracy**
- **Relationship updates**
- **Personality evolution**
- **Error handling**
- **Database integrity**

## Debugging Tips

### Common Issues and Solutions

#### 1. API Won't Start (Port Issues)

```bash
# Check if port is in use
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Use automatic port finding
python run_api.py  # Finds available port
```

#### 2. Ollama Connection Failed

```bash
# Check Ollama is running
ollama list

# Test specific model
ollama run gemma:2b "test"

# Check Ollama API
curl http://localhost:11434/api/tags
```

#### 3. Database Errors

```bash
# Reinitialize database
rm data/alezia.db
python init_db.py

# Check database integrity
python backend/test_db_connection.py
```

#### 4. Memory/Embedding Issues

- Check if embedding model is downloaded
- Verify `data/embeddings/` directory exists
- Check available RAM (embeddings can be memory-intensive)
- Consider using smaller embedding model

#### 5. Slow Response Times

- Switch to lighter LLM model (gemma:2b)
- Check available VRAM/RAM
- Reduce context window size
- Limit memory retrieval results

### Logging and Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints in code
logger.debug(f"Memory retrieval: {len(memories)} results")
logger.debug(f"Character state: {character.dict()}")
```

### Using FastAPI Debug Mode

```bash
# Run with auto-reload and debug
uvicorn backend.app:app --reload --log-level debug
```

## Important Considerations

### Security

- **No authentication currently implemented** - consider adding for production
- **Input validation** through Pydantic models
- **SQL injection prevention** via parameterized queries
- **CORS enabled** for local development

### Performance

- **Async operations** for I/O-bound tasks
- **Connection pooling** for database
- **Embedding caching** to reduce computation
- **Memory limits** on conversation history

### Data Privacy

- **Local data storage** (SQLite in `data/`)
- **No external API calls** except to local Ollama
- **User conversations stored locally**

### Scalability Considerations

Current limitations:
- SQLite (single-file database)
- Local LLM only
- No distributed caching
- Single-server deployment

For scaling, consider:
- PostgreSQL for database
- Redis for caching
- Cloud LLM APIs as fallback
- Load balancing for multiple instances

### Character Quality

- **Prompt engineering** is crucial for character consistency
- **Memory relevance** affects conversation quality
- **Personality evolution** should be gradual and realistic
- **Universe context** enriches character responses

### Future Development Areas

Based on existing roadmap and improvements:
- Enhanced UI/UX
- Real-time streaming responses
- Multi-character conversations
- Voice integration
- Advanced personality systems
- Cloud deployment support

## Working with Claude

### Best Practices for AI-Assisted Development

1. **Provide context**: Reference this file when starting new features
2. **Be specific**: Clear requirements lead to better implementations
3. **Review changes**: Always review AI-generated code before committing
4. **Test incrementally**: Test each change before moving to the next
5. **Ask questions**: If something is unclear, ask for clarification

### Useful Prompts for Common Tasks

```
"Add a new endpoint to retrieve character relationships"
"Improve memory retrieval to prioritize recent interactions"
"Add error handling for when Ollama is not responding"
"Optimize database queries in the character service"
"Add unit tests for the relationship service"
"Debug why character responses are slow"
"Refactor the LLM service to support streaming"
```

### What to Keep in Mind

- **Preserve existing functionality** unless explicitly asked to change it
- **Maintain code style consistency** with existing codebase
- **Update documentation** when making significant changes
- **Consider backward compatibility** for database schema changes
- **Test on different platforms** if possible (Windows/Linux/macOS)

---

**Version**: 1.0
**Last Updated**: 2025-11-20
**Project**: Alezia AI
**Maintainer**: Development Team

For more information:
- **Quick Start**: See [START.md](START.md)
- **Full Documentation**: See [README.md](README.md)
- **Roadmap**: See [ROADMAP.md](ROADMAP.md)
- **Improvements**: See [IMPROVEMENTS.md](IMPROVEMENTS.md)
