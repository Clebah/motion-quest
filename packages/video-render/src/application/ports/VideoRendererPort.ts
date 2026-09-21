import { VideoManifest } from "../../domain/entities/Manifest.js";

export interface VideoRendererPort {
  renderVideo(manifest: VideoManifest, outputPath: string): Promise<string>;
}
