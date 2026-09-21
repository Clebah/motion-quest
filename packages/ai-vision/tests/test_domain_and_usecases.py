"""Unit and use case tests for AI Vision Worker (SPEC-002 v3)."""
import asyncio
import json
import pytest
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


def test_character_validation_rules():
    # Valid character
    char = Character(
        id="char_1",
        name="Ana",
        description="Aventureira",
        photos=[
            CharacterPhoto(path=Path("head.png"), photo_type="headshot"),
            CharacterPhoto(path=Path("body.png"), photo_type="fullbody"),
        ],
    )
    assert char.validate() == []

    # Invalid: no fullbody
    invalid_char = Character(
        id="char_2",
        name="Carlos",
        description="Mago",
        photos=[
            CharacterPhoto(path=Path("head.png"), photo_type="headshot"),
        ],
    )
    errors = invalid_char.validate()
    assert any("full-body" in e for e in errors)


def test_storyboard_validation_hard_and_soft_constraints():
    # Less than 12 scenes -> Hard Error
    too_short_scenes = [
        Scene(scene_number=i, duration_seconds=5.0, character_ids=["c1"], visual_prompt="p", narration_text="n")
        for i in range(1, 10)
    ]
    sb_short = Storyboard(project_id="p1", title="Curto", scenes=too_short_scenes)
    errors = sb_short.validate()
    assert any("Too few scenes" in e for e in errors)

    # 15 scenes (within 12-30 hard range, but outside 18-24 soft range) -> Warning
    fifteen_scenes = [
        Scene(scene_number=i, duration_seconds=5.0, character_ids=["c1"], visual_prompt="p", narration_text="n")
        for i in range(1, 16)
    ]
    sb_fifteen = Storyboard(project_id="p2", title="Ok com Warning", scenes=fifteen_scenes)
    errors = sb_fifteen.validate()
    blocking = [e for e in errors if not e.startswith("WARN:")]
    warnings = [e for e in errors if e.startswith("WARN:")]
    assert len(blocking) == 0
    assert len(warnings) > 0


@pytest.mark.asyncio
async def test_generate_storyboard_use_case():
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

    storyboard = await uc.execute(
        characters=[char],
        user_prompt="Uma jornada interestelar fantástica",
    )

    assert len(storyboard.scenes) == 18
    assert storyboard.total_duration_seconds == 90.0
    assert storyboard.cost_estimate is not None
    assert storyboard.cost_estimate.total > 0


@pytest.mark.asyncio
async def test_export_manifest_json_contract(tmp_path):
    storage = LocalStorageAdapter(tmp_path)
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
    manifest_path = await export_uc.execute(sb, [char], "manifest.json")

    assert Path(manifest_path).exists()
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "1.0"
    assert data["projectId"] == "proj_test"
    assert data["resolution"]["width"] == 1080
    assert data["resolution"]["height"] == 1920
    assert len(data["characters"]) == 1
    assert len(data["scenes"]) == 1
    assert data["scenes"][0]["sceneNumber"] == 1
