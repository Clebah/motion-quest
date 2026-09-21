"""Storyboard entity — represents the full video structure with scenes."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class SceneStatus(str, Enum):
    PENDING = "pending"
    IMAGE_GENERATED = "image_generated"
    CLIP_GENERATED = "clip_generated"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Scene:
    """A single scene in the storyboard (3-7 seconds of video)."""
    scene_number: int
    duration_seconds: float  # 3.0 to 7.0, default 5.0
    character_ids: list[str]
    visual_prompt: str
    narration_text: str
    image_path: Path | None = None
    clip_path: Path | None = None
    status: SceneStatus = SceneStatus.PENDING
    retry_count: int = 0

    @property
    def is_retryable(self) -> bool:
        return self.status == SceneStatus.FAILED and self.retry_count < 3


@dataclass
class CostEstimate:
    """Estimated cost breakdown for generating all scenes."""
    currency: str = "USD"
    image_generation: float = 0.0
    video_animation: float = 0.0

    @property
    def total(self) -> float:
        return round(self.image_generation + self.video_animation, 2)


@dataclass
class AudioTrack:
    """Background music configuration for the video."""
    music_path: Path | None = None
    volume: float = 0.3


@dataclass
class Storyboard:
    """The full video structure: cast, scenes, audio, and render config.

    Business rules (SPEC-002 v3):
    - Soft constraint: 18-24 scenes (warning).
    - Hard constraint: 12-30 scenes (blocking).
    - Scene duration: 3-7s (default 5s).
    - Total duration: 60s-150s.
    """
    project_id: str
    title: str
    scenes: list[Scene] = field(default_factory=list)
    resolution_width: int = 1080
    resolution_height: int = 1920  # 9:16 vertical default
    fps: int = 30
    audio: AudioTrack = field(default_factory=AudioTrack)
    cost_estimate: CostEstimate | None = None

    @property
    def total_duration_seconds(self) -> float:
        return sum(s.duration_seconds for s in self.scenes)

    @property
    def completed_scenes(self) -> list[Scene]:
        return [s for s in self.scenes if s.status == SceneStatus.COMPLETED]

    @property
    def failed_scenes(self) -> list[Scene]:
        return [s for s in self.scenes if s.status == SceneStatus.FAILED]

    @property
    def progress_pct(self) -> float:
        if not self.scenes:
            return 0.0
        return len(self.completed_scenes) / len(self.scenes) * 100

    def validate(self) -> list[str]:
        """Returns validation errors. Warnings are prefixed with 'WARN:'."""
        errors: list[str] = []
        n = len(self.scenes)

        # Hard constraints
        if n < 12:
            errors.append(f"Too few scenes: {n} (minimum 12)")
        if n > 30:
            errors.append(f"Too many scenes: {n} (maximum 30)")

        total = self.total_duration_seconds
        if total < 60:
            errors.append(f"Total duration too short: {total}s (minimum 60s)")
        if total > 150:
            errors.append(f"Total duration too long: {total}s (maximum 150s)")

        for scene in self.scenes:
            if not (3 <= scene.duration_seconds <= 7):
                errors.append(
                    f"Scene {scene.scene_number}: duration {scene.duration_seconds}s "
                    f"out of range (3-7s)"
                )

        # Soft constraints (warnings, not blocking)
        if 12 <= n < 18:
            errors.append(f"WARN: Few scenes ({n}). Recommended: 18-24.")
        if 24 < n <= 30:
            errors.append(f"WARN: Many scenes ({n}). Recommended: 18-24.")

        return errors
