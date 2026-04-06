"""File utilities for rd-agent-mcp."""

import json
import yaml
from pathlib import Path
from typing import Any, Optional


def read_json(path: str | Path) -> dict:
    """Read JSON file."""
    with open(path) as f:
        return json.load(f)


def write_json(data: dict, path: str | Path, indent: int = 2):
    """Write JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)


def read_yaml(path: str | Path) -> dict:
    """Read YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def write_yaml(data: dict, path: str | Path):
    """Write YAML file."""
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def ensure_dir(path: str | Path) -> Path:
    """Ensure directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_files(directory: str | Path, pattern: str = "*") -> list[Path]:
    """Find files matching pattern in directory."""
    path = Path(directory)
    return list(path.glob(pattern))


def safe_read(path: str | Path, default: str = "") -> str:
    """Safely read file, returning default if error."""
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return default


def atomic_write(path: str | Path, content: str):
    """Atomically write to file."""
    import tempfile
    import shutil

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first
    fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            f.write(content)
        # Move temp file to final location
        shutil.move(temp_path, path)
    except Exception:
        # Clean up temp file on error
        Path(temp_path).unlink(missing_ok=True)
        raise
