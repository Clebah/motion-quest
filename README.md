# 🎬 Motion Quest

> Plataforma de geração de vídeos animados personalizados (1m30s a 2min) a partir de fotos reais e roteiros customizados, construída com **Arquitetura Híbrida Hexagonal (Python + TypeScript / Remotion)** e orientada a especificações (**Harness SDD / SPEC-002 v3**).

---

## 🏛️ Arquitetura Híbrida dos Workers

```
┌──────────────────────────────────────────────────────────────────┐
│   Worker 1: packages/ai-vision (Python 3.9+)                    │
├──────────────────────────────────────────────────────────────────┤
│ • Roteirização: Google Gemini (mesma chave do projeto Mimo)     │
│ • Geração Visual: Google Imagen 3 (via Gemini API)              │
│ • Animação I2V: Google Veo 2 (via Gemini API)                   │
│ • Visão Computacional: rembg + OpenCV + MediaPipe               │
│ • Domínio & Portas: Arquitetura Hexagonal pura                  │
│ • Saída: manifest.json + assets das cenas                       │
└─────────────────────────────┬────────────────────────────────────┘
                              │ manifest.json
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│   Worker 2: packages/video-render (TypeScript + Remotion)        │
├──────────────────────────────────────────────────────────────────┤
│ • Consumo de Contrato: Validador de manifest.json               │
│ • Renderização Programática: Remotion + React                   │
│ • Visual Cinematográfico: Efeito Ken-Burns, selo de personagens, │
│   legendas/narração estilizadas e formato 1080x1920 (9:16)       │
│ • Saída: Arquivo final .mp4                                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Como Executar

### 1. Testes Automatizados (Ambos os Workers)
```bash
make test
```

### 2. Executar o Pipeline Completo (Mock / Offline)
Executa os testes, roda o pipeline de IA gerando 18 cenas de 5s (90s total), exporta o `manifest.json` e orquestra a renderização no worker de vídeo:
```bash
make all
```

### 3. Executar o Pipeline de IA (Modo Live com Gemini)
1. Configure sua chave no arquivo `packages/ai-vision/.env`:
   ```env
   GEMINI_API_KEY=sua_chave_do_mimo_aqui
   ```
2. Execute o pipeline:
   ```bash
   cd packages/ai-vision
   python3 -m src.adapters.inbound.cli.pipeline --prompt "Aventura épica no espaço" --output ./output/meu_video
   ```
3. Renderize o vídeo com o Remotion:
   ```bash
   cd packages/video-render
   node dist/adapters/inbound/cli/index.js --manifest=../ai-vision/output/meu_video/manifest.json --out=out/final.mp4
   ```

---

## 📋 Especificações e Governança SDD

Este projeto adota o framework **TLC Harness Toolkit** (`.tlc/harness/config.json`):
- [SPEC-001: Arquitetura Hexagonal e Estrutura Monorepo](docs/sdd/SPEC_001_MOTION_QUEST_HEXAGONAL.md)
- [SPEC-002: Geração de Vídeos Animados Personalizados (PoC)](docs/sdd/SPEC_002_PERSONA_VIDEO_GENERATION_POC.md)

---

## 📱 Roadmap: Cloud & Multiplataforma

A Arquitetura Hexagonal foi desenhada para **Zero Refatoração de Domínio**:
- **PoC:** Execução local via CLI e arquivos em disco.
- **MVP Cloud:** Deploy no Cloud Run / AWS Lambda (`@remotion/lambda`), bucket S3 e API FastAPI para o website.
- **Mobile:** Apps Android e iOS via React Native / Expo (mesma estratégia multiplataforma do projeto Mimo).
