"""Outbound port: File/asset storage."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StoragePort(ABC):
    """Abstract port for storing and retrieving assets.

    PoC adapter: Local filesystem (output/ folder).
    Prod adapter: AWS S3 / Google Cloud Storage.
    """

    @abstractmethod
    async def save(self, local_path: Path, destination_key: str) -> str:
        """Save a local file to storage. Returns the storage URI/path."""
        ...

    @abstractmethod
    async def load(self, source_key: str, local_path: Path) -> Path:
        """Load a file from storage to local path."""
        ...

    @abstractmethod
    async def save_json(self, data: dict, destination_key: str) -> str:
        """Serialize and save a dict as JSON. Returns the storage URI/path."""
        ...
