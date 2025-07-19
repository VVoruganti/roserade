import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator

from roserade.core.database import Database
from roserade.models.config import AppConfig


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_db(temp_dir: Path) -> Database:
    """Create a test database."""
    db_path = temp_dir / "test.db"
    db = Database(db_path)
    db.init_schema()
    return db


@pytest.fixture
def test_config() -> AppConfig:
    """Create a test configuration."""
    return AppConfig()


@pytest.fixture
def sample_text() -> str:
    """Sample text for testing."""
    return """
    This is a sample document for testing purposes. It contains multiple sentences
    and paragraphs to test various functionality. The document should be long
    enough to test chunking strategies effectively.
    
    This is the second paragraph with more content. We need to ensure that the
    chunking works correctly with different text lengths and structures.
    
    Final paragraph with some additional text to make sure we have enough
    content for testing the various components of the system.
    """


@pytest.fixture
def sample_pdf_content() -> str:
    """Sample PDF content for testing."""
    return """
    Sample PDF Document
    
    This is a sample PDF document for testing purposes. It contains multiple
    sections and paragraphs to simulate real PDF content.
    
    Section 1: Introduction
    This section introduces the document and provides context for testing.
    
    Section 2: Content
    This section contains the main content of the document with various
    formatting elements and text structures.
    
    Section 3: Conclusion
    This section concludes the document with final thoughts and summaries.
    """


@pytest.fixture
def sample_markdown_content() -> str:
    """Sample markdown content for testing."""
    return """
    # Sample Markdown Document
    
    ## Introduction
    This is a sample markdown document for testing purposes.
    
    ### Features
    - Lists and bullet points
    - Code blocks
    - Headers and sections
    
    ```python
    def hello_world():
        return "Hello, World!"
    ```
    
    ## Conclusion
    This concludes our sample markdown document.
    """


@pytest.fixture
def create_test_file(temp_dir: Path):
    """Factory to create test files."""
    def _create_test_file(filename: str, content: str) -> Path:
        file_path = temp_dir / filename
        file_path.write_text(content)
        return file_path
    return _create_test_file