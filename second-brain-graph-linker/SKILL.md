---
name: second-brain-graph-linker
description: Mantém o grafo do second brain (vault Obsidian) ativamente conectado — roda link_orphans.py, sugere links para notas novas ou recém-editadas, e garante que nenhuma nota fique órfã, seguindo o princípio "sempre linkar, nunca deixar órfã". Use quando o pedido for "linka essa nota", "atualiza o grafo do second brain", "tem nota órfã?", "conecta essa nota no vault", ou depois de criar/editar uma nota no second brain via search-second-brain ou manualmente. NÃO use para busca/leitura de conteúdo do vault — isso é a skill search-second-brain.
---

# /second-brain-graph-linker — manutenção ativa do grafo

## Por que existe

A regra do vault é "graph-first": toda nota deve estar conectada, nunca órfã. A skill `search-second-brain` cobre busca e CRUD de nós, mas não fecha o loop de manutenção do grafo — isso hoje depende de rodar `link_orphans.py` manualmente e lembrar de fazê-lo.

## Passos ao ser acionado

1. Rode `link_orphans.py` (localizado junto com as demais ferramentas de `search-second-brain`, em `~/.claude/skills/search-second-brain/`) contra o vault (`~/second-brain` por padrão, ou `$SECOND_BRAIN_VAULT` se definido).
2. Para cada nota órfã encontrada, proponha 1-3 links plausíveis com base no conteúdo/título antes de aplicar — não linke automaticamente sem alguma checagem de relevância semântica.
3. Se a tarefa foi motivada pela criação de uma nota nova (via `node_from_turn.py` ou manual), verifique especificamente que essa nota recebeu ao menos um link de entrada e um de saída antes de considerar a tarefa concluída.
4. Reporte ao final: quantas órfãs havia, quantas foram linkadas, e quais ficaram sem link claro (para decisão humana em vez de link forçado).

## Contexto de referência

Ver memórias locais `second-brain-graph-first` e `second-brain-setup`. Usa as mesmas ferramentas de `search-second-brain` (não duplica o modelo Ollama nem a lógica de busca).
