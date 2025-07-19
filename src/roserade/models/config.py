from pydantic import BaseModel, Field
from typing import List, Optional
from pathlib import Path


class DatabaseConfig(BaseModel):
    path: Path = Field(default=Path("~/.config/roserade/index.db").expanduser())


class OllamaConfig(BaseModel):
    host: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    timeout: int = 30


class ChunkingConfig(BaseModel):
    strategy: str = "semantic"  # fixed, semantic
    size: int = 512
    overlap: int = 50
    min_chunk_size: int = 100
    max_chunk_size: int = 2048


class ProcessingConfig(BaseModel):
    supported_extensions: List[str] = [".pdf", ".txt", ".md"]
    max_file_size: str = "50MB"
    encoding: str = "utf-8"


class AppConfig(BaseModel):
    database: DatabaseConfig = DatabaseConfig()
    ollama: OllamaConfig = OllamaConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    processing: ProcessingConfig = ProcessingConfig()

    class Config:
        env_prefix = "ROSERADE_"
        case_sensitive = False