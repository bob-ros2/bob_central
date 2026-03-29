---
name: qdrant_memory
description: "A skill for storing and retrieving text data with optional embeddings using Qdrant vector database"
version: "1.0.0"
category: "system"
---

# Qdrant Memory Skill

## Goal
Provide a reliable interface to store, retrieve, and search text data using Qdrant vector database, supporting both plain text storage and vector similarity search.

## Description
This skill enables Eva to use Qdrant as a persistent memory layer for text data. It supports:
- Plain text storage with metadata
- Text storage with pre-computed embeddings
- Similarity search using embeddings
- Collection management (create, list, delete)
- Document retrieval by ID

The skill handles Qdrant connection management and provides a simple, robust API for memory operations.

## Usage

### Python API Usage
```python
# Import the skill functions
from qdrant_memory import save_text, load_text, search_similar, list_collections

# Store text without embeddings
doc_id = save_text("conversations", "Hello Eva!", {"user": "bob", "type": "greeting"})

# Load text by ID
document = load_text("conversations", doc_id)
print(f"Text: {document['text']}")
print(f"Metadata: {document['metadata']}")

# Search for similar texts (requires embeddings)
results = search_similar("knowledge_base", query_embedding, limit=5)

# List all collections
collections = list_collections()
```

### Skill Execution via Eva
```python
# Execute the CLI tool
execute_skill_script("qdrant_memory", "scripts/cli.py", "store conversations 'Hello world' --metadata '{\"user\": \"bob\"}'")

# Test connection
execute_skill_script("qdrant_memory", "scripts/cli.py", "test")

# List collections
execute_skill_script("qdrant_memory", "scripts/cli.py", "list")
```

### Command Line Usage
```bash
# Direct execution
python3 -m scripts.cli test
python3 -m scripts.cli store conversations "Test message"
python3 -m scripts.cli list
python3 -m scripts.cli search knowledge_base "artificial intelligence"
```

## Parameters

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_HTTP_API` | Qdrant HTTP API endpoint | `http://eva-qdrant:6333` |
| `QDRANT_GRPC_API` | Qdrant gRPC API endpoint | `http://eva-qdrant:6334` |

### Script Arguments
- `store <collection> <text> [--metadata JSON]`: Store text in collection
- `load <collection> <doc_id>`: Load text by ID
- `search <collection> <query> [--limit N]`: Search for similar texts
- `list`: List all collections
- `create <collection> [--size N]`: Create new collection
- `delete <collection>`: Delete collection
- `test`: Test Qdrant connection
- `all <collection> [--limit N]`: List all documents in collection

## Requirements
- Qdrant vector database running (configured in `.env`)
- `qdrant-client` Python package installed
- Network access to Qdrant service

## Technical Details

### Architecture
The skill uses a layered architecture:
1. **Connection Layer**: Manages Qdrant client with automatic reconnection
2. **Storage Layer**: Handles text storage with 1D dummy vectors for plain text
3. **Search Layer**: Provides similarity search for embeddings
4. **CLI Layer**: Command-line interface for manual operations

### Data Model
- Each document has: ID, text, metadata, timestamp
- Collections can store either:
  - Plain text (with 1D dummy vectors)
  - Text with embeddings (user-provided vectors)
- Metadata is stored as JSON-serializable dictionary

### Error Handling
- Connection errors are caught and reported
- Invalid operations return `None` or empty lists
- Collections are auto-created on first write

## Best Practices

### Environment Variables
- Always use `os.environ.get()` with sensible defaults
- Keep Qdrant URLs in the central `.env` file
- Update `.env.template` when adding new variables

### Collection Naming
- Use descriptive names: `conversations`, `knowledge_base`, `user_preferences`
- Include namespace prefixes if needed: `eva.conversations`, `system.logs`

### Data Management
- Store metadata consistently (same keys for similar data)
- Include timestamps for all documents
- Use reasonable limits for search operations

### Performance
- Batch operations when storing many documents
- Use appropriate vector dimensions for embeddings
- Monitor collection sizes and clean up old data

### Integration
- This skill can be called from other skills
- Use as a memory layer for conversation history
- Store search results for later retrieval
- Cache frequently accessed data

## Examples
See the `examples/` directory for complete usage examples:
- `basic_usage.py`: Basic storage and retrieval
- `embedding_demo.py`: Working with embeddings
- `conversation_memory.py`: Storing chat history
- `knowledge_base.py`: Building a searchable knowledge base