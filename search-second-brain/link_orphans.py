#!/usr/bin/env python3
"""Wire orphan nodes into the graph.

Scans the vault's nodes/ folder for notes that have no '## Links' section and
appends links to their most-relevant existing notes (via the retrieval scorer)
plus the chronologically previous node. Keeps the second brain a connected graph.

Usage: python3 link_orphans.py [--all]
  (default: only nodes missing a Links section; --all re-links everything)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sb_lib as sb


def main():
    relink_all = "--all" in sys.argv
    if not sb.NODES_DIR.exists():
        print("(no nodes folder)")
        return 0

    nodes = sorted(p for p in sb.NODES_DIR.glob("*.md") if not p.name.startswith("_"))
    linked = 0
    for i, path in enumerate(nodes):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "## Links" in text and not relink_all:
            continue

        # Relevant existing notes (exclude self) + previous node for a time chain.
        links = []
        for _score, hit, _t in sb.retrieve(_query_from(text), k=3):
            if hit.stem != path.stem:
                links.append(hit.stem)
        if i > 0:
            links.append(nodes[i - 1].stem)
        links = list(dict.fromkeys(links))
        if not links:
            continue

        block = "\n## Links\n" + "\n".join(f"- [[{l}]]" for l in links) + "\n"
        if "## Links" in text and relink_all:
            text = text.split("## Links")[0].rstrip() + "\n" + block
            path.write_text(text, encoding="utf-8")
        else:
            with path.open("a", encoding="utf-8") as f:
                f.write(block)
        linked += 1
        print(f"linked: {path.name} -> {', '.join(links)}")

    print(f"\n{linked} node(s) wired into the graph.")
    return 0


def _query_from(text: str) -> str:
    # Use the title + body (skip frontmatter) as the retrieval query.
    body = text.split("---", 2)[-1] if text.startswith("---") else text
    return body[:1200]


if __name__ == "__main__":
    sys.exit(main())
