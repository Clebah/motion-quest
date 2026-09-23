"""Tests for the web API pydantic schemas (SPEC-003 §8.5)."""
from __future__ import annotations

import unittest

from pydantic import ValidationError

from src.adapters.inbound.web.schemas import (
    CharacterSummary,
    GenerateRequest,
    JobStatus,
    SceneProgress,
    TemplateOut,
)


class TestWebSchemas(unittest.TestCase):

    def test_generate_request_accepts_valid_roteiro(self):
        req = GenerateRequest(characterIds=["char_1"], roteiro="x" * 20)
        self.assertEqual(len(req.characterIds), 1)

    def test_generate_request_rejects_short_roteiro(self):
        with self.assertRaises(ValidationError):
            GenerateRequest(characterIds=["char_1"], roteiro="curto demais")

    def test_job_status_rejects_unknown_status_literal(self):
        with self.assertRaises(ValidationError):
            JobStatus(jobId="job_1", status="bogus", stage="generating_storyboard")

    def test_job_status_rejects_unknown_stage_literal(self):
        with self.assertRaises(ValidationError):
            JobStatus(jobId="job_1", status="pending", stage="bogus_stage")

    def test_job_status_accepts_valid_payload_with_defaults(self):
        status = JobStatus(jobId="job_1", status="running", stage="generating_assets")
        self.assertEqual(status.message, "")
        self.assertIsNone(status.sceneProgress)
        self.assertIsNone(status.videoUrl)

    def test_job_status_with_scene_progress_and_video_url(self):
        status = JobStatus(
            jobId="job_1",
            status="completed",
            stage="done",
            sceneProgress=SceneProgress(current=18, total=18),
            videoUrl="/api/jobs/job_1/video",
        )
        self.assertEqual(status.sceneProgress.current, 18)
        self.assertEqual(status.videoUrl, "/api/jobs/job_1/video")

    def test_character_summary_and_template_out_roundtrip(self):
        char = CharacterSummary(
            id="char_1", name="Pedro", description="Explorador",
            headshotPreviewUrl="/media/chars/char_1/head_face.png",
            fullbodyPreviewUrl="/media/chars/char_1/body_nobg.png",
        )
        self.assertEqual(char.name, "Pedro")

        tpl = TemplateOut(
            id="terror", genre="Terror", title="A Última Noite na Cabana",
            synopsis="...", promptText="x" * 30,
        )
        self.assertEqual(tpl.genre, "Terror")


if __name__ == "__main__":
    unittest.main()
