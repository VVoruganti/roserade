"""Sample test files for testing purposes."""

SAMPLE_PDF_CONTENT = """
# Sample PDF Document

This is a sample PDF document for testing purposes. It contains multiple sections
and paragraphs to simulate real PDF content.

## Section 1: Introduction
This section introduces the document and provides context for testing. We need
enough content to test various functionality including chunking and processing.

## Section 2: Content Analysis
This section contains the main content of the document with various formatting
elements and text structures. The content should be substantial enough to create
multiple chunks when processed.

### Subsection 2.1: Features
- Lists and bullet points
- Headers and sections
- Multiple paragraphs
- Various text formats

### Subsection 2.2: Technical Details
```python
def process_document():
    """Process a document for indexing."""
    return "Document processed successfully"
```

## Section 3: Conclusion
This section concludes the document with final thoughts and summaries. The
document should provide enough content for comprehensive testing of all components.
"""

SAMPLE_TXT_CONTENT = """
This is a sample text document for testing purposes.
It contains multiple lines and paragraphs.

The document should have enough content to test:
- Document processing
- Text extraction
- Content analysis
- Various text formats

This is the second paragraph with more content.
We need to ensure that the processing works correctly
with different text lengths and structures.

Final paragraph with some additional text to make sure
we have enough content for testing the various components
of the system.
"""

SAMPLE_MD_CONTENT = """# Sample Markdown Document

## Overview
This is a sample markdown document for testing purposes. It contains various
markdown elements including headers, lists, code blocks, and links.

## Features
- **Bold text** and *italic text*
- [Links](https://example.com)
- Lists and bullet points
- Code blocks and inline `code`

### Code Example
```python
def hello_world():
    """A simple hello world function."""
    return "Hello, World!"

class TestClass:
    def __init__(self):
        self.value = 42
```

### Lists
1. Ordered list item 1
2. Ordered list item 2
3. Ordered list item 3

- Unordered list item
- Another item
- Final item

## Conclusion
This concludes our sample markdown document.
"""

SAMPLE_JSON_CONTENT = """
{
    "title": "Sample Document",
    "content": "This is sample content",
    "metadata": {
        "author": "Test Author",
        "date": "2024-01-01"
    }
}
"""

SAMPLE_CSV_CONTENT = """
name,age,city
John,25,New York
Jane,30,Los Angeles
Bob,35,Chicago
"""

def create_test_pdf(temp_dir: str) -> str:
    """Create a test PDF file."""
    from pathlib import Path
    
    pdf_path = Path(temp_dir) / "sample.pdf"
    
    # For testing purposes, we'll create a text file that simulates PDF content
    # In real tests, you might want to use a proper PDF library
    pdf_path.write_text(SAMPLE_PDF_CONTENT)
    return str(pdf_path)

def create_test_txt(temp_dir: str) -> str:
    """Create a test TXT file."""
    from pathlib import Path
    
    txt_path = Path(temp_dir) / "sample.txt"
    txt_path.write_text(SAMPLE_TXT_CONTENT)
    return str(txt_path)

def create_test_md(temp_dir: str) -> str:
    """Create a test MD file."""
    from pathlib import Path
    
    md_path = Path(temp_dir) / "sample.md"
    md_path.write_text(SAMPLE_MD_CONTENT)
    return str(md_path)

def create_test_files(temp_dir: str) -> dict:
    """Create all test files in a directory."""
    return {
        'pdf': create_test_pdf(temp_dir),
        'txt': create_test_txt(temp_dir),
        'md': create_test_md(temp_dir),
    }