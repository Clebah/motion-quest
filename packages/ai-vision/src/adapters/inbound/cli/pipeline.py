"""CLI Pipeline entry point for Motion Quest AI & Vision Worker."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from src.application.use_cases.register_character import RegisterCharacterUseCase
from src.application.use_cases.generate_storyboard import GenerateStoryboardUseCase
from src.application.use_cases.generate_scene_assets import GenerateSceneAssetsUseCase
from src.application.use_cases.export_manifest import ExportManifestUseCase
from src.adapters.outbound.local_storage_adapter import LocalStorageAdapter
from src.adapters.outbound.mock_adapters import (
    MockLlmAdapter,
    MockImageGeneratorAdapter,
    MockVideoAnimatorAdapter,
    MockImageProcessorAdapter,
)


def create_sample_photo(path: Path, label: str):
    """Creates a sample dummy image file using standard library."""
    path.parent.mkdir(parents=True, exist_ok=True)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00"
        b"\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    with open(path, "wb") as f:
        f.write(png_bytes)


def load_env_file():
    """Loads environment variables from .env file if present."""
    env_path = Path(".env")
    if not env_path.exists():
        env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def discover_characters(inputs_dir: Path) -> list[dict]:
    """Discovers characters from inputs/personagens directory."""
    characters = []
    chars_base = inputs_dir / "personagens" if (inputs_dir / "personagens").exists() else inputs_dir

    if not chars_base.exists():
        return characters

    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}

    for char_dir in chars_base.iterdir():
        if char_dir.is_dir() and not char_dir.name.startswith("."):
            name = char_dir.name.capitalize()
            headshots_dir = char_dir / "headshots"
            fullbody_dir = char_dir / "fullbody"

            headshots = [
                f for f in headshots_dir.glob("*") if f.suffix.lower() in valid_exts
            ] if headshots_dir.exists() else []

            fullbody = [
                f for f in fullbody_dir.glob("*") if f.suffix.lower() in valid_exts
            ] if fullbody_dir.exists() else []

            description = f"Personagem {name} cadastrado a partir de fotos reais."
            for desc_name in ["descricao.txt", "perfil.txt", "description.txt"]:
                desc_file = char_dir / desc_name
                if desc_file.exists():
                    try:
                        with open(desc_file, "r", encoding="utf-8") as f:
                            custom_desc = f.read().strip()
                            if custom_desc:
                                description = custom_desc
                                break
                    except Exception:
                        pass

            if headshots and fullbody:
                characters.append({
                    "name": name,
                    "description": description,
                    "headshots": headshots,
                    "fullbody": fullbody,
                })

    return characters


async def run_pipeline(args):
    load_env_file()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    is_live = bool(gemini_key and not args.mock)

    print("=" * 60)
    print("🚀 Motion Quest — AI & Vision Worker (SPEC-002 v3)")
    print(f"📁 Diretório de Saída: {output_dir}")
    print(f"⚙️  Modo de Execução: {'⚡ LIVE (Google Gemini API)' if is_live else '🧪 MOCK (Offline / Teste Local)'}")
    print("=" * 60)

    # 1. Setup Adapters
    storage = LocalStorageAdapter(output_dir)

    if is_live:
        try:
            from src.adapters.outbound.gemini_llm_adapter import GeminiLlmAdapter
            from src.adapters.outbound.gemini_image_generator import GeminiImageGeneratorAdapter
            llm_provider = GeminiLlmAdapter()
            image_processor = MockImageProcessorAdapter()
            image_gen = GeminiImageGeneratorAdapter()
            video_anim = MockVideoAnimatorAdapter()
            print("🔑 Chave GEMINI_API_KEY carregada com sucesso!")
            print("🎨 Adaptador Gemini Visual (gemini-2.5-flash-image) ativado para geração de cenas!")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar adaptadores Gemini ({e}). Alternando para mock.")
            llm_provider = MockLlmAdapter()
            image_processor = MockImageProcessorAdapter()
            image_gen = MockImageGeneratorAdapter()
            video_anim = MockVideoAnimatorAdapter()
    else:
        if not gemini_key:
            print("💡 Dica: Configure sua chave no arquivo .env para executar em modo LIVE.")
        llm_provider = MockLlmAdapter()
        image_processor = MockImageProcessorAdapter()
        image_gen = MockImageGeneratorAdapter()
        video_anim = MockVideoAnimatorAdapter()

    # 2. Use Cases
    register_char_uc = RegisterCharacterUseCase(image_processor)
    generate_storyboard_uc = GenerateStoryboardUseCase(llm_provider)
    generate_assets_uc = GenerateSceneAssetsUseCase(image_gen, video_anim)
    export_manifest_uc = ExportManifestUseCase(storage)

    # 3. Descobrir e Registrar Personagens
    print("\n[Etapa 1/4] 👥 Cadastrando Elenco...")
    inputs_dir = Path(args.inputs).resolve()
    discovered = discover_characters(inputs_dir)
    registered_characters = []

    if discovered:
        for d in discovered:
            char = await register_char_uc.execute(
                name=d["name"],
                description=d["description"],
                headshot_paths=d["headshots"],
                fullbody_paths=d["fullbody"],
                output_dir=output_dir,
            )
            registered_characters.append(char)
            print(f"   ✓ Personagem Real: {char.name} ({len(d['headshots'])} headshots, {len(d['fullbody'])} fullbody)")
    else:
        # Fallback para fotos de demonstração
        headshot = output_dir / "inputs" / "pedro_headshot.png"
        fullbody = output_dir / "inputs" / "pedro_fullbody.png"
        if not headshot.exists() or not fullbody.exists():
            create_sample_photo(headshot, "Headshot Pedro")
            create_sample_photo(fullbody, "Fullbody Pedro")

        char1 = await register_char_uc.execute(
            name="Pedro",
            description="Jovem aventureiro e explorador com jaqueta azul.",
            headshot_paths=[headshot],
            fullbody_paths=[fullbody],
            output_dir=output_dir,
        )
        registered_characters.append(char1)
        print(f"   ✓ Personagem Padrão: {char1.name} (ID: {char1.id})")

    # 4. Obter Roteiro / História
    print("\n[Etapa 2/4] 📝 Processando Roteiro e Gerando Cenas...")
    prompt_text = ""
    if args.prompt:
        prompt_text = args.prompt
    elif Path(args.prompt_file).exists():
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
            prompt_text = " ".join(lines)
    else:
        prompt_text = "Uma viagem épica pelo espaço em busca de um cristal cósmico perdido."

    print(f"   📖 Roteiro Base: \"{prompt_text[:80]}...\"")
    storyboard = await generate_storyboard_uc.execute(
        characters=registered_characters,
        user_prompt=prompt_text,
        story_template=args.template or "Jornada do Herói",
    )
    print(f"   ✓ Título do Storyboard: '{storyboard.title}'")
    print(f"   ✓ Cenas Criadas: {len(storyboard.scenes)} cenas ({storyboard.total_duration_seconds:.1f}s de vídeo)")
    if storyboard.cost_estimate:
        print(f"   ✓ Custo Estimado da Produção: ${storyboard.cost_estimate.total:.2f} {storyboard.cost_estimate.currency}")

    # 5. Gerar Assets das Cenas
    print("\n[Etapa 3/4] 🎨 Gerando Imagens e Animações das Cenas...")
    def on_progress(current, total, message):
        print(f"   [{current}/{total}] {message}")

    storyboard = await generate_assets_uc.execute(
        storyboard=storyboard,
        characters=registered_characters,
        output_dir=output_dir,
        on_progress=on_progress,
    )

    # 6. Exportar Contrato manifest.json
    print("\n[Etapa 4/4] 📄 Exportando manifest.json para o Remotion...")
    manifest_path = await export_manifest_uc.execute(storyboard, registered_characters, "manifest.json")
    print(f"   ✓ Manifest gravado em: {manifest_path}")

    print("\n" + "=" * 60)
    print("🎉 Pipeline concluído com sucesso!")
    print(f"👉 Para renderizar o vídeo agora:")
    print(f"   cd ../video-render && node dist/adapters/inbound/cli/index.js --manifest={manifest_path} --out=out/meu_video.mp4")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Motion Quest AI & Vision Worker CLI")
    parser.add_argument("--prompt", type=str, default="", help="Prompt direto do roteiro")
    parser.add_argument("--prompt-file", type=str, default="../../inputs/roteiro.txt", help="Arquivo .txt com o roteiro")
    parser.add_argument("--inputs", type=str, default="../../inputs", help="Pasta com as fotos dos personagens")
    parser.add_argument("--template", type=str, default="Jornada do Herói", help="Template narrativo")
    parser.add_argument("--output", type=str, default="./output/poc_run", help="Diretório de saída")
    parser.add_argument("--mock", action="store_true", help="Forçar modo mock mesmo com chave presente")

    args = parser.parse_args()
    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
