#!/usr/bin/env python3
"""CRUD for second-brain nodes.

  crud_node.py create --title T [--body B] [--tags a,b] [--type node] [--links X,Y] [--source manual]
  crud_node.py read   --name NAME
  crud_node.py update --name NAME [--append TEXT | --body TEXT]
  crud_node.py delete --name NAME
  crud_node.py list
"""
import sys
import argparse
import sb_lib as sb


def _csv(v):
    return [x.strip() for x in v.split(",") if x.strip()] if v else []


def main():
    ap = argparse.ArgumentParser(prog="crud_node")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create")
    c.add_argument("--title", required=True)
    c.add_argument("--body", default="")
    c.add_argument("--tags", default="")
    c.add_argument("--type", default="node", dest="ntype")
    c.add_argument("--links", default="")
    c.add_argument("--source", default="manual")

    r = sub.add_parser("read")
    r.add_argument("--name", required=True)

    u = sub.add_parser("update")
    u.add_argument("--name", required=True)
    u.add_argument("--append", default=None)
    u.add_argument("--body", default=None)

    d = sub.add_parser("delete")
    d.add_argument("--name", required=True)

    sub.add_parser("list")

    args = ap.parse_args()

    if args.cmd == "create":
        p = sb.create_node(args.title, args.body, _csv(args.tags),
                           args.ntype, _csv(args.links), args.source)
        print(f"created: {p}")

    elif args.cmd == "read":
        p = sb.find_node(args.name)
        if not p:
            print(f"not found: {args.name}"); return 1
        print(p.read_text(encoding="utf-8"))

    elif args.cmd == "update":
        p = sb.find_node(args.name)
        if not p:
            print(f"not found: {args.name}"); return 1
        if args.append is not None:
            with p.open("a", encoding="utf-8") as f:
                f.write("\n" + args.append + "\n")
            print(f"appended: {p}")
        elif args.body is not None:
            p.write_text(args.body, encoding="utf-8")
            print(f"overwrote: {p}")
        else:
            print("nothing to update (pass --append or --body)"); return 1

    elif args.cmd == "delete":
        p = sb.find_node(args.name)
        if not p:
            print(f"not found: {args.name}"); return 1
        p.unlink()
        print(f"deleted: {p}")

    elif args.cmd == "list":
        if not sb.NODES_DIR.exists():
            print("(no nodes yet)"); return 0
        for p in sorted(sb.NODES_DIR.glob("*.md")):
            if p.name.startswith("_"):
                continue
            print(p.stem)
    return 0


if __name__ == "__main__":
    sys.exit(main())
