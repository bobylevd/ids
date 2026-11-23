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

The skill asks about your stack (log sources, databases, owners, output). It saves the answers in the project: `.claude/ids/config.md` and one query script per source in `.claude/ids/sources/`. Each investigation adds its indicators to `.claude/ids/indicators.tsv`, its actor signatures to `.claude/ids/watch/` and its source notes to `config.md`. Commit this folder to share the setup with your team.

Give the lanes a read-only identity. A lane reads text that the attacker wrote, and a read-only identity limits what an injected instruction can do.

## Use

Describe the incident ("we see forged callbacks from 1.2.3.4 since Monday"), a flood, an alert, or ask "what did we miss". The skill sets a class (intrusion, fraud, availability, triage, hunt) and a profile (quick, standard) and starts the first wave of that class.

Each investigation has one folder in your incidents folder: the ledger, the lane results and the extracts. The report is the file next to it. All state is in one file, `ledger.json`. `scripts/ledger.py` is its only writer:
- it checks each lane result (fields, evidence files, queries) and refuses a result with a defect;
- it plans the follow-up work: a unit for each unfinished source, each new path and each verdict conflict;
- it lets a finding into the final report only after a second lane confirmed it;
- it writes the report from the records, in one language.

Start the skill again in a new session to continue.

The skill asks its questions in the conversation and continues the work while it waits for the answer.

At the end, `scripts/items.py` merges the actions into `open-items.json` and writes two lists for the teams from it: dev (code changes, grouped by rule) and ops (all other actions). It adds the indicators to `.claude/ids/indicators.tsv` and the actor signatures to `.claude/ids/watch/`.

## Scripts

- `scripts/ledger.py`: the ledger. `scripts/items.py`: the open items. Tests: `python3 -m unittest scripts/test_ledger.py`.
- `scripts/recheck.sh`: runs each saved query again and compares the row count with its extract.
- `scripts/check-masking.sh`: finds emails, phone numbers and credentials in the report and the work folder.
- `scripts/watch.sh`: runs each watch query for a time window and prints HIT or QUIET.
