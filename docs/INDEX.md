# 📚 Índice da Base de Conhecimento — Motion Quest

Bem-vindo à documentação oficial do projeto **Motion Quest**. Abaixo está o índice categorizado de todos os documentos técnicos, especificações e guias disponíveis.

---

## 🏛️ Arquitetura & Design
- [Visão Geral da Arquitetura (ARCHITECTURE.md)](architecture/ARCHITECTURE.md): Diagramas de alto nível, responsabilidades dos workers, fluxo de execução e estratégia de evolução para nuvem e mobile.
- [Contrato de Dados do Manifest (CONTRACTS.md)](architecture/CONTRACTS.md): Especificação completa do schema JSON que interliga o worker de IA ao worker de vídeo.
- [Registro de Decisões de Arquitetura (DECISIONS.md)](architecture/DECISIONS.md): ADRs documentando escolhas tecnológicas, simplificações da PoC e formato de mídia.

---

## 📋 Especificações de Produto (SDD)
- [SPEC-001: Estrutura Monorepo e Arquitetura Hexagonal](sdd/SPEC_001_MOTION_QUEST_HEXAGONAL.md): Especificação fundacional das fronteiras e camadas.
- [SPEC-002: Geração de Vídeos Animados Personalizados (PoC)](sdd/SPEC_002_PERSONA_VIDEO_GENERATION_POC.md): Especificação implementada de negócio e técnica para a PoC do gerador de vídeos.
- [SPEC-003: Interface Web Local para Criação de Personagens e Roteiros](sdd/SPEC_003_WEB_UI_LOCAL.md): Especificação da UI local (FastAPI + HTML/JS puro) para cadastrar elenco, escolher/escrever roteiro e gerar o vídeo com progresso em tempo real.

---

## 🛠️ Guias Operacionais
- [Guia de Desenvolvimento & Comandos (DEVELOPMENT.md)](guides/DEVELOPMENT.md): Instruções de configuração local, variáveis de ambiente e comandos do `Makefile`.

---

## 🧰 Skills de Agentes (Tech Leads Club)
Skills instaladas em `.agents/skills/` (espelhadas em `.claude/skills/`):
- `tlc-spec-driven`: Orquestrador Spec-Driven Development do Harness Toolkit.
- `tlc-plan`: Fatiamento de requisitos em tarefas atômicas observáveis.
- `tlc-implement`: Execução guiada por testes e validação contínua em gates.
- `tactical-ddd`: Modelagem de domínio rico e regras de camadas hexagonais.
- `modular-design-principles`: Princípios de dependências acíclicas e baixo acoplamento.
- `react-best-practices`: Melhores práticas de renderização e performance React/Remotion.
- `coding-guidelines`: Convenções universais de código limpo.
- `docs-writer`: Padrões para escrita de documentação técnica.

---

## 🤖 Agentes e Automação
- [Manual de Instruções para Agentes (AGENTS.md)](../AGENTS.md): Diretrizes para agentes de inteligência artificial (Claude, Antigravity, Gemini).
