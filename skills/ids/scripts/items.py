#!/usr/bin/env python3
"""Open items of all investigations.

`<incidents folder>/open-items.json` holds the items. This script is its only writer.
It writes `open-items-dev.md` and `open-items-ops.md` from it.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PRIORITIES = ("P0", "P1", "P2", "P3")
OPEN = ("OPEN", "PARTIAL", "IN PROGRESS")
CLOSED = ("DONE", "DECLINED")


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load(folder):
    return json.loads((Path(folder) / "open-items.json").read_text())


def save(folder, registry):
    (Path(folder) / "open-items.json").write_text(json.dumps(registry, indent=1, ensure_ascii=False) + "\n")
    render(Path(folder), registry)


def new_id(records, prefix):
    return f"{prefix}{max((int(r['id'][1:]) for r in records), default=0) + 1}"


def by_id(records, record_id):
    return next(r for r in records if r["id"] == record_id)


def cmd_init(args):
    path = Path(args.folder) / "open-items.json"
    if path.exists():
        sys.exit(f"INVALID {path} exists")
    save(args.folder, {"groups": [], "items": []})
    print(f"CREATED {path}")


def cmd_merge(args):
    work = Path(args.work).resolve()
    folder = work.parent
    registry = load(folder)
    ledger = json.loads((work / "ledger.json").read_text())
    incident = ledger["incident"]["id"]
    added = linked = 0

    def has_ref(action_id):
        return any(ref["incident"] == incident and ref["action"] == action_id
                   for item in registry["items"] for ref in item["refs"])

    def add(action_id, link, record):
        registry["items"].append({
            "id": new_id(registry["items"], "O"), "status": "OPEN", "note": "", "updated": today(),
            "refs": [{"incident": incident, "action": action_id, "link": link}], **record})

    for action in ledger["actions"]:
        if has_ref(action["id"]):
            continue
        evidence = action.get("evidence") or [{"file": "README.md"}]
        link = f"incident-{incident}.md" if action["scope"] == "incident" else f"{incident}/{evidence[0]['file']}"
        if action.get("item"):
            item = by_id(registry["items"], action["item"])
            item["refs"].append({"incident": incident, "action": action["id"], "link": link})
            item["priority"] = min(item["priority"], action["priority"])
            item["updated"] = today()
            linked += 1
        else:
            add(action["id"], link, {"list": action["list"], "group": action.get("group", ""),
                                     "text": action["text"], "owner": action["owner"],
                                     "priority": action["priority"], "file": action.get("file", "")})
            added += 1
    for unit in ledger["units"]:
        if unit.get("blocked_by") == "user" and not has_ref(unit["id"]):
            add(unit["id"], f"incident-{incident}.md", {"list": "ops", "group": "", "text": unit["question"],
                                                         "owner": "user", "priority": "P2", "file": ""})
            added += 1
    for update in ledger["item_updates"]:
        by_id(registry["items"], update["item"]).update(status=update["status"], note=update["note"],
                                                         updated=today())
    save(folder, registry)
    print(f"ITEMS {added} added, {linked} linked to an item, {len(ledger['item_updates'])} updated")


def cmd_set(args):
    registry = load(args.folder)
    if args.status not in OPEN + CLOSED:
        sys.exit(f"INVALID status is one of {', '.join(OPEN + CLOSED)}")
    by_id(registry["items"], args.item).update(status=args.status, note=args.note, updated=today())
    save(args.folder, registry)
    print(f"SET {args.item} {args.status}")


def cmd_group(args):
    registry = load(args.folder)
    group = {"id": new_id(registry["groups"], "G"), "title": args.title, "body": Path(args.body).read_text().strip()}
    registry["groups"].append(group)
    save(args.folder, registry)
    print(f"GROUP {group['id']} {group['title']}")


def cmd_list(args):
    registry = load(args.folder)
    for group in registry["groups"]:
        print(f"{group['id']}\tdev rule\t{group['title']}")
    for item in registry["items"]:
        if item["status"] in OPEN:
            print(f"{item['id']}\t{item['list']}\t{item['priority']}\t{item['status']}\t{item['group']}\t{item['text'][:160]}")


def cmd_render(args):
    render(Path(args.folder), load(args.folder))


def cell(text):
    return str(text or "").replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    if not rows:
        return []
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    return lines + ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows] + [""]


def refs(item):
    return ", ".join(f"[{ref['incident']}]({ref['link']}) {ref['action']}".strip() for ref in item["refs"])


def task(item):
    return item["text"] + (f" (`{item['file']}`)" if item["file"] else "")


def render(folder, registry):
    items = sorted(registry["items"], key=lambda i: (i["priority"], int(i["id"][1:])))
    head = f"State on {today()}. `scripts/items.py` writes this file from `open-items.json`; do not edit it by hand."
    columns = ["ID", "What to fix", "Report(s)", "Owner", "Status", "Note"]

    def row(item):
        return [item["id"], task(item), refs(item), item["owner"], item["status"], item["note"]]

    def done(kind):
        return ["## Done", ""] + table(["ID", "Item", "Status", "Date", "Report(s)", "Note"], [
            [i["id"], task(i), i["status"], i["updated"], refs(i), i["note"]]
            for i in items if i["list"] == kind and i["status"] in CLOSED])

    ops = ["# Open items: operations", "", head, "",
           "Priority: P0 = now, P1 = this week, P2 = this month, P3 = backlog. Code changes: "
           "[open-items-dev.md](open-items-dev.md).", ""]
    for priority in PRIORITIES:
        rows = [row(i) for i in items if i["list"] == "ops" and i["priority"] == priority and i["status"] in OPEN]
        if rows:
            ops += [f"## {priority}", ""] + table(columns, rows)
    (folder / "open-items-ops.md").write_text("\n".join(ops + done("ops")))

    dev = ["# Open items: development", "", head, "",
           "Each rule lists the code changes that enforce it. Operations work: "
           "[open-items-ops.md](open-items-ops.md).", ""]
    for group in registry["groups"] + [{"id": "", "title": "No rule yet", "body": ""}]:
        rows = [[i["id"], task(i), i["priority"], i["owner"], i["status"], refs(i), i["note"]]
                for i in items if i["list"] == "dev" and i["group"] == group["id"] and i["status"] in OPEN]
        if rows or group["id"]:
            dev += [f"## {group['id']} {group['title']}".replace("##  ", "## "), ""]
            dev += [group["body"], ""] if group["body"] else []
            dev += table(["ID", "Task", "Priority", "Owner", "Status", "Report(s)", "Note"], rows)
    (folder / "open-items-dev.md").write_text("\n".join(dev + done("dev")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name, func, *names):
        sub = commands.add_parser(name)
        for arg in names:
            sub.add_argument(arg)
        sub.set_defaults(func=func)

    command("init", cmd_init, "folder")
    command("merge", cmd_merge, "work")
    command("set", cmd_set, "folder", "item", "status", "note")
    command("group", cmd_group, "folder", "title", "body")
    command("list", cmd_list, "folder")
    command("render", cmd_render, "folder")
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
