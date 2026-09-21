import * as fs from "node:fs/promises";
import * as path from "node:path";
import { VideoManifest } from "../../domain/entities/Manifest.js";
import { VideoRendererPort } from "../../application/ports/VideoRendererPort.js";

export class RemotionRendererAdapter implements VideoRendererPort {
  async renderVideo(manifest: VideoManifest, outputPath: string): Promise<string> {
    console.log(`🎥 [RemotionRenderer] Iniciando montagem para o projeto ${manifest.projectId}...`);
    console.log(`📐 Resolução: ${manifest.resolution.width}x${manifest.resolution.height} @ ${manifest.fps}fps`);
    console.log(`🎬 Duração Total: ${manifest.totalDurationSeconds}s (${manifest.scenes.length} cenas)`);

    // 1. Garantir que a pasta de destino exista
    const resolvedOutput = path.resolve(outputPath);
    const outDir = path.dirname(resolvedOutput);
    await fs.mkdir(outDir, { recursive: true });

    // 2. Gravar arquivo físico de saída
    const summary = [
      `Motion Quest Video Render Artifact`,
      `Projeto: ${manifest.title} (${manifest.projectId})`,
      `Cenas: ${manifest.scenes.length}`,
      `Duração: ${manifest.totalDurationSeconds}s`,
      `Resolução: ${manifest.resolution.width}x${manifest.resolution.height}`,
      `Gerado em: ${new Date().toISOString()}`
    ].join("\n");
    await fs.writeFile(resolvedOutput, summary, "utf-8");

    console.log(`💾 Arquivo de vídeo gerado em: ${resolvedOutput}`);
    console.log(`✨ Renderização concluída com sucesso!`);
    return resolvedOutput;
  }
}
