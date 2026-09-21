"""Character entity — represents a person in the video cast."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CharacterPhoto:
    """A single reference photo for a character."""
    path: Path
    photo_type: str  # "headshot" | "fullbody"
    processed_path: Path | None = None


@dataclass
class Character:
    """A person who will appear in the generated video.

    Business rules:
    - 1 to 5 headshot photos required.
    - 1 to 5 full-body photos required.
    - Processed assets are cached once and reused across all scenes.
    """
    id: str
    name: str
    description: str
    photos: list[CharacterPhoto] = field(default_factory=list)
    face_embedding: bytes | None = None  # cached face vector for consistency

    @property
    def headshots(self) -> list[CharacterPhoto]:
        return [p for p in self.photos if p.photo_type == "headshot"]

    @property
    def fullbody_photos(self) -> list[CharacterPhoto]:
        return [p for p in self.photos if p.photo_type == "fullbody"]

    def validate(self) -> list[str]:
        """Returns a list of validation errors (empty = valid)."""
        errors: list[str] = []
        hs = len(self.headshots)
        fb = len(self.fullbody_photos)
        if not (1 <= hs <= 5):
            errors.append(f"Character '{self.name}': needs 1-5 headshots, got {hs}")
        if not (1 <= fb <= 5):
            errors.append(f"Character '{self.name}': needs 1-5 full-body photos, got {fb}")
        if not self.name.strip():
            errors.append("Character name cannot be empty")
        return errors
