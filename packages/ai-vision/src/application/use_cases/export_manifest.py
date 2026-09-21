"""Use Case: Export Storyboard and Cast to manifest.json contract."""
from __future__ import annotations

from pathlib import Path

from src.application.ports.outbound.storage_port import StoragePort
from src.domain.entities.character import Character
from src.domain.entities.storyboard import Storyboard


class ExportManifestUseCase:
    """Exports storyboard, characters, and assets to the agreed manifest.json format."""

    def __init__(self, storage: StoragePort):
        self._storage = storage

    async def execute(
        self,
        storyboard: Storyboard,
        characters: list[Character],
        destination_filename: str = "manifest.json",
    ) -> str:
        manifest_data = {
            "version": "1.0",
            "projectId": storyboard.project_id,
            "title": storyboard.title,
            "totalScenes": len(storyboard.scenes),
            "totalDurationSeconds": storyboard.total_duration_seconds,
            "resolution": {
                "width": storyboard.resolution_width,
                "height": storyboard.resolution_height,
            },
            "fps": storyboard.fps,
            "characters": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "headshotPath": str(c.headshots[0].processed_path) if c.headshots and c.headshots[0].processed_path else None,
                    "fullbodyPath": str(c.fullbody_photos[0].processed_path) if c.fullbody_photos and c.fullbody_photos[0].processed_path else None,
                }
                for c in characters
            ],
            "scenes": [
                {
                    "sceneNumber": s.scene_number,
                    "durationSeconds": s.duration_seconds,
                    "characterIds": s.character_ids,
                    "visualPrompt": s.visual_prompt,
                    "narrationText": s.narration_text,
                    "imagePath": str(s.image_path) if s.image_path else None,
                    "clipPath": str(s.clip_path) if s.clip_path else None,
                    "status": s.status.value,
                }
                for s in storyboard.scenes
            ],
            "audio": {
                "backgroundMusicPath": str(storyboard.audio.music_path) if storyboard.audio.music_path else None,
                "volume": storyboard.audio.volume,
            },
            "estimatedCost": {
                "currency": storyboard.cost_estimate.currency,
                "imageGeneration": storyboard.cost_estimate.image_generation,
                "videoAnimation": storyboard.cost_estimate.video_animation,
                "total": storyboard.cost_estimate.total,
            } if storyboard.cost_estimate else None,
        }

        manifest_path = await self._storage.save_json(manifest_data, destination_filename)
        return manifest_path
