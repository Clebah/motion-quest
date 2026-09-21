"""Use Case: Register and preprocess a character's photos."""
from __future__ import annotations

import uuid
from pathlib import Path

from src.application.ports.outbound.image_processor_port import ImageProcessorPort
from src.domain.entities.character import Character, CharacterPhoto


class RegisterCharacterUseCase:
    """Registers a character and preprocesses their photos.

    Steps:
    1. Validate photo counts (1-5 headshots, 1-5 full-body).
    2. Remove background from each photo.
    3. Crop face from headshots.
    4. Create reference collages.
    5. Cache processed assets in the Character entity (process once, reuse everywhere).
    """

    def __init__(self, image_processor: ImageProcessorPort):
        self._image_processor = image_processor

    async def execute(
        self,
        name: str,
        description: str,
        headshot_paths: list[Path],
        fullbody_paths: list[Path],
        output_dir: Path,
    ) -> Character:
        char_id = f"char_{uuid.uuid4().hex[:8]}"
        photos: list[CharacterPhoto] = []

        # Add headshot photos
        for path in headshot_paths:
            photos.append(CharacterPhoto(path=path, photo_type="headshot"))

        # Add full-body photos
        for path in fullbody_paths:
            photos.append(CharacterPhoto(path=path, photo_type="fullbody"))

        character = Character(
            id=char_id,
            name=name,
            description=description,
            photos=photos,
        )

        # Validate
        errors = character.validate()
        blocking_errors = [e for e in errors if not e.startswith("WARN:")]
        if blocking_errors:
            raise ValueError(f"Character validation failed: {'; '.join(blocking_errors)}")

        # Preprocess: remove backgrounds + crop faces
        char_dir = output_dir / "chars" / char_id
        char_dir.mkdir(parents=True, exist_ok=True)

        for photo in character.headshots:
            bg_removed = await self._image_processor.remove_background(
                photo.path, char_dir / f"{photo.path.stem}_nobg.png"
            )
            cropped = await self._image_processor.crop_face(
                bg_removed, char_dir / f"{photo.path.stem}_face.png"
            )
            photo.processed_path = cropped

        for photo in character.fullbody_photos:
            bg_removed = await self._image_processor.remove_background(
                photo.path, char_dir / f"{photo.path.stem}_nobg.png"
            )
            photo.processed_path = bg_removed

        # Create reference collage from processed headshots
        processed_headshots = [
            p.processed_path for p in character.headshots if p.processed_path
        ]
        if processed_headshots:
            await self._image_processor.create_reference_collage(
                processed_headshots,
                char_dir / "reference_collage.png",
            )

        return character
