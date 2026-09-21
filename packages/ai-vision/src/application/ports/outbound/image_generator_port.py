"""Outbound port: Image generation via generative AI APIs."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ImageGeneratorPort(ABC):
    """Abstract port for AI image generation.

    PoC adapter: Google Imagen 3 (via Gemini API, same key as Mimo).
    Fallback adapter: fal-client (FLUX.1/SDXL + IP-Adapter).
    """

    @abstractmethod
    async def generate_scene_image(
        self,
        prompt: str,
        reference_images: list[Path],
        output_path: Path,
        width: int = 1080,
        height: int = 1920,
    ) -> Path:
        """Generate a scene image from a visual prompt + character references."""
        ...
