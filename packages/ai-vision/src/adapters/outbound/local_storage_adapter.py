"""Adapter: Local filesystem storage for PoC."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.application.ports.outbound.storage_port import StoragePort


class LocalStorageAdapter(StoragePort):
    """Stores assets directly on local disk for local development/PoC.
    
    Can be replaced with S3StorageAdapter in production without changing
    domain or use cases.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, local_path: Path, destination_key: str) -> str:
        dest = self.base_dir / destination_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, dest)
        return str(dest)

    async def load(self, source_key: str, local_path: Path) -> Path:
        src = self.base_dir / source_key
        if not src.exists():
            raise FileNotFoundError(f"Asset not found: {src}")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, local_path)
        return local_path

    async def save_json(self, data: dict, destination_key: str) -> str:
        dest = self.base_dir / destination_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return str(dest)
