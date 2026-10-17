"""Integrity helpers for Deploy Relay."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    """Return lowercase SHA-256 hex digest."""
    return sha256(data).hexdigest()


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Hash a file without loading it all into memory."""
    digest = sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
