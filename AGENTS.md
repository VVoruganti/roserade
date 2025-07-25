# Roserade Development Checklist

## Updated Specification for MVP (Phase 1)

### Core Requirements (Simplified)
- **Database**: SQLite with sqlite-vec Python wrapper
- **Schema**: Use exact schema from spec.md (documents, chunks, chunk_embeddings, indexing_jobs)
- **Ollama**: Single embedding model (nomic-embed-text), no fallback
- **Document Processing**: PDF, TXT, MD only using pdfplumber
- **Chunking**: Fixed-size and semantic strategies using Chonkie latest API
- **CLI**: Core commands only (init, add, search, list, remove)

### Simplified Configuration (Phase 1)
```yaml
# Minimal config.yaml
database:
  path: "~/.config/roserade/index.db"

ollama:
  host: "http://localhost:11434"
  embedding_model: "nomic-embed-text"

chunking:
  strategy: "semantic"
  size: 512
  overlap: 50

processing:
  supported_extensions: [".pdf", ".txt", ".md"]
  max_file_size: "50MB"
```

## Development Checklist

### Phase 1: MVP Core (Priority Order)

#### 1. Project Setup
- [x] Initialize UV project structure
- [x] Create pyproject.toml with minimal dependencies
- [x] Set up src/roserade/ directory structure
- [x] Create basic __init__.py files

#### 2. Database Layer
- [x] Install sqlite-vec Python wrapper
- [x] Create database.py with connection management
- [x] Implement schema creation (exact SQL from spec)
- [x] Add basic CRUD operations for documents
- [x] Add CRUD operations for chunks
- [x] Add vector storage operations

#### 3. Configuration System
- [x] Create models/config.py with simplified AppConfig
- [x] Implement config loading from YAML
- [x] Add XDG directory support (~/.config/roserade/)
- [x] Create default config file generation

#### 4. Document Processing
- [x] Install pdfplumber
- [x] Create document_processor.py
- [x] Implement PDF text extraction
- [x] Implement TXT file reading
- [x] Implement MD file reading
- [x] Add file type detection
- [x] Add content hashing (SHA-256)

#### 5. Chunking System
- [x] Install chonkie latest version
- [x] Create chunker.py with Chonkie integration
- [x] Implement fixed-size chunking
- [x] Implement semantic chunking
- [x] Add chunk metadata (word count, sentence count)
- [x] Add content hashing for chunks

#### 6. Ollama Integration
- [x] Create embedder.py
- [x] Implement Ollama client
- [x] Add embedding generation
- [x] Add batch processing
- [x] Add error handling for connection issues

#### 7. CLI Interface
- [x] Install click
- [x] Create cli/main.py
- [x] Implement `roserade init` command
- [x] Implement `roserade add` command (single file/directory)
- [x] Implement `roserade search` command
- [x] Implement `roserade list` command
- [x] Implement `roserade remove` command
- [x] Add global options (--db-path, --config, --verbose)

#### 8. Indexing Pipeline
- [x] Create indexer.py
- [x] Implement document indexing workflow
- [x] Add duplicate detection (path + mtime)
- [x] Add progress reporting
- [x] Add error handling and logging

#### 9. Search Functionality
- [x] Implement vector similarity search
- [x] Add result formatting (table, json)
- [x] Add similarity threshold filtering
- [x] Add result limiting

#### 10. Testing
- [x] Set up pytest configuration
- [x] Add unit tests for database operations
- [x] Add tests for document processing
- [x] Add tests for chunking
- [x] Add CLI integration tests
- [x] Add test fixtures and sample files

#### 11. Documentation
- [x] Create README.md with installation instructions
- [x] Add CLI help documentation
- [x] Create basic usage examples
- [x] Add configuration documentation

### Phase 2: Enhanced Features (Future)
- [ ] Advanced chunking strategies
- [ ] Cron job system
- [ ] Configuration management commands
- [ ] Additional document formats (DOCX, HTML)
- [ ] Database backup/restore
- [ ] Performance optimizations
- [ ] Advanced search features

### Phase 3: Advanced Features (Future)
- [ ] Web interface
- [ ] Plugin system
- [ ] Cloud sync
- [ ] Analytics and monitoring
- [ ] Export/import functionality

## Development Commands

```bash
# Setup
uv venv
uv pip install -e ".[dev,test]"

# Development
uv run pytest
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/

# Build
uv build

# Run CLI
uv run roserade --help
uv run roserade init
uv run roserade add README.md
uv run roserade search "python"
```

## File Structure (Phase 1)
```
src/roserade/
├── __init__.py
├── cli/
│   ├── __init__.py
│   └── main.py
├── core/
│   ├── __init__.py
│   ├── database.py
│   ├── document_processor.py
│   ├── chunker.py
│   └── embedder.py
├── models/
│   ├── __init__.py
│   ├── config.py
│   ├── document.py
│   └── chunk.py
└── utils/
    ├── __init__.py
    └── config.py
```

## Dependencies (Phase 1)
```toml
[project]
dependencies = [
    "click>=8.0.0",
    "pydantic>=2.5.0",
    "pyyaml>=6.0",
    "requests>=2.28.0",
    "rich>=13.0.0",
    "tqdm>=4.64.0",
    "chonkie>=0.1.0",
    "pdfplumber>=0.10.0",
    "sqlite-vec>=0.0.1",
]
```

## Testing Checklist
- [x] All unit tests pass
- [x] CLI commands work end-to-end
- [x] Database operations are atomic
- [x] Error handling is graceful
- [x] Performance is acceptable for 1000+ documents
- [x] Configuration loading works correctly
- [x] XDG directories are created properly