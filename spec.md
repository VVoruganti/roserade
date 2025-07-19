# Roserade: Document Indexing CLI Tool Specification

## Project Overview

**Roserade** is a command-line interface (CLI) tool for indexing and chunking local documents into a SQLite database with the sqlite-vec extension, using Ollama for language models and embedding generation. Named after the Pokémon known for its thorny vines and beautiful flowers, Roserade helps you cultivate and harvest knowledge from your document gardens. The tool should support configurable database locations and automated re-indexing through cron job registration.

**Primary Inspiration**: [Haiku RAG](https://github.com/ggozad/haiku.rag) - A RAG tool with document indexing capabilities

**Development Stack**:

- **Package Manager**: UV for fast Python package management and distribution
- **Data Modeling**: Pydantic for robust data validation and serialization
- **Chunking**: Chonkie library for advanced document chunking strategies
- **Target Platform**: Unix-based systems (macOS, Linux) following XDG standards
- **Distribution**: PyPI with uvx support for easy installation and execution

#### Unix Configuration Directory Structure

The tool follows XDG Base Directory specification for macOS/Unix systems:

```
~/.config/roserade/
├── config.yaml           # Main configuration file
├── jobs.yaml             # Cron job definitions
├── index.db              # SQLite database (default location)
├── backups/              # Database backups
│   ├── index.db.2025-07-19.backup
│   └── index.db.2025-07-18.backup
└── logs/                 # Application logs
    ├── roserade.log
    ├── cron.log
    └── error.log
```

## Core Requirements

### 1. Database & Storage

- **Database**: SQLite with sqlite-vec extension for vector storage
- **Configuration**: Configurable database location via CLI arguments and config file
- **Schema**: Support for documents, chunks, embeddings, and metadata storage
- **Migrations**: Automatic schema creation and migration handling

### 2. Document Processing

- **Supported Formats**: PDF, TXT, MD, DOCX, HTML, CSV, JSON
- **Chunking Strategies**:
  - Fixed-size chunking with configurable overlap
  - Semantic chunking (sentence/paragraph boundaries)
  - Content-aware chunking for structured documents
- **Metadata Extraction**: File path, creation date, modification date, file type, size
- **Duplicate Detection**: Content-based deduplication using file hashes

### 3. Embedding & Language Models

- **Provider**: Ollama for both embedding and language models
- **Configurable Models**: Support for different embedding models (e.g., `nomic-embed-text`, `mxbai-embed-large`)
- **Batch Processing**: Efficient batch embedding generation
- **Error Handling**: Retry logic and graceful degradation for model failures

### 4. CLI Interface

#### Core Commands

```bash
# Initialize new index
roserade init --db-path ~/.config/roserade/index.db --config ~/.config/roserade/config.yaml

# Index single file or directory
roserade add /path/to/document.pdf
roserade add /path/to/directory --recursive

# Search indexed documents
roserade search "query text" --limit 10 --threshold 0.7

# List indexed documents
roserade list --format table|json

# Remove documents from index
roserade remove /path/to/document.pdf
roserade remove --pattern "*.txt"

# Re-index existing documents
roserade reindex --all
roserade reindex /path/to/directory

# Cron job management
roserade cron add /Users/username/Documents --schedule "0 2 * * *" --name daily-docs
roserade cron list
roserade cron remove daily-docs
roserade cron run daily-docs

# Configuration management
roserade config show
roserade config set embedding.model nomic-embed-text
roserade config set chunking.size 512

# Database operations
roserade db info
roserade db vacuum
roserade db export --format jsonl --output export.jsonl
```

#### Command Options

**Global Options:**

- `--db-path`: Database file path (default: `~/.config/roserade/index.db`)
- `--config`: Configuration file path (default: `~/.config/roserade/config.yaml`)
- `--verbose/-v`: Enable verbose logging
- `--quiet/-q`: Suppress non-error output

**Add Command Options:**

- `--recursive/-r`: Process directories recursively
- `--exclude`: Glob patterns to exclude
- `--force`: Re-index existing documents
- `--chunk-size`: Override default chunk size
- `--chunk-overlap`: Override default chunk overlap

**Search Command Options:**

- `--limit/-n`: Number of results (default: 10)
- `--threshold`: Similarity threshold (0.0-1.0)
- `--format`: Output format (table, json, text)
- `--context`: Show surrounding context for matches

### 5. Configuration System

#### Configuration File Structure (`config.yaml`)

```yaml
# Database settings
database:
  path: "~/.config/roserade/index.db"
  backup_enabled: true
  backup_interval: "24h"

# Ollama settings
ollama:
  host: "http://localhost:11434"
  embedding_model: "nomic-embed-text"
  timeout: 30

# Chunking configuration
chunking:
  strategy: "semantic" # fixed, semantic, content-aware, chonky
  size: 512
  overlap: 50
  min_chunk_size: 100
  max_chunk_size: 2048
  # Chonky-specific settings
  chonky:
    method: "sentence_split" # sentence_split, paragraph_split, markdown_split
    respect_boundaries: true
    language: "en"

# Document processing
processing:
  supported_extensions: [".pdf", ".txt", ".md", ".docx", ".html"]
  max_file_size: "50MB"
  encoding: "utf-8"
  parallel_workers: 4

# Indexing settings
indexing:
  batch_size: 100
  vector_dimensions: 768
  similarity_metric: "cosine"

# Cron job settings
cron:
  enabled: true
  job_file: "~/.config/roserade/jobs.yaml"
  log_retention: "30d"

# Logging
logging:
  level: "info"
  file: "~/.config/roserade/roserade.log"
  max_size: "10MB"
  backup_count: 5
```

#### Unix Configuration Directory Structure

The tool follows XDG Base Directory specification for macOS/Unix systems:

```
~/.config/roserade/
├── config.yaml           # Main configuration file
├── jobs.yaml             # Cron job definitions
├── index.db              # SQLite database (default location)
├── backups/              # Database backups
│   ├── index.db.2025-07-19.backup
│   └── index.db.2025-07-18.backup
└── logs/                 # Application logs
    ├── roserade.log
    ├── cron.log
    └── error.log
```

#### Job Configuration Structure

```yaml
jobs:
  daily-docs:
    path: "/Users/username/Documents"
    schedule: "0 2 * * *"
    recursive: true
    exclude_patterns: ["*.tmp", "*.log", ".DS_Store"]
    enabled: true
    last_run: "2025-07-18T02:00:00Z"
    next_run: "2025-07-19T02:00:00Z"

  project-sync:
    path: "/Users/username/workspace/projects"
    schedule: "*/30 * * * *"
    recursive: true
    force_reindex: false
    enabled: true
```

#### Cron Features

- **Schedule Management**: Create, list, update, and remove scheduled indexing jobs
- **Job Execution**: Manual job execution and automatic scheduling
- **Logging**: Detailed job execution logs with rotation
- **Status Monitoring**: Track job success/failure and execution times
- **Conflict Resolution**: Handle overlapping job execution

### 7. Database Schema

#### Tables Structure

```sql
-- Documents table
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    size_bytes INTEGER,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_indexed TIMESTAMP,
    metadata JSON
);

-- Chunks table
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    start_offset INTEGER,
    end_offset INTEGER,
    chunk_metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector embeddings table (using sqlite-vec)
CREATE VIRTUAL TABLE chunk_embeddings USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding FLOAT[768]  -- Adjust dimension based on model
);

-- Indexing jobs table
CREATE TABLE indexing_jobs (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    schedule TEXT NOT NULL,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    status TEXT DEFAULT 'active',
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8. Core Components Architecture

#### Component Structure

```
src/roserade/
├── cli/
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── init.py
│   │   ├── add.py
│   │   ├── search.py
│   │   ├── cron.py
│   │   └── config.py
│   └── main.py
├── core/
│   ├── __init__.py
│   ├── database.py
│   ├── document_processor.py
│   ├── chunker.py
│   ├── embedder.py
│   └── indexer.py
├── models/
│   ├── __init__.py
│   ├── config.py
│   ├── document.py
│   ├── chunk.py
│   └── job.py
├── utils/
│   ├── __init__.py
│   ├── config.py
│   ├── logging.py
│   └── file_utils.py
├── cron/
│   ├── __init__.py
│   ├── scheduler.py
│   └── job_runner.py
└── __init__.py
```

#### Pydantic Models

**Configuration Models** (`models/config.py`)

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from pathlib import Path

class DatabaseConfig(BaseModel):
    path: Path = Field(default=Path("~/.config/roserade/index.db").expanduser())
    backup_enabled: bool = True
    backup_interval: str = "24h"

class OllamaConfig(BaseModel):
    host: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    timeout: int = 30

class ChonkyConfig(BaseModel):
    method: Literal["sentence_split", "paragraph_split", "markdown_split"] = "sentence_split"
    respect_boundaries: bool = True
    language: str = "en"

class ChunkingConfig(BaseModel):
    strategy: Literal["fixed", "semantic", "content-aware", "chonky"] = "semantic"
    size: int = Field(default=512, ge=100, le=4096)
    overlap: int = Field(default=50, ge=0, le=512)
    min_chunk_size: int = Field(default=100, ge=50)
    max_chunk_size: int = Field(default=2048, le=8192)
    chonky: ChonkyConfig = ChonkyConfig()

    @validator('overlap')
    def validate_overlap(cls, v, values):
        if 'size' in values and v >= values['size']:
            raise ValueError('overlap must be less than size')
        return v

class ProcessingConfig(BaseModel):
    supported_extensions: List[str] = [".pdf", ".txt", ".md", ".docx", ".html"]
    max_file_size: str = "50MB"
    encoding: str = "utf-8"
    parallel_workers: int = Field(default=4, ge=1, le=16)

class IndexingConfig(BaseModel):
    batch_size: int = Field(default=100, ge=1, le=1000)
    vector_dimensions: int = 768
    similarity_metric: Literal["cosine", "euclidean", "dot_product"] = "cosine"

class CronConfig(BaseModel):
    enabled: bool = True
    job_file: Path = Field(default=Path("~/.config/roserade/jobs.yaml").expanduser())
    log_retention: str = "30d"

class LoggingConfig(BaseModel):
    level: Literal["debug", "info", "warning", "error"] = "info"
    file: Path = Field(default=Path("~/.config/roserade/roserade.log").expanduser())
    max_size: str = "10MB"
    backup_count: int = 5

class AppConfig(BaseModel):
    database: DatabaseConfig = DatabaseConfig()
    ollama: OllamaConfig = OllamaConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    processing: ProcessingConfig = ProcessingConfig()
    indexing: IndexingConfig = IndexingConfig()
    cron: CronConfig = CronConfig()
    logging: LoggingConfig = LoggingConfig()

    class Config:
        env_prefix = "ROSERADE_"
        case_sensitive = False
```

**Document Models** (`models/document.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"

class DocumentMetadata(BaseModel):
    author: Optional[str] = None
    title: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

class Document(BaseModel):
    id: Optional[int] = None
    path: Path
    filename: str
    file_type: str
    size_bytes: int
    content_hash: str
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_indexed: Optional[datetime] = None
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)

    class Config:
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat()
        }
```

**Chunk Models** (`models/chunk.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ChunkMetadata(BaseModel):
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    paragraph_index: Optional[int] = None
    sentence_count: int = 0
    word_count: int = 0
    language: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

class Chunk(BaseModel):
    id: Optional[int] = None
    document_id: int
    chunk_index: int
    content: str
    content_hash: str
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    embedding: Optional[List[float]] = None
    metadata: ChunkMetadata = Field(default_factory=ChunkMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SearchResult(BaseModel):
    chunk: Chunk
    similarity_score: float
    document_path: str
    context_before: Optional[str] = None
    context_after: Optional[str] = None
```

**Job Models** (`models/job.py`)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from croniter import croniter

class JobStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"

class JobConfig(BaseModel):
    recursive: bool = True
    exclude_patterns: List[str] = Field(default_factory=lambda: ["*.tmp", "*.log", ".DS_Store"])
    force_reindex: bool = False
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    custom_settings: Dict[str, Any] = Field(default_factory=dict)

class IndexingJob(BaseModel):
    id: Optional[int] = None
    name: str
    path: Path
    schedule: str
    status: JobStatus = JobStatus.ACTIVE
    config: JobConfig = Field(default_factory=JobConfig)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    failure_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('schedule')
    def validate_cron_schedule(cls, v):
        try:
            croniter(v)
        except ValueError as e:
            raise ValueError(f"Invalid cron schedule: {e}")
        return v

    class Config:
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat()
        }
```

#### Enhanced Chunker Implementation with Chonkie

```python
from chonkie import TokenChunker, WordChunker, SentenceChunker, MarkdownChunker
from typing import List, Dict, Any, Protocol

class ChunkingStrategy(Protocol):
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        ...

class ChonkieChunker:
    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.chunkers = {
            "token": TokenChunker(chunk_size=config.size, chunk_overlap=config.overlap),
            "word": WordChunker(chunk_size=config.size, chunk_overlap=config.overlap),
            "sentence": SentenceChunker(chunk_size=config.size, chunk_overlap=config.overlap),
            "markdown": MarkdownChunker(chunk_size=config.size, chunk_overlap=config.overlap),
        }

    def chunk_document(self, content: str, file_type: str, metadata: Dict[str, Any]) -> List[Chunk]:
        # Select appropriate chunker based on file type and config
        if file_type == ".md" and self.config.chonky.method == "markdown_split":
            chunker = self.chunkers["markdown"]
        elif self.config.chonky.method == "sentence_split":
            chunker = self.chunkers["sentence"]
        else:
            chunker = self.chunkers["token"]

        chunks = chunker.chunk(content)

        return [
            Chunk(
                document_id=metadata["document_id"],
                chunk_index=i,
                content=chunk.text,
                content_hash=self._hash_content(chunk.text),
                start_offset=chunk.start_index,
                end_offset=chunk.end_index,
                metadata=ChunkMetadata(
                    word_count=len(chunk.text.split()),
                    sentence_count=len([s for s in chunk.text.split('.') if s.strip()]),
                    custom_fields={"chunker_type": type(chunker).__name__}
                )
            )
            for i, chunk in enumerate(chunks)
        ]
```

**DocumentProcessor**

- File format detection and content extraction
- Metadata extraction
- Content preprocessing and normalization

**Chunker**

- Multiple chunking strategies implementation including Chonky integration
- Configurable chunk size and overlap
- Content-aware boundary detection
- Smart chunking based on document structure

**Embedder**

- Ollama client integration
- Batch processing capabilities
- Error handling and retry logic

**VectorDatabase**

- SQLite-vec wrapper
- CRUD operations for documents and embeddings
- Similarity search implementation

**CronManager**

- Job scheduling and management
- Cron expression parsing and validation
- Job execution and monitoring

### 9. Error Handling & Recovery

- **Graceful Failures**: Continue processing other files when individual files fail
- **Resume Capability**: Resume interrupted indexing operations
- **Rollback Support**: Transaction-based operations with rollback on failure
- **Corruption Detection**: Detect and handle database corruption
- **Lock Management**: Prevent concurrent access conflicts

### 10. Performance Considerations

- **Lazy Loading**: Load documents and chunks on demand
- **Connection Pooling**: Efficient database connection management
- **Memory Management**: Process large files in chunks to avoid memory issues
- **Parallel Processing**: Multi-threaded document processing
- **Caching**: Cache frequently accessed embeddings and metadata

### 11. Security & Privacy

- **Local Processing**: All processing happens locally (no cloud dependencies)
- **Access Controls**: File system permission respect
- **Data Sanitization**: Clean extracted content of sensitive patterns
- **Audit Logging**: Track all indexing and search operations

### 12. Installation & Dependencies

#### UV Package Manager Integration

**pyproject.toml**

````toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "roserade"
version = "0.1.0"
description = "A CLI tool for indexing and chunking local documents with Ollama and sqlite-vec"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
license = "MIT"
requires-python = ">=3.9"
keywords = ["cli", "documents", "indexing", "rag", "ollama", "sqlite", "pokemon"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: MacOS",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Text Processing :: Indexing",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

dependencies = [
    "click>=8.0.0",
    "pydantic>=2.5.0",
    "sqlalchemy>=2.0.0",
    "pyyaml>=6.0",
    "requests>=2.28.0",
    "python-magic>=0.4.27",
    "croniter>=1.4.0",
    "rich>=13.0.0",
    "tqdm>=4.64.0",
    "chonkie>=0.1.0",
    "pathspec>=0.11.0",
    "aiofiles>=23.0.0",
    "httpx>=0.25.0",
    "typer>=0.9.0",  # Alternative to click for better type support
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "pre-commit>=3.0.0",
]

test = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.12.0",
    "faker>=20.0.0",
]

docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.4.0",
    "mkdocstrings[python]>=0.24.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/roserade"
Repository = "https://github.com/yourusername/roserade"
Issues = "https://github.com/yourusername/roserade/issues"

[project.scripts]
roserade = "roserade.cli.main:main"

[tool.hatch.build.targets.wheel]
packages = ["src/roserade"]

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/tests",
    "/docs",
    "/README.md",
    "/LICENSE",
]

# Ruff configuration
[tool.ruff]
target-version = "py39"
line-length = 100
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "UP", # pyupgrade
    "C4", # flake8-comprehensions
    "B",  # flake8-bugbear
]

# Black configuration
[tool.black]
line-length = 100
target-version = ['py39']
include = '\.pyi?

### 13. Testing Requirements

- **Unit Tests**: All core components
- **Integration Tests**: End-to-end workflows
- **Performance Tests**: Large file handling
- **CLI Tests**: Command interface validation
- **Database Tests**: Schema and query validation

### 14. Documentation Requirements

- **CLI Help**: Comprehensive built-in help system
- **Configuration Guide**: Detailed configuration options
- **Troubleshooting Guide**: Common issues and solutions
- **API Documentation**: Internal API documentation
- **Example Workflows**: Common use case examples

### 15. Future Enhancements

- **Web Interface**: Optional web UI for browsing and searching
- **Plugin System**: Support for custom document processors
- **Cloud Sync**: Optional cloud backup and sync
- **Advanced Analytics**: Usage statistics and performance metrics
- **Multi-language Support**: Internationalization support

## Implementation Priority

### Phase 1 (MVP)
1. Basic CLI structure with click
2. SQLite database with sqlite-vec setup
3. Simple document processing (PDF, TXT, MD)
4. Basic chunking (fixed-size)
5. Ollama embedding integration
6. Core indexing and search functionality

### Phase 2 (Enhanced Features)
1. Advanced chunking strategies
2. Cron job system implementation
3. Configuration management
4. Additional document formats
5. Performance optimizations

### Phase 3 (Advanced Features)
1. Advanced search capabilities
2. Database management tools
3. Export/import functionality
4. Monitoring and analytics
5. Error recovery mechanisms

Great! Now I'll add a section about command aliases and shell integration since you mentioned being open to that approach:

## Additional CLI Features

### Command Aliases & Shell Integration

While the primary command is `roserade`, users can easily set up shorter aliases in their shell configuration:

**Bash/Zsh aliases** (`~/.bashrc` or `~/.zshrc`):
```bash
# Short aliases for roserade
alias rag='roserade'
alias rose='roserade'
alias r='roserade'

# Function aliases with common options
ragadd() { roserade add "$@" --recursive; }
rags() { roserade search "$@" --limit 20; }
````

**Fish shell aliases** (`~/.config/fish/config.fish`):

```fish
abbr rag roserade
abbr rose roserade
abbr r roserade
```

This approach allows users to choose their preferred command length while keeping the official package name clear and memorable.

# MyPy configuration

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true

# Pytest configuration

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --cov=src/roserade --cov-report=term-missing"
testpaths = ["tests"]
pythonpath = ["src"]
markers = [
"slow: marks tests as slow",
"integration: marks tests as integration tests",
]

# Coverage configuration

[tool.coverage.run]
source = ["src/roserade"]
branch = true

[tool.coverage.report]
exclude_lines = [
"pragma: no cover",
"def __repr__",
"if self.debug:",
"if settings.DEBUG",
"raise AssertionError",
"raise NotImplementedError",
"if 0:",
"if __name__ == .__main__.:",
"class .*\bProtocol\\):",
"@(abc\\.)?abstractmethod",
]

````

#### UV Scripts and Distribution

**UV Development Commands**
```bash
# Install with uv (development)
uv pip install -e ".[dev,test]"

# Run with uvx (for distribution testing)
uvx roserade --help

# Build and publish with uv
uv build
uv publish --token $PYPI_TOKEN

# Development workflow
uv run pytest
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/
````

**Makefile for Development**

```makefile
.PHONY: install dev test lint format build clean

install:
	uv pip install -e .

dev:
	uv pip install -e ".[dev,test,docs]"

test:
	uv run pytest

lint:
	uv run ruff check src/ tests/
	uv run mypy src/

format:
	uv run black src/ tests/
	uv run ruff check --fix src/ tests/

build:
	uv build

clean:
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

publish-test:
	uv publish --repository testpypi

publish:
	uv publish

docs:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build
```

### 13. Testing Requirements

- **Unit Tests**: All core components
- **Integration Tests**: End-to-end workflows
- **Performance Tests**: Large file handling
- **CLI Tests**: Command interface validation
- **Database Tests**: Schema and query validation

### 14. Documentation Requirements

- **CLI Help**: Comprehensive built-in help system
- **Configuration Guide**: Detailed configuration options
- **Troubleshooting Guide**: Common issues and solutions
- **API Documentation**: Internal API documentation
- **Example Workflows**: Common use case examples

### 15. Future Enhancements

- **Web Interface**: Optional web UI for browsing and searching
- **Plugin System**: Support for custom document processors
- **Cloud Sync**: Optional cloud backup and sync
- **Advanced Analytics**: Usage statistics and performance metrics
- **Multi-language Support**: Internationalization support

## Implementation Priority

### Phase 1 (MVP)

1. Basic CLI structure with click
2. SQLite database with sqlite-vec setup
3. Simple document processing (PDF, TXT, MD)
4. Basic chunking (fixed-size)
5. Ollama embedding integration
6. Core indexing and search functionality

### Phase 2 (Enhanced Features)

1. Advanced chunking strategies
2. Cron job system implementation
3. Configuration management
4. Additional document formats
5. Performance optimizations

### Phase 3 (Advanced Features)

1. Advanced search capabilities
2. Database management tools
3. Export/import functionality
4. Monitoring and analytics
5. Error recovery mechanisms

This specification provides a comprehensive foundation for building a robust, scalable document indexing CLI tool that meets your requirements while incorporating best practices from existing RAG systems.
