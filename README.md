# claude-skills

Coleção de skills pessoais para o [Claude Code](https://claude.com/claude-code) — cada uma é um diretório com um `SKILL.md` (frontmatter YAML + instruções) que o Claude Code carrega via `/nome-da-skill`.

## Skills

| Skill | O que faz |
|---|---|
| [`browse`](./browse) | Abre um Chromium real para navegar, inspecionar e testar uma URL local ou de preview (snapshot acessível, cliques, console, screenshots). |
| [`gchat-capture`](./gchat-capture) | Captura e classifica mensagens do Google Chat para alimentar memória/second brain. |
| [`graphify`](./graphify) | Transforma qualquer input (código, docs, papers, imagens, vídeos) em um grafo de conhecimento persistente com god nodes, detecção de comunidades e ferramentas de query/path/explain. |
| [`llm-council`](./llm-council) | Roda uma decisão por um conselho de 5 conselheiros de IA que analisam independentemente, revisam uns aos outros anonimamente e sintetizam um veredito final (metodologia LLM Council do Karpathy). |
| [`search-second-brain`](./search-second-brain) | Busca e consulta um vault Obsidian ("second brain") usando um modelo Ollama local, com CLI de CRUD de nós. |
| [`spike`](./spike) | Valida uma mudança em um recorte isolado (sandbox com dependências mockadas e testes de caracterização) antes de propagar para o projeto inteiro. |
| [`task-observer`](./task-observer) | Observa a execução de tarefas para identificar oportunidades de melhoria/criação de skills, capturando padrões e correções do usuário. |

## Instalação

Copie o diretório da skill desejada para `~/.claude/skills/`:

```bash
cp -r <skill> ~/.claude/skills/
```

## Nota de proveniência

- `graphify` e `task-observer` empacotam/adaptam trabalho de terceiros (repos open-source citados dentro de cada `SKILL.md`); mantidos aqui como estão instalados localmente.
- Skills específicas de sistemas internos de uma empresa foram deliberadamente deixadas fora deste repositório.
