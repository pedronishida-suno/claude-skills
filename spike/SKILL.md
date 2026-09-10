---
name: spike
description: Valida uma mudança em recorte isolado antes de aplicar ao projeto inteiro. Analisa a seção de código referenciada, clona só a fatia coberta para um sandbox, mocka as dependências externas, escreve testes de caracterização, implementa a mudança na fatia, e SÓ após aprovação explícita do usuário propaga a conversão para o projeto. Use quando o pedido for "testar essa abordagem antes", "refatorar X mas quero ver funcionando isolado primeiro", "migrar padrão Y em todo o projeto", "trocar lib/API em N lugares", ou qualquer mudança transversal/arriscada. NÃO use para bug fix pontual de 1 arquivo — vá direto.
---

# /spike — recorte → isola → mocka → testa → muda → aprova → propaga

## Por que existe

Mudança transversal (trocar padrão, migrar API, refatorar util usado em 40 lugares) tem dois
modos de falha: (a) aplicar direto e quebrar o projeto em pontos não previstos; (b) planejar
no abstrato e descobrir na implementação que a abordagem não fecha. O spike mata os dois:
prova a abordagem em uma fatia pequena, com testes, e só então escala.

Regra de ouro: **nada toca o projeto real antes do gate 5.** Até lá, todo trabalho vive em
`.spike/<slug>/` (gitignored) ou em worktree dedicado.

## Uso

```
/spike <ref>                       # ref = caminho:linhas, símbolo, ou descrição da seção
/spike <ref> -- <mudança>          # já com a mudança pretendida descrita
/spike --resume <slug>             # retoma spike existente em .spike/<slug>/
/spike --propagate <slug>          # pula direto para a fase 6 (spike já aprovado)
```

## Fases (executar em ordem; cada gate exige o output indicado antes de avançar)

### 1. Analisar a seção referenciada

- Resolver `<ref>` para arquivo(s) + intervalo de linhas concreto. Se ambíguo, listar candidatos
  e perguntar — não adivinhar.
- Mapear a **fronteira** da fatia: o que ela importa, o que a importa, side effects
  (I/O, rede, banco, env, relógio, aleatoriedade), estado global tocado.
- Contar os **pontos de propagação**: quantos outros lugares do projeto usam o mesmo padrão
  e precisariam da mesma mudança. Isso define o tamanho da fase 6.
- Se `graphify-out/` existir no repo, usar `/graphify` como primeira fonte para o mapa de
  dependências (é local, só AST — permitido pelo guardrail).

**Gate 1 →** imprimir um bloco `## Fatia` com: arquivos/linhas, dependências de entrada,
dependentes, side effects, N pontos de propagação, e a mudança pretendida em 1 frase.

### 2. Clonar a fatia para o sandbox

- Criar `.spike/<slug>/` na raiz do repo (slug = kebab-case curto da mudança). Adicionar
  `.spike/` ao `.gitignore` se ainda não estiver; **não commitar o sandbox nunca**.
- Copiar **só** os arquivos da fatia + o mínimo de tipos/helpers que ela precisa para compilar.
  Preferir cópia literal a reescrita: o objetivo é reproduzir o comportamento atual, não
  melhorá-lo ainda.
- Registrar em `.spike/<slug>/MANIFEST.md` a origem de cada arquivo copiado
  (`caminho-original → caminho-no-sandbox`). Isso é o mapa de volta para a fase 6.

### 3. Isolar e mockar

- Para cada dependência externa listada no gate 1, escolher **uma** estratégia e anotar no
  MANIFEST:
  - **stub** — retorno fixo (para I/O, rede, banco, tempo);
  - **fake** — implementação em memória com comportamento real (para repositórios, caches);
  - **real** — manter a dependência quando for pura e barata (utils, tipos).
- Nunca mockar a própria coisa que está sendo mudada. Mock é para a fronteira, não para o
  alvo.
- Usar o test runner que o projeto já tem (vitest/jest/pytest/etc.). Não introduzir runner novo
  só para o spike.
- Se a fatia envolve UI, o "mockup" é uma story/fixture renderizável — não screenshot manual.
  Validar com `/browse` em sessão própria (`-s=spike-<slug>`): snapshot mostra o esperado e
  `console` sem erro. Isso entra no gate 2.

**Gate 2 →** a fatia clonada **compila/importa** no sandbox com as dependências mockadas, sem
tocar em nada fora de `.spike/`. Mostrar o comando que provou isso e sua saída resumida.

### 4. Testes de caracterização (comportamento ATUAL)

- Antes de mudar qualquer coisa, escrever testes que fixam o que a fatia faz **hoje**,
  incluindo comportamento estranho/bugado que exista — o objetivo é detectar regressão, não
  julgar.
- Cobrir: caminho feliz, bordas conhecidas, e pelo menos um caso por side effect mockado.
- Rodar. Tudo verde. Se algo não passa contra o código original copiado, o mock está errado —
  corrigir o mock, não o teste.

**Gate 3 →** suite verde contra o código original. Imprimir contagem de testes e o comando.

### 5. Implementar a mudança na fatia

- Aplicar a mudança **dentro do sandbox**, arquivo por arquivo do MANIFEST.
- Rodar os testes de caracterização. Para cada teste que quebrar, classificar explicitamente:
  - **regressão** → corrigir a implementação;
  - **mudança intencional de comportamento** → atualizar o teste E anotar no MANIFEST em
    `## Comportamentos alterados` (essa lista vai para o usuário no gate 5).
- Adicionar testes novos para o comportamento novo, se houver.
- Produzir o **diff da fatia**: `diff -ru` entre a cópia original (guardar em
  `.spike/<slug>/before/`) e a versão mudada (`.spike/<slug>/after/`).

**Gate 4 →** suite verde na versão mudada. Imprimir: testes passando, diff resumido
(arquivos + linhas +/-), e a lista `## Comportamentos alterados`.

### 6. Aprovação — PARAR AQUI

Apresentar ao usuário, nesta ordem, sem pedir permissão implícita:

1. O diff da fatia (completo se < 150 linhas; senão, por arquivo com resumo).
2. `## Comportamentos alterados` — vazio se refatoração pura.
3. Os **N pontos de propagação** do gate 1, agrupados por padrão de mudança (ex.: "12 arquivos
   trocam `parseFloat(x.replace(',', '.'))` por `parseBRL(x)`").
4. Riscos que o sandbox **não** cobre (integração real, migrations, dados de prod, i18n…).
5. Estimativa honesta do tamanho da fase 7, sinalizada como estimativa.

Usar `AskUserQuestion` com opções: **Aprovar e propagar** / **Ajustar o spike** / **Descartar**.
Não avançar sem resposta. "Parece bom" em texto livre conta como aprovar; silêncio não.

**Gate 5 →** aprovação explícita registrada.

### 7. Propagar para o projeto

- Entrar em worktree (`EnterWorktree`) se ainda não estiver em um — o `.spike/` original fica
  no checkout de origem e continua servindo de referência.
- Aplicar a mudança aos pontos de propagação **em lotes** pelo agrupamento do gate 5. Após
  cada lote: build + testes do projeto e, se há telas afetadas, smoke test via `/browse`
  (snapshot + console limpo). Se um lote quebra — teste ou visual —, parar, reportar, não
  seguir para o próximo.
- Levar os testes de caracterização do sandbox para o local canônico de testes do projeto
  (adaptando imports) — eles são o legado útil do spike.
- Ao final: suite completa do projeto verde, `git diff --stat`, commit por lote ou único
  conforme o padrão do repo. Mencionar o slug do spike na mensagem de commit.
- Sugerir remover `.spike/<slug>/` só depois do merge; não apagar automaticamente.

**Gate 6 →** relatório: arquivos alterados, testes antes/depois, o que ficou fora e por quê.

## Regras que não se negociam

- Fases 1–5 **nunca** editam arquivos fora de `.spike/`. Se a tentação for "só ajustar esse
  import no original", é sinal de que a fatia foi mal cortada — volte ao gate 1.
- Não pular a fase 4. Sem caracterização, o gate 4 não prova nada.
- Sandbox não vai para o git. Se `.spike/` aparecer em `git status`, corrigir o `.gitignore`
  antes de qualquer commit.
- Se o projeto tiver worktrees paralelos (`git worktree list`), checar se já existe um spike
  ou branch para a mesma mudança antes de começar — não duplicar trabalho.
- Estimativas de esforço e de risco são estimativas; dizer isso.

## Anti-padrões que este fluxo evita

| Tentação | Por que o spike bloqueia |
|---|---|
| "Vou aplicar em tudo e rodar os testes" | Testes do projeto raramente cobrem a fronteira exata da mudança; o spike cria essa cobertura primeiro |
| "Refatoro a fatia enquanto clono" | Mistura mudança com cópia e você perde o baseline do gate 3 |
| "Mocko o alvo porque é complicado" | Mock do alvo testa o mock, não o código |
| "Aprovação implícita — o usuário mandou fazer" | O gate 5 existe para o usuário ver o diff **antes** de 40 arquivos mudarem |
