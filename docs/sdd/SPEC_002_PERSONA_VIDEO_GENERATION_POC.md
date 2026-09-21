# SPEC-002: Geração de Vídeos Animados Personalizados a partir de Fotos Reais e Roteiros (PoC)

## Metadata
- **Status:** APPROVED
- **Author:** Motion Quest Product & Engineering Team
- **Created:** 2026-09-20
- **Version:** 1.0.0
- **Active Spec:** Sim

---

## 1. Visão Geral do Produto (PoC)

Permitir que qualquer usuário crie vídeos animados personalizados com duração entre **1m30s e 2min** a partir de fotos reais de pessoas (elenco de até 5 personagens) e roteiros customizados, contando com divisão automática em cenas (18 a 24 cenas de 5s cada), acompanhamento de progresso e download do vídeo final em formato `.mp4`.

---

## 2. Capacidades de Negócio & Requisitos Funcionais

### RF-01: Cadastro do Elenco (Personagens)
- **Qtd. Máxima:** Até 5 personagens por projeto.
- **Perfil:** Nome + Breve descrição de estilo e características marcantes.
- **Fotos de Referência:**
  - 1 a 5 fotos focadas no rosto (Headshots).
  - 1 a 5 fotos de corpo inteiro (Full-body).
- **Preparação Visual Automática:** Pipeline de pré-processamento de imagem (remoção de fundo, alinhamento facial e extração de embedding/features visuais) para garantir consistência dos rostos nas cenas.

### RF-02: Definição da História (Roteiro e Cenas)
- **Seleção de Elenco:** Escolha de quais personagens cadastrados participam da história.
- **Modo de Criação:**
  - *Modelo Pronto:* Jornada do Herói, Comédia, Aventura, etc.
  - *Texto Livre:* Prompt/roteiro customizado fornecido pelo usuário.
- **Divisão Automática em Cenas:** O sistema divide o roteiro em **18 a 24 cenas de 5 segundos cada** (garantindo duração total de 90s a 120s).
- **Revisão pelo Usuário:** Visualização da lista de cenas com atribuição de personagens por cena, prompt visual e legenda/narração, permitindo edição prévia.

### RF-03: Fabricação do Vídeo (Pipeline de Produção)
- **Geração Visual Consistente:** Criação da imagem estática de cada cena preservando a identidade visual dos personagens.
- **Animação das Cenas:** Transformação de cada cena estática em um clipe animado de 5 segundos (Image-to-Video).
- **Acompanhamento Transparente:** Exibição do progresso em tempo real (`X` de `N` cenas animadas, percentual concluído e etapa atual).
- **Montagem Final Automática:** Concatenação ordenada das 18-24 cenas na timeline contínua do Remotion.

### RF-04: Entrega e Consumo
- **Player de Pré-visualização:** Player de vídeo integrado no frontend para reprodução imediata pós-renderização.
- **Download MP4:** Exportação e download do arquivo `.mp4` final em alta qualidade.

---

## 3. Mapeamento na Arquitetura Hexagonal

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 WORKER 1: packages/ai-vision                                │
├───────────────────────────────┬───────────────────────────────┬─────────────────────────────┤
│ Domain Entities               │ Inbound Ports (Use Cases)     │ Outbound Ports (Adapters)   │
├───────────────────────────────┼───────────────────────────────┼─────────────────────────────┤
│ • Character (Perfil, Embeds)  │ • RegisterCharacterPort       │ • ImageProcessorPort        │
│ • Storyboard (18-24 scenes)   │ • GenerateStoryboardPort      │ • StoryGeneratorPort (LLM)  │
│ • SceneAsset (Image Specs)    │ • GenerateSceneAssetsPort     │ • ImageGeneratorPort        │
└───────────────────────────────┴───────────────────────────────┴─────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                               WORKER 2: packages/video-render                               │
├───────────────────────────────┬───────────────────────────────┬─────────────────────────────┤
│ Domain Entities               │ Inbound Ports (Use Cases)     │ Outbound Ports (Adapters)   │
├───────────────────────────────┼───────────────────────────────┼─────────────────────────────┤
│ • RenderJob (Status, Progress)│ • AnimateScenePort            │ • VideoAnimatorPort (I2V)   │
│ • StorylineTimeline (5s/seg)  │ • AssembleTimelinePort        │ • RemotionEnginePort        │
│ • ExportArtifact (.mp4)       │ • RenderFinalVideoPort        │ • StoragePort               │
└───────────────────────────────┴───────────────────────────────┴─────────────────────────────┘
```

---

## 4. Estrutura de Dados & Contratos JSON

### 4.1 Contrato do Storyboard (Output do Worker 1 ──► Input do Worker 2)

```json
{
  "projectId": "proj_123456",
  "title": "Aventuras de Pedro e Ana",
  "totalScenes": 20,
  "totalDurationSeconds": 100,
  "characters": [
    {
      "id": "char_1",
      "name": "Pedro",
      "description": "Homem jovem, alegre, casaco azul",
      "processedHeadshotUrls": ["https://storage/char_1_face.png"]
    }
  ],
  "scenes": [
    {
      "sceneNumber": 1,
      "durationSeconds": 5,
      "characterIds": ["char_1"],
      "visualPrompt": "Pedro acenando na praia ensolarada estilo ilustração animada",
      "narrationText": "Tudo começou em um dia ensolarado de verão...",
      "generatedImageUrl": "https://storage/scene_01.png"
    }
  ]
}
```

---

## 5. Gates de Qualidade & Aceite (Harness SDD)

1. **Gate 1 - Validação do Elenco:**
   - Todo personagem cadastrado deve conter entre 1 e 5 fotos de rosto e 1 e 5 de corpo.
2. **Gate 2 - Validação de Duração e Cenas:**
   - O storyboard deve obrigatoriamente gerar entre **18 e 24 cenas**.
   - Cada cena deve ter duração exata de **5 segundos**.
   - Duração total deve estar restrita a **90s <= T <= 120s**.
3. **Gate 3 - Renderização Remotion:**
   - O vídeo final deve ser exportado no formato `.mp4` com resolução mínima de 1080x1920 (Vertical 9:16) ou 1920x1080.
4. **Gate 4 - Testes Automatizados:**
   - `npm test` deve validar os UseCases com mocks dos adaptadores de IA e Animação.

---

## 6. Atualização no Harness Config

A especificação ativa em `.tlc/harness/config.json` foi definida para `SPEC_002_PERSONA_VIDEO_GENERATION_POC.md`.
