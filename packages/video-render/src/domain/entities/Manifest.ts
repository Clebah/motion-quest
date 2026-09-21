/**
 * Domain entity & contract: Video Manifest consumed by Remotion renderer.
 * Strictly adheres to SPEC-002 v3 contract emitted by packages/ai-vision.
 */

export interface CharacterManifest {
  id: string;
  name: string;
  description: string;
  headshotPath?: string | null;
  fullbodyPath?: string | null;
}

export interface SceneManifest {
  sceneNumber: number;
  durationSeconds: number;
  characterIds: string[];
  visualPrompt: string;
  narrationText: string;
  imagePath?: string | null;
  clipPath?: string | null;
  status: "pending" | "image_generated" | "clip_generated" | "completed" | "failed";
}

export interface AudioManifest {
  backgroundMusicPath?: string | null;
  volume: number;
}

export interface VideoManifest {
  version: string;
  projectId: string;
  title: string;
  totalScenes: number;
  totalDurationSeconds: number;
  resolution: {
    width: number;
    height: number;
  };
  fps: number;
  characters: CharacterManifest[];
  scenes: SceneManifest[];
  audio?: AudioManifest;
  estimatedCost?: {
    currency: string;
    imageGeneration: number;
    videoAnimation: number;
    total: number;
  };
}

export function validateManifest(data: unknown): VideoManifest {
  const m = data as Partial<VideoManifest>;
  if (!m.projectId || !m.title) {
    throw new Error("Invalid manifest: missing projectId or title");
  }
  if (!m.scenes || !Array.isArray(m.scenes) || m.scenes.length === 0) {
    throw new Error("Invalid manifest: scenes must be a non-empty array");
  }
  if (!m.resolution || !m.resolution.width || !m.resolution.height) {
    throw new Error("Invalid manifest: missing valid resolution");
  }
  return data as VideoManifest;
}
