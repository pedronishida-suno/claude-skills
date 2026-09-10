#!/usr/bin/env python3
"""Create a second-brain node summarizing the just-finished Claude turn.

Invoked detached by the Stop hook with one arg: a temp file holding the hook's
stdin JSON ({session_id, transcript_path, cwd, ...}). Best-effort and silent:
any failure just skips node creation so Claude is never affected.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sb_lib as sb


def parse_last_turn(transcript_path: str):
    """Return (last_user_text, assistant_text, tool_names) from a JSONL transcript."""
    user_text, asst_text, tools = "", [], []
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return user_text, "", tools

    # Walk from the end: collect the final assistant block(s) and the user msg before it.
    for line in lines:
        try:
            ev = json.loads(line)
        except Exception:
            continue
        msg = ev.get("message") or {}
        role = msg.get("role") or ev.get("type")
        content = msg.get("content")
        texts = []
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    texts.append(b.get("text", ""))
                elif b.get("type") == "tool_use":
                    tools.append(b.get("name", "?"))
        joined = "\n".join(t for t in texts if t).strip()
        if role == "user" and joined and not joined.startswith("<"):
            user_text = joined  # keep latest real user message
            asst_text = []       # reset assistant accumulation after a new user turn
        elif role == "assistant" and joined:
            asst_text.append(joined)

    return user_text[:1500], "\n".join(asst_text)[:4000], tools


def main():
    if len(sys.argv) < 2:
        return 0
    tmp = Path(sys.argv[1])
    try:
        hook = json.loads(tmp.read_text(encoding="utf-8"))
    except Exception:
        return 0
    finally:
        try:
            tmp.unlink()
        except Exception:
            pass

    transcript = hook.get("transcript_path", "")
    cwd = hook.get("cwd", "")
    session = (hook.get("session_id", "") or "")[:8]
    user_text, asst_text, tools = parse_last_turn(transcript)
    if not user_text and not asst_text:
        return 0

    tool_summary = ", ".join(dict.fromkeys(tools)) or "none"

    # Summarize with the local model; fall back to a template on any failure.
    title, summary = _fallback_title(user_text), ""
    if sb.ensure_ollama(wait_s=10) and sb.model_available():
        prompt = (
            "Summarize this Claude Code work turn for a knowledge base node.\n"
            "Return EXACTLY two lines:\n"
            "TITLE: <max 8 words>\n"
            "SUMMARY: <2-3 sentences on what was asked and done>\n\n"
            f"USER REQUEST:\n{user_text}\n\nASSISTANT DID:\n{asst_text}\n\n"
            f"TOOLS USED: {tool_summary}\n"
        )
        try:
            out = sb.ollama_generate(prompt, timeout=60, num_predict=300)
            for ln in out.splitlines():
                if ln.upper().startswith("TITLE:"):
                    title = ln.split(":", 1)[1].strip() or title
                elif ln.upper().startswith("SUMMARY:"):
                    summary = ln.split(":", 1)[1].strip()
        except Exception:
            pass

    body_parts = []
    if summary:
        body_parts.append(summary)
    body_parts.append(f"\n**Request:** {user_text[:600]}")
    body_parts.append(f"**Tools used:** {tool_summary}")
    if cwd:
        body_parts.append(f"**Working dir:** `{cwd}`")
    if session:
        body_parts.append(f"**Session:** `{session}`")

    # Wire the node into the graph: hang it off the day's journal hub, plus any
    # curated note it genuinely matches. Deliberately no node->node edges: they
    # were 97% of the graph and fused every note into one unreadable blob.
    links = [_day_hub()]
    try:
        for _score, path, _text in sb.retrieve(
            f"{title}\n{user_text}", k=2, curated_only=True, min_score=11.0
        ):
            links.append(path.stem)
    except Exception:
        pass
    links = list(dict.fromkeys(links))  # dedupe, preserve order

    sb.create_node(
        title=title,
        body="\n".join(body_parts),
        tags=["claude-session", "auto"],
        node_type="turn",
        source="claude-stop-hook",
        links=links,
    )
    return 0


def _day_hub():
    """Today's journal note, created on demand. Each day is a hub in the graph."""
    from datetime import date
    day = date.today().isoformat()
    f = sb.VAULT / "journal" / f"{day}.md"
    if not f.exists():
        f.parent.mkdir(exist_ok=True)
        f.write_text(
            f"---\ncreated: {day}\ntags: [daily, auto]\ntype: journal\n---\n\n"
            f"# {day}\n\nCapturas de sessão deste dia.\n\n## Nodes\n",
            encoding="utf-8",
        )
    return day


def _latest_node():
    """Stem of the most recently created node, for temporal chaining."""
    try:
        cands = [p for p in sb.NODES_DIR.glob("*.md") if not p.name.startswith("_")]
        if not cands:
            return None
        return max(cands, key=lambda p: p.stat().st_mtime).stem
    except Exception:
        return None


def _fallback_title(user_text: str) -> str:
    words = (user_text or "Claude turn").split()
    return " ".join(words[:8]) or "Claude turn"


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # never surface errors
