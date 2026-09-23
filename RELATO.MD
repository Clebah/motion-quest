# Relato — Uso do TLC Harness Toolkit na Implementação da SPEC-003

Este documento conta, com alguma profundidade, como o ecossistema **Tech Leads Club** — as skills de Spec-Driven Development e o runtime `@tech-leads-club/harness-toolkit` — foi usado do início ao fim da SPEC-003 (a interface web local do Motion Quest). A ideia não é só listar o que foi ligado, mas explicar *por que* cada peça entrou, onde ela realmente pesou no resultado e onde ficou só configurada para o futuro.

---

## 1. Por que instalar o harness antes de qualquer coisa

Antes mesmo de existir uma linha de código da SPEC-003, o usuário pediu para instalar o `@tech-leads-club/harness-toolkit` globalmente (`npm i -g @tech-leads-club/harness-toolkit` + `tlc harness install`). O harness é o runtime que fica "por baixo" do Claude Code: ele se conecta via hooks e passa a observar e, quando configurado para isso, gatear o que o agente faz — testes, comentários, escopo de mudanças, lições entre sessões.

A primeira barreira foi de ambiente: o harness exige Node ≥24 ou Bun, e a máquina estava em Node v20.20.2. Em vez de contornar isso, o caminho certo era atualizar o runtime de verdade — Node foi atualizado para v24.21.0 via `nvm` e definido como padrão. Sobre o runtime dos próprios hooks (Node vs Bun), a escolha consciente foi ficar em Node: Bun deixaria cada hook ~65x mais rápido (≈1ms contra ≈65ms medidos nesta máquina), mas para uma sessão de desenvolvimento isso é um ganho marginal, não algo que valha instalar mais uma ferramenta agora.

Com o runtime instalado, o próximo passo foi o wizard `harness-init`, que conecta o harness a *este* repositório especificamente — nada do que vem a seguir é automático por instalar o pacote; cada capacidade é um opt-in explícito, apresentado com benefício, trade-off e default antes de ser ligada.

## 2. O que foi decidido ligar (e por quê)

O wizard percorreu o catálogo inteiro de capacidades uma a uma. Do que foi aceito, o que realmente importou para a SPEC-003:

- **`grind` ligado**, com `lintCommand`/`testCommand` apontando para `make test` (o único comando de teste que já existia no projeto, cobrindo os dois workers) e `maxLoops: 3`. A ideia do grind é rodar automaticamente lint/test a cada turno completo e insistir se falhar — na prática, mesmo sem confirmação de que o hook disparou sozinho nesta sessão (ver seção 7), o *espírito* dessa capacidade foi seguido à risca manualmente: `make test` ou `make test-ai` rodou antes de cada um dos 15 commits da SPEC-003, sem exceção.
- **`planGate` ligado**, para bloquear o stop se um turno mexesse em arquivos fora de um escopo declarado via `HARNESS_PLAN:`. Ficou configurado, mas nenhum turno desta sessão chegou a declarar um plano — então essa capacidade nunca teve a chance de agir.
- **`rules` ligado**, com uma regra própria escrita junto com o usuário: `test-before-stop` (`.tlc/harness/rules/test-before-stop.md`), exigindo `gate(test) since HEAD` no stop, com verdict `follow-up` caso não satisfeita. É a tradução, em forma de regra observável, do checklist de entrega que já existia no `CLAUDE.md` do projeto ("os testes de ambos os workers foram executados e passaram com `make test`?").
- **`untrustedContent` ligado**, modo `frame` — framing de segurança para quando o agente lê PRs, issues ou páginas externas. Não chegou a ser exercitado, porque esta sessão não leu conteúdo externo.
- **`intelligence.lessons` ligado** — esta foi a capacidade que efetivamente voltou a ser usada mais tarde, na seção 5.

Ficaram deliberadamente desligadas, por não fazerem parte do escopo que o usuário aceitou: `shipGate`, `duplication`, `supplyChain`, allowlist de subagentes, `docsGate`, `observe`, `globalSpool`.

## 2.1. O que entrou sem ser pedido — segurança e outros requisitos não-funcionais

A lista da seção 2 é só o que foi *decidido* no wizard. Existe uma segunda camada, que roda independente de qualquer escolha — nunca foi uma pergunta, nem apareceu como opção pra ligar ou desligar.

**Piso de segurança do harness (não-configurável, sempre ativo).** Antes mesmo de discutir qualquer capacidade, o `harness-init` deixa claro que cinco regras rodam à frente de qualquer política, para qualquer sessão, neste ou em qualquer outro projeto na máquina:

| Regra | O que bloqueia |
| :--- | :--- |
| `outside-project-destruction` | Comando destrutivo cujo alvo resolve fora do projeto e fora do temp do SO |
| `unprovable-destruction` | Verbo destrutivo com alvo que não dá pra resolver (variável, substituição, comando montado em runtime) |
| `secret-access` | Ler `.env`, `~/.ssh`, `~/.aws`, `*.pem` e afins pra dentro do transcript da conversa |
| `history-rewrite` | `git push --force` (o `--force-with-lease` continua permitido, porque recusa sozinho se o remoto mudou) |
| `machine-control` | `shutdown`, `reboot`, `halt`, `poweroff` |

E, junto disso, a própria política do harness não é editável pelo agente — nem eu, rodando dentro da sessão, consigo mudar `.tlc/harness/config.json` ou desligar essas regras. Um gate que o próprio agente pode desligar não seria gate nenhum.

**Capacidades ligadas por padrão de fábrica (shipped default = ligado), que eu não perguntei porque já vêm assim:**

- **`secrets.redactOutput` (segurança)** — qualquer saída de comando/tool passa por uma varredura que mascara chave da AWS, token do GitHub/Slack/Stripe, bloco de chave privada PEM, JWT ou string de alta entropia não rotulada, trocando por um placeholder determinístico *antes* de eu (o modelo) sequer ver o valor real.
- **`shell.catastrophicAsk` (segurança)** — pergunta antes de qualquer comando shell que possa destruir dados fora do workspace.
- **`gapFeedback`, `failureClassification`, `progressiveHandoff`, `progressiveContext`, `autopilot` (continuidade entre sessões)** — menos sobre segurança, mais sobre confiabilidade: garantem que uma falha de gate carregue contexto estruturado pra próxima tentativa, e que a próxima sessão herde os gaps da anterior em vez de começar do zero.

**Decisões de NFR que tomei no design da SPEC-003 (§8 da spec), como consequência natural dos requisitos — não porque foram escritas como RF:**

- **Bind só em `127.0.0.1`** — a spec pediu "sem autenticação"; a contrapartida de segurança que eu decidi foi nunca escutar fora de localhost, pra essa ausência de auth não virar uma porta aberta na rede.
- **Validação de extensão nas fotos enviadas** (só `.png/.jpg/.jpeg/.webp` aceitos) — evita upload de qualquer tipo de arquivo arbitrário pelo formulário.
- **Limite de 5 fotos por tipo validado nos dois lados** (front e back) — defesa em profundidade: mesmo que alguém contorne a checagem do navegador, o backend reafirma a regra de negócio.
- **Um job de geração por vez (NF-02)** — evita duas gerações concorrentes disputando o mesmo Chromium/ffmpeg e corrompendo o estado em memória.
- As **3 correções pós-implementação** da seção 5 (thread para I/O bloqueante, acumular uploads, parar polling em erro) também são, no fundo, requisitos não-funcionais de robustez — nasceram do uso real, não de um RF escrito de antemão.

## 3. Planejamento — as 4 fases do SDD (skill `tlc-spec-driven`)

A SPEC-003 em si nasceu de uma segunda skill do mesmo ecossistema, distinta do runtime do harness: `tlc-spec-driven`, que estrutura o trabalho em quatro fases adaptativas — Specify, Design, Tasks, Execute.

**Specify** começou por explorar o código existente (os quatro use cases do Worker 1, o CLI `pipeline.py`, o `manifest.json`) antes de escrever qualquer requisito, para garantir que a nova interface reaproveitasse o que já existia em vez de duplicar lógica. O resultado foi `docs/sdd/SPEC_003_WEB_UI_LOCAL.md`, com requisitos em notação EARS (RF-01 a RF-05, mais restrições não-funcionais de concorrência e ausência de autenticação), validado explicitamente com o usuário antes de seguir — a regra do SDD é literal: "validar com o usuário antes de avançar de fase."

**Design** (§8 da spec) detalhou a arquitetura antes do primeiro arquivo de código: a estrutura de diretórios do novo adaptador `web/`, um diagrama de sequência completo (cadastro → templates → geração assíncrona → polling → render → player), a máquina de estados do job (`pending → running → completed/failed`), os schemas Pydantic da API e uma tabela de tratamento de erro por caso de borda. Foi nessa fase, por exemplo, que surgiu a decisão de extrair um `adapter_factory.py` compartilhado entre CLI e Web, para as duas interfaces nunca divergirem na detecção LIVE/MOCK.

**Tasks** quebrou a implementação em 11 tarefas atômicas (T1 a T11), cada uma com arquivos afetados, dependências explícitas nas tarefas anteriores, comando de verificação e a mensagem de commit já definida em Conventional Commits — tudo isso decidido *antes* de qualquer código, e registrado na própria spec (§9) para rastreabilidade.

**Execute** rodou as 11 tarefas em ordem, uma tarefa por vez, cada uma terminando em exatamente um commit atômico só depois do gate (`make test`) passar verde. Essa disciplina de "uma tarefa, um commit, gate primeiro" é a regra crítica nº2 e nº3 do `tlc-spec-driven` ("o gate deve passar antes da tarefa ser considerada concluída"; "um commit atômico por tarefa").

## 4. Implementação — o que saiu no final

Ao todo, a SPEC-003 resultou em **15 commits atômicos**: os 11 das tarefas T1–T11, mais um commit inicial de spec/design/tasks, e três commits de correção que só apareceram depois, quando o usuário rodou a aplicação de verdade (seção 6 do relato do walkthrough). Entraram **37 testes automatizados** novos ou ajustados em `packages/ai-vision` — cobrindo o catálogo de templates, os schemas da API, o store de personagens em memória, a orquestração de jobs em background e as rotas HTTP — todos em `unittest` (o runner de testes existente foi ensinado a descobrir automaticamente qualquer `test_*.py` novo, para que o gate do harness realmente enxergasse os testes futuros sem precisar editar o runner de novo). Em nenhum momento houve regressão nos testes que já existiam nos dois workers.

## 5. Lições aprendidas — onde o harness realmente "aprendeu" algo

A parte mais interessante da relação com o harness aconteceu depois da implementação "completa", quando o usuário rodou a interface de verdade, em modo LIVE, com a chave real do Gemini e personagens reais. Isso expôs três bugs de robustez que o smoke test em modo MOCK nunca teria revelado, porque nenhum dos três é lógica de negócio — são todos sobre como a aplicação se comporta sob I/O real e lento:

1. O servidor inteiro travava durante a geração (não só o job em andamento) porque os adaptadores do Gemini faziam chamadas de rede síncronas dentro de métodos `async def`, bloqueando o único event loop do `uvicorn`.
2. Adicionar fotos "aos poucos" apagava as anteriores, porque o `<input type="file">` nativo substitui a seleção a cada escolha em vez de somar.
3. Depois de reiniciar o servidor, a tela ficava presa fazendo polling silencioso contra um job que não existia mais (404 infinito), porque o front-end ignorava respostas de erro em vez de parar e avisar.

Cada um desses achados virou uma lição gravada com `tlc harness lessons add`, para que uma sessão futura — neste projeto ou em qualquer outro, no caso das lições globais — não precise redescobrir o mesmo problema:

| ID | Tier | Lição |
| :--- | :--- | :--- |
| `manual:af16dca9008d` | global | I/O de rede síncrono dentro de `async def` trava o event loop inteiro — sempre envolver em `asyncio.to_thread` |
| `manual:d3a7656e9ea3` | projeto (`--gate test`, `--ref pyproject.toml`) | Dependências Python deste repo vão para o python3 do sistema (`pip install --user`), o `.venv` existe mas não é usado pelo `Makefile` |
| `manual:12f6db58ce75` | global (`--ref app.js`) | `<input type=file multiple>` substitui a seleção a cada escolha — é preciso acumular manualmente |
| `manual:31d74b56b667` | global (`--ref app.js`) | Um loop de polling deve parar e avisar em resposta não-ok, nunca ignorar silenciosamente e insistir para sempre |

Três delas foram gravadas como lição **global** (`--global`) de propósito: são princípios de engenharia que valem para qualquer projeto que rode em cima de um event loop assíncrono ou tenha um `<input type=file>`, não só para o Motion Quest. A quarta — sobre onde as dependências Python deste repo realmente são instaladas — é específica deste projeto, então ficou como lição de projeto, amarrada por `--ref` ao `pyproject.toml`: se esse arquivo mudar de forma que a lição pare de fazer sentido, ela se retira sozinha.

Depois de gravadas, `tlc harness lessons sync-rules` foi rodado para sincronizar o arquivo durável `.tlc/harness/lessons.md`.

## 6. Memória criada — um mecanismo paralelo, não o mesmo

Vale separar bem uma coisa: as lições do harness (seção 5) e a memória do Claude são dois sistemas diferentes, com propósitos que se sobrepõem mas não são idênticos. As lições do harness são lidas pelo *runtime* do harness e reinjetadas conforme um gate específico falha ou estagna; a memória do Claude é lida no início de qualquer conversa futura neste diretório, independentemente de o harness estar rodando ou não.

Por isso, os mesmos três achados de ambiente/arquitetura também viraram memória de projeto, em arquivos próprios:

- `motion_quest_python_env.md` — a mesma pegadinha do `.venv` não utilizado, para qualquer sessão futura que precise instalar uma dependência Python neste projeto.
- `motion_quest_live_api_key.md` — o fato, verificado na prática, de que `packages/ai-vision/.env` tem uma chave `GEMINI_API_KEY` real e funcional; a instrução associada é sempre confirmar modo mock vs. LIVE antes de rodar qualquer geração, para não gastar API por engano.
- `motion_quest_spec_003_web_ui.md` — o registro de que a SPEC-003 existe, roda como processo único de event loop único, e que qualquer adaptador outbound novo precisa herdar o cuidado de nunca bloquear esse loop.

Os três estão indexados em `MEMORY.md`, com uma linha de resumo cada, para não pesar o contexto de sessões futuras que não precisem do detalhe completo.

## 7. O que ficou configurado, mas não foi de fato exercido

Para não deixar a impressão de que houve mais automação do que realmente aconteceu nesta sessão:

- **`grind` e a regra `test-before-stop` não foram observados disparando sozinhos via hook** durante esta implementação. O `doctor`, logo depois do `harness-init`, já avisava que a regra ainda não tinha nenhuma observação registrada — hooks de sessão do Claude Code só passam a valer de fato depois de reiniciar a sessão, e não houve confirmação direta de que isso aconteceu no meio da implementação. O que efetivamente garantiu a disciplina de "não commitar sem teste passando" foi a skill `tlc-spec-driven` sendo seguida manualmente, turno a turno.
- **`planGate`** nunca chegou a bloquear ou validar nada, porque nenhuma tarefa declarou `HARNESS_PLAN:` — não havia necessidade, já que o escopo de cada tarefa das 11 já estava definido e restrito desde a fase de Tasks.
- Tudo que ficou desligado na seção 2 (`shipGate`, `duplication`, `supplyChain`, allowlist de subagentes, `docsGate`, `observe`, `globalSpool`) continua desligado — nenhuma decisão nova foi tomada sobre elas durante a SPEC-003.
