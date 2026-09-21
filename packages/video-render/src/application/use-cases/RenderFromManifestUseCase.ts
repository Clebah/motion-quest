import * as fs from "node:fs/promises";
import { validateManifest, VideoManifest } from "../../domain/entities/Manifest.js";
import { VideoRendererPort } from "../ports/VideoRendererPort.js";

export class RenderFromManifestUseCase {
  constructor(private readonly renderer: VideoRendererPort) {}

  async execute(manifestPath: string, outputPath: string): Promise<string> {
    const rawContent = await fs.readFile(manifestPath, "utf-8");
    const parsed = JSON.parse(rawContent);
    const manifest = validateManifest(parsed);

    console.log(`🎬 Loaded Manifest: "${manifest.title}" (ID: ${manifest.projectId})`);
    console.log(`⏱️  Scenes: ${manifest.scenes.length} | Resolution: ${manifest.resolution.width}x${manifest.resolution.height}`);

    const resultPath = await this.renderer.renderVideo(manifest, outputPath);
    return resultPath;
  }
}
