# Lanes

## Prompt frame

```
Read-only security investigation. Working dir: <scratchpad>.
Read <skill dir>/references/lanes.md ("Lane rules"), ~/.claude/security-audit/config.md and BRIEF.md.
Lane: <name>. Window: <from> -> now (UTC). Context files: <lanes/*.md>.
Questions: 1. ...
Write lanes/<name>.md and return a summary of <N> lines, NEW INDICATORS first.
```

Use the strongest model for lanes that reason over code or value flows; a faster one for wide log sweeps.

## Catalog

| Lane | When | Covers |
|---|---|---|
| `edge` | first wave | Every request from the indicators on all edge logs: first seen, hosts, paths, status, UA, TLS fingerprint, blocks |
| `api` | first wave | Endpoints hit, auth failures, id enumeration, error spikes, handler code |
| `identity` | first wave | Sign-ups, logins, sessions, API keys and tokens, MFA changes, admin actions |
| `db` | first wave | Database ground truth. Reports databases it cannot read |
| `history` | first wave | Real start of activity, fingerprint/ASN pivots across all retention |
| `<business>` | indicators touch the flow | What the actor created, changed, read or took; value gained; trust in caller |
| `code-audit` | a flaw is found | Same flaw elsewhere, file:line, deployed version |
| `exposure`, `activity`, `block-impact`, `change` | see SKILL.md | |
| `verify` | open questions remain | One status per question |
| `report` | from the first results | Draft now, merge each lane result, see `report.md` |

## BRIEF.md

Established facts (time, source, evidence file); indicator register (type, value, first/last seen, source, actor / probable / not actor); pointer to these rules.

## Lane rules

- Read only. Exceptions: `change` edits only its own worktree, never commits; paid-scan lanes create only incident-named resources and list them.
- Use only the access in `config.md`. If something is denied, stop that step and report it.
- Before the first query, check the schema and use the mandatory filters, time limit and window from `config.md`. A slow query is a wrong query: narrow it.
- When a source's retention ends, query the older source. Retention is not a gap.
- No live requests to production. Write a GET-only script for the user instead.
- Mask personal data (`***@domain`, phone country code). No credentials or header values in files.
- Accounts as `<term> <id> (<tenant>)`, never a bare id. Confirm value units with a second field.
- Each fact cites its extract file and query. Extracts have a header row. Re-run the key query before you return.

Output `lanes/<name>.md`: summary; UTC timeline (time, source, event, evidence); key numbers; NEW INDICATORS (with first/last seen and the link); open questions with status; sources checked and their ranges.
