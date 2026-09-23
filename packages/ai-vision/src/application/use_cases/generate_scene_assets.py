"""Use Case: Generate scene assets (images + animated clips) with retry/fallback."""
from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Callable

from src.application.ports.outbound.image_generator_port import ImageGeneratorPort
from src.application.ports.outbound.video_animator_port import VideoAnimatorPort
from src.domain.entities.character import Character
from src.domain.entities.storyboard import SceneStatus, Storyboard


class GenerateSceneAssetsUseCase:
    """Generates images and animated clips for each scene.

    Features:
    - Retry with exponential backoff (3 attempts per scene).
    - Progress reporting via callback.
    - Partial processing: saves progress; retomable on failure.
    """

    MAX_RETRIES = 3
    BASE_DELAY_SECONDS = 2.0

    def __init__(
        self,
        image_generator: ImageGeneratorPort,
        video_animator: VideoAnimatorPort,
    ):
        self._image_gen = image_generator
        self._video_anim = video_animator

    async def execute(
        self,
        storyboard: Storyboard,
        characters: list[Character],
        output_dir: Path,
        on_progress: Callable[[int, int, str], None] | None = None,
    ) -> Storyboard:
        scenes_dir = output_dir / "scenes"
        clips_dir = output_dir / "clips"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        clips_dir.mkdir(parents=True, exist_ok=True)

        char_map = {c.id: c for c in characters}
        total = len(storyboard.scenes)

        for i, scene in enumerate(storyboard.scenes):
            # Skip already completed scenes (for resumability)
            if scene.status == SceneStatus.COMPLETED:
                continue

            scene_label = f"Scene {scene.scene_number}/{total}"

            if on_progress:
                on_progress(i + 1, total, f"🎨 Generating image: {scene_label}")

            # Gather reference images from characters in this scene
            reference_images: list[Path] = []
            target_chars = [char_map[cid] for cid in scene.character_ids if cid in char_map]
            if not target_chars:
                # Fallback: check if prompt mentions any character by name
                for c in characters:
                    if c.name.lower() in scene.visual_prompt.lower() or c.name.lower() in scene.narration_text.lower():
                        target_chars.append(c)

            for char in target_chars:
                for photo in char.headshots:
                    p = photo.processed_path or photo.path
                    if p and Path(p).exists():
                        reference_images.append(Path(p))

            # Step 1: Generate scene image (with retry)
            image_path = scenes_dir / f"scene_{scene.scene_number:02d}.png"
            success = await self._retry_with_backoff(
                self._generate_image,
                scene=scene,
                reference_images=reference_images,
                output_path=image_path,
                storyboard=storyboard,
            )
            if not success:
                scene.status = SceneStatus.FAILED
                continue

            scene.image_path = image_path
            scene.status = SceneStatus.IMAGE_GENERATED

            # Step 2: Animate the image into a clip (with retry)
            if on_progress:
                on_progress(i + 1, total, f"🎬 Animating: {scene_label}")

            clip_path = clips_dir / f"scene_{scene.scene_number:02d}.mp4"
            success = await self._retry_with_backoff(
                self._animate_clip,
                scene=scene,
                image_path=image_path,
                output_path=clip_path,
            )
            if not success:
                scene.status = SceneStatus.FAILED
                continue

            scene.clip_path = clip_path
            scene.status = SceneStatus.COMPLETED

            if on_progress:
                on_progress(i + 1, total, f"✅ Completed: {scene_label}")

        return storyboard

    async def _generate_image(
        self, *, scene, reference_images, output_path, storyboard
    ) -> None:
        await self._image_gen.generate_scene_image(
            prompt=scene.visual_prompt,
            reference_images=reference_images,
            output_path=output_path,
            width=storyboard.resolution_width,
            height=storyboard.resolution_height,
        )

    async def _animate_clip(self, *, scene, image_path, output_path) -> None:
        await self._video_anim.animate_scene(
            image_path=image_path,
            prompt=scene.visual_prompt,
            output_path=output_path,
            duration_seconds=scene.duration_seconds,
        )

    async def _retry_with_backoff(
        self, func, *, max_retries: int | None = None, **kwargs
    ) -> bool:
        """Execute func with exponential backoff. Returns True on success."""
        retries = max_retries or self.MAX_RETRIES
        for attempt in range(retries):
            try:
                await func(**kwargs)
                return True
            except Exception as exc:
                delay = self.BASE_DELAY_SECONDS * (2 ** attempt)
                print(
                    f"   ⚠️ Attempt {attempt + 1}/{retries} failed: {exc}. "
                    f"Retrying in {delay}s..."
                )
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
        return False
