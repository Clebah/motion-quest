"""Mock adapters for testing without external API calls or third-party dependencies."""
from __future__ import annotations

import shutil
from pathlib import Path

from src.application.ports.outbound.image_processor_port import ImageProcessorPort
from src.application.ports.outbound.image_generator_port import ImageGeneratorPort
from src.application.ports.outbound.video_animator_port import VideoAnimatorPort
from src.application.ports.outbound.llm_provider_port import (
    LlmProviderPort,
    StoryboardSchema,
)


class MockImageProcessorAdapter(ImageProcessorPort):
    """Mock image processor that handles photos without rembg/cv2."""

    async def remove_background(self, input_path: Path, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_path, output_path)
        return output_path

    async def crop_face(self, input_path: Path, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_path, output_path)
        return output_path

    async def create_reference_collage(
        self, image_paths: list[Path], output_path: Path
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if image_paths:
            shutil.copy2(image_paths[0], output_path)
        else:
            with open(output_path, "wb") as f:
                f.write(b"MOCK_COLLAGE")
        return output_path


class MockLlmAdapter(LlmProviderPort):
    """Mock LLM adapter for offline testing using only pure Python."""

    async def generate_storyboard(
        self,
        characters_description: str,
        user_prompt: str,
        story_template: str | None = None,
        min_scenes: int = 18,
        max_scenes: int = 24,
    ) -> StoryboardSchema:
        scenes = []
        for i in range(1, 19):
            scenes.append(
                StoryboardSchema.SceneSchema(
                    scene_number=i,
                    duration_seconds=5.0,
                    character_ids=["char_demo_1"],
                    visual_prompt=f"Cena {i}: Aventura animada com visual vibrante. {user_prompt[:30]}",
                    narration_text=f"Momento {i} da jornada inesquecível.",
                )
            )
        return StoryboardSchema(
            title=f"Aventura: {user_prompt[:25]}",
            scenes=scenes,
        )


class MockImageGeneratorAdapter(ImageGeneratorPort):
    """Generates placeholder PNG images without requiring Pillow for mock tests."""

    _SAMPLE_PNG_BYTES = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00"
        b"\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    async def generate_scene_image(
        self,
        prompt: str,
        reference_images: list[Path],
        output_path: Path,
        width: int = 1080,
        height: int = 1920,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(self._SAMPLE_PNG_BYTES)
        return output_path


class MockVideoAnimatorAdapter(VideoAnimatorPort):
    """Creates a mock video file for testing without cloud video APIs."""

    async def animate_scene(
        self,
        image_path: Path,
        prompt: str,
        output_path: Path,
        duration_seconds: float = 5.0,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(b"MOCK_MP4_VIDEO_STREAM_" + prompt.encode("utf-8")[:32])
        return output_path
