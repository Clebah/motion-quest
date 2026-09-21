# 🛠️ Guia de Desenvolvimento — Motion Quest

Este guia orienta o setup local, execução de testes, comandos operacionais e boas práticas de desenvolvimento no monorepo.

---

## 1. Pré-requisitos
- **Node.js**: >= 20.x
- **Python**: >= 3.9 (recomendado 3.12)
- **Make**: Padrão em sistemas Unix / macOS

---

## 2. Comandos do Makefile

O projeto conta com automação centralizada via `Makefile` na raiz:

| Comando | Descrição |
| :--- | :--- |
| `make help` | Exibe a lista de comandos disponíveis |
| `make test` | Executa a bateria de testes automatizados de ambos os workers |
| `make test-ai` | Executa apenas os testes unitários do Worker de IA (Python) |
| `make test-video` | Executa apenas os testes unitários do Worker de Vídeo (Remotion/Node) |
| `make pipeline-mock` | Executa o pipeline de IA em modo mock e gera o `manifest.json` |
| `make render` | Executa a renderização do vídeo consumindo o `manifest.json` |
| `make all` | Executa o fluxo completo: testes + pipeline mock + renderização |

---

## 3. Configuração de Variáveis de Ambiente

Crie ou edite o arquivo `packages/ai-vision/.env`:
```env
# Mesma chave Google Gemini utilizada no projeto Mimo
GEMINI_API_KEY=sua_chave_aqui

# Opcional (fallback para provedores de difusão de terceiros)
FAL_KEY=sua_chave_fal_se_necessario
```

---

## 4. Estrutura de Diretórios dos Pacotes

```
motion-quest/
├── Makefile                     # Orquestração central de build e testes
├── package.json                 # Monorepo workspaces
├── .tlc/harness/config.json     # Governança de testes e SDD
├── docs/                        # Base de conhecimento e documentação
│   ├── INDEX.md
│   ├── architecture/
│   │   ├── ARCHITECTURE.md
│   │   ├── CONTRACTS.md
│   │   └── DECISIONS.md
│   ├── guides/
│   │   └── DEVELOPMENT.md
│   └── sdd/
│       ├── SPEC_001_MOTION_QUEST_HEXAGONAL.md
│       └── SPEC_002_PERSONA_VIDEO_GENERATION_POC.md
├── packages/
│   ├── ai-vision/               # Worker Python (IA, Visão e Roteiro)
│   └── video-render/            # Worker TypeScript / Remotion
└── AGENTS.md                    # Manual consolidado para agentes autônomos
```
