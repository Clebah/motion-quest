import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  OffthreadVideo,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { SceneManifest, VideoManifest } from "../../../domain/entities/Manifest.js";

interface SceneViewProps {
  scene: SceneManifest;
  manifest: VideoManifest;
}

const SceneView: React.FC<SceneViewProps> = ({ scene, manifest }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Gentle Ken-Burns zoom effect
  const scale = interpolate(frame, [0, durationInFrames], [1, 1.08], {
    extrapolateRight: "clamp",
  });

  // Fade in and out
  const opacity = interpolate(
    frame,
    [0, 15, durationInFrames - 15, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Subtitle slide up
  const textTranslateY = interpolate(frame, [0, 20], [30, 0], {
    extrapolateRight: "clamp",
  });

  // Find character names for this scene
  const sceneCharacters = manifest.characters.filter((c) =>
    scene.characterIds.includes(c.id)
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#090d16",
        opacity,
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* Visual Asset: Video or Still Image */}
      <AbsoluteFill style={{ overflow: "hidden" }}>
        {scene.clipPath && scene.clipPath.endsWith(".mp4") ? (
          <OffthreadVideo
            src={scene.clipPath}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${scale})`,
            }}
          />
        ) : scene.imagePath ? (
          <Img
            src={scene.imagePath}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${scale})`,
            }}
          />
        ) : (
          <div
            style={{
              width: "100%",
              height: "100%",
              background: "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#94a3b8",
            }}
          >
            <h3>Cena {scene.sceneNumber}</h3>
          </div>
        )}
      </AbsoluteFill>

      {/* Cinematic Vignette Overlay */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0.4) 65%, rgba(0,0,0,0.92) 100%)",
        }}
      />

      {/* Top Header: Scene Number & Cast Pills */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 40,
          right: 40,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span
          style={{
            fontSize: 22,
            fontWeight: 700,
            letterSpacing: 2,
            textTransform: "uppercase",
            color: "#f8fafc",
            background: "rgba(15, 23, 42, 0.75)",
            backdropFilter: "blur(12px)",
            padding: "8px 20px",
            borderRadius: 30,
            border: "1px solid rgba(255,255,255,0.15)",
          }}
        >
          Cena {scene.sceneNumber} / {manifest.scenes.length}
        </span>

        {sceneCharacters.length > 0 && (
          <div style={{ display: "flex", gap: 10 }}>
            {sceneCharacters.map((c) => (
              <span
                key={c.id}
                style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: "#38bdf8",
                  background: "rgba(15, 23, 42, 0.75)",
                  backdropFilter: "blur(12px)",
                  padding: "6px 16px",
                  borderRadius: 20,
                  border: "1px solid rgba(56, 189, 248, 0.3)",
                }}
              >
                👤 {c.name}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Subtitle / Narration Box */}
      <div
        style={{
          position: "absolute",
          bottom: 120,
          left: 48,
          right: 48,
          transform: `translateY(${textTranslateY}px)`,
        }}
      >
        <div
          style={{
            background: "rgba(10, 15, 29, 0.85)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            borderRadius: 24,
            padding: "24px 32px",
            boxShadow: "0 20px 40px rgba(0, 0, 0, 0.6)",
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 32,
              lineHeight: 1.4,
              fontWeight: 600,
              color: "#ffffff",
              textAlign: "center",
              textShadow: "0 2px 10px rgba(0,0,0,0.5)",
            }}
          >
            {scene.narrationText}
          </p>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const PersonaStoryComposition: React.FC<{ manifest: VideoManifest }> = ({
  manifest,
}) => {
  const fps = manifest.fps || 30;
  let currentFrameOffset = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {manifest.scenes.map((scene) => {
        const sceneDurationFrames = Math.round(scene.durationSeconds * fps);
        const from = currentFrameOffset;
        currentFrameOffset += sceneDurationFrames;

        return (
          <Sequence
            key={scene.sceneNumber}
            from={from}
            durationInFrames={sceneDurationFrames}
          >
            <SceneView scene={scene} manifest={manifest} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
