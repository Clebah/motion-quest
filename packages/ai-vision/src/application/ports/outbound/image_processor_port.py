"""Outbound port: Image preprocessing (background removal, crop, collages)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ImageProcessorPort(ABC):
    """Abstract port for image preprocessing operations.

    Responsibilities:
    - Remove background from photos (rembg).
    - Crop faces and create reference collages (OpenCV + Pillow).
    - Cache processed images for reuse across scenes.
    """

    @abstractmethod
    async def remove_background(self, input_path: Path, output_path: Path) -> Path:
        """Remove background from a photo. Returns path to processed image."""
        ...

    @abstractmethod
    async def crop_face(self, input_path: Path, output_path: Path) -> Path:
        """Detect and crop the face region. Returns path to cropped image."""
        ...

    @abstractmethod
    async def create_reference_collage(
        self, image_paths: list[Path], output_path: Path
    ) -> Path:
        """Create a collage of reference images for the generative model."""
        ...
