"""State management for tracking processed files."""
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


STATE_DIR = Path.home() / ".mkgraph"
STATE_FILE = STATE_DIR / "state.json"


@dataclass
class FileState:
    """State for a single processed file."""
    path: str
    hash: str
    last_processed: str


@dataclass
class State:
    """Global state for the knowledge graph."""
    processed_files: dict[str, FileState] = field(default_factory=dict)
    last_run: Optional[str] = None


def ensure_state_dir():
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> State:
    """Load state from file."""
    ensure_state_dir()
    
    if not STATE_FILE.exists():
        return State()
    
    with open(STATE_FILE) as f:
        data = json.load(f)
    
    processed_files = {}
    for path, file_data in data.get("processed_files", {}).items():
        processed_files[path] = FileState(
            path=file_data["path"],
            hash=file_data["hash"],
            last_processed=file_data["last_processed"]
        )
    
    return State(
        processed_files=processed_files,
        last_run=data.get("last_run")
    )


def save_state(state: State):
    """Save state to file."""
    ensure_state_dir()
    
    data = {
        "processed_files": {
            path: {
                "path": fs.path,
                "hash": fs.hash,
                "last_processed": fs.last_processed
            }
            for path, fs in state.processed_files.items()
        },
        "last_run": state.last_run
    }
    
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file contents."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def has_file_changed(file_path: Path, state: State) -> bool:
    """Check if a file has changed since last processing."""
    path_str = str(file_path)
    
    if path_str not in state.processed_files:
        return True  # Never processed
    
    stored = state.processed_files[path_str]
    
    # Quick check: compare mtime
    try:
        current_mtime = file_path.stat().st_mtime
        stored_mtime = stored.hash  # We store hash, not mtime actually
        
        # Compare current hash with stored
        current_hash = compute_file_hash(file_path)
        return current_hash != stored.hash
    except (OSError, FileNotFoundError):
        return True  # File doesn't exist or can't be accessed


def mark_file_processed(file_path: Path, state: State):
    """Mark a file as processed."""
    path_str = str(file_path)
    
    state.processed_files[path_str] = FileState(
        path=path_str,
        hash=compute_file_hash(file_path),
        last_processed=__import__("datetime").datetime.now().isoformat()
    )


def reset_state():
    """Reset all state (clear processed files)."""
    ensure_state_dir()
    
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def get_processed_count(state: State) -> int:
    """Get count of processed files."""
    return len(state.processed_files)


def get_unprocessed_files(file_paths: list[Path], state: State) -> list[Path]:
    """Get list of files that need processing."""
    return [fp for fp in file_paths if has_file_changed(fp, state)]
