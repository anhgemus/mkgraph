"""Unit tests for state management."""
import json
from pathlib import Path
from unittest.mock import patch
import pytest

from mkgraph.state import (
    State,
    FileState,
    load_state,
    save_state,
    compute_file_hash,
    has_file_changed,
    mark_file_processed,
    reset_state,
    get_unprocessed_files,
    STATE_FILE,
)


@pytest.fixture
def tmp_state_file(tmp_path, monkeypatch):
    """Create a temporary state file."""
    state_file = tmp_path / "state.json"
    monkeypatch.setattr("mkgraph.state.STATE_FILE", state_file)
    return state_file


class TestFileState:
    """Tests for FileState dataclass."""

    def test_file_state_creation(self):
        """Should create FileState with correct attributes."""
        fs = FileState(path="/test.md", hash="abc123", last_processed="2026-01-01")
        
        assert fs.path == "/test.md"
        assert fs.hash == "abc123"
        assert fs.last_processed == "2026-01-01"


class TestState:
    """Tests for State dataclass."""

    def test_state_creation(self):
        """Should create State with default values."""
        state = State()
        
        assert state.processed_files == {}
        assert state.last_run is None

    def test_state_with_data(self):
        """Should create State with provided data."""
        state = State(
            processed_files={"test.md": FileState("test.md", "hash", "2026-01-01")},
            last_run="2026-01-02"
        )
        
        assert len(state.processed_files) == 1
        assert state.last_run == "2026-01-02"


class TestLoadSaveState:
    """Tests for load and save state functions."""

    def test_load_empty_state(self, tmp_state_file):
        """Should return empty state when no file exists."""
        state = load_state()
        
        assert state.processed_files == {}
        assert state.last_run is None

    def test_save_and_load_state(self, tmp_state_file):
        """Should save and load state correctly."""
        state = State(
            processed_files={"test.md": FileState("test.md", "abc123", "2026-01-01")},
            last_run="2026-01-02"
        )
        
        save_state(state)
        
        loaded = load_state()
        
        assert len(loaded.processed_files) == 1
        assert "test.md" in loaded.processed_files
        assert loaded.last_run == "2026-01-02"


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_hash_consistency(self, tmp_path):
        """Same content should produce same hash."""
        file = tmp_path / "test.txt"
        file.write_text("hello world")
        
        hash1 = compute_file_hash(file)
        hash2 = compute_file_hash(file)
        
        assert hash1 == hash2

    def test_different_content_different_hash(self, tmp_path):
        """Different content should produce different hashes."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("hello world")
        file2.write_text("hello world!")
        
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        
        assert hash1 != hash2


class TestHasFileChanged:
    """Tests for has_file_changed function."""

    def test_new_file(self, tmp_path):
        """New file should be marked as changed."""
        file = tmp_path / "new.md"
        file.write_text("content")
        
        state = State()
        
        assert has_file_changed(file, state) is True

    def test_unchanged_file(self, tmp_path):
        """File with same hash should not be marked as changed."""
        file = tmp_path / "test.md"
        file.write_text("content")
        
        state = State()
        state.processed_files[str(file)] = FileState(
            path=str(file),
            hash=compute_file_hash(file),
            last_processed="2026-01-01"
        )
        
        assert has_file_changed(file, state) is False

    def test_changed_file(self, tmp_path):
        """File with different hash should be marked as changed."""
        file = tmp_path / "test.md"
        file.write_text("content")
        
        state = State()
        state.processed_files[str(file)] = FileState(
            path=str(file),
            hash="different_hash",
            last_processed="2026-01-01"
        )
        
        assert has_file_changed(file, state) is True


class TestMarkFileProcessed:
    """Tests for mark_file_processed function."""

    def test_mark_new_file(self, tmp_path):
        """Should add new file to state."""
        file = tmp_path / "test.md"
        file.write_text("content")
        
        state = State()
        mark_file_processed(file, state)
        
        assert str(file) in state.processed_files
        assert state.processed_files[str(file)].hash == compute_file_hash(file)

    def test_update_existing_file(self, tmp_path):
        """Should update hash for existing file."""
        file = tmp_path / "test.md"
        file.write_text("content")
        
        state = State()
        state.processed_files[str(file)] = FileState(
            path=str(file),
            hash="old_hash",
            last_processed="2026-01-01"
        )
        
        mark_file_processed(file, state)
        
        assert state.processed_files[str(file)].hash == compute_file_hash(file)


class TestGetUnprocessedFiles:
    """Tests for get_unprocessed_files function."""

    def test_all_unprocessed(self, tmp_path):
        """Should return all files when none processed."""
        files = [tmp_path / "a.md", tmp_path / "b.md"]
        for f in files:
            f.write_text("content")
        
        state = State()
        
        result = get_unprocessed_files(files, state)
        
        assert len(result) == 2

    def test_some_processed(self, tmp_path):
        """Should filter out processed files."""
        file1 = tmp_path / "a.md"
        file2 = tmp_path / "b.md"
        file1.write_text("content")
        file2.write_text("content")
        
        state = State()
        state.processed_files[str(file1)] = FileState(
            path=str(file1),
            hash=compute_file_hash(file1),
            last_processed="2026-01-01"
        )
        
        result = get_unprocessed_files([file1, file2], state)
        
        assert len(result) == 1
        assert result[0] == file2


class TestResetState:
    """Tests for reset_state function."""

    def test_reset_clears_file(self, tmp_state_file):
        """Should delete state file."""
        # Create state file
        state = State()
        save_state(state)
        assert tmp_state_file.exists()
        
        # Reset
        reset_state()
        
        # File should be gone
        assert not tmp_state_file.exists()
