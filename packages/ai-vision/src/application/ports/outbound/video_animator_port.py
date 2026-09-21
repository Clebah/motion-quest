"""Outbound port: Image-to-Video animation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class VideoAnimatorPort(ABC):
    """Abstract port for Image-to-Video (I2V) animation.

    PoC adapter: Google Veo 2 (via Gemini API).
    Fallback adapter: fal-client (Kling / Luma Dream Machine).
    """

    @abstractmethod
    async def animate_scene(
        self,
        image_path: Path,
        prompt: str,
        output_path: Path,
        duration_seconds: float = 5.0,
    ) -> Path:
        """Animate a still image into a video clip. Returns path to the clip."""
        ...
