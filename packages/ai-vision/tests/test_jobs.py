"""Tests for background job orchestration (SPEC-003 RF-03, NF-02, §8.3-8.4)."""
from __future__ import annotations

import asyncio
import shutil
import unittest
from pathlib import Path

from src.adapters.inbound.web import jobs as jobs_module
from src.adapters.inbound.web.jobs import JobAlreadyRunningError, JobStore
from src.adapters.outbound.mock_adapters import (
    MockImageGeneratorAdapter,
    MockLlmAdapter,
    MockVideoAnimatorAdapter,
)
from src.application.use_cases.generate_scene_assets import GenerateSceneAssetsUseCase
from src.application.use_cases.generate_storyboard import GenerateStoryboardUseCase
from src.domain.entities.character import Character, CharacterPhoto


def _make_character() -> Character:
    return Character(
        id="char_demo_1",
        name="Pedro",
        description="Explorador",
        photos=[
            CharacterPhoto(path=Path("head.png"), photo_type="headshot", processed_path=Path("head.png")),
            CharacterPhoto(path=Path("body.png"), photo_type="fullbody", processed_path=Path("body.png")),
        ],
    )


async def _fake_render_ok(manifest_path: Path, video_out_path: Path) -> None:
    video_out_path.parent.mkdir(parents=True, exist_ok=True)
    video_out_path.write_bytes(b"FAKE_MP4")


async def _fake_render_fails(manifest_path: Path, video_out_path: Path) -> None:
    raise RuntimeError("remotion boom")


async def _wait_for_terminal(store: JobStore, job_id: str, timeout: float = 5.0):
    elapsed = 0.0
    step = 0.02
    while elapsed < timeout:
        job = store.get_job(job_id)
        if job.status in ("completed", "failed"):
            return job
        await asyncio.sleep(step)
        elapsed += step
    raise AssertionError(f"job {job_id} did not reach a terminal state in {timeout}s (last: {store.get_job(job_id)})")


def _make_store(render_fn) -> JobStore:
    return JobStore(
        generate_storyboard_uc=GenerateStoryboardUseCase(MockLlmAdapter()),
        generate_assets_uc=GenerateSceneAssetsUseCase(MockImageGeneratorAdapter(), MockVideoAnimatorAdapter()),
        render_video=render_fn,
    )


class TestJobStore(unittest.TestCase):

    def tearDown(self):
        if jobs_module.RUNS_ROOT.exists():
            shutil.rmtree(jobs_module.RUNS_ROOT)

    def test_full_success_flow_reaches_completed(self):
        async def scenario():
            store = _make_store(_fake_render_ok)
            job_id = store.start_job([_make_character()], "x" * 30)

            first = store.get_job(job_id)
            self.assertEqual(first.status, "pending")

            job = await _wait_for_terminal(store, job_id)
            self.assertEqual(job.status, "completed")
            self.assertEqual(job.stage, "done")
            self.assertIsNotNone(job.manifestPath)
            self.assertEqual(job.videoUrl, f"/api/jobs/{job_id}/video")

            video_path = store.get_video_path(job_id)
            self.assertTrue(video_path.exists())

        asyncio.run(scenario())

    def test_render_failure_marks_job_failed_with_stage_and_error(self):
        async def scenario():
            store = _make_store(_fake_render_fails)
            job_id = store.start_job([_make_character()], "x" * 30)

            job = await _wait_for_terminal(store, job_id)
            self.assertEqual(job.status, "failed")
            self.assertEqual(job.stage, "rendering_video")
            self.assertIn("remotion boom", job.error)

        asyncio.run(scenario())

    def test_concurrent_generate_is_rejected_while_a_job_is_active(self):
        async def scenario():
            store = _make_store(_fake_render_ok)
            job_id = store.start_job([_make_character()], "x" * 30)

            with self.assertRaises(JobAlreadyRunningError):
                store.start_job([_make_character()], "outro roteiro" * 3)

            # let the first job finish so the single-active-job slot frees up again
            await _wait_for_terminal(store, job_id)

            second_job_id = store.start_job([_make_character()], "x" * 30)
            self.assertNotEqual(second_job_id, job_id)
            await _wait_for_terminal(store, second_job_id)

        asyncio.run(scenario())

    def test_unknown_job_id_returns_none(self):
        store = _make_store(_fake_render_ok)
        self.assertIsNone(store.get_job("does_not_exist"))
        self.assertIsNone(store.get_video_path("does_not_exist"))


if __name__ == "__main__":
    unittest.main()
