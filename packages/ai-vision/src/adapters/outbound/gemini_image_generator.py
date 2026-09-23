"""Adapter: Google Gemini Visual Models for scene image generation (via Gemini API)."""
from __future__ import annotations

import asyncio
import base64
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

from src.application.ports.outbound.image_generator_port import ImageGeneratorPort

DEFAULT_MODELS = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
    "gemini-3-pro-image-preview",
]


def _urlopen_json(req: urllib.request.Request, timeout: int) -> dict:
    """Blocking HTTP call, meant to run inside asyncio.to_thread — never call directly
    from a coroutine, or it blocks the whole event loop (every request the web server
    is handling) for up to `timeout` seconds."""
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class GeminiImageGeneratorAdapter(ImageGeneratorPort):
    """Generates scene images using Gemini multimodal image models.

    Supports reference persona photos (e.g. Cleber headshots) to maintain
    character likeness in the animated sci-fi style.
    """

    def __init__(self, model: str = "gemini-2.5-flash-image"):
        self._api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not self._api_key:
            raise EnvironmentError("GEMINI_API_KEY not set.")
        self._primary_model = model

    async def generate_scene_image(
        self,
        prompt: str,
        reference_images: list[Path],
        output_path: Path,
        width: int = 1080,
        height: int = 1920,
    ) -> Path:
        """Generate a scene image using Gemini Visual model."""
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Skip if already exists and has valid content (>10KB)
        if output_path.exists() and output_path.stat().st_size > 10000:
            return output_path

        aspect_ratio = "vertical 9:16" if height > width else "horizontal 16:9"
        
        # Prepare parts
        parts: list[dict] = []

        # Find a valid reference image if provided
        valid_ref: Path | None = None
        for ref in reference_images:
            p = Path(ref).resolve()
            if p.exists() and p.stat().st_size > 1000:
                valid_ref = p
                break

        if valid_ref:
            try:
                with open(valid_ref, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode("utf-8")
                
                mime = "image/jpeg" if valid_ref.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
                parts.append({
                    "inline_data": {
                        "mime_type": mime,
                        "data": img_b64,
                    }
                })

                instruction = (
                    f"Transform the person shown in the reference photo into an animated sci-fi character. "
                    f"Maintain their facial features, glasses, beard, and likeness recognizably. "
                    f"Scene: {prompt}. "
                    f"Style: Cinematic 2D/3D sci-fi animation, {aspect_ratio} composition, "
                    f"vibrant cosmic colors, gorgeous dynamic lighting, high resolution."
                )
            except Exception as e:
                print(f"   ⚠️ Could not read reference image {valid_ref}: {e}")
                instruction = (
                    f"Animated sci-fi scene: {prompt}. "
                    f"Style: Cinematic animation, {aspect_ratio} composition, vibrant colors, dynamic lighting."
                )
        else:
            instruction = (
                f"Animated sci-fi scene: {prompt}. "
                f"Style: Cinematic animation, {aspect_ratio} composition, vibrant colors, dynamic lighting."
            )

        parts.insert(0, {"text": instruction})

        models_to_try = [self._primary_model] + [m for m in DEFAULT_MODELS if m != self._primary_model]
        last_error = None

        for model_name in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self._api_key}"
                payload = {
                    "contents": [{"parts": parts}],
                    "generationConfig": {
                        "responseModalities": ["IMAGE"]
                    }
                }

                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )

                # Up to 60s timeout for generative image
                res = await asyncio.to_thread(_urlopen_json, req, 60)
                candidates = res.get("candidates", [])
                if not candidates:
                    raise RuntimeError("No candidates returned by model")

                content_parts = candidates[0].get("content", {}).get("parts", [])
                for part in content_parts:
                    if "inlineData" in part:
                        img_bytes = base64.b64decode(part["inlineData"]["data"])
                        with open(output_path, "wb") as f:
                            f.write(img_bytes)
                        return output_path

                raise RuntimeError("Response contained no inline image data")
            except Exception as e:
                last_error = e
                # Try next model if current model fails
                continue

        raise RuntimeError(f"All image models failed to generate scene. Last error: {last_error}")
