"""In-memory session store for characters registered through the web UI (SPEC-003 §8.6)."""
from __future__ import annotations

import uuid
from pathlib import Path

from src.application.ports.outbound.image_processor_port import ImageProcessorPort
from src.application.use_cases.register_character import RegisterCharacterUseCase
from src.domain.entities.character import Character

from src.adapters.inbound.web.schemas import CharacterSummary

SESSION_ROOT = Path("output/web/session")
UPLOADS_DIR = SESSION_ROOT / "uploads"

VALID_PHOTO_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


class SessionCharacterStore:
    """Single-process, in-memory registry of characters for the current web session.

    Not thread-safe by design: this spec runs as a single uvicorn process/event loop
    (SPEC-003 §8.7), which is enough for a local single-user tool.
    """

    def __init__(self, image_processor: ImageProcessorPort):
        self._image_processor = image_processor
        self._characters: dict[str, Character] = {}

    async def register(
        self,
        name: str,
        description: str,
        headshot_files: list[tuple[str, bytes]],
        fullbody_files: list[tuple[str, bytes]],
    ) -> CharacterSummary:
        """Saves uploaded bytes to disk, then registers via RegisterCharacterUseCase.

        Raises ValueError (from Character.validate()) when photo counts are outside
        1-5 per type — the same rule the CLI enforces (SPEC-003 RF-01.2 / RF-01.4).
        """
        tmp_id = uuid.uuid4().hex[:8]
        upload_dir = UPLOADS_DIR / tmp_id
        headshot_paths = _save_uploads(upload_dir / "headshots", headshot_files)
        fullbody_paths = _save_uploads(upload_dir / "fullbody", fullbody_files)

        use_case = RegisterCharacterUseCase(self._image_processor)
        character = await use_case.execute(
            name=name,
            description=description,
            headshot_paths=headshot_paths,
            fullbody_paths=fullbody_paths,
            output_dir=SESSION_ROOT,
        )
        self._characters[character.id] = character
        return _to_summary(character)

    def list(self) -> list[CharacterSummary]:
        return [_to_summary(c) for c in self._characters.values()]

    def remove(self, character_id: str) -> bool:
        return self._characters.pop(character_id, None) is not None

    def get_many(self, character_ids: list[str]) -> list[Character]:
        return [self._characters[cid] for cid in character_ids if cid in self._characters]


def _save_uploads(target_dir: Path, files: list[tuple[str, bytes]]) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for filename, content in files:
        ext = Path(filename).suffix.lower()
        if ext not in VALID_PHOTO_EXTS:
            raise ValueError(f"Tipo de foto não suportado: {filename!r}")
        dest = target_dir / Path(filename).name
        dest.write_bytes(content)
        saved.append(dest)
    return saved


def _to_summary(character: Character) -> CharacterSummary:
    headshot = character.headshots[0] if character.headshots else None
    fullbody = character.fullbody_photos[0] if character.fullbody_photos else None
    return CharacterSummary(
        id=character.id,
        name=character.name,
        description=character.description,
        headshotPreviewUrl=_to_media_url(headshot.processed_path if headshot else None),
        fullbodyPreviewUrl=_to_media_url(fullbody.processed_path if fullbody else None),
    )


def _to_media_url(path) -> str:
    if not path:
        return ""
    try:
        rel = Path(path).resolve().relative_to(SESSION_ROOT.resolve())
    except ValueError:
        return ""
    return f"/media/{rel.as_posix()}"
