"""Shared helpers for the second-brain skill: vault access, Ollama calls, node CRUD.

Used by search.py, crud_node.py and node_from_turn.py.
"""
import os
import math
import re
import json
import time
import signal
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# --- Configuration (env-overridable) ---------------------------------------
VAULT = Path(os.environ.get("SECOND_BRAIN_VAULT", str(Path.home() / "second-brain")))
MODEL = os.environ.get("SECOND_BRAIN_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
NODES_DIR = VAULT / "nodes"


# --- Ollama -----------------------------------------------------------------
def _api_up() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def ensure_ollama(wait_s: int = 30) -> bool:
    """Make sure `ollama serve` is reachable; start it detached if not."""
    if _api_up():
        return True
    # Start the server detached so it survives this process.
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError:
        return False
    deadline = time.time() + wait_s
    while time.time() < deadline:
        if _api_up():
            return True
        time.sleep(1)
    return _api_up()


def model_available(model: str = MODEL) -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=5) as r:
            tags = json.load(r)
        names = [m.get("name", "") for m in tags.get("models", [])]
        base = model.split(":")[0]
        return any(n == model or n.split(":")[0] == base for n in names)
    except Exception:
        return False


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def ollama_generate(prompt: str, model: str = MODEL, timeout: int = 120,
                    num_predict: int = 800) -> str:
    """One-shot generation. Strips <think> blocks emitted by reasoning models."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,  # ignored by non-reasoning models
        "options": {"temperature": 0.2, "num_predict": num_predict},
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate", data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.load(r)
    text = out.get("response", "")
    return _THINK_RE.sub("", text).strip()


_DAILY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# --- Retrieval --------------------------------------------------------------
def iter_notes(curated_only: bool = False):
    """Yield (path, text) for every markdown note in the vault.

    ``curated_only`` skips the auto-captured nodes/ folder. Session nodes share
    a boilerplate vocabulary ("the assistant investigated", "Tools used"), so
    scoring them against each other produces near-random edges — a node should
    hang off curated knowledge, not off other nodes.
    """
    for p in VAULT.rglob("*.md"):
        if curated_only:
            # skip nodes/ and the daily hubs: both are link lists, not content
            if NODES_DIR in p.parents or _DAILY_RE.match(p.stem):
                continue
        # skip the auto-generated CRUD log to avoid feedback loops
        if NODES_DIR in p.parents and p.name.startswith("_"):
            continue
        if "/.obsidian/" in str(p):
            continue
        try:
            yield p, p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue


# Portuguese/English function words: frequent enough to be pure noise in TF
_STOP = {
    "que", "com", "para", "por", "dos", "das", "uma", "num", "não", "mas", "seu",
    "sua", "como", "está", "são", "ser", "foi", "the", "and", "for", "with", "this",
    "that", "was", "are", "has", "have", "you", "não", "mais", "quando", "pelo",
}

_IDF_CACHE = {}


def retrieve(query: str, k: int = 6, min_ratio: float = 0.25,
             curated_only: bool = False, min_score: float = 0.0):
    """BM25 scoring over the vault.

    Raw term frequency (the previous scheme) is dominated by document length:
    a 130 KB transcript contains every common word hundreds of times and wins
    every query regardless of topic. BM25 normalises by length and weighs terms
    by IDF, so a term present in nearly every note contributes ~nothing.

    Results below ``min_ratio`` of the top score are dropped, so a query with no
    genuine match returns few or no links instead of noise.
    """
    terms = [
        t for t in re.findall(r"\w+", query.lower())
        if len(t) > 2 and t not in _STOP and not t.isdigit()
    ]
    if not terms:
        return []

    docs = list(iter_notes(curated_only=curated_only))
    if not docs:
        return []

    k1, b = 1.5, 0.75
    lows = [(path, text, text.lower()) for path, text in docs]
    lengths = [len(low.split()) or 1 for _, _, low in lows]
    avglen = sum(lengths) / len(lengths)
    n_docs = len(lows)

    # document frequency per term, for IDF
    df = {t: sum(1 for _, _, low in lows if t in low) for t in set(terms)}

    scored = []
    for (path, text, low), dlen in zip(lows, lengths):
        title = path.stem.lower()
        score = 0.0
        for t in set(terms):
            tf = low.count(t)
            if not tf:
                continue
            idf = math.log(1 + (n_docs - df[t] + 0.5) / (df[t] + 0.5))
            if idf <= 0:
                continue
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dlen / avglen))
            if t in title:
                score += 2 * idf  # title hits weigh more, but still IDF-gated
        if score > 0:
            scored.append((score, path, text))

    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return []
    floor = max(scored[0][0] * min_ratio, min_score)
    return [s for s in scored[:k] if s[0] >= floor]


# --- Node CRUD --------------------------------------------------------------
def slugify(text: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    s = re.sub(r"[\s_]+", "-", s)
    return s[:maxlen].strip("-") or "node"


def create_node(title: str, body: str, tags=None, node_type: str = "node",
                links=None, source: str = "manual") -> Path:
    NODES_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d_%H%M%S")
    slug = slugify(title)
    path = NODES_DIR / f"{stamp}_{slug}.md"
    tags = tags or []
    links = links or []
    fm = [
        "---",
        f"created: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"type: {node_type}",
        f"tags: [{', '.join(tags)}]",
        f"source: {source}",
        "---",
        "",
        f"# {title}",
        "",
        body.strip(),
        "",
    ]
    if links:
        fm.append("## Links")
        fm += [f"- [[{l}]]" for l in links]
        fm.append("")
    path.write_text("\n".join(fm), encoding="utf-8")
    _append_log(now, path, title, source)
    return path


def _append_log(now: datetime, path: Path, title: str, source: str):
    log = NODES_DIR / "_log.md"
    if not log.exists():
        log.write_text("# Node Log\n\nAuto-generated CRUD log of vault nodes.\n\n", encoding="utf-8")
    line = f"- `{now.strftime('%Y-%m-%d %H:%M')}` **{source}** — [[{path.stem}]] — {title}\n"
    with log.open("a", encoding="utf-8") as f:
        f.write(line)


def find_node(name: str):
    """Resolve a node by exact stem, slug, or substring match."""
    if not NODES_DIR.exists():
        return None
    cands = list(NODES_DIR.glob("*.md"))
    for p in cands:
        if p.stem == name or p.name == name:
            return p
    for p in cands:
        if name.lower() in p.stem.lower():
            return p
    return None
