import { RenderFromManifestUseCase } from "../../application/use-cases/RenderFromManifestUseCase.js";
import { RemotionRendererAdapter } from "../../adapters/outbound/RemotionRendererAdapter.js";

async function main() {
  const args = process.argv.slice(2);
  let manifestPath = "";
  let outputPath = "out/video.mp4";

  for (const arg of args) {
    if (arg.startsWith("--manifest=")) {
      manifestPath = arg.replace("--manifest=", "");
    } else if (arg.startsWith("--out=")) {
      outputPath = arg.replace("--out=", "");
    }
  }

  if (!manifestPath) {
    console.error("❌ Error: Missing --manifest argument.");
    console.error("Usage: npm start -- --manifest=path/to/manifest.json [--out=out/video.mp4]");
    process.exit(1);
  }

  const renderer = new RemotionRendererAdapter();
  const useCase = new RenderFromManifestUseCase(renderer);

  try {
    const result = await useCase.execute(manifestPath, outputPath);
    console.log(`\n🎉 Render finished! Video file ready at: ${result}`);
  } catch (err) {
    console.error("❌ Error during render:", err);
    process.exit(1);
  }
}

main();
