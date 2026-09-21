"""Adapter: Google Gemini LLM provider (same API key as Mimo project)."""
from __future__ import annotations

import json
import os
import ssl
import urllib.request
from src.application.ports.outbound.llm_provider_port import (
    LlmProviderPort,
    StoryboardSchema,
    SceneSchema,
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

Respond ONLY with valid JSON with this exact structure:
{{
  "title": "Story Title",
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 5.0,
      "character_ids": ["char_id"],
      "visual_prompt": "description of visuals",
      "narration_text": "narration audio or subtitle"
    }}
  ]
}}"""


class GeminiLlmAdapter(LlmProviderPort):
    """Concrete adapter for Google Gemini API.

    Supports both official google-genai SDK and standard-library REST fallback.
    Shares the same GEMINI_API_KEY as the Mimo project.
    """

    def __init__(self, model: str = "gemini-2.0-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY not set. Copy it from your Mimo project .env"
            )
        self._api_key = api_key
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

        user_message = f"""## Cast of Characters\n{characters_description}\n\n## Story Prompt\n{user_prompt}\n"""
        if story_template:
            user_message += f"\n## Story Template: {story_template}\n"

        # Try using SDK if available
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self._api_key)
            response = client.models.generate_content(
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
        except Exception:
            # Fallback to direct REST API via urllib (zero external dependency)
            return await self._generate_via_rest(system_instruction, user_message)

    async def _generate_via_rest(
        self, system_instruction: str, user_message: str
    ) -> StoryboardSchema:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={self._api_key}"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": user_message}]}],
            "generationConfig": {
                "temperature": 0.8,
                "responseMimeType": "application/json",
            },
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
        )

        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=ctx) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        raw_text = body["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_text)

        scenes = [
            SceneSchema(
                scene_number=s.get("scene_number", idx + 1),
                duration_seconds=float(s.get("duration_seconds", 5.0)),
                character_ids=s.get("character_ids", []),
                visual_prompt=s.get("visual_prompt", ""),
                narration_text=s.get("narration_text", ""),
            )
            for idx, s in enumerate(parsed.get("scenes", []))
        ]

        return StoryboardSchema(title=parsed.get("title", "História Animada"), scenes=scenes)
