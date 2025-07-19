import pytest
from roserade.core.chunker import Chunker
from roserade.models.config import ChunkingConfig


class TestChunker:
    def test_init(self):
        """Test chunker initialization."""
        config = ChunkingConfig(strategy="fixed", size=100, overlap=20)
        chunker = Chunker(config)
        
        assert chunker.config.strategy == "fixed"
        assert chunker.config.size == 100
        assert chunker.config.overlap == 20

    def test_fixed_size_chunking(self):
        """Test fixed-size chunking."""
        config = ChunkingConfig(strategy="fixed", size=50, overlap=10)
        chunker = Chunker(config)
        
        text = "This is a test document with enough content to create multiple chunks. " * 10
        chunks = chunker.chunk_document(text, document_id=1, file_type=".txt")
        
        assert len(chunks) > 1
        assert all(chunk['document_id'] == 1 for chunk in chunks)
        assert all(chunk['content_hash'] for chunk in chunks)
        assert all('word_count' in chunk['metadata'] for chunk in chunks)

    def test_semantic_chunking(self):
        """Test semantic chunking."""
        config = ChunkingConfig(strategy="semantic", size=100, overlap=20)
        chunker = Chunker(config)
        
        text = "This is a test document. It has multiple sentences. Each sentence should be considered. " * 5
        chunks = chunker.chunk_document(text, document_id=1, file_type=".txt")
        
        assert len(chunks) >= 1
        assert all(chunk['document_id'] == 1 for chunk in chunks)

    def test_chunk_metadata(self):
        """Test chunk metadata generation."""
        config = ChunkingConfig(strategy="fixed", size=30, overlap=5)
        chunker = Chunker(config)
        
        text = "This is a simple test document for metadata testing."
        chunks = chunker.chunk_document(text, document_id=1, file_type=".txt")
        
        for chunk in chunks:
            assert 'word_count' in chunk['metadata']
            assert 'sentence_count' in chunk['metadata']
            assert 'chunker_type' in chunk['metadata']
            assert chunk['metadata']['strategy'] == "fixed"
            assert isinstance(chunk['metadata']['word_count'], int)
            assert isinstance(chunk['metadata']['sentence_count'], int)

    def test_content_hashing(self):
        """Test content hashing for chunks."""
        config = ChunkingConfig(strategy="fixed", size=50, overlap=10)
        chunker = Chunker(config)
        
        text = "This is test content for hashing verification."
        chunks = chunker.chunk_document(text, document_id=1, file_type=".txt")
        
        for chunk in chunks:
            assert len(chunk['content_hash']) == 64  # SHA-256
            assert chunk['content_hash'] != chunk['content']  # Should be hashed

    def test_chunk_stats(self):
        """Test chunk statistics."""
        config = ChunkingConfig(strategy="fixed", size=30, overlap=5)
        chunker = Chunker(config)
        
        text = "Short text"
        chunks = chunker.chunk_document(text, document_id=1, file_type=".txt")
        stats = chunker.get_chunk_stats(chunks)
        
        assert stats['total_chunks'] == len(chunks)
        assert 'avg_chunk_size' in stats
        assert 'min_chunk_size' in stats
        assert 'max_chunk_size' in stats
        assert 'total_words' in stats

    def test_empty_content(self):
        """Test handling of empty content."""
        config = ChunkingConfig(strategy="fixed", size=50, overlap=10)
        chunker = Chunker(config)
        
        chunks = chunker.chunk_document("", document_id=1, file_type=".txt")
        
        assert len(chunks) == 0
        stats = chunker.get_chunk_stats(chunks)
        assert stats['total_chunks'] == 0

    def test_very_short_content(self):
        """Test handling of very short content."""
        config = ChunkingConfig(strategy="fixed", size=100, overlap=10)
        chunker = Chunker(config)
        
        text = "Short"
        chunks = chunker.chunk_document(text, document_id=1, file_type=".txt")
        
        assert len(chunks) == 1
        assert chunks[0]['content'] == "Short"

    def test_invalid_strategy(self):
        """Test handling of invalid chunking strategy."""
        config = ChunkingConfig(strategy="invalid", size=50, overlap=10)
        chunker = Chunker(config)
        
        with pytest.raises(ValueError, match="Unsupported chunking strategy"):
            chunker.chunk_document("test", document_id=1, file_type=".txt")

    def test_chunk_indexing(self):
        """Test that chunk indices are correctly assigned."""
        config = ChunkingConfig(strategy="fixed", size=20, overlap=5)
        chunker = Chunker(config)
        
        text = "This is a longer document that will create multiple chunks for testing purposes."
        chunks = chunker.chunk_document(text, document_id=1, file_type=".txt")
        
        indices = [chunk['chunk_index'] for chunk in chunks]
        assert indices == list(range(len(chunks)))

    def test_offset_tracking(self):
        """Test that start/end offsets are tracked when available."""
        config = ChunkingConfig(strategy="fixed", size=30, overlap=5)
        chunker = Chunker(config)
        
        text = "This is a test document with offset tracking."
        chunks = chunker.chunk_document(text, document_id=1, file_type=".txt")
        
        for chunk in chunks:
            assert 'start_offset' in chunk
            assert 'end_offset' in chunk
            if chunk['start_offset'] is not None:
                assert isinstance(chunk['start_offset'], int)
                assert isinstance(chunk['end_offset'], int)