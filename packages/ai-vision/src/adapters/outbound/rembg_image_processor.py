"""Adapter: Image preprocessing using rembg, OpenCV and Pillow."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

from src.application.ports.outbound.image_processor_port import ImageProcessorPort


class RembgImageProcessorAdapter(ImageProcessorPort):
    """Concrete adapter for image preprocessing.

    Uses:
    - rembg (BiRefNet/ONNX) for background removal.
    - OpenCV + MediaPipe for face detection and cropping.
    - Pillow for collage creation.
    """

    async def remove_background(self, input_path: Path, output_path: Path) -> Path:
        """Remove the background from a photo using rembg."""
        with open(input_path, "rb") as f:
            input_data = f.read()

        result = remove(input_data)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(result)

        return output_path

    async def crop_face(self, input_path: Path, output_path: Path) -> Path:
        """Detect and crop the face region using OpenCV's Haar Cascade.

        For the PoC, Haar Cascade is sufficient. In production, this adapter
        would be swapped for InsightFace with higher accuracy.
        """
        img = cv2.imread(str(input_path))
        if img is None:
            raise FileNotFoundError(f"Could not read image: {input_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Use built-in Haar Cascade (shipped with OpenCV)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )

        if len(faces) == 0:
            # Fallback: if no face detected, return the full image
            img_pil = Image.open(input_path)
            img_pil.save(output_path)
            return output_path

        # Take the largest detected face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

        # Add padding around the face (30%)
        pad = int(max(w, h) * 0.3)
        img_h, img_w = img.shape[:2]
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img_w, x + w + pad)
        y2 = min(img_h, y + h + pad)

        cropped = img[y1:y2, x1:x2]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), cropped)

        return output_path

    async def create_reference_collage(
        self, image_paths: list[Path], output_path: Path
    ) -> Path:
        """Create a grid collage from multiple reference images.

        The collage is used as context for the generative model to maintain
        character consistency across scenes.
        """
        if not image_paths:
            raise ValueError("No images provided for collage")

        images: list[Image.Image] = []
        for p in image_paths:
            img = Image.open(p).convert("RGBA")
            images.append(img)

        # Normalize all images to the same size
        target_size = (256, 256)
        resized = [img.resize(target_size, Image.Resampling.LANCZOS) for img in images]

        # Create a grid (max 3 columns)
        cols = min(3, len(resized))
        rows = (len(resized) + cols - 1) // cols
        canvas_w = cols * target_size[0]
        canvas_h = rows * target_size[1]

        canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 0))
        for idx, img in enumerate(resized):
            col = idx % cols
            row = idx // cols
            canvas.paste(img, (col * target_size[0], row * target_size[1]))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path, "PNG")

        return output_path
