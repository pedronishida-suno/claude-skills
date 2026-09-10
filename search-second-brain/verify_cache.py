#!/usr/bin/env python3
"""Verification cache for the second-brain-verifier agent.

Stamps each audited note with a fingerprint of its body so the agent can skip
notes that haven't changed since the last verification.

Stamp format (single frontmatter line, easy to hand-edit):
    sb_verified: "VERDICT|<body-md5-12>|<YYYY-MM-DD>"
Plus the tag `sb-verified` is added to the note's `tags:` for Obsidian visibility.

Commands:
    pending <path...>            list notes that need (re)verification (changed or never stamped)
    cached  <path...>            list already-verified notes as "<path>\\t<verdict>\\t<date>"
    stamp   <file> <verdict> [--date YYYY-MM-DD]   write/refresh the stamp on one note

A note is "pending" when it has no stamp, or its current body hash differs from
the stamped hash (i.e. it was edited). Paths may be files or directories
(directories are scanned recursively for *.md, skipping names starting with "_").
"""
import sys
import os
import re
import hashlib
from datetime import date
from pathlib import Path

STAMP_KEY = "sb_verified"
TAG = "sb-verified"
VALID_VERDICTS = {"KEEP", "FIX", "MERGE", "DROP"}


def split_frontmatter(text):
    """Return (frontmatter_lines, body_text). frontmatter_lines excludes the --- fences."""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            fm = text[4:end]
            body = text[end + 4:]
            if body.startswith("\n"):
                body = body[1:]
            return fm.splitlines(), body
    return [], text


def body_hash(body):
    return hashlib.md5(body.strip().encode("utf-8")).hexdigest()[:12]


def read_stamp(fm_lines):
    """Return (verdict, hash, date) from the stamp line, or None."""
    for line in fm_lines:
        m = re.match(rf'^\s*{STAMP_KEY}\s*:\s*"?([^"]*)"?\s*$', line)
        if m:
            parts = m.group(1).split("|")
            if len(parts) == 3:
                return parts[0], parts[1], parts[2]
    return None


def iter_notes(paths):
    for p in paths:
        path = Path(p).expanduser()
        if path.is_dir():
            for f in sorted(path.rglob("*.md")):
                if f.name.startswith("_"):
                    continue
                yield f
        elif path.is_file() and path.suffix == ".md":
            yield path


def cmd_pending(paths):
    for f in iter_notes(paths):
        text = f.read_text(encoding="utf-8", errors="replace")
        fm, body = split_frontmatter(text)
        stamp = read_stamp(fm)
        if stamp is None or stamp[1] != body_hash(body):
            print(str(f))


def cmd_cached(paths):
    for f in iter_notes(paths):
        text = f.read_text(encoding="utf-8", errors="replace")
        fm, body = split_frontmatter(text)
        stamp = read_stamp(fm)
        if stamp is not None and stamp[1] == body_hash(body):
            print(f"{f}\t{stamp[0]}\t{stamp[2]}")


def _ensure_tag(fm_lines):
    """Ensure the sb-verified tag is present in an inline `tags: [..]` line."""
    for i, line in enumerate(fm_lines):
        m = re.match(r'^(\s*tags\s*:\s*)\[(.*)\]\s*$', line)
        if m:
            items = [t.strip() for t in m.group(2).split(",") if t.strip()]
            if TAG not in items:
                items.append(TAG)
            fm_lines[i] = f"{m.group(1)}[{', '.join(items)}]"
            return fm_lines
        if re.match(r'^\s*tags\s*:\s*$', line):
            # block-style tags: insert a list item right after, if not present
            if not any(re.match(rf'^\s*-\s*{TAG}\s*$', l) for l in fm_lines):
                fm_lines.insert(i + 1, f"  - {TAG}")
            return fm_lines
    # no tags key at all
    fm_lines.append(f"tags: [{TAG}]")
    return fm_lines


def cmd_stamp(file, verdict, stamp_date):
    verdict = verdict.upper()
    if verdict not in VALID_VERDICTS:
        sys.exit(f"verdict must be one of {sorted(VALID_VERDICTS)}, got {verdict!r}")
    f = Path(file).expanduser()
    text = f.read_text(encoding="utf-8", errors="replace")
    fm, body = split_frontmatter(text)
    had_fm = text.startswith("---\n")
    if not had_fm:
        body = text  # whole file is body
        fm = []
    h = body_hash(body)
    stamp_val = f'{STAMP_KEY}: "{verdict}|{h}|{stamp_date}"'
    # replace existing stamp line or append
    replaced = False
    for i, line in enumerate(fm):
        if re.match(rf'^\s*{STAMP_KEY}\s*:', line):
            fm[i] = stamp_val
            replaced = True
            break
    if not replaced:
        fm.append(stamp_val)
    fm = _ensure_tag(fm)
    new_text = "---\n" + "\n".join(fm) + "\n---\n" + body
    f.write_text(new_text, encoding="utf-8")
    print(f"stamped {f} -> {verdict} ({h})")


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    cmd = argv[1]
    if cmd == "pending":
        cmd_pending(argv[2:])
    elif cmd == "cached":
        cmd_cached(argv[2:])
    elif cmd == "stamp":
        rest = argv[2:]
        stamp_date = str(date.today())
        if "--date" in rest:
            i = rest.index("--date")
            stamp_date = rest[i + 1]
            rest = rest[:i] + rest[i + 2:]
        if len(rest) != 2:
            sys.exit("usage: stamp <file> <verdict> [--date YYYY-MM-DD]")
        cmd_stamp(rest[0], rest[1], stamp_date)
    else:
        sys.exit(f"unknown command {cmd!r}\n{__doc__}")


if __name__ == "__main__":
    main(sys.argv)
