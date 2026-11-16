# First-run setup

Goal: write `~/.claude/security-audit/config.md`.

1. Ask permission to inspect the machine read-only (kube contexts, cloud profiles, the infra repo the user names). Show what you found; the user corrects it.
2. Ask the rest with AskUserQuestion, up to 4 questions at a time. Ask only what discovery did not answer. Write "none" for anything the user lacks; lanes skip it.
3. Write `config.md` in the format below. No secrets, only secret store paths.
4. Run one cheap query per source. Mark each OK or FAILED and fix failures with the user.

## config.md format

```markdown
# security-audit config

## System
- What it does; tenancy (tenant term, e.g. org, project)
- Account types: <term> = <who>, id field in logs / DB. Write accounts as `<term> <id> (<tenant> <n>)`.

## Sources
| Source | Access command | Retention | Mandatory filters | Time limit / window | Client IP, account id fields |
|---|---|---|---|---|---|
Cover: CDN/WAF/LB/gateway logs, app logs and traces, cloud audit logs, databases, paid scan engine (with default budget).
Older-data fallback: <source A after N days -> source B>.

## Database access
Read-only role, credential path, endpoint, connect command, how to grant and remove access to one more DB.

## Business lanes
Flows an attacker can abuse (payments, credits, promotions, data exports, quota...). Per flow: services, sources, value units, owner. Delete if none.

## Change
Code and IaC locations, dry-run commands, git rules (who commits, pushes, applies), rollout order.

## Owners
Incident owner, support, external providers.

## Output
Incidents folder, report language(s), reporting currency, writing style.
```
