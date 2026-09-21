# 📄 Contrato de Dados: manifest.json — Motion Quest

Este documento formaliza a especificação da interface entre o **Worker 1 (IA & Visão)** e o **Worker 2 (Video Render / Remotion)**.

---

## 1. Visão Geral do Contrato

O `manifest.json` é o artefato gerado ao final da execução do pipeline de IA que descreve integralmente o projeto de vídeo: elenco, metadados de resolução, timeline de cenas, caminhos de mídia (imagens e clipes de vídeo) e trilha sonora.

---

## 2. Schema JSON de Referência (v1.0)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "VideoManifest",
  "type": "object",
  "required": [
    "version",
    "projectId",
    "title",
    "totalScenes",
    "totalDurationSeconds",
    "resolution",
    "fps",
    "characters",
    "scenes"
  ],
  "properties": {
    "version": { "type": "string", "example": "1.0" },
    "projectId": { "type": "string", "example": "proj_abc123" },
    "title": { "type": "string", "example": "Aventuras no Espaço" },
    "totalScenes": { "type": "integer", "minimum": 12, "maximum": 30 },
    "totalDurationSeconds": { "type": "number", "minimum": 60, "maximum": 150 },
    "resolution": {
      "type": "object",
      "required": ["width", "height"],
      "properties": {
        "width": { "type": "integer", "example": 1080 },
        "height": { "type": "integer", "example": 1920 }
      }
    },
    "fps": { "type": "integer", "example": 30 },
    "characters": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "description"],
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "description": { "type": "string" },
          "headshotPath": { "type": ["string", "null"] },
          "fullbodyPath": { "type": ["string", "null"] }
        }
      }
    },
    "scenes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "sceneNumber",
          "durationSeconds",
          "characterIds",
          "visualPrompt",
          "narrationText",
          "status"
        ],
        "properties": {
          "sceneNumber": { "type": "integer" },
          "durationSeconds": { "type": "number", "minimum": 3.0, "maximum": 7.0 },
          "characterIds": { "type": "array", "items": { "type": "string" } },
          "visualPrompt": { "type": "string" },
          "narrationText": { "type": "string" },
          "imagePath": { "type": ["string", "null"] },
          "clipPath": { "type": ["string", "null"] },
          "status": {
            "type": "string",
            "enum": ["pending", "image_generated", "clip_generated", "completed", "failed"]
          }
        }
      }
    },
    "audio": {
      "type": "object",
      "properties": {
        "backgroundMusicPath": { "type": ["string", "null"] },
        "volume": { "type": "number", "default": 0.3 }
      }
    },
    "estimatedCost": {
      "type": "object",
      "properties": {
        "currency": { "type": "string", "example": "USD" },
        "imageGeneration": { "type": "number" },
        "videoAnimation": { "type": "number" },
        "total": { "type": "number" }
      }
    }
  }
}
```

---

## 3. Validação Cruzada

- **No Worker Python (`ai-vision`):** Gerado por [`ExportManifestUseCase.py`](file:///Users/cleber/Documents/dev/antigravity/tendencias/motion-quest/packages/ai-vision/src/application/use_cases/export_manifest.py).
- **No Worker Node/TS (`video-render`):** Validado por [`validateManifest()` em Manifest.ts](file:///Users/cleber/Documents/dev/antigravity/tendencias/motion-quest/packages/video-render/src/domain/entities/Manifest.ts).
