# Walkthrough — SPEC-003: Interface Web Local

Smoke test manual end-to-end, executado em modo **MOCK** (offline), cobrindo o fluxo completo da UI: cadastro de personagem → escolha de template → geração → vídeo pronto.

## Setup

```bash
GEMINI_API_KEY= PYTHONPATH=. python3 -m uvicorn src.adapters.inbound.web.app:app --host 127.0.0.1 --port 8000
# (a partir de packages/ai-vision; GEMINI_API_KEY vazio força modo MOCK mesmo com .env presente)
```

`GET /api/mode` confirmado como `{"isLive": false}` antes de iniciar.

## Passos executados (via navegador)

1. **Página inicial** (`GET /`) carrega com o badge "🧪 Modo MOCK (offline)", os 5 templates renderizados (Terror, Ficção Científica, Drama, Romance, Comédia), contador "0 caracteres (mínimo 20)" e o botão "Gerar Vídeo" **desabilitado** com a mensagem "Cadastre ao menos um personagem primeiro." — confirma RF-02.3 no estado inicial.
2. **Cadastro de personagem**: preenchido nome "Pedro", descrição, e duas fotos (headshot + fullbody). Submissão via `POST /api/characters` retornou 200; o card do personagem apareceu na lista com preview de imagem servido via `/media/chars/<id>/...png` — confirma RF-01.1.
3. Após o cadastro, a mensagem do botão mudou para "Escreva ou escolha um roteiro (mínimo 20 caracteres)." — confirma a transição de RF-02.3 para RF-02.4.
4. **Seleção de template**: clique no card "Terror — A Última Noite na Cabana" preencheu a textarea com o `promptText` completo (362 caracteres) e o hint/erro desapareceu, liberando o botão "Gerar Vídeo" — confirma RF-02.1/RF-02.2.
5. **Geração**: clique em "Gerar Vídeo" disparou `POST /api/generate` (200, retornou `jobId`). A UI entrou em polling (`GET /api/jobs/{id}` a cada 2s) e exibiu mensagens de progresso, incluindo "Renderizando vídeo final..." — confirma RF-03.1/RF-03.2.
6. **Conclusão**: job chegou a `status: "completed"`, a seção de resultado exibiu o player `<video>` e o link "⬇ Baixar .mp4" apontando para `/api/jobs/{id}/video` — confirma RF-04.1.
7. `GET /api/jobs/{id}/video` verificado via `curl`: `200 OK`, `content-type: video/mp4`, arquivo servido corretamente pelo `FileResponse`.

## Observação sobre o conteúdo do vídeo final

O worker de renderização (`RemotionRendererAdapter.ts`, pré-existente à SPEC-003) tenta renderizar via Chromium headless e, quando isso falha — como neste sandbox, que não tem um Chromium instalado —, cai num fallback já existente que grava um artefato de texto no lugar do `.mp4` binário (mesmo comportamento de `make run`/`make render` hoje, independente da UI web). A integração ponta a ponta (subprocess, exit code 0, arquivo servido) funcionou corretamente; o conteúdo do artefato é uma limitação de ambiente do Worker 2, não uma regressão desta spec.

## Regressão

```bash
make test
```

Resultado: **todos os testes de `ai-vision` (37) e `video-render` (2) passaram**, sem regressão introduzida pela SPEC-003.

## Limitações conhecidas (aceitas por design, ver SPEC_003 §1/§8.7)

- Sem persistência entre reinícios do servidor (elenco e histórico de jobs vivem em memória).
- Um job de geração por vez.
- Sem autenticação — pensado para uso 100% local (`127.0.0.1`).
