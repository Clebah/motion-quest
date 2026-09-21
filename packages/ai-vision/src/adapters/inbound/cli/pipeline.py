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
    # Minimal 1x1 PNG bytes
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00"
        b"\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    with open(path, "wb") as f:
        f.write(png_bytes)


async def run_pipeline(args):
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🚀 Motion Quest — AI & Vision Worker (SPEC-002 v3)")
    print(f"📁 Output Directory: {output_dir}")
    print(f"⚙️  Mode: {'MOCK (Offline)' if args.mock else 'LIVE (Gemini APIs)'}")
    print("=" * 60)

    # 1. Setup Adapters
    storage = LocalStorageAdapter(output_dir)

    if args.mock:
        image_processor = MockImageProcessorAdapter()
        llm_provider = MockLlmAdapter()
        image_gen = MockImageGeneratorAdapter()
        video_anim = MockVideoAnimatorAdapter()
    else:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            print("⚠️  GEMINI_API_KEY not found in environment or .env!")
            print("💡 Falling back to --mock mode for this execution.")
            image_processor = MockImageProcessorAdapter()
            llm_provider = MockLlmAdapter()
            image_gen = MockImageGeneratorAdapter()
            video_anim = MockVideoAnimatorAdapter()
        else:
            from src.adapters.outbound.rembg_image_processor import RembgImageProcessorAdapter
            from src.adapters.outbound.gemini_llm_adapter import GeminiLlmAdapter
            from src.adapters.outbound.gemini_image_generator import GeminiImageGeneratorAdapter
            from src.adapters.outbound.gemini_video_animator import GeminiVideoAnimatorAdapter

            image_processor = RembgImageProcessorAdapter()
            llm_provider = GeminiLlmAdapter()
            image_gen = GeminiImageGeneratorAdapter()
            video_anim = GeminiVideoAnimatorAdapter()

    # 2. Use Cases
    register_char_uc = RegisterCharacterUseCase(image_processor)
    generate_storyboard_uc = GenerateStoryboardUseCase(llm_provider)
    generate_assets_uc = GenerateSceneAssetsUseCase(image_gen, video_anim)
    export_manifest_uc = ExportManifestUseCase(storage)

    # 3. Register Characters
    print("\n[Step 1/4] 👤 Registering Cast...")
    characters = []
    
    # Check for photo inputs or generate demo photos
    headshot = output_dir / "inputs" / "pedro_headshot.png"
    fullbody = output_dir / "inputs" / "pedro_fullbody.png"
    if not headshot.exists() or not fullbody.exists():
        create_sample_photo(headshot, "Headshot Pedro")
        create_sample_photo(fullbody, "Fullbody Pedro")

    char1 = await register_char_uc.execute(
        name="Pedro",
        description="Homem jovem de 28 anos, cabelos castanhos e jaqueta azul moderna.",
        headshot_paths=[headshot],
        fullbody_paths=[fullbody],
        output_dir=output_dir,
    )
    characters.append(char1)
    print(f"   ✓ Registered: {char1.name} (ID: {char1.id})")

    # 4. Generate Storyboard
    print("\n[Step 2/4] 📝 Generating Storyboard...")
    prompt = args.prompt or "Uma viagem épica pelo espaço em busca de um cristal perdido."
    storyboard = await generate_storyboard_uc.execute(
        characters=characters,
        user_prompt=prompt,
        story_template=args.template or "Jornada do Herói",
    )
    print(f"   ✓ Storyboard Title: '{storyboard.title}'")
    print(f"   ✓ Total Scenes: {len(storyboard.scenes)} (Duration: {storyboard.total_duration_seconds:.1f}s)")
    if storyboard.cost_estimate:
        print(f"   ✓ Estimated Cost: ${storyboard.cost_estimate.total:.2f} {storyboard.cost_estimate.currency}")

    # 5. Generate Scene Assets
    print("\n[Step 3/4] 🎨 Generating Scene Assets & Animations...")
    def on_progress(current, total, message):
        print(f"   [{current}/{total}] {message}")

    storyboard = await generate_assets_uc.execute(
        storyboard=storyboard,
        characters=characters,
        output_dir=output_dir,
        on_progress=on_progress,
    )

    # 6. Export Manifest
    print("\n[Step 4/4] 📄 Exporting manifest.json for Remotion...")
    manifest_path = await export_manifest_uc.execute(storyboard, characters, "manifest.json")
    print(f"   ✓ Manifest successfully written to: {manifest_path}")

    print("\n" + "=" * 60)
    print("🎉 AI Vision Pipeline completed successfully!")
    print(f"👉 Next step: Render video with Remotion using {manifest_path}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Motion Quest AI & Vision Worker CLI")
    parser.add_argument("--prompt", type=str, default="Aventura épica na floresta mágica.", help="User story prompt")
    parser.add_argument("--template", type=str, default="Jornada do Herói", help="Story template style")
    parser.add_argument("--output", type=str, default="./output", help="Output directory")
    parser.add_argument("--mock", action="store_true", help="Run with mock AI adapters without making API calls")

    args = parser.parse_args()
    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
