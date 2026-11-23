#!/usr/bin/env python3
"""Ledger of one investigation.

The work dir is the folder of the investigation: `<incidents folder>/<date>-<slug>/`.
`<work dir>/ledger.json` holds all state. This script is its only writer.
It checks each lane result, plans the follow-up units and writes the report
`<incidents folder>/incident-<date>-<slug>.md` from the records.
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SECTIONS = ("impact", "timeline", "cause", "exposure", "detail", "closed", "elsewhere")
VERIFIED_SECTIONS = ("impact", "cause", "exposure")
BLOCKED_BY = ("no-data", "owner", "user")
SOURCE_STATUS = ("done", "timeout", "skipped", "no-access")
VERDICTS = ("actor", "probable", "not-actor")
PRIORITIES = ("P0", "P1", "P2", "P3")
INCIDENT_FIELDS = (
    "title", "severity", "status", "exposure", "owner", "first_activity", "detected",
    "contained", "activity", "systems", "notification", "summary", "what_happened",
    "detection", "well", "badly", "lucky",
)
HEADER = (
    ("severity", "Severity"), ("status", "Status"), ("exposure", "Exposure"),
    ("owner", "Incident owner"), ("first_activity", "First attacker activity"),
    ("detected", "Detected"), ("contained", "Contained"), ("activity", "Activity"),
    ("systems", "Systems"), ("notification", "Notification"),
)
REGISTRY_COLUMNS = ("type", "value", "verdict", "incident", "first_seen", "last_seen", "note")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def load(work):
    return json.loads((Path(work) / "ledger.json").read_text())


def report_path(work):
    work = Path(work).resolve()
    return work.parent / f"incident-{work.name}.md"


def open_items(work):
    return json.loads((Path(work).resolve().parent / "open-items.json").read_text())


def save(work, ledger):
    (Path(work) / "ledger.json").write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n")
    render(Path(work), ledger)


def stop(lines):
    print("\n".join(lines))
    sys.exit(1)


def new_id(records, prefix):
    numbers = [int(r["id"][1:]) for r in records if r["id"].startswith(prefix)]
    return f"{prefix}{max(numbers, default=0) + 1}"


def add_unit(ledger, lane, question, origin="", status="planned"):
    unit = {"id": new_id(ledger["units"], "U"), "lane": lane, "question": question,
            "status": status, "origin": origin}
    ledger["units"].append(unit)
    return unit


def follow_up(ledger, lane, question, origin):
    status = "deferred" if ledger["incident"]["profile"] == "quick" else "planned"
    return add_unit(ledger, lane, question, origin, status)


def find(records, record_id):
    return next((r for r in records if r["id"] == record_id), None)


def by_id(records, record_id):
    return next(r for r in records if r["id"] == record_id)


# ---------------------------------------------------------------- checks of a lane result

def fields(record, required, optional, where, errors):
    if not isinstance(record, dict):
        errors.append(f"{where}: not an object")
        return False
    missing = [k for k in required if not record.get(k)]
    unknown = [k for k in record if k not in required + optional]
    if missing:
        errors.append(f"{where}: no {', '.join(missing)}")
    if unknown:
        errors.append(f"{where}: unknown field {', '.join(unknown)}")
    return not missing and not unknown


def check_evidence(work, items, where, errors):
    if not isinstance(items, list) or not items:
        errors.append(f"{where}: no evidence")
        return
    for item in items:
        if not fields(item, ("file", "label"), (), f"{where} evidence", errors):
            continue
        path = work / item["file"]
        if not item["file"].startswith("lanes/") or ".." in Path(item["file"]).parts or not path.is_file():
            errors.append(f"{where}: no file {item['file']} in the work dir")
        elif path.suffix == ".tsv" and not path.with_suffix(".sql").is_file():
            errors.append(f"{where}: no query file for {item['file']}")


def check_result(work, ledger, result, errors):
    lane = result.get("lane")
    known = (
        "lane", "units", "findings", "indicators", "actions", "new_units", "verdicts",
        "notes", "resources", "incident", "items",
    )
    for key in result:
        if key not in known:
            errors.append(f"unknown top-level field {key}")
    entry = next((x for x in ledger["lanes"] if x["lane"] == lane), None)
    if not entry or entry["status"] != "running":
        errors.append(f"lane {lane} is not running in the ledger")
        return

    owned = {u["id"] for u in ledger["units"] if u.get("owner") == lane and u["status"] == "running"}
    seen = set()
    for r in result.get("units", []):
        where = f"unit {r.get('id')}"
        if not fields(r, ("id", "status"), ("answer", "evidence", "blocked_by", "owner", "note", "sources"),
                      where, errors):
            continue
        if r["id"] not in owned or r["id"] in seen:
            errors.append(f"{where}: not a running unit of this lane, or given two times")
        seen.add(r["id"])
        if r["status"] == "answered":
            if not r.get("answer"):
                errors.append(f"{where}: no answer")
            check_evidence(work, r.get("evidence"), where, errors)
        elif r["status"] == "blocked":
            if r.get("blocked_by") not in BLOCKED_BY or not r.get("note"):
                errors.append(f"{where}: blocked needs blocked_by ({', '.join(BLOCKED_BY)}) and a note")
            if r.get("blocked_by") == "owner" and not r.get("owner"):
                errors.append(f"{where}: no owner")
        else:
            errors.append(f"{where}: status is answered or blocked")
        for row in r.get("sources", []):
            if fields(row, ("source", "from", "to", "status"), ("note",), f"{where} source", errors) \
                    and row["status"] not in SOURCE_STATUS:
                errors.append(f"{where}: source status is one of {', '.join(SOURCE_STATUS)}")
    for unit_id in sorted(owned - seen):
        errors.append(f"unit {unit_id}: no result")

    for n, r in enumerate(result.get("findings", []), 1):
        where = f"finding {n}"
        if fields(r, ("section", "title", "text", "evidence"), ("time", "gained", "at_risk", "key"), where, errors):
            if r["section"] not in SECTIONS:
                errors.append(f"{where}: section is one of {', '.join(SECTIONS)}")
            if r["section"] in ("timeline", "exposure") and not r.get("time"):
                errors.append(f"{where}: no time")
            check_evidence(work, r["evidence"], where, errors)
    for n, r in enumerate(result.get("indicators", []), 1):
        where = f"indicator {n}"
        if fields(r, ("type", "value", "verdict", "first_seen", "last_seen", "evidence"), ("note",), where, errors):
            if r["verdict"] not in VERDICTS:
                errors.append(f"{where}: verdict is one of {', '.join(VERDICTS)}")
            check_evidence(work, r["evidence"], where, errors)
    for n, r in enumerate(result.get("actions", []), 1):
        where = f"action {n}"
        if fields(r, ("text", "owner", "priority", "list", "scope"), ("file", "due", "evidence"), where, errors):
            if r["priority"] not in PRIORITIES or r["list"] not in ("dev", "ops") \
                    or r["scope"] not in ("incident", "elsewhere"):
                errors.append(f"{where}: priority P0-P3, list dev/ops, scope incident/elsewhere")
            if r.get("evidence"):
                check_evidence(work, r["evidence"], where, errors)
    for n, r in enumerate(result.get("new_units", []), 1):
        fields(r, ("lane", "question"), ("why",), f"new unit {n}", errors)
    for r in result.get("verdicts", []):
        where = f"verdict {r.get('id')}"
        if not fields(r, ("id", "state"), ("note", "verdict"), where, errors):
            continue
        target = find(ledger["findings"] + ledger["indicators"], r["id"])
        if not target:
            errors.append(f"{where}: no such finding or indicator")
        elif target["lane"] == lane:
            errors.append(f"{where}: a lane does not verify its own record")
        elif r["state"] not in ("confirmed", "rejected"):
            errors.append(f"{where}: state is confirmed or rejected")
        elif r["id"].startswith("I") and r["state"] == "rejected" and r.get("verdict") not in VERDICTS:
            errors.append(f"{where}: a rejected indicator verdict needs the correct verdict")
    for n, r in enumerate(result.get("notes", []), 1):
        fields(r, ("source", "fact", "how"), (), f"note {n}", errors)
    for n, r in enumerate(result.get("resources", []), 1):
        fields(r, ("what", "created"), ("removed",), f"resource {n}", errors)
    if "incident" in result:
        fields(result["incident"], (), INCIDENT_FIELDS, "incident", errors)
    registry = open_items(work) if result.get("items") else {}
    for n, r in enumerate(result.get("items", []), 1):
        where = f"item link {n}"
        if not fields(r, (), ("action", "item", "group", "status", "note"), where, errors):
            continue
        if r.get("action") and not find(ledger["actions"], r["action"]):
            errors.append(f"{where}: no action {r['action']}")
        if r.get("item") and not find(registry["items"], r["item"]):
            errors.append(f"{where}: no open item {r['item']}")
        if r.get("group") and not find(registry["groups"], r["group"]):
            errors.append(f"{where}: no group {r['group']}")
        if not r.get("action") and not (r.get("item") and r.get("status") and r.get("note")):
            errors.append(f"{where}: give an action to link, or an item with a status and a note")


# ---------------------------------------------------------------- commands

def cmd_init(args):
    work = Path(args.work).resolve()
    (work / "lanes").mkdir(parents=True)
    waves = json.loads((SKILL / "references" / "waves.json").read_text())
    ledger = {
        "incident": {
            "id": work.name, "title": args.title, "class": args.cls, "profile": args.profile,
            "budget": args.budget, "from": args.start, "status": "INVESTIGATING",
            "config": str(Path(args.config).resolve()),
        },
        "lanes": [], "units": [], "indicators": [], "findings": [], "actions": [],
        "resources": [], "notes": [], "item_updates": [],
    }
    for lane in waves["classes"][args.cls]:
        add_unit(ledger, lane, waves["lanes"][lane])
    save(work, ledger)
    print(f"REPORT {report_path(work)}")
    print_next(ledger)


def cmd_resume(args):
    ledger = load(args.work)
    for unit in ledger["units"]:
        if unit["status"] == "running":
            unit["status"] = "planned"
    for lane in ledger["lanes"]:
        if lane["status"] == "running":
            lane["status"] = "stopped"
    save(args.work, ledger)
    print(f"REPORT {report_path(args.work)}")
    print_next(ledger)


def cmd_unit(args):
    ledger = load(args.work)
    unit = add_unit(ledger, args.lane, args.question)
    save(args.work, ledger)
    print(f"PLANNED {unit['id']} {unit['lane']}: {unit['question']}")


def cmd_start(args):
    ledger = load(args.work)
    budget = ledger["incident"]["budget"]
    if budget and len(ledger["lanes"]) >= budget:
        stop([f"BUDGET {budget} lanes used; ask the user for more or finish"])
    if any(x["lane"] == args.lane for x in ledger["lanes"]):
        stop([f"INVALID lane name {args.lane} is used; give the new lane a number"])
    units = [find(ledger["units"], unit_id) for unit_id in args.units]
    if not all(u and u["status"] == "planned" for u in units):
        stop(["INVALID each unit must exist with the status planned"])
    for unit in units:
        unit.update(status="running", owner=args.lane)
    ledger["lanes"].append({"lane": args.lane, "model": args.model, "started": now(), "status": "running"})
    save(args.work, ledger)
    print(f"STARTED {args.lane} ({args.model}): {' '.join(args.units) or 'no unit'}")


def cmd_merge(args):
    work = Path(args.work)
    ledger = load(work)
    result = json.loads((work / args.result).read_text())
    errors = []
    check_result(work, ledger, result, errors)
    if errors:
        stop([f"INVALID {e}" for e in errors])
    lane = result["lane"]
    out = []

    for r in result.get("units", []):
        unit = by_id(ledger["units"], r["id"])
        unit.update({k: v for k, v in r.items() if k != "id"})
        for row in r.get("sources", []):
            if row["status"] != "done":
                question = (f"Finish {row['source']} {row['from']} -> {row['to']} ({row['status']}) "
                            f"for: {unit['question']}")
                follow_up(ledger, "gap", question, unit["id"])
    for r in result.get("new_units", []):
        follow_up(ledger, r["lane"], r["question"], lane)

    registry = read_registry(ledger)
    for r in result.get("indicators", []):
        old = next((i for i in ledger["indicators"] if (i["type"], i["value"]) == (r["type"], r["value"])), None)
        if old and old["verdict"] != r["verdict"]:
            out.append(f"CONFLICT {r['type']} {r['value']}: {old['verdict']} ({old['lane']}) "
                       f"against {r['verdict']} ({lane})")
            add_unit(ledger, "verify", f"Give one verdict for {r['type']} {r['value']}: "
                     f"{old['verdict']} ({old['lane']}) against {r['verdict']} ({lane})", old["id"])
        elif old:
            old["first_seen"] = min(old["first_seen"], r["first_seen"])
            old["last_seen"] = max(old["last_seen"], r["last_seen"])
            old["evidence"] += [e for e in r["evidence"] if e not in old["evidence"]]
        else:
            ledger["indicators"].append({"id": new_id(ledger["indicators"], "I"), "lane": lane, **r})
            out.append(f"NEW-INDICATOR {r['type']} {r['value']} {r['verdict']}")
            for row in registry:
                if row["value"] == r["value"] and row["incident"] != ledger["incident"]["id"]:
                    out.append(f"KNOWN {r['type']} {r['value']}: {row['verdict']} in {row['incident']}")
    for r in result.get("findings", []):
        ledger["findings"].append({"id": new_id(ledger["findings"], "F"), "lane": lane, "state": "candidate", **r})
    for r in result.get("actions", []):
        prefix = "A" if r["scope"] == "incident" else "E"
        ledger["actions"].append({"id": new_id(ledger["actions"], prefix), "lane": lane, "status": "OPEN", **r})
    for r in result.get("verdicts", []):
        target = by_id(ledger["findings"] + ledger["indicators"], r["id"])
        target["verified_by"] = lane
        if r["id"].startswith("F"):
            target["state"] = r["state"]
        elif r["state"] == "rejected":
            target["verdict"] = r["verdict"]
        if r.get("note"):
            target["verify_note"] = r["note"]
    ledger["notes"] += [{"lane": lane, **r} for r in result.get("notes", [])]
    for r in result.get("resources", []):
        ledger["resources"].append({"id": new_id(ledger["resources"], "R"), **r})
    ledger["incident"].update(result.get("incident", {}))
    for r in result.get("items", []):
        if r.get("action"):
            by_id(ledger["actions"], r["action"]).update({k: r[k] for k in ("item", "group") if r.get(k)})
        else:
            ledger["item_updates"].append({k: r[k] for k in ("item", "status", "note")})
    next(x for x in ledger["lanes"] if x["lane"] == lane)["status"] = "done"

    save(work, ledger)
    print(f"MERGED {lane}: {len(result.get('units', []))} units, {len(result.get('findings', []))} findings, "
          f"{len(result.get('indicators', []))} indicators, {len(result.get('actions', []))} actions")
    print("\n".join(out), end="\n" if out else "")
    print_next(ledger)


def cmd_ask(args):
    ledger = load(args.work)
    unit = add_unit(ledger, "user", args.question, status="blocked")
    unit.update(blocked_by="user", note=f"asked {now()}")
    save(args.work, ledger)
    print(f"WAITING {unit['id']}: {unit['question']}")


def cmd_answer(args):
    ledger = load(args.work)
    unit = find(ledger["units"], args.unit)
    if not unit or unit.get("blocked_by") != "user":
        stop([f"INVALID {args.unit} does not wait for the user"])
    unit.update(status="answered", answer=f"User ({now()}): {args.answer}")
    del unit["blocked_by"]
    save(args.work, ledger)
    print(f"ANSWERED {unit['id']}")


def cmd_resource(args):
    ledger = load(args.work)
    if args.id:
        by_id(ledger["resources"], args.id)["removed"] = args.text
    else:
        ledger["resources"].append({"id": new_id(ledger["resources"], "R"), "what": args.text, "created": now()})
    save(args.work, ledger)
    print("\n".join(f"{r['id']} {r['what']}: {r.get('removed', 'OPEN')}" for r in ledger["resources"]))


def unverified(ledger):
    findings = [f["id"] for f in ledger["findings"]
                if f["section"] in VERIFIED_SECTIONS and f["state"] == "candidate"]
    indicators = [i["id"] for i in ledger["indicators"] if i["verdict"] == "actor" and not i.get("verified_by")]
    return findings + indicators


def print_next(ledger):
    lines = [f"PLANNED {u['id']} {u['lane']}: {u['question']}" for u in ledger["units"] if u["status"] == "planned"]
    ids = unverified(ledger)
    if ids:
        lines.append(f"VERIFY {' '.join(ids)}")
    lines += [f"WAITING {u['id']}: {u['question']}" for u in ledger["units"] if u.get("blocked_by") == "user"]
    running = [x["lane"] for x in ledger["lanes"] if x["status"] == "running"]
    if running:
        lines.append(f"RUNNING {' '.join(running)}")
    budget = ledger["incident"]["budget"]
    if budget:
        lines.append(f"BUDGET {budget - len(ledger['lanes'])} lanes left")
    if not ids and not running and not any(u["status"] == "planned" for u in ledger["units"]):
        lines.append("IDLE no open unit and no record to verify")
    print("\n".join(lines))


def cmd_next(args):
    print_next(load(args.work))


def cmd_brief(args):
    ledger = load(args.work)
    inc = ledger["incident"]
    print(f"# {inc['id']}: {inc['title']}\nClass: {inc['class']}. Profile: {inc['profile']}. Window: {inc['from']} -> now (UTC).")
    print("\n## Indicators (id, type, value, verdict, first seen, last seen, note)")
    for i in ledger["indicators"]:
        print(f"{i['id']}\t{i['type']}\t{i['value']}\t{i['verdict']}\t{i['first_seen']}\t{i['last_seen']}\t{i.get('note', '')}")
    print("\n## Findings (id, section, state, lane, time, title: text)")
    for f in ledger["findings"]:
        if f["state"] != "rejected":
            print(f"{f['id']}\t{f['section']}\t{f['state']}\t{f['lane']}\t{f.get('time', '')}\t{f['title']}: {f['text'][:300]}")
    print("\n## Units (id, lane, status, question -> answer)")
    for u in ledger["units"]:
        print(f"{u['id']}\t{u['lane']}\t{u['status']}\t{u['question']} -> {u.get('answer') or u.get('note', '')}")
    print("\n## Evidence files (work dir paths)")
    files = sorted({e["file"] for r in ledger["findings"] + ledger["indicators"] for e in r["evidence"]})
    print("\n".join(files))


def cmd_show(args):
    ledger = load(args.work)
    print(json.dumps([by_id(ledger["findings"] + ledger["indicators"] + ledger["units"] + ledger["actions"], i)
                      for i in args.ids], indent=1, ensure_ascii=False))


def defects(ledger):
    inc = ledger["incident"]
    lines = [f"OPEN {u['id']} {u['lane']}: {u['question']}" for u in ledger["units"]
             if u["status"] in ("planned", "running")]
    lines += [f"UNVERIFIED {i}" for i in unverified(ledger)]
    lines += [f"RUNNING {x['lane']}" for x in ledger["lanes"] if x["status"] == "running"]
    lines += [f"CLEANUP {r['id']} {r['what']}" for r in ledger["resources"] if not r.get("removed")]
    lines += [f"NO-FIELD {k}" for k in ("severity", "summary", "what_happened", "detection") if not inc.get(k)]
    if inc["status"] == "INVESTIGATING":
        lines.append("NO-FIELD status")
    return lines


def cmd_check(args):
    lines = defects(load(args.work))
    if lines:
        stop(lines)
    print("CLEAN")


def cmd_prune(args):
    work = Path(args.work)
    ledger = load(work)
    if defects(ledger):
        stop(["INVALID prune needs a clean check"])
    records = ledger["findings"] + ledger["indicators"] + ledger["units"] + ledger["actions"]
    keep = {e["file"] for r in records for e in r.get("evidence", [])}
    keep |= {str(Path(f).with_suffix(".sql")) for f in keep if f.endswith(".tsv")}
    extra = [p for p in sorted((work / "lanes").glob("*/**/*"))
             if p.is_file() and str(p.relative_to(work)) not in keep]
    for path in extra:
        path.unlink()
    print(f"PRUNED {len(extra)} files that no record links to; {len(keep)} kept")


def read_registry(ledger):
    path = Path(ledger["incident"]["config"]) / "indicators.tsv"
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def cmd_learn(args):
    ledger = load(args.work)
    incident = ledger["incident"]["id"]
    rows = read_registry(ledger)
    path = Path(ledger["incident"]["config"]) / "indicators.tsv"
    added = 0
    with path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, REGISTRY_COLUMNS, delimiter="\t", lineterminator="\n")
        for i in ledger["indicators"]:
            same = [r for r in rows if (r["type"], r["value"]) == (i["type"], i["value"])]
            for r in same:
                if r["verdict"] != i["verdict"] and r["incident"] != incident:
                    print(f"CONFLICT {i['type']} {i['value']}: {r['verdict']} in {r['incident']}, {i['verdict']} here")
            if not any(r["incident"] == incident for r in same):
                writer.writerow({**{k: i.get(k, "") for k in REGISTRY_COLUMNS}, "incident": incident})
                added += 1
    print(f"REGISTRY {added} rows added to {path}")
    for note in ledger["notes"]:
        print(f"NOTE {note['source']}: {note['fact']} (confirmed: {note['how']}; lane {note['lane']})")
    for i in ledger["indicators"]:
        if i["verdict"] == "actor":
            print(f"SIGNATURE {i['id']} {i['type']} {i['value']}")


# ---------------------------------------------------------------- report

def cell(text):
    return str(text or "").replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    if not rows:
        return []
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    return lines + ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows] + [""]


def section(title, body):
    return [f"## {title}", ""] + body if body else []


def render(work, ledger):
    inc = ledger["incident"]
    report = report_path(work)
    used = {}

    def links(record):
        out = []
        for item in record.get("evidence", []):
            used.setdefault(item["file"], []).append((item["label"], record["id"]))
            out.append(f"[{item['label']}]({inc['id']}/{item['file']})")
        return ", ".join(out)

    findings = [f for f in ledger["findings"] if f["state"] != "rejected"]

    def rows(name, columns, key=False):
        chosen = [f for f in findings if f["section"] == name and (f.get("key") or not key)]
        if name in ("timeline",):
            chosen.sort(key=lambda f: f["time"])
        return [[f.get(c, "") for c in columns] + [links(f)] for f in chosen]

    def unit_status(u):
        if u["status"] == "answered":
            return f"VERIFIED: {u['answer']}"
        if u["status"] == "blocked":
            label = {"no-data": "CANNOT-VERIFY", "owner": f"NEEDS-OWNER ({u.get('owner', '')})",
                     "user": "NEEDS-USER"}[u["blocked_by"]]
            return f"{label}: {u['note']}"
        return "OPEN"

    actions = sorted((a for a in ledger["actions"] if a["scope"] == "incident"),
                     key=lambda a: (a["priority"], int(a["id"][1:])))
    lessons = [inc.get(k) or [] for k in ("well", "badly", "lucky")]
    lesson_rows = [[col[n] if n < len(col) else "" for col in lessons] for n in range(max(map(len, lessons)))]

    lines = [f"# INC-{inc['id']}: {inc['title']}", "", "| Field | Value |", "|---|---|"]
    lines += [f"| {label} | {cell(inc[key])} |" for key, label in HEADER if inc.get(key)]
    lines += [f"| Scope | class {inc['class']}, profile {inc['profile']}, {len(ledger['lanes'])} lanes |",
              f"| Evidence | [{inc['id']}/README.md]({inc['id']}/README.md) |",
              f"| Last update | {now()} |", ""]
    body = [
        ("1. Executive summary", [inc["summary"], ""] if inc.get("summary") else []),
        ("2. Impact", table(["Area", "Confirmed", "Value gained by attacker", "At risk now", "Evidence"],
                            rows("impact", ["title", "text", "gained", "at_risk"]))),
        ("3. What happened", [inc["what_happened"], ""] if inc.get("what_happened") else []),
        ("4. Key timeline", table(["Time (UTC)", "Event", "Evidence"], rows("timeline", ["time", "text"], key=True))),
        ("5. Detection and response", [inc["detection"], ""] if inc.get("detection") else []),
        ("6. Root cause and contributing factors", table(["Factor", "Effect", "Evidence"],
                                                         rows("cause", ["title", "text"]))),
        ("7. Current exposure", table(["Item", "State", "Since", "Evidence"],
                                      rows("exposure", ["title", "text", "time"]))),
        ("8. Action items",
         table(["ID", "Action", "Owner", "Priority", "Due", "Status", "Evidence"],
               [[a["id"], a["text"] + (f" (`{a['file']}`)" if a.get("file") else ""), a["owner"], a["priority"],
                 a.get("due", "to set"), a["status"], links(a)] for a in actions])
         + table(["Cleanup", "Created (UTC)", "Removed (UTC) or command for the user"],
                 [[r["what"], r["created"], r.get("removed", "OPEN")] for r in ledger["resources"]])),
        ("9. Lessons learned", table(["What went well", "What went badly", "Where we were lucky"], lesson_rows)),
        ("10. Open questions", table(["ID", "Question", "Status", "Evidence"],
                                     [[u["id"], u["question"], unit_status(u), links(u)]
                                      for u in ledger["units"] if u["status"] != "deferred"])),
        ("Appendix A. Full timeline", table(["Time (UTC)", "Event", "Evidence"], rows("timeline", ["time", "text"]))),
        ("Appendix B. Indicators",
         table(["Type", "Value", "First seen", "Last seen", "Verdict", "Evidence"],
               [[i["type"], i["value"] + (f" ({i['note']})" if i.get("note") else ""), i["first_seen"],
                 i["last_seen"], i["verdict"], links(i)] for i in ledger["indicators"]])),
        ("Appendix C. Detailed findings", table(["Item", "Detail", "Evidence"], rows("detail", ["title", "text"]))),
        ("Appendix D. Checked and closed", table(["Item", "Result", "Evidence"], rows("closed", ["title", "text"]))),
        ("Appendix E. Not checked", table(["ID", "Lane", "Question"],
                                          [[u["id"], u["lane"], u["question"]]
                                           for u in ledger["units"] if u["status"] == "deferred"])),
    ]
    for title, content in body:
        lines += section(title, content)
    report.write_text("\n".join(lines))

    index = [f"# Evidence: INC-{inc['id']}", "",
             f"Report: [{report.name}](../{report.name}). Each `.tsv` has a `.sql` with the same base name; "
             "line 1 of the `.sql` names its source.", ""]
    index += table(["File", "What it shows", "Used in"],
                   [[f"[{rel}]({rel})", "; ".join(sorted({label for label, _ in used[rel]})),
                     ", ".join(sorted({record for _, record in used[rel]}))] for rel in sorted(used)])
    (Path(work) / "README.md").write_text("\n".join(index))


# ---------------------------------------------------------------- command line

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    def command(name, func, *arguments):
        sub = commands.add_parser(name)
        sub.add_argument("work")
        for flags, options in arguments:
            sub.add_argument(*flags, **options)
        sub.set_defaults(func=func)

    command("init", cmd_init,
            (["--title"], {"required": True}),
            (["--class"], {"dest": "cls", "required": True}),
            (["--profile"], {"choices": ["quick", "standard"], "required": True}),
            (["--from"], {"dest": "start", "required": True}),
            (["--config"], {"required": True}),
            (["--budget"], {"type": int, "default": 0}))
    command("resume", cmd_resume)
    command("unit", cmd_unit, (["lane"], {}), (["question"], {}))
    command("start", cmd_start, (["lane"], {}), (["model"], {}), (["units"], {"nargs": "*"}))
    command("merge", cmd_merge, (["result"], {}))
    command("ask", cmd_ask, (["question"], {}))
    command("answer", cmd_answer, (["unit"], {}), (["answer"], {}))
    command("resource", cmd_resource, (["text"], {}), (["--id"], {}))
    command("next", cmd_next)
    command("brief", cmd_brief)
    command("show", cmd_show, (["ids"], {"nargs": "+"}))
    command("check", cmd_check)
    command("prune", cmd_prune)
    command("learn", cmd_learn)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
