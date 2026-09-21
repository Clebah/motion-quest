# 🤖 AGENTS.md — Diretrizes e Contexto para Agentes Autônomos (Antigravity & Claude)

> Este arquivo é o ponto de entrada primário para agentes de inteligência artificial (Google Antigravity, Claude Code, Cursor, Copilot) atuando no projeto **Motion Quest**.
> **Nota:** Este arquivo é espelhado via link simbólico para `CLAUDE.md` e `GEMINI.md`. Qualquer alteração realizada aqui reflete automaticamente em todos os ambientes.

---

## 🧭 Índice da Documentação do Projeto

Antes de realizar modificações ou propor mudanças arquiteturais, consulte a documentação especializada:

- 📚 [Índice Geral da Documentação](docs/INDEX.md)
- 🏛️ [Arquitetura Hexagonal & Diagramas (ARCHITECTURE.md)](docs/architecture/ARCHITECTURE.md)
- 📄 [Contrato de Dados do manifest.json (CONTRACTS.md)](docs/architecture/CONTRACTS.md)
- 🧭 [Decisões Arquiteturais / ADRs (DECISIONS.md)](docs/architecture/DECISIONS.md)
- 🛠️ [Guia de Desenvolvimento & Makefile (DEVELOPMENT.md)](docs/guides/DEVELOPMENT.md)
- 📋 [Especificação Ativa (SPEC-002 v3)](docs/sdd/SPEC_002_PERSONA_VIDEO_GENERATION_POC.md)

---

## 🎯 Visão do Produto e Objetivo Atual

O **Motion Quest** gera vídeos animados personalizados (1m30s a 2min) a partir de fotos de pessoas reais e roteiros customizados.
- **Fase Atual:** PoC local funcional validando o pipeline completo de ponta a ponta sem acoplamento de infraestrutura.
- **Próximas Fases:** MVP Cloud (FastAPI + S3 + Redis + Next.js) e Multiplataforma (React Native / Expo para Android e iOS, reaproveitando a mesma abordagem adotada no projeto `mimo`).

---

## 🏛️ Regras Arquiteturais Invioláveis

1. **Arquitetura Hexagonal Estrita:**
   - **Camada de Domínio (`domain`):** Entidades puras, regras de negócio e validações. NUNCA importe bibliotecas de infraestrutura, SDKs externos ou frameworks web no domínio.
   - **Camada de Aplicação (`application`):** Casos de Uso e Portas (`ports/inbound` e `ports/outbound`). Toda comunicação com o mundo externo é mediada por interfaces/ports abstratas.
   - **Camada de Adaptadores (`adapters`):** Implementações concretas de portas (Gemini, Remotion, rembg, OpenCV, Storage local ou S3).

2. **Divisão de Responsabilidades dos Workers:**
   - **Worker 1 (`packages/ai-vision`):** Python puro. Responsável exclusivo por visão computacional, extração facial, roteirização via LLM, geração de imagem e animação de cenas. Entrega sempre o contrato `manifest.json` com assets.
   - **Worker 2 (`packages/video-render`):** TypeScript + Remotion. Responsável exclusivo por consumir o `manifest.json`, validar o schema e renderizar o vídeo programático com React.

3. **Chave de API do Gemini:**
   - Utiliza a mesma chave de API do projeto `mimo` (`GEMINI_API_KEY`).
   - Carregada via variável de ambiente ou arquivo `packages/ai-vision/.env`.

4. **Zero Refatoração de Domínio:**
   - A transição da PoC para Cloud deve ocorrer apenas substituindo ou adicionando adaptadores (ex: `LocalStorageAdapter` ➔ `S3StorageAdapter`), sem alterar Casos de Uso ou Entidades.

---

## ⚡ Comandos Essenciais para o Agente

Todos os comandos devem ser disparados a partir da raiz do monorepo via `make`:

```bash
# Executa a bateria de testes automatizados de ambos os workers (Gate SDD)
make test

# Executa testes unitários específicos do Worker Python
make test-ai

# Executa testes unitários específicos do Worker Node/Remotion
make test-video

# Executa o pipeline de IA em modo mock offline (gera manifest.json)
make pipeline-mock

# Renderiza o vídeo final a partir do manifest.json gerado
make render

# Executa todo o fluxo de ponta a ponta (testes + pipeline + render)
make all
```

---

## 📐 Padrões de Código e Convenções

- **Python (`ai-vision`):**
  - Tipagem estrita com type hints (`from __future__ import annotations`).
  - Uso de `dataclasses` no domínio e `pydantic` nos schemas de LLM.
  - Testes com `unittest` e `pytest`.
  - Tratamento resiliente de imports externos com fallbacks limpos.
- **TypeScript (`video-render`):**
  - Módulos ES (`"type": "module"`).
  - TypeScript estrito (`strict: true`).
  - Validação explícita de contratos com funções como `validateManifest()`.
  - Componentes Remotion desacoplados com tipagem clara de props.

---

## ✅ Checklist de Entrega para Agentes

Ao concluir qualquer tarefa ou implementação no repositório:
- [ ] O código respeita a separação hexagonal (Domínio -> Aplicação -> Adaptadores)?
- [ ] Os testes de ambos os workers foram executados e passaram com `make test`?
- [ ] Nenhuma credencial sensível ou chave de API foi commitada no repositório?
- [ ] A documentação ou especificação correspondente em `docs/` foi atualizada?
- [ ] O contrato `manifest.json` foi preservado sem quebras de compatibilidade?
