"""Standard library unittest runner for AI Vision Worker."""
import asyncio
import json
import unittest
from pathlib import Path

from src.domain.entities.character import Character, CharacterPhoto
from src.domain.entities.storyboard import Storyboard, Scene, SceneStatus
from src.application.use_cases.generate_storyboard import GenerateStoryboardUseCase
from src.application.use_cases.export_manifest import ExportManifestUseCase
from src.adapters.outbound.mock_adapters import (
    MockLlmAdapter,
    MockImageGeneratorAdapter,
    MockVideoAnimatorAdapter,
)
from src.adapters.outbound.local_storage_adapter import LocalStorageAdapter


class TestAiVisionWorker(unittest.TestCase):

    def test_character_validation_rules(self):
        char = Character(
            id="char_1",
            name="Ana",
            description="Aventureira",
            photos=[
                CharacterPhoto(path=Path("head.png"), photo_type="headshot"),
                CharacterPhoto(path=Path("body.png"), photo_type="fullbody"),
            ],
        )
        self.assertEqual(char.validate(), [])

        invalid_char = Character(
            id="char_2",
            name="Carlos",
            description="Mago",
            photos=[
                CharacterPhoto(path=Path("head.png"), photo_type="headshot"),
            ],
        )
        errors = invalid_char.validate()
        self.assertTrue(any("full-body" in e for e in errors))

    def test_storyboard_validation_hard_and_soft_constraints(self):
        too_short_scenes = [
            Scene(scene_number=i, duration_seconds=5.0, character_ids=["c1"], visual_prompt="p", narration_text="n")
            for i in range(1, 10)
        ]
        sb_short = Storyboard(project_id="p1", title="Curto", scenes=too_short_scenes)
        errors = sb_short.validate()
        self.assertTrue(any("Too few scenes" in e for e in errors))

        fifteen_scenes = [
            Scene(scene_number=i, duration_seconds=5.0, character_ids=["c1"], visual_prompt="p", narration_text="n")
            for i in range(1, 16)
        ]
        sb_fifteen = Storyboard(project_id="p2", title="Ok com Warning", scenes=fifteen_scenes)
        errors = sb_fifteen.validate()
        blocking = [e for e in errors if not e.startswith("WARN:")]
        warnings = [e for e in errors if e.startswith("WARN:")]
        self.assertEqual(len(blocking), 0)
        self.assertTrue(len(warnings) > 0)

    def test_generate_storyboard_use_case(self):
        mock_llm = MockLlmAdapter()
        uc = GenerateStoryboardUseCase(mock_llm)

        char = Character(
            id="char_demo_1",
            name="Pedro",
            description="Explorador",
            photos=[
                CharacterPhoto(path=Path("head.png"), photo_type="headshot"),
                CharacterPhoto(path=Path("body.png"), photo_type="fullbody"),
            ],
        )

        storyboard = asyncio.run(
            uc.execute(
                characters=[char],
                user_prompt="Uma jornada interestelar fantástica",
            )
        )

        self.assertEqual(len(storyboard.scenes), 18)
        self.assertEqual(storyboard.total_duration_seconds, 90.0)
        self.assertIsNotNone(storyboard.cost_estimate)
        self.assertGreater(storyboard.cost_estimate.total, 0)

    def test_export_manifest_json_contract(self):
        tmp_dir = Path("./output/test_manifest")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        storage = LocalStorageAdapter(tmp_dir)
        export_uc = ExportManifestUseCase(storage)

        char = Character(
            id="char_1",
            name="Pedro",
            description="Explorador",
            photos=[
                CharacterPhoto(path=Path("head.png"), photo_type="headshot", processed_path=Path("head_nobg.png")),
                CharacterPhoto(path=Path("body.png"), photo_type="fullbody", processed_path=Path("body_nobg.png")),
            ],
        )

        scenes = [
            Scene(
                scene_number=1,
                duration_seconds=5.0,
                character_ids=["char_1"],
                visual_prompt="Pedro na nave",
                narration_text="Início da missão",
                image_path=Path("scenes/s1.png"),
                clip_path=Path("clips/s1.mp4"),
                status=SceneStatus.COMPLETED,
            )
        ]

        sb = Storyboard(project_id="proj_test", title="Missão Espacial", scenes=scenes)
        manifest_path = asyncio.run(export_uc.execute(sb, [char], "manifest.json"))

        self.assertTrue(Path(manifest_path).exists())
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["version"], "1.0")
        self.assertEqual(data["projectId"], "proj_test")
        self.assertEqual(data["resolution"]["width"], 1080)
        self.assertEqual(data["resolution"]["height"], 1920)
        self.assertEqual(len(data["characters"]), 1)
        self.assertEqual(len(data["scenes"]), 1)


if __name__ == "__main__":
    unittest.main()
