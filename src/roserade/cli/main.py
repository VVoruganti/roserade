import click
import asyncio
import logging
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ..core.database import Database
from ..core.document_processor import DocumentProcessor
from ..core.chunker import Chunker
from ..core.embedder import OllamaEmbedder
from ..models.config import AppConfig
from ..utils.config import load_config, get_default_config_path, create_default_config

console = Console()

@click.group()
@click.option('--db-path', type=click.Path(path_type=Path), help='Database file path')
@click.option('--config', type=click.Path(path_type=Path), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, db_path, config, verbose):
    """Roserade: Document indexing CLI tool with Ollama and sqlite-vec."""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Load configuration
    config_path = config or get_default_config_path()
    app_config = load_config(config_path)
    
    # Override database path if provided
    if db_path:
        app_config.database.path = db_path
    
    ctx.obj['config'] = app_config
    ctx.obj['db'] = Database(app_config.database.path)

@cli.command()
@click.option('--db-path', type=click.Path(path_type=Path), help='Database file path')
@click.option('--config', type=click.Path(path_type=Path), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def init(ctx, db_path, config, verbose):
    """Initialize a new Roserade index."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Load configuration
    config_path = config or get_default_config_path()
    app_config = load_config(config_path)
    
    # Override database path if provided
    if db_path:
        app_config.database.path = db_path
    
    db = Database(app_config.database.path)
    
    try:
        db.init_schema()
        create_default_config()
        console.print(f"✅ Initialized Roserade index at {app_config.database.path}")
        console.print(f"✅ Created default config at {get_default_config_path()}")
    except Exception as e:
        console.print(f"❌ Failed to initialize: {e}")
        raise click.Abort()

@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option('--recursive', '-r', is_flag=True, help='Process directories recursively')
@click.option('--force', is_flag=True, help='Re-index existing documents')
@click.option('--chunk-size', type=int, help='Override default chunk size')
@click.option('--chunk-overlap', type=int, help='Override default chunk overlap')
@click.option('--db-path', type=click.Path(path_type=Path), help='Database file path')
@click.option('--config', type=click.Path(path_type=Path), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def add(ctx, path, recursive, force, chunk_size, chunk_overlap, db_path, config, verbose):
    """Add documents to the index."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Load configuration
    config_path = config or get_default_config_path()
    app_config = load_config(config_path)
    
    # Override database path if provided
    if db_path:
        app_config.database.path = db_path
    
    db = Database(app_config.database.path)
    
    # Ensure database is initialized
    try:
        db.init_schema()
    except Exception:
        pass  # Already initialized
    
    # Override chunking config if provided
    if chunk_size or chunk_overlap:
        if chunk_size:
            app_config.chunking.size = chunk_size
        if chunk_overlap:
            app_config.chunking.overlap = chunk_overlap
    
    # Initialize components
    processor = DocumentProcessor()
    chunker = Chunker(app_config.chunking)
    embedder = OllamaEmbedder(app_config.ollama)
    
    # Check Ollama connection
    async def check_ollama():
        return await embedder.check_connection()
    
    try:
        ollama_available = asyncio.run(check_ollama())
        if not ollama_available:
            console.print("❌ Ollama is not running. Please start Ollama first.")
            raise click.Abort()
    except Exception as e:
        console.print(f"❌ Failed to connect to Ollama: {e}")
        raise click.Abort()
    
    # Collect files to process
    files_to_process = []
    if path.is_file():
        files_to_process = [path]
    else:
        pattern = "**/*" if recursive else "*"
        for ext in config.processing.supported_extensions:
            files_to_process.extend(path.glob(f"{pattern}{ext}"))
    
    if not files_to_process:
        console.print("No files found to process.")
        return
    
    console.print(f"Found {len(files_to_process)} files to process...")
    
    # Process files
    processed_count = 0
    skipped_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task("Processing documents...", total=len(files_to_process))
        
        for file_path in files_to_process:
            try:
                # Check if already indexed
                existing = db.get_document_by_path(str(file_path.absolute()))
                if existing and not force:
                    skipped_count += 1
                    progress.advance(task)
                    continue
                
                # Extract text and metadata
                file_info = processor.get_file_info(file_path)
                text_data = processor.extract_text(file_path)
                
                # Insert document
                document_data = {
                    'path': str(file_path.absolute()),
                    'filename': file_info['filename'],
                    'file_type': file_info['file_type'],
                    'size_bytes': file_info['size_bytes'],
                    'content_hash': text_data['content_hash'],
                    'metadata': text_data['metadata']
                }
                
                if existing:
                    doc_id = existing['id']
                    # Update existing document
                    db.update_document_indexed_time(doc_id)
                else:
                    doc_id = db.insert_document(document_data)
                
                # Chunk the document
                chunks = chunker.chunk_document(text_data['content'], doc_id, file_info['file_type'])
                
                # Generate embeddings
                chunk_texts = [chunk['content'] for chunk in chunks]
                embeddings = asyncio.run(embedder.sync_generate_embeddings(chunk_texts))
                
                # Store chunks and embeddings
                for chunk, embedding in zip(chunks, embeddings):
                    chunk_id = db.insert_chunk(chunk)
                    db.insert_embedding(chunk_id, embedding)
                
                processed_count += 1
                progress.advance(task)
                
            except Exception as e:
                console.print(f"\n❌ Error processing {file_path}: {e}")
                progress.advance(task)
    
    console.print(f"✅ Processed {processed_count} documents, skipped {skipped_count} existing documents")

@cli.command()
@click.argument('query')
@click.option('--limit', '-n', default=10, help='Number of results to show')
@click.option('--threshold', type=float, help='Similarity threshold (0.0-1.0)')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--db-path', type=click.Path(path_type=Path), help='Database file path')
@click.option('--config', type=click.Path(path_type=Path), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def search(ctx, query, limit, threshold, output_format, db_path, config, verbose):
    """Search indexed documents."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Load configuration
    config_path = config or get_default_config_path()
    app_config = load_config(config_path)
    
    # Override database path if provided
    if db_path:
        app_config.database.path = db_path
    
    db = Database(app_config.database.path)
    embedder = OllamaEmbedder(app_config.ollama)
    
    # Generate query embedding
    async def get_query_embedding():
        return await embedder.generate_embedding(query)
    
    try:
        query_embedding = asyncio.run(get_query_embedding())
    except Exception as e:
        console.print(f"❌ Failed to generate query embedding: {e}")
        raise click.Abort()
    
    # Search for similar chunks
    results = db.search_similar_chunks(query_embedding, limit)
    
    if threshold:
        results = [r for r in results if r['similarity'] >= threshold]
    
    if not results:
        console.print("No results found.")
        return
    
    if output_format == 'json':
        import json
        click.echo(json.dumps(results, indent=2))
    else:
        table = Table(title=f"Search Results for: {query}")
        table.add_column("Score", style="cyan")
        table.add_column("File", style="green")
        table.add_column("Content", style="white", max_width=80)
        
        for result in results:
            table.add_row(
                f"{result['similarity']:.3f}",
                result['filename'],
                result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
            )
        
        console.print(table)

@cli.command()
@click.option('--limit', default=20, help='Number of documents to show')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--db-path', type=click.Path(path_type=Path), help='Database file path')
@click.option('--config', type=click.Path(path_type=Path), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def list_docs(ctx, limit, output_format, db_path, config, verbose):
    """List indexed documents."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Load configuration
    config_path = config or get_default_config_path()
    app_config = load_config(config_path)
    
    # Override database path if provided
    if db_path:
        app_config.database.path = db_path
    
    db = Database(app_config.database.path)
    
    documents = db.list_documents(limit)
    
    if not documents:
        console.print("No documents indexed yet.")
        return
    
    if output_format == 'json':
        import json
        click.echo(json.dumps(documents, indent=2, default=str))
    else:
        table = Table(title="Indexed Documents")
        table.add_column("ID", style="cyan")
        table.add_column("Filename", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Size", style="blue")
        table.add_column("Indexed", style="magenta")
        
        for doc in documents:
            table.add_row(
                str(doc['id']),
                doc['filename'],
                doc['file_type'],
                f"{doc['size_bytes']:,} bytes",
                doc['last_indexed'] or "Never"
            )
        
        console.print(table)

@cli.command()
@click.argument('path', type=click.Path(path_type=Path))
@click.option('--pattern', help='Remove documents matching pattern (glob)')
@click.option('--db-path', type=click.Path(path_type=Path), help='Database file path')
@click.option('--config', type=click.Path(path_type=Path), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def remove(ctx, path, pattern, db_path, config, verbose):
    """Remove documents from the index."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Load configuration
    config_path = config or get_default_config_path()
    app_config = load_config(config_path)
    
    # Override database path if provided
    if db_path:
        app_config.database.path = db_path
    
    db = Database(app_config.database.path)
    
    if pattern:
        import fnmatch
        documents = db.list_documents(limit=1000)
        to_remove = []
        
        for doc in documents:
            if fnmatch.fnmatch(doc['path'], pattern):
                to_remove.append(doc['id'])
        
        if not to_remove:
            console.print("No documents match the pattern.")
            return
        
        for doc_id in to_remove:
            db.delete_document(doc_id)
        
        console.print(f"Removed {len(to_remove)} documents matching pattern: {pattern}")
    else:
        # Remove specific document
        doc = db.get_document_by_path(str(path.absolute()))
        if doc:
            db.delete_document(doc['id'])
            console.print(f"Removed document: {path}")
        else:
            console.print(f"Document not found: {path}")


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    console.print("Roserade v0.1.0")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()