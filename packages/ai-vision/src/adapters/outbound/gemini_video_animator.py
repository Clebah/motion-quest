"""Adapter: Google Veo 2 for Image-to-Video animation (via Gemini API)."""
from __future__ import annotations

import os
import time
from pathlib import Path

from google import genai
from google.genai import types

from src.application.ports.outbound.video_animator_port import VideoAnimatorPort


class GeminiVideoAnimatorAdapter(VideoAnimatorPort):
    """Animates still images into video clips using Google Veo 2.

    Uses the same GEMINI_API_KEY as the Mimo project.
    """

    def __init__(self, model: str = "veo-2.0-generate-001"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not set.")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def animate_scene(
        self,
        image_path: Path,
        prompt: str,
        output_path: Path,
        duration_seconds: float = 5.0,
    ) -> Path:
        """Animate a still image into a video clip using Veo 2.

        Veo 2 generates 5-8 second clips from an image + prompt.
        """
        # Read the source image
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        image_part = types.RawReferenceImage(
            reference_image=types.Image(image_bytes=image_bytes),
            reference_id=0,
            reference_type="STYLE",
        )

        enhanced_prompt = (
            f"Animate this scene: {prompt}. "
            f"Smooth cinematic motion, subtle character animation, "
            f"maintain visual consistency with the source image."
        )

        # Veo 2 is an async operation — poll until complete
        operation = self._client.models.generate_videos(
            model=self._model,
            prompt=enhanced_prompt,
            image=image_part,
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                number_of_videos=1,
            ),
        )

        # Poll for completion (Veo 2 can take 1-3 minutes)
        while not operation.done:
            time.sleep(10)
            operation = self._client.operations.get(operation)

        if not operation.response or not operation.response.generated_videos:
            raise RuntimeError("Veo 2 failed to generate video clip")

        video = operation.response.generated_videos[0].video
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(video.video_bytes)

        return output_path
