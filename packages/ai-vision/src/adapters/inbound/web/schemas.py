"""Pydantic request/response schemas for the local web UI API (SPEC-003 §5, §8.5)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CharacterSummary(BaseModel):
    id: str
    name: str
    description: str
    headshotPreviewUrl: str
    fullbodyPreviewUrl: str


class TemplateOut(BaseModel):
    id: str
    genre: str
    title: str
    synopsis: str
    promptText: str


class GenerateRequest(BaseModel):
    characterIds: list[str]
    roteiro: str = Field(min_length=20)


class SceneProgress(BaseModel):
    current: int
    total: int


JobStage = Literal[
    "generating_storyboard",
    "generating_assets",
    "exporting_manifest",
    "rendering_video",
    "done",
]

JobStatusValue = Literal["pending", "running", "completed", "failed"]


class JobStatus(BaseModel):
    jobId: str
    status: JobStatusValue
    stage: JobStage
    # Optional[...] instead of `X | None`: pydantic evaluates annotations at runtime,
    # and the `|` union syntax needs Python 3.10+ (this package targets 3.9).
    sceneProgress: Optional[SceneProgress] = None
    message: str = ""
    manifestPath: Optional[str] = None
    videoUrl: Optional[str] = None
    error: Optional[str] = None
