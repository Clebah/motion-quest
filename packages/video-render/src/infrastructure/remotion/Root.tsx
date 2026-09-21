import React from "react";
import { Composition } from "remotion";
import { PersonaStoryComposition } from "./compositions/PersonaStoryComposition.js";
import { VideoManifest } from "../../domain/entities/Manifest.js";

// Default fallback manifest for development preview
const defaultManifest: VideoManifest = {
  version: "1.0",
  projectId: "preview_demo",
  title: "Aventura Épica no Espaço",
  totalScenes: 18,
  totalDurationSeconds: 90.0,
  resolution: {
    width: 1080,
    height: 1920,
  },
  fps: 30,
  characters: [
    {
      id: "char_1",
      name: "Pedro",
      description: "Jovem aventureiro",
    },
  ],
  scenes: [
    {
      sceneNumber: 1,
      durationSeconds: 5.0,
      characterIds: ["char_1"],
      visualPrompt: "Pedro observando as estrelas na cabine da nave",
      narrationText: "Tudo começou quando um sinal misterioso cruzou os céus.",
      status: "completed",
    },
    {
      sceneNumber: 2,
      durationSeconds: 5.0,
      characterIds: ["char_1"],
      visualPrompt: "Nave acelerando em direção a uma nebulosa cósmica",
      narrationText: "O chamado para a maior jornada de sua vida não podia esperar.",
      status: "completed",
    },
  ],
};

export const Root: React.FC = () => {
  const fps = defaultManifest.fps;
  const durationInFrames = Math.round(defaultManifest.totalDurationSeconds * fps);

  return (
    <>
      <Composition
        id="PersonaStory"
        component={PersonaStoryComposition as unknown as React.ComponentType<Record<string, unknown>>}
        durationInFrames={durationInFrames}
        fps={fps}
        width={defaultManifest.resolution.width}
        height={defaultManifest.resolution.height}
        defaultProps={{
          manifest: defaultManifest,
        }}
      />
    </>
  );
};
