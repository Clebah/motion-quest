# Walkthrough — SPEC-003: Interface Web Local

Duas rodadas de validação end-to-end: um smoke test em modo **MOCK** (offline, abaixo) e, depois, uma **validação real em modo LIVE** com Gemini de verdade (ver seção própria), que encontrou e levou à correção de 3 bugs de robustez que o MOCK não conseguia revelar.

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

## Observação sobre o conteúdo do vídeo final (smoke test MOCK)

O worker de renderização (`RemotionRendererAdapter.ts`, pré-existente à SPEC-003) tenta renderizar via Chromium headless e, quando isso falha — como no sandbox onde este smoke test MOCK rodou, sem Chromium instalado —, cai num fallback já existente que grava um artefato de texto no lugar do `.mp4` binário (mesmo comportamento de `make run`/`make render` hoje, independente da UI web). A integração ponta a ponta (subprocess, exit code 0, arquivo servido) funcionou corretamente; o conteúdo do artefato ali foi uma limitação de ambiente do Worker 2, não uma regressão desta spec — confirmado pela validação real abaixo, que rodou num ambiente com Chromium disponível e produziu um `.mp4` binário de verdade.

---

## Validação real em modo LIVE (máquina do usuário, com Gemini de verdade)

Depois do smoke test MOCK, o usuário rodou `make web` na própria máquina em modo **LIVE** (`GEMINI_API_KEY` real do `.env`), cadastrou 2 personagens reais ("Cleber" e "Mileni", com fotos de verdade) e gerou um vídeo com roteiro livre. Esse uso real — não coberto pelo MOCK — expôs 3 bugs de robustez, documentados e corrigidos na SPEC-003 §10:

1. **Servidor inteiro travava durante a geração** (não só o job) — chamadas de rede síncronas do Gemini bloqueando o único event loop do `uvicorn`. Corrigido com `asyncio.to_thread` (commit `a57d0e2`).
2. **Adicionar fotos "aos poucos" apagava as anteriores** — comportamento nativo do `<input type="file">`. Corrigido acumulando seleções em estado próprio do `app.js` (commit `882405f`).
3. **Polling infinito e silencioso em `GET /api/jobs/{id}` após reiniciar o servidor** (job antigo não existe mais → 404 para sempre, sem feedback). Corrigido parando o polling e avisando o usuário (commit `e2897fc`).

Após as 3 correções, uma geração completa em LIVE rodou do início ao fim sem travar, monitorada em tempo real via `GET /api/jobs/{id}` e pela lista de processos do sistema:

- Job `job_6732f558`: 24 cenas geradas via Gemini real, storyboard → assets → manifest → render, todas as etapas reportando progresso corretamente enquanto o servidor continuava respondendo a outras requisições.
- Etapa final de renderização confirmada como trabalho real (não travamento): `chrome-headless-shell` do Remotion renderizando frames, seguido de `ffmpeg` (`libx264`, 1080x1920 @30fps) costurando o `.mp4` final, ambos consumindo CPU ativamente.
- Resultado: `.mp4` binário real de **110.157.934 bytes** (`file` confirmou `ISO Media, MP4 Base Media v1`) em `packages/ai-vision/output/web/runs/job_6732f558/video.mp4`, servido corretamente pelo player e pelo link de download da UI — confirma RF-04.1 com dados reais, fechando a lacuna que o smoke test MOCK não cobria.

## Regressão

```bash
make test
```

Resultado: **todos os testes de `ai-vision` (37) e `video-render` (2) passaram**, sem regressão introduzida pela SPEC-003.

## Limitações conhecidas (aceitas por design, ver SPEC_003 §1/§8.7)

- Sem persistência entre reinícios do servidor (elenco e histórico de jobs vivem em memória).
- Um job de geração por vez.
- Sem autenticação — pensado para uso 100% local (`127.0.0.1`).
