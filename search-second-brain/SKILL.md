---
name: search-second-brain
description: Search and query the personal Obsidian "second brain" vault using a local Ollama model (qwen2.5:7b). Use whenever the user wants to READ, search, ask questions about, or recall anything from their second brain / notes / vault (e.g. "what does my second brain say about X", "search my notes for Y", "read the second brain"). Also exposes a node CRUD CLI for manual create/read/update/delete of vault nodes.
---

# Search Second Brain

Local-first retrieval over the user's Obsidian vault at `~/Documentos/second-brain`
using Ollama (`qwen2.5:7b`). No data leaves the machine.

## When to use

Invoke this skill whenever the user wants to **read / search / query / recall**
anything from their second brain or notes.

## How to search

Run the search script with the user's question as the argument:

```bash
python3 ~/.claude/skills/search-second-brain/search.py "<the user's question>"
```

The script will:
1. Ensure `ollama serve` is running (starts it detached if needed).
2. Verify the model is present.
3. Retrieve the most relevant notes (keyword scoring over the vault).
4. Ask `qwen2.5:7b` to answer using only those notes, with sources.

Relay the answer to the user, and mention which notes were retrieved.

## Node CRUD

Each Claude turn already auto-creates a node via the Stop hook (see
`nodes/` and `nodes/_log.md` in the vault). For manual operations:

```bash
SB=~/.claude/skills/search-second-brain/crud_node.py
python3 $SB create --title "Title" --body "Text" --tags a,b --links Other-Note
python3 $SB read   --name <node-stem-or-substring>
python3 $SB update --name <node> --append "more text"
python3 $SB delete --name <node>
python3 $SB list
```

## Graph-first

This vault is a knowledge graph. Keep it connected:

- Auto-captured nodes are linked into the graph automatically (Stop hook links
  each node to its top relevant notes + the previous node).
- When you create or curate notes, add a `## Links` section with `[[wikilinks]]`.
- Repair orphans anytime:

  ```bash
  python3 ~/.claude/skills/search-second-brain/link_orphans.py        # link only orphans
  python3 ~/.claude/skills/search-second-brain/link_orphans.py --all  # re-link everything
  ```

## Configuration (env overrides)

- `SECOND_BRAIN_VAULT`  — vault path (default `~/Documentos/second-brain`)
- `SECOND_BRAIN_MODEL`  — Ollama model (default `qwen2.5:7b`)
- `OLLAMA_HOST`         — Ollama API (default `http://localhost:11434`)
