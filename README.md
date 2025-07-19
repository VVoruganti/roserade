# Roserade

A local RAG (Retrieval-Augmented Generation) system that creates embeddings from your notes and documents, enabling semantic search and retrieval using Ollama and SQLite.

## Features

- **Local-first**: All processing happens on your machine using Ollama
- **Multiple formats**: Supports PDF, TXT, and Markdown files
- **Semantic search**: Find relevant content using natural language queries
- **Efficient storage**: Uses SQLite with vector extensions for fast similarity search
- **Flexible chunking**: Configurable chunking strategies (fixed-size or semantic)
- **CLI interface**: Simple command-line tools for all operations

## Quick Start

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd roserade

# Create virtual environment and install
uv venv
uv pip install -e "."

# Ensure Ollama is running with the embedding model
ollama pull nomic-embed-text
```

### Basic Usage

```bash
# Initialize the database
roserade init

# Add documents (single file or directory)
roserade add README.md
roserade add -r ./docs/          # Recursive

# Search your documents
roserade search "python async functions"
roserade search "machine learning" --limit 5

# List indexed documents
roserade list-docs

# Remove a document
roserade remove document.pdf
```

## Configuration

Roserade uses a YAML configuration file at `~/.config/roserade/config.yaml`:

```yaml
database:
  path: "~/.config/roserade/index.db"

ollama:
  host: "http://localhost:11434"
  embedding_model: "nomic-embed-text"

chunking:
  strategy: "semantic" # or "fixed"
  size: 512
  overlap: 50

processing:
  supported_extensions: [".pdf", ".txt", ".md"]
  max_file_size: "50MB"
```

## Commands

### `roserade init`

Initialize a new Roserade index database.

**Options:**

- `--db-path`: Custom database location
- `--config`: Custom config file

### `roserade add <path>`

Add documents to the index.

**Options:**

- `--recursive, -r`: Process directories recursively
- `--force`: Re-index existing documents
- `--chunk-size`: Override default chunk size
- `--chunk-overlap`: Override default overlap
- `--db-path`: Custom database location

### `roserade search <query>`

Search indexed documents using semantic similarity.

**Options:**

- `--limit, -n`: Number of results (default: 10)
- `--threshold`: Similarity threshold (0.0-1.0)
- `--format`: Output format (table/json)

### `roserade list-docs`

List all indexed documents.

**Options:**

- `--limit`: Maximum documents to show
- `--format`: Output format (table/json)

### `roserade remove <path>`

Remove documents from the index.

**Options:**

- `--pattern`: Remove by pattern (glob)
- `--force`: Skip confirmation

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv pip install -e ".[dev,test]"

# Run tests
uv run pytest

# Format code
uv run black src/ tests/
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Project Structure

```
src/roserade/
├── cli/           # Command-line interface
├── core/          # Core functionality
├── models/        # Data models
└── utils/         # Utilities
```

## How It Works

1. **Document Processing**: Extracts text from PDF, TXT, and MD files
2. **Chunking**: Breaks documents into manageable chunks using semantic or fixed-size strategies
3. **Embedding**: Generates vector embeddings using Ollama's nomic-embed-text model
4. **Storage**: Stores documents, chunks, and embeddings in SQLite with vector extensions
5. **Search**: Uses cosine similarity to find relevant chunks based on query embeddings

## Bash Setup

Can add the following line to you `.zshrc` so you can run the project from
anywhere. I use the `rag` alias, but pick whatever works for you

```zsh
rag() {
    uv run --project ~/<project-directory>/roserade roserade "$@"
}
```

## To Do

- [ ] I'm feeling lucky style open the top search in neovim or less
- [ ] cron job for re-syncing embeddings whenever they are out of re-sync
- [ ] Experiment with making it more fine grained (sections of markdown files)
- [ ] Add the text content to the database (and/or line number of section)

## Inspiration

https://github.com/ggozad/haiku.rag
