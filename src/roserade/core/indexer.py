from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
from rich.progress import Progress

from .database import Database
from .document_processor import DocumentProcessor
from .chunker import Chunker
from .embedder import OllamaEmbedder
from ..models.config import AppConfig


class Indexer:
    def __init__(self, config: AppConfig, db: Database):
        self.config = config
        self.db = db
        self.processor = DocumentProcessor()
        self.chunker = Chunker(config.chunking)
        self.embedder = OllamaEmbedder(config.ollama)

    async def index_file(self, file_path: Path, force: bool = False) -> Dict[str, Any]:
        """Index a single file."""
        try:
            # Check if already indexed
            existing = self.db.get_document_by_path(str(file_path.absolute()))
            if existing and not force:
                return {"status": "skipped", "reason": "already_indexed", "path": str(file_path)}

            # Extract text and metadata
            file_info = self.processor.get_file_info(file_path)
            text_data = self.processor.extract_text(file_path)

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
                self.db.update_document_indexed_time(doc_id)
            else:
                doc_id = self.db.insert_document(document_data)

            # Chunk the document
            chunks = self.chunker.chunk_document(text_data['content'], doc_id, file_info['file_type'])

            # Generate embeddings
            chunk_texts = [chunk['content'] for chunk in chunks]
            embeddings = await self.embedder.generate_embeddings_batch(chunk_texts)

            # Store chunks and embeddings
            for chunk, embedding in zip(chunks, embeddings):
                chunk_id = self.db.insert_chunk(chunk)
                self.db.insert_embedding(chunk_id, embedding)

            return {"status": "success", "path": str(file_path), "chunks": len(chunks)}

        except Exception as e:
            return {"status": "error", "path": str(file_path), "error": str(e)}

    async def index_directory(
        self, 
        directory: Path, 
        recursive: bool = False, 
        force: bool = False,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Index all files in a directory."""
        
        # Collect files to process
        files_to_process = []
        pattern = "**/*" if recursive else "*"
        
        for ext in self.config.processing.supported_extensions:
            files_to_process.extend(directory.glob(f"{pattern}{ext}"))
        
        # Filter excluded patterns
        if exclude_patterns:
            import fnmatch
            filtered_files = []
            for file_path in files_to_process:
                if not any(fnmatch.fnmatch(str(file_path), pattern) for pattern in exclude_patterns):
                    filtered_files.append(file_path)
            files_to_process = filtered_files

        if not files_to_process:
            return []

        # Check Ollama connection
        if not await self.embedder.check_connection():
            raise RuntimeError("Cannot connect to Ollama. Please ensure it's running.")

        # Process files
        results = []
        
        for file_path in files_to_process:
            result = await self.index_file(file_path, force)
            results.append(result)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        return {
            "total_documents": self.db.get_document_count(),
            "total_chunks": sum(
                self.db.get_chunk_count(doc_id) 
                for doc_id in [doc['id'] for doc in self.db.list_documents(limit=1000)]
            )
        }