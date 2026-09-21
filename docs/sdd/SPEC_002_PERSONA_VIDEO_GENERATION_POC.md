# SPEC-002: Geração de Vídeos Animados Personalizados a partir de Fotos Reais e Roteiros

## Metadata
- **Status:** APPROVED
- **Author:** Motion Quest Product & Engineering Team
- **Created:** 2026-09-20
- **Revised:** 2026-09-21
- **Version:** 3.0.0

---

## 1. Visão Geral

Permitir que qualquer usuário crie vídeos animados personalizados de **1m30s a 2min** a partir de fotos reais (até 5 personagens) e roteiros customizados, com divisão automática em cenas, acompanhamento de progresso e download do `.mp4` final.

### Visão de Produto (Roadmap)

| Fase | Escopo | Interface |
| :--- | :--- | :--- |
| **PoC (esta spec)** | Pipeline CLI local, validação do fluxo completo | CLI Python + CLI Remotion |
| **MVP Cloud** | Deploy em cloud (GCP/AWS), API REST, website | FastAPI + Next.js (Web) |
| **Multiplataforma** | Apps nativos Android/iOS (como o Mimo) | React Native / Expo |

> A Arquitetura Hexagonal garante que o código de domínio e use cases da PoC seja **reutilizado integralmente** no MVP Cloud e nos apps móveis — apenas os adaptadores de entrada (CLI → API → Mobile SDK) e de infraestrutura (local → S3 → CDN) mudam.

---

## 2. Arquitetura Híbrida (Python + TypeScript)

```
┌───────────────────────────────────────────────────────────────────┐
│   Worker 1: packages/ai-vision  (Python 3.12+)                   │
├───────────────────────────────────────────────────────────────────┤
│ • LLM/Roteirização: Google Gemini (google-genai)                 │
│ • Geração de Imagem: Imagen 3 (Gemini API) + fal-client fallback│
│ • Visão: rembg + OpenCV + Pillow + MediaPipe                    │
│ • Animação I2V: Veo 2 (Gemini API) + fal-client fallback        │
│ • Roteirização: Funções Python + Pydantic (structured output)    │
│ • Entry PoC: CLI sequencial (pipeline.py)                        │
│ • Entry Prod: FastAPI + Celery/Temporal                          │
└──────────────────────────────┬────────────────────────────────────┘
                               │ manifest.json + assets
                               │ PoC: pasta local  │  Prod: S3 + Redis Queue
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│   Worker 2: packages/video-render  (TypeScript + Remotion)       │
├───────────────────────────────────────────────────────────────────┤
│ • Lê manifest.json e monta timeline de vídeo                     │
│ • Composições React: <Sequence>, <OffthreadVideo>, <Audio>       │
│ • Formato default: 1080x1920 (9:16 vertical)                    │
│ • Entry PoC: CLI Node                                            │
│ • Entry Prod: @remotion/lambda (AWS) ou Cloud Run                │
└───────────────────────────────────────────────────────────────────┘
```

### Transição PoC → Produção (Zero Refatoração de Domínio)

| Camada | PoC | Produção |
| :--- | :--- | :--- |
| Storage | Pasta local `output/` | AWS S3 / GCS |
| Queue | Chamada direta (sequencial) | Redis + BullMQ |
| Inbound API | CLI Python | FastAPI + WebSocket (progresso) |
| Frontend Web | — | Next.js |
| Mobile | — | React Native / Expo |
| Face Detection | MediaPipe (~5MB) | InsightFace (embeddings de alta precisão) |
| Roteirização | Funções + Pydantic | LangGraph StateGraph |
| Renderização | `@remotion/renderer` local | `@remotion/lambda` (AWS) |
| CDN / Entrega | Arquivo local | CloudFront / Cloud CDN |

---

## 3. Requisitos Funcionais

### RF-01: Cadastro do Elenco (Personagens)
- Até 5 personagens por projeto.
- Perfil: nome + descrição de estilo/características.
- Fotos: 1 a 5 headshots + 1 a 5 full-body por personagem.
- Pré-processamento automático:
  - Remoção de fundo (`rembg`).
  - Crop facial inteligente (`OpenCV` + `MediaPipe`).
  - Colagens de referência para consistência visual.
  - Cache de embeddings (processados uma vez, reutilizados em todas as cenas).

### RF-02: Definição da História (Roteiro e Cenas)
- Seleção de quais personagens participam.
- Modo modelo pronto (Jornada do Herói, Comédia, Aventura) ou texto livre.
- Divisão automática via Google Gemini com structured output (Pydantic):
  - **Range recomendado:** 18 a 24 cenas (soft constraint, warning ao usuário).
  - **Range permitido:** 12 a 30 cenas (hard constraint).
  - **Duração por cena:** 3s a 7s (default 5s).
  - **Duração total:** 60s a 150s.
- Revisão e edição pelo usuário antes de produzir.

### RF-03: Fabricação do Vídeo (Pipeline)
- Geração visual consistente por cena (Imagen 3 / fal-client fallback).
- Animação I2V de cada cena (Veo 2 / fal-client fallback).
- **Retry com backoff exponencial** (3 tentativas por cena).
- **Fallback de provedor** automático (Gemini API → fal-client).
- **Processamento parcial:** progresso salvo; retomável em caso de falha.
- Progresso transparente em tempo real.
- Estimativa de custo antes da execução (`EstimateCostUseCase`).

### RF-04: Entrega e Consumo
- Player de pré-visualização integrado (Web/Mobile na produção).
- Download `.mp4` (9:16 vertical por default, 16:9 horizontal opcional).

---

## 4. Stack Tecnológica — Matriz de Decisão

| Responsabilidade | Tecnologia | Justificativa |
| :--- | :--- | :--- |
| LLM / Roteirização | **Google Gemini** (`google-genai`) | Mesma chave do Mimo. Structured output nativo com `response_schema`. |
| Geração de Imagem | **Imagen 3** (Gemini API) + **fal-client** fallback | Uma chave, um billing. Fallback para FLUX.1/SDXL se qualidade insuficiente. |
| Animação I2V | **Veo 2** (Gemini API) + **fal-client** fallback (Kling/Luma) | Mesma chave. Fallback se Veo 2 não atender qualidade ou duração. |
| Visão / Pré-processamento | **rembg** + **OpenCV** + **Pillow** + **MediaPipe** | Ecossistema Python maduro. MediaPipe leve para PoC, InsightFace para prod. |
| Tipagem / Validação | **Pydantic v2** | Garante output estruturado da LLM sem falha de JSON. |
| Composição de Vídeo | **Remotion** (`remotion`, `react`, `react-dom`) | Timeline programática com componentes React. |
| Renderização | **`@remotion/renderer`** (PoC) / **`@remotion/lambda`** (Prod) | Headless `.mp4`. Lambda escala horizontalmente. |
| Orquestração (Prod) | **Makefile** (PoC) / **Celery ou Temporal** (Prod) | PoC não precisa de orquestrador; prod escala com workers. |

---

## 5. Contrato: `manifest.json`

Output do Worker Python → Input do Worker Remotion:

```json
{
  "version": "1.0",
  "projectId": "proj_abc123",
  "title": "Aventuras de Pedro e Ana",
  "resolution": { "width": 1080, "height": 1920 },
  "fps": 30,
  "characters": [
    {
      "id": "char_1",
      "name": "Pedro",
      "description": "Homem jovem, alegre, casaco azul",
      "headshotPath": "chars/char_1_face.png",
      "fullbodyPath": "chars/char_1_body.png"
    }
  ],
  "scenes": [
    {
      "sceneNumber": 1,
      "durationSeconds": 5,
      "characterIds": ["char_1"],
      "visualPrompt": "Pedro acenando na praia ensolarada",
      "narrationText": "Tudo começou em um dia ensolarado...",
      "imagePath": "scenes/scene_01.png",
      "clipPath": "clips/scene_01.mp4",
      "status": "completed"
    }
  ],
  "audio": {
    "backgroundMusicPath": "audio/bg_music.mp3",
    "volume": 0.3
  },
  "estimatedCost": {
    "currency": "USD",
    "imageGeneration": 1.20,
    "videoAnimation": 3.40,
    "total": 4.60
  }
}
```

---

## 6. Gates de Qualidade (Harness SDD)

| Gate | Validação | Tipo |
| :--- | :--- | :--- |
| **Elenco** | 1-5 fotos rosto + 1-5 fotos corpo por personagem | Hard |
| **Duração** | 12-30 cenas; 3-7s por cena; total 60s-150s | Hard |
| **Renderização** | `.mp4` mínimo 1080x1920 | Hard |
| **Testes Python** | `pytest packages/ai-vision/tests/` | Automated |
| **Testes Remotion** | `npm test --workspace=packages/video-render` | Automated |
| **Manifest válido** | Schema JSON validado antes de enviar ao Remotion | Hard |

---

## 7. Configuração do Gemini

Chave API Google Gemini **compartilhada com o projeto Mimo** (`https://github.com/Clebah/mimo`).
Variável de ambiente `GEMINI_API_KEY` carregada via `.env`.
