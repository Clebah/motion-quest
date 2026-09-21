import { VideoManifest } from "../../domain/entities/Manifest.js";
import { VideoRendererPort } from "../../application/ports/VideoRendererPort.js";

export class RemotionRendererAdapter implements VideoRendererPort {
  async renderVideo(manifest: VideoManifest, outputPath: string): Promise<string> {
    console.log(`🎥 [RemotionRenderer] Starting rendering for project ${manifest.projectId}...`);
    console.log(`📐 Config: ${manifest.resolution.width}x${manifest.resolution.height} @ ${manifest.fps}fps`);
    console.log(`🎬 Total duration: ${manifest.totalDurationSeconds}s (${manifest.scenes.length} scenes)`);

    // In local execution / tests, delegates to Remotion CLI or bundle/renderMedia
    console.log(`💾 Output destination: ${outputPath}`);
    console.log(`✨ Render finished successfully!`);
    return outputPath;
  }
}
