import pytest
import json
from pathlib import Path

from roserade.core.database import Database


class TestDatabase:
    def test_init_schema(self, test_db: Database):
        """Test database schema initialization."""
        # Should not raise any exceptions
        test_db.init_schema()
        
        # Verify tables exist by running a simple query
        with test_db.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
        assert 'documents' in tables
        assert 'chunks' in tables
        assert 'chunk_embeddings' in tables
        assert 'indexing_jobs' in tables

    def test_insert_and_get_document(self, test_db: Database):
        """Test inserting and retrieving a document."""
        document_data = {
            'path': '/test/document.pdf',
            'filename': 'document.pdf',
            'file_type': '.pdf',
            'size_bytes': 1024,
            'content_hash': 'abc123',
            'metadata': {'title': 'Test Document'}
        }
        
        doc_id = test_db.insert_document(document_data)
        assert doc_id > 0
        
        retrieved = test_db.get_document_by_path('/test/document.pdf')
        assert retrieved is not None
        assert retrieved['filename'] == 'document.pdf'
        assert retrieved['content_hash'] == 'abc123'
        assert json.loads(retrieved['metadata'])['title'] == 'Test Document'

    def test_insert_chunk(self, test_db: Database):
        """Test inserting a chunk."""
        # First insert a document
        doc_id = test_db.insert_document({
            'path': '/test/doc.txt',
            'filename': 'doc.txt',
            'file_type': '.txt',
            'size_bytes': 100,
            'content_hash': 'hash123',
            'metadata': {}
        })
        
        chunk_data = {
            'document_id': doc_id,
            'chunk_index': 0,
            'content': 'This is a test chunk',
            'content_hash': 'chunk_hash',
            'start_offset': 0,
            'end_offset': 20,
            'metadata': {'word_count': 5}
        }
        
        chunk_id = test_db.insert_chunk(chunk_data)
        assert chunk_id > 0

    def test_insert_embedding(self, test_db: Database):
        """Test inserting an embedding."""
        # Insert document and chunk first
        doc_id = test_db.insert_document({
            'path': '/test/doc.txt',
            'filename': 'doc.txt',
            'file_type': '.txt',
            'size_bytes': 100,
            'content_hash': 'hash123',
            'metadata': {}
        })
        
        chunk_id = test_db.insert_chunk({
            'document_id': doc_id,
            'chunk_index': 0,
            'content': 'Test content',
            'content_hash': 'chunk_hash',
            'metadata': {}
        })
        
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 153 + [0.1, 0.2, 0.3]  # 768 dimensions
        test_db.insert_embedding(chunk_id, embedding)
        
        # Should not raise any exceptions
        assert True

    def test_list_documents(self, test_db: Database):
        """Test listing documents."""
        # Insert test documents
        for i in range(3):
            test_db.insert_document({
                'path': f'/test/doc{i}.txt',
                'filename': f'doc{i}.txt',
                'file_type': '.txt',
                'size_bytes': 100 + i,
                'content_hash': f'hash{i}',
                'metadata': {}
            })
        
        documents = test_db.list_documents(limit=10)
        assert len(documents) == 3
        assert documents[0]['filename'] == 'doc2.txt'  # Most recent first

    def test_delete_document(self, test_db: Database):
        """Test deleting a document."""
        doc_id = test_db.insert_document({
            'path': '/test/to_delete.txt',
            'filename': 'to_delete.txt',
            'file_type': '.txt',
            'size_bytes': 100,
            'content_hash': 'hash123',
            'metadata': {}
        })
        
        test_db.delete_document(doc_id)
        
        # Verify document is deleted
        documents = test_db.list_documents(limit=10)
        assert len(documents) == 0

    def test_document_count(self, test_db: Database):
        """Test document count functionality."""
        assert test_db.get_document_count() == 0
        
        test_db.insert_document({
            'path': '/test/doc1.txt',
            'filename': 'doc1.txt',
            'file_type': '.txt',
            'size_bytes': 100,
            'content_hash': 'hash1',
            'metadata': {}
        })
        
        assert test_db.get_document_count() == 1

    def test_duplicate_document_path(self, test_db: Database):
        """Test handling duplicate document paths."""
        document_data = {
            'path': '/test/duplicate.txt',
            'filename': 'duplicate.txt',
            'file_type': '.txt',
            'size_bytes': 100,
            'content_hash': 'hash1',
            'metadata': {}
        }
        
        doc_id1 = test_db.insert_document(document_data)
        
        # Try to insert same path again - should handle gracefully
        document_data['content_hash'] = 'hash2'
        doc_id2 = test_db.insert_document(document_data)
        
        # Should return the same ID due to UNIQUE constraint
        assert doc_id1 == doc_id2