"""Outbound port: LLM provider for script/storyboard generation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

try:
    from pydantic import BaseModel
except ImportError:
    # Graceful fallback to pure Python dataclass-like structure if pydantic is not installed yet
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


class SceneSchema(BaseModel):
    scene_number: int
    duration_seconds: float = 5.0
    character_ids: list[str]
    visual_prompt: str
    narration_text: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)


class StoryboardSchema(BaseModel):
    title: str
    scenes: list[SceneSchema]

    SceneSchema: ClassVar[type] = SceneSchema

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k, v in kwargs.items():
            if k == "scenes" and isinstance(v, list):
                parsed = [item if isinstance(item, SceneSchema) else SceneSchema(**item) for item in v]
                setattr(self, k, parsed)
            else:
                setattr(self, k, v)


class LlmProviderPort(ABC):
    """Abstract port for LLM interactions.

    The adapter implementing this port must:
    - Accept a list of characters + a user prompt/template.
    - Return structured output matching StoryboardSchema.
    """

    @abstractmethod
    async def generate_storyboard(
        self,
        characters_description: str,
        user_prompt: str,
        story_template: str | None = None,
        min_scenes: int = 18,
        max_scenes: int = 24,
    ) -> StoryboardSchema:
        """Generate a structured storyboard from characters and prompt."""
        ...
