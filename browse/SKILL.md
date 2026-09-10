---
name: browse
description: Abre um Chromium real para navegar, inspecionar e testar uma URL — local (localhost, dev server, sandbox do /spike) ou de preview. Lê a página como snapshot acessível com refs, clica/preenche, lê console e requests, tira screenshot. Funciona para a sessão principal, subagentes e forks, em paralelo sem colisão. Use quando o pedido for "abre no browser", "testa a tela", "vê se renderiza", "navega em localhost:3000", "o que aparece no console", "screenshot da página", "valida o fluxo de login/formulário". NÃO use para fetch simples de HTML/JSON — aí é curl/WebFetch.
---

# /browse — Chromium para agentes via `playwright-cli` (+ MCP na sessão principal)

## O que existe

| Peça | Onde | Para quem |
|---|---|---|
| `playwright-cli` 0.1.19 | `~/.local/bin/playwright-cli` | **qualquer agente** (só precisa de Bash). Caminho padrão para subagentes e forks. |
| MCP `playwright` (0.0.80) | escopo user, tools `mcp__playwright__browser_*` | sessão principal, quando quiser screenshot voltando como imagem para o modelo. |
| Config compartilhado | `~/.claude/browse/config.json` | headless, 1366×800, `pt-BR`, `America/Sao_Paulo`, saída em `~/.claude/browse/out` |
| Browser | Chromium 1243 do Playwright (`~/.cache/ms-playwright/chromium-1243`) | CLI e MCP usam o mesmo binário |
| Skill upstream completa | `~/.local/lib/node_modules/@playwright/cli/skills/playwright-cli/` (SKILL.md + `references/`) | request-mocking, tracing, video, storage-state, test-generation — **não duplicar aqui, ler lá** |

## Regra 1 — toda sessão tem nome

```bash
playwright-cli -s=<slug> open <url> --config=$HOME/.claude/browse/config.json
```

- `<slug>` = nome curto da tarefa (`main`, `spike-parse-brl`, `verify-kpi`). **Nunca** omitir `-s`:
  a sessão default é compartilhada e dois agentes em paralelo se atropelam.
- Um agente **só fecha a sessão que abriu** (`-s=<slug> close`). `close-all` / `kill-all` só a
  sessão principal, no fim do trabalho. `list` mostra o que está aberto.
- Subagente que recebe uma tarefa com browser cria a sua sessão, faz, fecha. Não herda a do pai.

## Regra 2 — snapshot antes de screenshot

Snapshot é texto, barato e traz os refs para agir. Screenshot é imagem, caro, e só quando o
**visual** é a pergunta (layout quebrado, cor, alinhamento).

```bash
C=$HOME/.claude/browse/config.json
S=-s=<slug>
playwright-cli $S open http://localhost:3000 --config=$C
playwright-cli $S --raw snapshot                 # árvore acessível com [ref=eN]
playwright-cli $S --raw find "Salvar"            # localizar um nó pelo texto
playwright-cli $S click e12                      # agir pelo ref, não por seletor CSS
playwright-cli $S fill e5 "1.700.000,00" --submit
playwright-cli $S --raw eval "document.querySelector('#total').textContent"
playwright-cli $S --raw console                  # erros/warnings acumulados
playwright-cli $S --raw requests                 # rede desde o load (falhas 4xx/5xx)
playwright-cli $S screenshot --filename=$HOME/.claude/browse/out/<slug>-<passo>.png
playwright-cli $S close
```

- `--raw` devolve só o resultado (sem status/snapshot) — bom para pipe e para `diff` de dois
  snapshots (antes/depois de uma ação).
- Refs mudam quando a página muda: **re-snapshot depois de navegar** antes de clicar de novo.
- Sem `--raw`, o CLI grava snapshot/console em arquivos em `out/` e imprime o caminho —
  preferir `--raw` para não acumular lixo.

## Regra 3 — URL local: checar antes de abrir

```bash
curl -sI http://localhost:3000 | head -1 || echo "porta morta"
```

Se o dev server não estiver de pé, **não** abrir o browser numa porta morta: subir o server com
`run_in_background`, esperar a porta responder (loop curto de `curl`), e só então `open`.
Ao terminar, derrubar o que você subiu; não derrubar o que já estava rodando.

## Login / SSO

1. Sessão visível para o usuário logar (Wayland ativo, funciona):
   `playwright-cli -s=<slug> open <url> --headed --config=$C` → o usuário loga na janela.
2. Persistir: `playwright-cli -s=<slug> state-save $HOME/.claude/browse/state/<app>.json`.
3. Reaproveitar depois: `playwright-cli -s=<slug> open <url> --config=$C` +
   `state-load $HOME/.claude/browse/state/<app>.json` + `reload`.
4. Alternativa: se o browser logado da `persona-audit` estiver rodando (CDP em 9777),
   `playwright-cli -s=<slug> attach --cdp=http://localhost:9777` e `detach` ao final — nunca
   `close` numa sessão attached, isso fecha o browser do outro.

## Confidencialidade (guardrail Suno)

- Tudo roda local. Screenshots, snapshots, `state-save` ficam em `~/.claude/browse/` — **fora de
  qualquer repo**. Não copiar para o projeto, não publicar em artifact, não colar no chat
  cookies/tokens que `cookie-list`/`state-save` revelam.
- `state/*.json` de contas Suno contém sessão válida: tratar como credencial. Não commitar,
  não mover, apagar quando não precisar mais (`rm`).
- Telas do Orbit mostram salário/ICP/dados de pessoas: screenshot só quando pedido, e o
  destino é o usuário, não um relatório externo.

## MCP (sessão principal)

Tools `mcp__playwright__browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`,
`browser_take_screenshot`, `browser_console_messages`, `browser_network_requests`… Mesmo
config, mesmo Chromium. Usar quando a imagem precisa **voltar para o modelo** (validar visual)
ou quando a interação é longa e o vai-e-volta de Bash atrapalha. Para subagentes paralelos,
preferir o CLI (sessões nomeadas). Remover se pesar no contexto:
`claude mcp remove playwright -s user`.

## Integração com `/spike`

- Fase 3 (isolar/mockar): se a fatia tem UI, o mockup renderizável é aberto com
  `-s=spike-<slug>` e validado por snapshot + console limpo — isso vira parte do gate 2.
- Fase 7 (propagar): após cada lote, smoke test das telas afetadas com `/browse` antes de
  seguir; falha visual = parar o lote, igual a teste vermelho.

## Manutenção

- Zumbis: `playwright-cli kill-all` mata daemons; `pgrep -f chromium-1243` confere.
- Atualizar CLI e MCP **juntos** (compartilham `playwright-core`): `npm i -g @playwright/cli@<v>`
  e trocar a versão em `claude mcp add`; se o `playwright-core` novo pedir outra revisão de
  Chromium, `node ~/.local/lib/node_modules/@playwright/cli/node_modules/playwright-core/cli.js install chromium`.
- Fallback para o Chromium do sistema (`/usr/bin/chromium`): em `config.json`,
  `browser.launchOptions.executablePath`. Não é o padrão porque quebra em update do pacman.
- Limpar `~/.claude/browse/out` de vez em quando; nada ali é fonte de verdade.
