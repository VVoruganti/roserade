import hashlib
from typing import List, Dict, Any
from pathlib import Path

from chonkie import TokenChunker, SentenceChunker
from ..models.config import ChunkingConfig


class Chunker:
    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.token_chunker = TokenChunker(
            chunk_size=config.size,
            chunk_overlap=config.overlap
        )
        self.sentence_chunker = SentenceChunker(
            chunk_size=config.size,
            chunk_overlap=config.overlap
        )

    def chunk_document(self, content: str, document_id: int, file_type: str) -> List[Dict[str, Any]]:
        """Chunk document content based on configured strategy."""
        if self.config.strategy == "fixed":
            return self._chunk_with_tokenizer(content, document_id)
        elif self.config.strategy == "semantic":
            return self._chunk_with_sentences(content, document_id)
        else:
            raise ValueError(f"Unsupported chunking strategy: {self.config.strategy}")

    def _chunk_with_tokenizer(self, content: str, document_id: int) -> List[Dict[str, Any]]:
        """Use token-based chunking for fixed-size strategy."""
        chunks = self.token_chunker.chunk(content)
        return self._create_chunk_dicts(chunks, document_id)

    def _chunk_with_sentences(self, content: str, document_id: int) -> List[Dict[str, Any]]:
        """Use sentence-based chunking for semantic strategy."""
        chunks = self.sentence_chunker.chunk(content)
        return self._create_chunk_dicts(chunks, document_id)

    def _create_chunk_dicts(self, chunks, document_id: int) -> List[Dict[str, Any]]:
        """Convert Chonkie chunks to our internal format."""
        result = []
        
        for idx, chunk in enumerate(chunks):
            content = chunk.text
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            # Calculate metadata
            word_count = len(content.split())
            sentence_count = len([s for s in content.split('.') if s.strip()])
            
            chunk_data = {
                'document_id': document_id,
                'chunk_index': idx,
                'content': content,
                'content_hash': content_hash,
                'start_offset': chunk.start_index if hasattr(chunk, 'start_index') else None,
                'end_offset': chunk.end_index if hasattr(chunk, 'end_index') else None,
                'metadata': {
                    'word_count': word_count,
                    'sentence_count': sentence_count,
                    'chunker_type': type(chunk).__name__,
                    'strategy': self.config.strategy
                }
            }
            
            result.append(chunk_data)
        
        return result

    def get_chunk_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the chunks."""
        if not chunks:
            return {
                'total_chunks': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
                'total_words': 0
            }
        
        sizes = [len(chunk['content']) for chunk in chunks]
        word_counts = [chunk['metadata']['word_count'] for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_chunk_size': sum(sizes) // len(sizes),
            'min_chunk_size': min(sizes),
            'max_chunk_size': max(sizes),
            'total_words': sum(word_counts),
            'avg_words_per_chunk': sum(word_counts) // len(word_counts)
        }