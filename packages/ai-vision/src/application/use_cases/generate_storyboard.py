"""Use Case: Generate a storyboard (script + scene breakdown) from characters and prompt."""
from __future__ import annotations

import uuid

from src.application.ports.outbound.llm_provider_port import LlmProviderPort
from src.domain.entities.character import Character
from src.domain.entities.storyboard import CostEstimate, Scene, Storyboard


# Approximate cost per operation (Gemini API / Imagen 3 / Veo 2)
COST_PER_IMAGE_USD = 0.06  # Imagen 3 per image
COST_PER_CLIP_USD = 0.15   # Veo 2 per 5s clip


class GenerateStoryboardUseCase:
    """Generates a storyboard by calling the LLM and validating the output.

    Steps:
    1. Build a character description from the cast.
    2. Call the LLM with structured output (Pydantic schema).
    3. Validate scene count & duration constraints.
    4. Compute cost estimate before proceeding.
    """

    def __init__(self, llm_provider: LlmProviderPort):
        self._llm = llm_provider

    async def execute(
        self,
        characters: list[Character],
        user_prompt: str,
        story_template: str | None = None,
    ) -> Storyboard:
        project_id = f"proj_{uuid.uuid4().hex[:8]}"

        # Build a character summary for the LLM
        chars_desc = "\n".join(
            f"- {c.name} ({c.id}): {c.description}" for c in characters
        )

        # Call LLM with structured output
        llm_result = await self._llm.generate_storyboard(
            characters_description=chars_desc,
            user_prompt=user_prompt,
            story_template=story_template,
        )

        # Map LLM output to domain entities
        scenes = [
            Scene(
                scene_number=s.scene_number,
                duration_seconds=s.duration_seconds,
                character_ids=s.character_ids,
                visual_prompt=s.visual_prompt,
                narration_text=s.narration_text,
            )
            for s in llm_result.scenes
        ]

        storyboard = Storyboard(
            project_id=project_id,
            title=llm_result.title,
            scenes=scenes,
        )

        # Compute cost estimate
        n_scenes = len(scenes)
        storyboard.cost_estimate = CostEstimate(
            image_generation=round(n_scenes * COST_PER_IMAGE_USD, 2),
            video_animation=round(n_scenes * COST_PER_CLIP_USD, 2),
        )

        # Validate
        errors = storyboard.validate()
        blocking_errors = [e for e in errors if not e.startswith("WARN:")]
        warnings = [e for e in errors if e.startswith("WARN:")]

        if blocking_errors:
            raise ValueError(
                f"Storyboard validation failed: {'; '.join(blocking_errors)}"
            )

        # Log warnings (non-blocking)
        for w in warnings:
            print(f"⚠️  {w}")

        return storyboard
