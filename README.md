# ids — intrusion detection system

Claude Code skill. It runs parallel read-only agents on every attack path, feeds each finding back into new agents, and repeats until every question about the attacker is answered.

## Install

In Claude Code:

```
/plugin marketplace add <github-user>/<repo>
/plugin install ids@ids
```

From a local folder: `/plugin marketplace add /path/to/this/folder`.

## First run

The skill asks about your stack (log sources, databases, owners, output). It saves the answers in the project: `.claude/ids/config.md` and one query script per source in `.claude/ids/sources/`. Commit this folder to share the setup with your team.

Give the lanes a read-only identity. A lane reads text that the attacker wrote, and a read-only identity limits what an injected instruction can do.

## Use

Describe the incident ("we see forged callbacks from 1.2.3.4 since Monday") or ask "what did we miss".

The investigation state is in a work folder (`BRIEF.md`, `STATE.md`, `lanes/`). Start the skill again in a new session to continue.

## Checks

- `scripts/recheck.sh`: runs each saved query again and compares the row count with its extract.
- `scripts/check-masking.sh`: finds emails, phone numbers and credentials in the report and its data folder.
