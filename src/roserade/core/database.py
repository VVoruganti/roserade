import sqlite3
import sqlite_vec
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple
import json
from contextlib import contextmanager


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        return conn

    @contextmanager
    def get_connection(self):
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        schema_sql = """
        -- Documents table
        CREATE TABLE IF NOT EXISTS documents (
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
        CREATE TABLE IF NOT EXISTS chunks (
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
        CREATE VIRTUAL TABLE IF NOT EXISTS chunk_embeddings USING vec0(
            chunk_id INTEGER PRIMARY KEY,
            embedding FLOAT[768]
        );

        -- Indexing jobs table
        CREATE TABLE IF NOT EXISTS indexing_jobs (
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

        -- Indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_documents_path ON documents(path);
        CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash);
        CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(content_hash);
        """
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)

    def get_document_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM documents WHERE path = ?", (path,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def insert_document(self, document_data: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO documents (path, filename, file_type, size_bytes, content_hash, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                document_data['path'],
                document_data['filename'],
                document_data['file_type'],
                document_data['size_bytes'],
                document_data['content_hash'],
                json.dumps(document_data.get('metadata', {}))
            ))
            
            if cursor.lastrowid == 0:
                # Document already exists, return existing ID
                existing = self.get_document_by_path(document_data['path'])
                return existing['id'] if existing else 0
            
            return cursor.lastrowid

    def update_document_indexed_time(self, document_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE documents SET last_indexed = CURRENT_TIMESTAMP WHERE id = ?",
                (document_id,)
            )

    def insert_chunk(self, chunk_data: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO chunks (document_id, chunk_index, content, content_hash, start_offset, end_offset, chunk_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk_data['document_id'],
                chunk_data['chunk_index'],
                chunk_data['content'],
                chunk_data['content_hash'],
                chunk_data.get('start_offset'),
                chunk_data.get('end_offset'),
                json.dumps(chunk_data.get('metadata', {}))
            ))
            return cursor.lastrowid

    def insert_embedding(self, chunk_id: int, embedding: List[float]) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO chunk_embeddings (chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, json.dumps(embedding))
            )

    def search_similar_chunks(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    c.id as chunk_id,
                    c.content,
                    c.chunk_index,
                    d.path as document_path,
                    d.filename,
                    vec_distance_cosine(embedding, ?) as similarity
                FROM chunk_embeddings e
                JOIN chunks c ON e.chunk_id = c.id
                JOIN documents d ON c.document_id = d.id
                ORDER BY similarity ASC
                LIMIT ?
            """, (json.dumps(query_embedding), limit))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['similarity'] = 1 - result['similarity']  # Convert to similarity score
                results.append(result)
            return results

    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM documents ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]

    def delete_document(self, document_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))

    def get_document_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM documents")
            return cursor.fetchone()['count']

    def get_chunk_count(self, document_id: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM chunks WHERE document_id = ?",
                (document_id,)
            )
            return cursor.fetchone()['count' ]