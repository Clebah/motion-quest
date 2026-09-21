"""Adapter: Google Gemini LLM provider (same API key as Mimo project)."""
from __future__ import annotations

import json
import os

from google import genai
from google.genai import types

from src.application.ports.outbound.llm_provider_port import (
    LlmProviderPort,
    StoryboardSchema,
)


SYSTEM_PROMPT = """You are a professional video storyboard writer.
Given a cast of characters and a story prompt, generate a structured storyboard
for an animated video. Each scene should last 3-7 seconds (default 5s).

Rules:
- Generate between {min_scenes} and {max_scenes} scenes.
- Total duration must be between 60 and 150 seconds.
- Each scene must specify which characters appear (by their IDs).
- visual_prompt: describe the visual composition in detail (style, lighting, camera angle, action).
- narration_text: short narration or subtitle for the scene.
- Use an engaging narrative arc (setup → conflict → resolution).
- Keep character appearances consistent with their descriptions.

Respond ONLY with valid JSON matching the schema provided."""


class GeminiLlmAdapter(LlmProviderPort):
    """Concrete adapter for Google Gemini API.

    Uses structured output (response_schema) for guaranteed JSON compliance.
    Shares the same GEMINI_API_KEY as the Mimo project.
    """

    def __init__(self, model: str = "gemini-2.0-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY not set. Copy it from your Mimo project .env"
            )
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate_storyboard(
        self,
        characters_description: str,
        user_prompt: str,
        story_template: str | None = None,
        min_scenes: int = 18,
        max_scenes: int = 24,
    ) -> StoryboardSchema:
        system_instruction = SYSTEM_PROMPT.format(
            min_scenes=min_scenes, max_scenes=max_scenes
        )

        user_message = f"""## Cast of Characters
{characters_description}

## Story Prompt
{user_prompt}
"""
        if story_template:
            user_message += f"\n## Story Template: {story_template}\n"

        response = self._client.models.generate_content(
            model=self._model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=StoryboardSchema,
                temperature=0.8,
            ),
        )

        data = json.loads(response.text)
        return StoryboardSchema(**data)
