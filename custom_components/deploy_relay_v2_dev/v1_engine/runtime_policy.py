"""Policy for runtime-generated artifacts that must never be deployed."""

from __future__ import annotations

from pathlib import PurePosixPath

_IGNORED_DIRECTORY_NAMES = frozenset({"__pycache__"})
_IGNORED_FILE_SUFFIXES = frozenset({".pyc", ".pyo"})


def is_runtime_generated_path(value: str) -> bool:
    """Return whether a relative path is a runtime-generated Python artifact."""
    path = PurePosixPath(value)
    parts = {part.casefold() for part in path.parts}

    if parts & _IGNORED_DIRECTORY_NAMES:
        return True

    return path.suffix.casefold() in _IGNORED_FILE_SUFFIXES
