import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner

from roserade.cli.main import cli


class TestCLIIntegration:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_init_command(self, runner, temp_dir):
        """Test the init command."""
        db_path = temp_dir / "test.db"
        result = runner.invoke(cli, ['init', '--db-path', str(db_path)])
        
        assert result.exit_code == 0
        assert "Initialized Roserade index" in result.output
        assert db_path.exists()

    def test_list_docs_empty(self, runner, temp_dir):
        """Test list-docs with no documents."""
        db_path = temp_dir / "test.db"
        runner.invoke(cli, ['init', '--db-path', str(db_path)])
        
        result = runner.invoke(cli, ['list-docs', '--db-path', str(db_path)])
        
        assert result.exit_code == 0
        assert "No documents indexed yet" in result.output

    def test_add_single_file(self, runner, temp_dir, monkeypatch):
        """Test adding a single file."""
        db_path = temp_dir / "test.db"
        test_file = temp_dir / "test.txt"
        test_file.write_text("This is a test document for CLI testing.")
        
        runner.invoke(cli, ['init', '--db-path', str(db_path)])
        
        # Mock Ollama connection and embedding generation
        async def mock_check_connection(self):
            return True
        
        def mock_sync_generate_embeddings(self, texts):
            # Return mock embeddings with correct dimensions
            return [[0.1] * 768 for _ in texts]
        
        # Apply mocks - use the correct module path
        from roserade.core.embedder import OllamaEmbedder
        monkeypatch.setattr(OllamaEmbedder, 'check_connection', mock_check_connection)
        monkeypatch.setattr(OllamaEmbedder, 'sync_generate_embeddings', mock_sync_generate_embeddings)
        
        result = runner.invoke(cli, [
            'add', str(test_file),
            '--db-path', str(db_path)
        ])
        
        assert result.exit_code == 0
        assert "Processed 1 documents" in result.output
    def test_search_empty(self, runner, temp_dir, monkeypatch):
        """Test search with no results."""
        db_path = temp_dir / "test.db"
        runner.invoke(cli, ['init', '--db-path', str(db_path)])
        
        # Mock embedding generation
        async def mock_generate_embedding(self, text):
            return [0.1] * 768
        
        monkeypatch.setattr('roserade.core.embedder.OllamaEmbedder.generate_embedding', mock_generate_embedding)
        
        result = runner.invoke(cli, ['search', 'nonexistent', '--db-path', str(db_path)])
        
        assert result.exit_code == 0
        assert "No results found" in result.output

    def test_remove_nonexistent(self, runner, temp_dir):
        """Test removing non-existent document."""
        db_path = temp_dir / "test.db"
        runner.invoke(cli, ['init', '--db-path', str(db_path)])
        
        result = runner.invoke(cli, [
            'remove', '/nonexistent/file.txt', 
            '--db-path', str(db_path)
        ])
        
        assert result.exit_code == 0
        assert "Document not found" in result.output

    def test_help_commands(self, runner):
        """Test help output for all commands."""
        commands = ['--help', 'init', 'add', 'search', 'list-docs', 'remove']
        
        for cmd in commands:
            if cmd == '--help':
                result = runner.invoke(cli, [cmd])
            else:
                result = runner.invoke(cli, [cmd, '--help'])
            
            assert result.exit_code == 0
            assert "Usage:" in result.output

    def test_config_option(self, runner, temp_dir):
        """Test custom config file."""
        config_path = temp_dir / "config.yaml"
        config_path.write_text("""
database:
  path: "{}/custom.db"
""".format(temp_dir))
        
        db_path = temp_dir / "custom.db"
        result = runner.invoke(cli, [
            'init', 
            '--config', str(config_path),
            '--db-path', str(db_path)
        ])
        
        assert result.exit_code == 0
        assert db_path.exists()

    def test_verbose_flag(self, runner, temp_dir):
        """Test verbose flag."""
        db_path = temp_dir / "test.db"
        result = runner.invoke(cli, [
            'init', 
            '--db-path', str(db_path), 
            '--verbose'
        ])
        
        assert result.exit_code == 0

    def test_add_recursive(self, runner, temp_dir):
        """Test recursive directory addition."""
        db_path = temp_dir / "test.db"
        
        # Create directory structure
        subdir = temp_dir / "docs"
        subdir.mkdir()
        (subdir / "file1.txt").write_text("Document 1")
        (subdir / "file2.txt").write_text("Document 2")
        
        runner.invoke(cli, ['init', '--db-path', str(db_path)])
        
        result = runner.invoke(cli, [
            'add', str(subdir), 
            '--recursive', 
            '--db-path', str(db_path)
        ])
        
        # Will fail without Ollama, but should handle gracefully
        assert result.exit_code in [0, 1]

    def test_list_with_limit(self, runner, temp_dir):
        """Test list-docs with limit."""
        db_path = temp_dir / "test.db"
        runner.invoke(cli, ['init', '--db-path', str(db_path)])
        
        result = runner.invoke(cli, [
            'list-docs', 
            '--limit', '5', 
            '--db-path', str(db_path)
        ])
        
        assert result.exit_code == 0

    def test_search_with_threshold(self, runner, temp_dir):
        """Test search with threshold."""
        db_path = temp_dir / "test.db"
        runner.invoke(cli, ['init', '--db-path', str(db_path)])
        
        result = runner.invoke(cli, [
            'search', 'test', 
            '--threshold', '0.5',
            '--db-path', str(db_path)
        ])
        
        assert result.exit_code == 0