"""Adapter: Google Imagen 3 for scene image generation (via Gemini API)."""
from __future__ import annotations

import base64
import os
from pathlib import Path

from google import genai
from google.genai import types

from src.application.ports.outbound.image_generator_port import ImageGeneratorPort


class GeminiImageGeneratorAdapter(ImageGeneratorPort):
    """Generates scene images using Google Imagen 3 via the Gemini API.

    Uses the same GEMINI_API_KEY as the Mimo project.
    """

    def __init__(self, model: str = "imagen-3.0-generate-002"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not set.")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate_scene_image(
        self,
        prompt: str,
        reference_images: list[Path],
        output_path: Path,
        width: int = 1080,
        height: int = 1920,
    ) -> Path:
        """Generate a scene image using Imagen 3.

        Note: Imagen 3 doesn't natively support IP-Adapter/reference images
        in the same way as FLUX.1. For the PoC, we embed the character
        description in the prompt. For production, swap this adapter for
        FalImageGeneratorAdapter which supports IP-Adapter.
        """
        # Enhance prompt with aspect ratio hint
        aspect = "vertical 9:16" if height > width else "horizontal 16:9"
        enhanced_prompt = (
            f"{prompt}. "
            f"High quality animated illustration style, {aspect} format, "
            f"vibrant colors, cinematic lighting."
        )

        response = self._client.models.generate_images(
            model=self._model,
            prompt=enhanced_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="9:16" if height > width else "16:9",
            ),
        )

        if not response.generated_images:
            raise RuntimeError(f"Imagen 3 returned no images for scene")

        image_data = response.generated_images[0].image.image_bytes
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_data)

        return output_path
