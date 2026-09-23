"""Background job orchestration for the video generation pipeline (SPEC-003 RF-03, §8.3-8.4)."""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Awaitable, Callable

from src.adapters.outbound.local_storage_adapter import LocalStorageAdapter
from src.application.use_cases.export_manifest import ExportManifestUseCase
from src.application.use_cases.generate_scene_assets import GenerateSceneAssetsUseCase
from src.application.use_cases.generate_storyboard import GenerateStoryboardUseCase
from src.domain.entities.character import Character

from src.adapters.inbound.web.schemas import JobStatus, SceneProgress

RUNS_ROOT = Path("output/web/runs")

# (manifest_path, video_out_path) -> None; raises on failure. Injectable so tests don't
# need a built video-render worker (SPEC-003 §9, T7).
RenderFn = Callable[[Path, Path], Awaitable[None]]

VIDEO_RENDER_DIR = Path(__file__).resolve().parents[5] / "video-render"


class JobAlreadyRunningError(Exception):
    """Raised when a new job is requested while one is still pending/running (RF-03.4)."""


async def default_render_video(manifest_path: Path, video_out_path: Path) -> None:
    """Invokes the Worker 2 (video-render) CLI as a subprocess, mirroring `make render`."""
    video_out_path.parent.mkdir(parents=True, exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        "node", "dist/adapters/inbound/cli/index.js",
        f"--manifest={manifest_path}",
        f"--out={video_out_path}",
        cwd=str(VIDEO_RENDER_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        tail = stderr.decode(errors="replace")[-2000:]
        raise RuntimeError(f"Renderização falhou (exit {proc.returncode}): {tail}")


class JobStore:
    """In-memory job registry + orchestration.

    Single active job at a time (SPEC-003 NF-02 / RF-03.4). Not thread-safe by design:
    this spec runs as a single uvicorn process/event loop (§8.7).
    """

    def __init__(
        self,
        generate_storyboard_uc: GenerateStoryboardUseCase,
        generate_assets_uc: GenerateSceneAssetsUseCase,
        render_video: RenderFn = default_render_video,
    ):
        self._generate_storyboard_uc = generate_storyboard_uc
        self._generate_assets_uc = generate_assets_uc
        self._render_video = render_video
        self._jobs: dict = {}
        self._active_job_id = None

    def start_job(self, characters: list[Character], roteiro: str) -> str:
        if self._active_job_id is not None:
            raise JobAlreadyRunningError(self._active_job_id)

        job_id = f"job_{uuid.uuid4().hex[:8]}"
        self._jobs[job_id] = JobStatus(
            jobId=job_id,
            status="pending",
            stage="generating_storyboard",
            message="Na fila...",
        )
        self._active_job_id = job_id
        asyncio.create_task(self._run(job_id, characters, roteiro))
        return job_id

    def get_job(self, job_id: str):
        return self._jobs.get(job_id)

    def get_video_path(self, job_id: str):
        job = self._jobs.get(job_id)
        if job is None or job.status != "completed" or not job.videoUrl:
            return None
        return RUNS_ROOT.resolve() / job_id / "video.mp4"

    async def _run(self, job_id: str, characters: list[Character], roteiro: str) -> None:
        run_dir = (RUNS_ROOT / job_id).resolve()
        run_dir.mkdir(parents=True, exist_ok=True)
        storage = LocalStorageAdapter(run_dir)
        export_manifest_uc = ExportManifestUseCase(storage)

        try:
            self._update(job_id, status="running", stage="generating_storyboard", message="Gerando roteiro e cenas...")
            storyboard = await self._generate_storyboard_uc.execute(
                characters=characters, user_prompt=roteiro, story_template=None,
            )

            self._update(job_id, stage="generating_assets", message="Gerando imagens e animações...")

            def on_progress(current: int, total: int, message: str) -> None:
                self._update(job_id, sceneProgress=SceneProgress(current=current, total=total), message=message)

            storyboard = await self._generate_assets_uc.execute(
                storyboard=storyboard, characters=characters, output_dir=run_dir, on_progress=on_progress,
            )

            self._update(job_id, stage="exporting_manifest", message="Exportando manifest.json...")
            manifest_path = await export_manifest_uc.execute(storyboard, characters, "manifest.json")

            self._update(job_id, stage="rendering_video", message="Renderizando vídeo final...")
            video_path = run_dir / "video.mp4"
            await self._render_video(Path(manifest_path), video_path)

            self._update(
                job_id,
                status="completed",
                stage="done",
                message="Concluído!",
                manifestPath=str(manifest_path),
                videoUrl=f"/api/jobs/{job_id}/video",
            )
        except Exception as exc:
            failed_at_stage = self._jobs[job_id].stage
            self._update(
                job_id,
                status="failed",
                error=str(exc),
                message=f"Falhou em '{failed_at_stage}': {exc}",
            )
        finally:
            self._active_job_id = None

    def _update(self, job_id: str, **updates) -> None:
        current = self._jobs[job_id]
        self._jobs[job_id] = current.model_copy(update=updates)
