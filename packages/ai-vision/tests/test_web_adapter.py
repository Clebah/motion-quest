"""Integration tests for the FastAPI web adapter (SPEC-003 §5, §8.9)."""
from __future__ import annotations

import asyncio
import os
import shutil
import time
import unittest
from pathlib import Path

# app.py builds its adapters once at import time via build_adapters(), which goes
# LIVE if GEMINI_API_KEY is set (it is, in this repo's .env, loaded by the same
# import). Force it empty *before* importing app_module so tests never fire a real
# Gemini call — they inject a fake render step below regardless, but the LLM/image
# adapters must be the Mock ones too, or GenerateStoryboardUseCase would hang on a
# real network request.
os.environ["GEMINI_API_KEY"] = ""

from fastapi.testclient import TestClient

from src.adapters.inbound.web import app as app_module
from src.adapters.inbound.web import jobs as jobs_module
from src.adapters.inbound.web import session_state as session_state_module

_SAMPLE_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00"
    b"\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
)


async def _fake_render_ok(manifest_path: Path, video_out_path: Path) -> None:
    video_out_path.parent.mkdir(parents=True, exist_ok=True)
    video_out_path.write_bytes(b"FAKE_MP4")


async def _fake_render_ok_slow(manifest_path: Path, video_out_path: Path) -> None:
    await asyncio.sleep(0.3)
    await _fake_render_ok(manifest_path, video_out_path)


def _register_sample_character(client: TestClient, name: str = "Pedro") -> str:
    resp = client.post(
        "/api/characters",
        data={"name": name, "description": "Explorador"},
        files=[
            ("headshots", ("head.png", _SAMPLE_PNG_BYTES, "image/png")),
            ("fullbody", ("body.png", _SAMPLE_PNG_BYTES, "image/png")),
        ],
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


class TestWebAdapter(unittest.TestCase):

    def setUp(self):
        # Tests don't need a real Remotion build; default to the fast fake render.
        app_module.job_store._render_video = _fake_render_ok

    def tearDown(self):
        for root in (session_state_module.SESSION_ROOT, jobs_module.RUNS_ROOT):
            if root.exists():
                shutil.rmtree(root)
        app_module.character_store._characters.clear()
        app_module.job_store._jobs.clear()
        app_module.job_store._active_job_id = None

    def test_index_page_serves_expected_frontend_anchors(self):
        with TestClient(app_module.app) as client:
            resp = client.get("/")
            self.assertEqual(resp.status_code, 200)
            body = resp.text
            for anchor_id in (
                "character-form", "character-list", "template-grid",
                "roteiro-textarea", "generate-button", "result-video",
            ):
                self.assertIn(f'id="{anchor_id}"', body)
            self.assertIn('src="/static/app.js"', body)

    def test_get_templates_returns_five(self):
        with TestClient(app_module.app) as client:
            resp = client.get("/api/templates")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(resp.json()), 5)

    def test_get_mode_reports_live_flag(self):
        with TestClient(app_module.app) as client:
            resp = client.get("/api/mode")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("isLive", resp.json())

    def test_register_and_list_and_delete_character(self):
        with TestClient(app_module.app) as client:
            char_id = _register_sample_character(client)

            listed = client.get("/api/characters").json()
            self.assertIn(char_id, [c["id"] for c in listed])

            delete_resp = client.delete(f"/api/characters/{char_id}")
            self.assertEqual(delete_resp.status_code, 204)

            listed_after = client.get("/api/characters").json()
            self.assertNotIn(char_id, [c["id"] for c in listed_after])

    def test_delete_unknown_character_returns_404(self):
        with TestClient(app_module.app) as client:
            resp = client.delete("/api/characters/does_not_exist")
            self.assertEqual(resp.status_code, 404)

    def test_register_character_without_fullbody_returns_400(self):
        with TestClient(app_module.app) as client:
            resp = client.post(
                "/api/characters",
                data={"name": "Ana", "description": "Aventureira"},
                files=[("headshots", ("head.png", _SAMPLE_PNG_BYTES, "image/png"))],
            )
            self.assertEqual(resp.status_code, 400)

    def test_generate_without_selected_characters_returns_400(self):
        with TestClient(app_module.app) as client:
            resp = client.post("/api/generate", json={"characterIds": [], "roteiro": "x" * 30})
            self.assertEqual(resp.status_code, 400)

    def test_get_unknown_job_returns_404(self):
        with TestClient(app_module.app) as client:
            resp = client.get("/api/jobs/does_not_exist")
            self.assertEqual(resp.status_code, 404)

    def test_get_video_before_completion_returns_404(self):
        # Mock pipeline is fast enough to finish between two sequential calls, so use
        # the slow fake render to reliably catch the job still in flight.
        app_module.job_store._render_video = _fake_render_ok_slow
        with TestClient(app_module.app) as client:
            char_id = _register_sample_character(client)
            job_id = client.post(
                "/api/generate", json={"characterIds": [char_id], "roteiro": "x" * 30},
            ).json()["jobId"]

            resp = client.get(f"/api/jobs/{job_id}/video")
            self.assertEqual(resp.status_code, 404)

            self._poll_until_terminal(client, job_id)

    def test_full_generation_flow_reaches_completed_and_serves_video(self):
        with TestClient(app_module.app) as client:
            char_id = _register_sample_character(client)
            job_id = client.post(
                "/api/generate", json={"characterIds": [char_id], "roteiro": "x" * 30},
            ).json()["jobId"]

            job = self._poll_until_terminal(client, job_id)
            self.assertEqual(job["status"], "completed")
            self.assertEqual(job["videoUrl"], f"/api/jobs/{job_id}/video")

            video_resp = client.get(f"/api/jobs/{job_id}/video")
            self.assertEqual(video_resp.status_code, 200)
            self.assertEqual(video_resp.content, b"FAKE_MP4")

    def test_concurrent_generate_returns_409(self):
        app_module.job_store._render_video = _fake_render_ok_slow
        with TestClient(app_module.app) as client:
            char_id = _register_sample_character(client)
            first = client.post("/api/generate", json={"characterIds": [char_id], "roteiro": "x" * 30})
            self.assertEqual(first.status_code, 200)

            second = client.post("/api/generate", json={"characterIds": [char_id], "roteiro": "y" * 30})
            self.assertEqual(second.status_code, 409)

            self._poll_until_terminal(client, first.json()["jobId"])

    def _poll_until_terminal(self, client: TestClient, job_id: str, timeout: float = 5.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            job = client.get(f"/api/jobs/{job_id}").json()
            if job["status"] in ("completed", "failed"):
                return job
            time.sleep(0.05)
        raise AssertionError(f"job {job_id} did not reach a terminal state in {timeout}s")


if __name__ == "__main__":
    unittest.main()
