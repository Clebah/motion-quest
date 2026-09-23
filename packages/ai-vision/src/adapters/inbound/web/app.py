"""FastAPI app for the local web UI (SPEC-003).

Single process, no authentication, binds to 127.0.0.1 only (NF-01). Note: no
`from __future__ import annotations` here on purpose — FastAPI resolves route
parameter annotations at runtime, and this package targets Python 3.9 where the
`X | None` union syntax isn't evaluable without extra tooling (see schemas.py).
"""
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.adapters.inbound.cli.adapter_factory import build_adapters
from src.adapters.inbound.cli.pipeline import load_env_file
from src.adapters.inbound.web import session_state as session_state_module
from src.adapters.inbound.web.jobs import JobAlreadyRunningError, JobStore
from src.adapters.inbound.web.schemas import CharacterSummary, GenerateRequest, JobStatus, TemplateOut
from src.adapters.inbound.web.session_state import SessionCharacterStore
from src.adapters.inbound.web.templates_catalog import get_templates
from src.application.use_cases.generate_scene_assets import GenerateSceneAssetsUseCase
from src.application.use_cases.generate_storyboard import GenerateStoryboardUseCase

load_env_file()

_STATIC_DIR = Path(__file__).resolve().parent / "static"

_bundle = build_adapters()
character_store = SessionCharacterStore(_bundle.image_processor)
job_store = JobStore(
    generate_storyboard_uc=GenerateStoryboardUseCase(_bundle.llm_provider),
    generate_assets_uc=GenerateSceneAssetsUseCase(_bundle.image_gen, _bundle.video_anim),
)

app = FastAPI(title="Motion Quest — Web UI Local")

session_state_module.SESSION_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
app.mount("/media", StaticFiles(directory=str(session_state_module.SESSION_ROOT.resolve())), name="media")


@app.get("/")
async def index():
    return FileResponse(str(_STATIC_DIR / "index.html"))


@app.get("/api/mode")
async def get_mode():
    """Exposes whether the server is running LIVE (Gemini) or MOCK (RF-05.1)."""
    return {"isLive": _bundle.is_live}


@app.get("/api/templates", response_model=List[TemplateOut])
async def list_templates():
    return get_templates()


@app.get("/api/characters", response_model=List[CharacterSummary])
async def list_characters():
    return character_store.list()


@app.post("/api/characters", response_model=CharacterSummary)
async def create_character(
    name: str = Form(...),
    description: str = Form(""),
    headshots: List[UploadFile] = File(default=[]),
    fullbody: List[UploadFile] = File(default=[]),
):
    headshot_files = [(f.filename, await f.read()) for f in headshots]
    fullbody_files = [(f.filename, await f.read()) for f in fullbody]
    try:
        return await character_store.register(name, description, headshot_files, fullbody_files)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete("/api/characters/{character_id}", status_code=204)
async def delete_character(character_id: str):
    if not character_store.remove(character_id):
        raise HTTPException(status_code=404, detail="Personagem não encontrado")
    return Response(status_code=204)


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    characters = character_store.get_many(req.characterIds)
    if not characters:
        raise HTTPException(status_code=400, detail="Selecione ao menos um personagem cadastrado")
    try:
        job_id = job_store.start_job(characters, req.roteiro)
    except JobAlreadyRunningError:
        raise HTTPException(
            status_code=409,
            detail="Já existe uma geração em andamento. Aguarde terminar.",
        )
    return {"jobId": job_id}


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job(job_id: str):
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return job


@app.get("/api/jobs/{job_id}/video")
async def get_job_video(job_id: str):
    video_path = job_store.get_video_path(job_id)
    if video_path is None or not video_path.exists():
        raise HTTPException(status_code=404, detail="Vídeo ainda não disponível")
    return FileResponse(str(video_path), media_type="video/mp4")
