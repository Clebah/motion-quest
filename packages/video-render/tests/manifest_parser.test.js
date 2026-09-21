import { test } from "node:test";
import assert from "node:assert";
import * as fs from "node:fs/promises";
import * as path from "node:path";
import { validateManifest } from "../dist/domain/entities/Manifest.js";

test("validateManifest parses valid manifest according to SPEC-002", () => {
  const valid = {
    version: "1.0",
    projectId: "proj_123",
    title: "Aventuras no Espaço",
    totalScenes: 18,
    totalDurationSeconds: 90.0,
    resolution: { width: 1080, height: 1920 },
    fps: 30,
    characters: [
      { id: "c1", name: "Pedro", description: "Jovem astronauta" }
    ],
    scenes: [
      {
        sceneNumber: 1,
        durationSeconds: 5.0,
        characterIds: ["c1"],
        visualPrompt: "Astronauta olhando a Terra",
        narrationText: "O início da viagem.",
        status: "completed"
      }
    ]
  };

  const parsed = validateManifest(valid);
  assert.strictEqual(parsed.projectId, "proj_123");
  assert.strictEqual(parsed.resolution.width, 1080);
  assert.strictEqual(parsed.resolution.height, 1920);
  assert.strictEqual(parsed.scenes.length, 1);
});

test("validateManifest rejects missing scenes or invalid resolutions", () => {
  assert.throws(() => {
    validateManifest({ projectId: "p", title: "t", scenes: [] });
  }, /scenes must be a non-empty array/);

  assert.throws(() => {
    validateManifest({ projectId: "p", title: "t", scenes: [{ sceneNumber: 1 }] });
  }, /missing valid resolution/);
});
