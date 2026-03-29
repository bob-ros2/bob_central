# Qdrant Memory Skill

A skill for storing and retrieving text data using Qdrant vector database, following the Anthropic Agent Skills Specification.

## Quick Start

### Installation
The skill is automatically available when placed in the skills directory. Ensure dependencies are installed:

```bash
pip install qdrant-client
```

### Basic Usage
```python
# Import from the skill
from qdrant_memory.scripts import save_text, load_text, list_collections

# Store text
doc_id = save_text("my_collection", "Hello world!", {"user": "bob"})

# Load text
document = load_text("my_collection", doc_id)

# List collections
collections = list_collections()
```

### CLI Usage
```bash
# Test connection
python3 -m scripts.cli test

# Store text
python3 -m scripts.cli store conversations "Hello Eva" --metadata '{"user": "bob"}'

# List collections
python3 -m scripts.cli list

# Get all documents
python3 -m scripts.cli all conversations --limit 10
```

## Skill Structure

```
qdrant_memory/
├── SKILL.md                    # Primary documentation (YAML frontmatter)
├── scripts/                    # Executable Python code
│   ├── __init__.py            # Main implementation
│   └── cli.py                 # Command-line interface
├── examples/                   # Usage examples
│   ├── basic_usage.py         # Basic storage/retrieval
│   ├── embedding_demo.py      # Working with embeddings
│   └── conversation_memory.py # Conversation history storage
└── resources/                 # (Optional) Configuration files
```

## API Reference

### Core Functions

#### Text Storage
- `save_text(collection, text, metadata=None)`: Save plain text
- `save_with_embedding(collection, text, embedding, metadata=None)`: Save text with embedding vector

#### Text Retrieval
- `load_text(collection, doc_id)`: Load text by document ID
- `get_all_texts(collection, limit=100)`: Get all texts from collection

#### Search
- `search_similar(collection, query_embedding, limit=10)`: Search using embedding vector

#### Collection Management
- `list_collections()`: List all collections
- `create_collection(collection, vector_size=384)`: Create new collection
- `delete_collection(collection)`: Delete collection

#### Utility
- `test_connection()`: Test Qdrant connection

## Configuration

### Environment Variables
Set these in your `.env` file:

```bash
# Qdrant Connection
QDRANT_HTTP_API="http://eva-qdrant:6333"
QDRANT_GRPC_API="http://eva-qdrant:6334"
```

### Defaults
- HTTP URL: `http://eva-qdrant:6333`
- Vector size for new collections: 384
- Distance metric: Cosine

## Examples

See the `examples/` directory for complete working examples:

1. **Basic Usage**: Simple storage and retrieval
2. **Embedding Demo**: Working with vector embeddings
3. **Conversation Memory**: Storing and retrieving chat history

## Integration with Eva

### As a Memory Layer
```python
# Store conversation history
from qdrant_memory.scripts import save_text

def store_conversation(user_message, assistant_response):
    save_text("conversations", user_message, {"role": "user"})
    save_text("conversations", assistant_response, {"role": "assistant"})
```

### For Knowledge Storage
```python
# Store facts or search results
from qdrant_memory.scripts import save_text, search_similar

# Store web search results
def store_knowledge(topic, content):
    save_text("knowledge_base", content, {"topic": topic, "source": "web"})

# Later retrieve similar information
def find_similar_knowledge(query_embedding):
    return search_similar("knowledge_base", query_embedding)
```

## Best Practices

### Collection Naming
- Use descriptive names: `user_conversations`, `system_knowledge`, `web_search_results`
- Include user IDs for personal data: `conversations_user123`
- Use consistent naming conventions

### Metadata
- Include timestamps for all documents
- Use consistent key names across similar documents
- Store source information (user, system, web, etc.)
- Add document type or category

### Performance
- Use appropriate batch sizes for bulk operations
- Monitor collection sizes
- Consider archiving old data
- Use embeddings only when similarity search is needed

### Error Handling
- Always check return values (None indicates failure)
- Handle connection errors gracefully
- Validate input data before storage
- Implement retry logic for transient failures

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check Qdrant service is running
   - Verify environment variables
   - Test network connectivity

2. **Collection Not Found**
   - Collections are auto-created on first write
   - Use `create_collection()` explicitly if needed
   - Check collection name spelling

3. **Embedding Dimension Mismatch**
   - All embeddings in a collection must have same dimension
   - Specify correct `vector_size` when creating collection
   - Use `vector_size=1` for plain text (no embeddings)

4. **Permission Denied**
   - Check Qdrant authentication if configured
   - Verify network permissions

### Debugging
```python
from qdrant_memory.scripts import test_connection, list_collections

# Test basic functionality
if test_connection():
    print("✓ Qdrant connection OK")
    print(f"Collections: {list_collections()}")
else:
    print("✗ Connection failed")
```

## Development

### Adding New Features
1. Update `SKILL.md` with YAML frontmatter
2. Implement in `scripts/` directory
3. Add examples in `examples/`
4. Update this README if needed

### Testing
```bash
# Run examples
python3 examples/basic_usage.py
python3 examples/conversation_memory.py

# Test CLI
python3 -m scripts.cli test
python3 -m scripts.cli list
```

## License & Credits
Part of the Eva ROS 2 Brain-Mesh system. Follows Anthropic Agent Skills Specification v1.0.