import pytest
from pathlib import Path
import tempfile

from roserade.core.document_processor import DocumentProcessor


class TestDocumentProcessor:
    def test_get_file_type(self):
        """Test file type detection."""
        processor = DocumentProcessor()
        
        assert processor.get_file_type(Path("test.pdf")) == ".pdf"
        assert processor.get_file_type(Path("test.txt")) == ".txt"
        assert processor.get_file_type(Path("test.md")) == ".md"
        assert processor.get_file_type(Path("test.PDF")) == ".pdf"

    def test_calculate_hash(self):
        """Test hash calculation."""
        processor = DocumentProcessor()
        
        hash1 = processor.calculate_hash("test content")
        hash2 = processor.calculate_hash("test content")
        hash3 = processor.calculate_hash("different content")
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64  # SHA-256 produces 64 character hex

    def test_extract_text_txt(self):
        """Test text extraction from TXT files."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test text file.\nIt has multiple lines.")
            temp_path = Path(f.name)
        
        try:
            result = processor.extract_text(temp_path)
            
            assert "This is a test text file" in result['content']
            assert "multiple lines" in result['content']
            assert result['metadata']['file_type'] == 'text'
            assert result['metadata']['line_count'] == 2
            assert len(result['content_hash']) == 64
        finally:
            temp_path.unlink()

    def test_extract_text_md(self):
        """Test text extraction from MD files."""
        processor = DocumentProcessor()
        
        content = "# Test Markdown\n\nThis is a **test** markdown file."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            result = processor.extract_text(temp_path)
            
            assert "# Test Markdown" in result['content']
            assert "**test**" in result['content']
            assert result['metadata']['file_type'] == 'markdown'
        finally:
            temp_path.unlink()

    def test_get_file_info(self):
        """Test file information extraction."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            info = processor.get_file_info(temp_path)
            
            assert info['filename'] == temp_path.name
            assert info['file_type'] == '.txt'
            assert info['size_bytes'] > 0
            assert str(temp_path.absolute()) in info['path']
            assert 'created_at' in info
            assert 'modified_at' in info
        finally:
            temp_path.unlink()

    def test_unsupported_file_type(self):
        """Test handling of unsupported file types."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.unsupported', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                processor.extract_text(temp_path)
        finally:
            temp_path.unlink()

    def test_nonexistent_file(self):
        """Test handling of non-existent files."""
        processor = DocumentProcessor()
        
        with pytest.raises(FileNotFoundError):
            processor.extract_text(Path("/nonexistent/file.txt"))

    def test_empty_file(self):
        """Test handling of empty files."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)
        
        try:
            result = processor.extract_text(temp_path)
            assert result['content'] == ""
            assert result['metadata']['word_count'] == 0
        finally:
            temp_path.unlink()

    def test_unicode_content(self):
        """Test handling of unicode content."""
        processor = DocumentProcessor()
        
        content = "Hello 世界 🌍 123"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', encoding='utf-8', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            result = processor.extract_text(temp_path)
            assert "世界" in result['content']
            assert "🌍" in result['content']
        finally:
            temp_path.unlink()