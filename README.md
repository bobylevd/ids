# security-audit

Claude Code skill. It runs parallel read-only agents on every attack path, feeds each finding back into new agents, and repeats until every question about the attacker is answered.

## Install

In Claude Code:

```
/plugin marketplace add <github-user>/<repo>
/plugin install security-audit@security-audit
```

From a local folder: `/plugin marketplace add /path/to/this/folder`.

## First run

The skill asks about your stack (log sources, databases, owners, output) and saves the answers to `~/.claude/security-audit/config.md`. Plugin updates keep this file.

## Use

Describe the incident ("we see forged callbacks from 1.2.3.4 since Monday") or ask "what did we miss".
