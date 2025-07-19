import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
import pdfplumber


class DocumentProcessor:
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

    @staticmethod
    def get_file_type(file_path: Path) -> str:
        """Determine file type based on extension and MIME type."""
        extension = file_path.suffix.lower()

        if extension in DocumentProcessor.SUPPORTED_EXTENSIONS:
            return extension

        # Fallback to MIME type detection
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if mime_type == "application/pdf":
                return ".pdf"
            elif mime_type.startswith("text/"):
                return ".txt"

        return extension

    @staticmethod
    def calculate_hash(content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def extract_text(file_path: Path) -> Dict[str, Any]:
        """Extract text and metadata from a file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_type = DocumentProcessor.get_file_type(file_path)

        if file_type == ".pdf":
            return DocumentProcessor._extract_pdf(file_path)
        elif file_type in {".txt", ".md"}:
            return DocumentProcessor._extract_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _extract_pdf(file_path: Path) -> Dict[str, Any]:
        """Extract text from PDF using pdfplumber."""
        text_parts = []
        metadata = {}

        try:
            with pdfplumber.open(file_path) as pdf:
                metadata = {
                    "page_count": len(pdf.pages),
                    "title": pdf.metadata.get("Title", ""),
                    "author": pdf.metadata.get("Author", ""),
                    "subject": pdf.metadata.get("Subject", ""),
                    "creator": pdf.metadata.get("Creator", ""),
                    "producer": pdf.metadata.get("Producer", ""),
                    "creation_date": pdf.metadata.get("CreationDate", ""),
                    "modification_date": pdf.metadata.get("ModDate", ""),
                }

                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {e}")

        content = "\n".join(text_parts)
        return {
            "content": content,
            "metadata": metadata,
            "content_hash": DocumentProcessor.calculate_hash(content),
        }

    @staticmethod
    def _extract_text_file(file_path: Path) -> Dict[str, Any]:
        """Extract text from text/markdown files."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read text file: {e}")

        metadata = {
            "file_type": "markdown" if file_path.suffix.lower() == ".md" else "text",
            "line_count": len(content.splitlines()),
            "word_count": len(content.split()),
            "character_count": len(content),
        }

        return {
            "content": content,
            "metadata": metadata,
            "content_hash": DocumentProcessor.calculate_hash(content),
        }

    @staticmethod
    def get_file_info(file_path: Path) -> Dict[str, Any]:
        """Get file information including size and type."""
        stat = file_path.stat()
        return {
            "path": str(file_path.absolute()),
            "filename": file_path.name,
            "file_type": DocumentProcessor.get_file_type(file_path),
            "size_bytes": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
        }

