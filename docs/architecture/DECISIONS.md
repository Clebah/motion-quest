# 🧭 Registros de Decisões de Arquitetura (ADRs) — Motion Quest

Este documento registra as principais decisões arquiteturais tomadas no projeto, suas justificativas e implicações técnicas.

---

## ADR-001: Separação de Workers Híbrida (Python para IA + TypeScript para Remotion)
- **Status:** Aprovado
- **Contexto:** Inicialmente foi cogitado monorepo em TypeScript único. Porém, visão computacional (`rembg`, OpenCV, BiRefNet, ONNX, MediaPipe/InsightFace) e ecossistemas de difusão de IA são nativos em CPython. Remotion, por sua vez, é React/Node.js puro.
- **Decisão:** Separar o sistema em 2 workers especializados: `packages/ai-vision` em Python e `packages/video-render` em Node.js/Remotion.
- **Consequência:** Máximo aproveitamento do melhor ecossistema para cada domínio, comunicando-se via contrato JSON padronizado.

---

## ADR-002: Descarte de Celery + Redis + S3 na PoC em favor de Pipeline Sequencial Local
- **Status:** Aprovado
- **Contexto:** Adicionar Redis, Celery e S3 exigiria subir múltiplos daemons locais para rodar a PoC, elevando dramaticamente o custo cognitivo e fragilidade de setup.
- **Decisão:** Implementar a PoC como pipeline sequencial CLI que persiste em pasta local (`output/`) e gera o `manifest.json`.
- **Consequência:** A Arquitetura Hexagonal garante que o adaptador de storage e de mensageria seja trocado por S3/Redis na migração para cloud sem alterar nenhuma linha de domínio ou de use cases.

---

## ADR-003: Consolidação no Provedor Google Gemini (mesma chave do projeto Mimo)
- **Status:** Aprovado
- **Contexto:** Usar múltiplos provedores (OpenAI para texto, fal-client para imagem, Runway para vídeo) criaria fragmentação de chaves e billing.
- **Decisão:** Consolidar a stack primária no Google Cloud: Gemini 2.0 para roteiro e structured output, Imagen 3 para geração de imagens e Veo 2 para animação I2V, reaproveitando a mesma credencial configurada no projeto Mimo.
- **Consequência:** Setup unificado, redução de custos e integração facilitada. Provedores alternativos (fal-client, Replicate) permanecem como adaptadores de fallback.

---

## ADR-004: Formato Padrão Vertical 1080x1920 (9:16)
- **Status:** Aprovado
- **Contexto:** A especificação original sugeria formatos indefinidos entre horizontal e vertical.
- **Decisão:** Definir 1080x1920 (9:16 vertical) como padrão nativo, otimizado para vídeos em redes sociais (Shorts, Reels, TikTok) e telas móveis (Android e iOS).
- **Consequência:** Coerência visual e alinhamento direto com a visão de apps móveis futuros.

---

## ADR-005: Flexibilização das Restrições de Cena (Regras Duras vs Avisos)
- **Status:** Aprovado
- **Contexto:** A regra inicial de estritamente 18-24 cenas bloqueava histórias que naturalmente requeriam 15 ou 26 cenas.
- **Decisão:** Definir 12 a 30 cenas (60s a 150s) como limite duro (bloqueante) e 18 a 24 cenas como recomendação suave (aviso não-bloqueante).
- **Consequência:** Maior flexibilidade narrativa sem comprometer os tempos de produção e qualidade.
