# First-run setup

Goal: write `.claude/ids/config.md` and `.claude/ids/sources/` in the project. Commit them to share the setup with the team.

1. Ask permission to inspect the machine read-only (kube contexts, cloud profiles, the infra repo the user names). Show what you found; the user corrects it.
2. Ask the rest with AskUserQuestion, up to 4 questions at a time. Ask only what discovery did not answer. Write "none" for anything the user lacks; lanes skip it.
3. Ask for a read-only identity for the lanes (a read-only cloud role, a view-only cluster context, a read-only database role). A lane reads text that the attacker wrote; a read-only identity limits what an injected instruction can do.
4. Write one script per query source into `sources/`: `<source>.sh "<query>"` prints the rows with a header row. The script holds the access command, the read-only identity and the time limit.
5. Write `config.md` in the format below. No secrets, only secret store paths.
6. Run one cheap query per source script. Mark each OK or FAILED and fix failures with the user.

## config.md format

```markdown
# ids config

## System
- What it does; tenancy (tenant term, e.g. org, project)
- Account types: <term> = <who>, id field in logs / DB. Write accounts as `<term> <id> (<tenant> <n>)`.

## Lanes
- Agent type: general-purpose
- Identity: <read-only profiles and contexts>. Check: <one command per identity>. Sign-in: <command>.

## Sources
| Source | Script | Retention | Mandatory filters | Time limit / window | Client IP, account id fields |
|---|---|---|---|---|---|
Cover: CDN/WAF/LB/gateway logs, app logs and traces, cloud audit logs, databases, paid scan engine (with default budget).
Older data: <source A after N days -> source B>.

## Database access
Read-only role, credential path, endpoint, connect command, how to grant and remove access to one more DB.

## Result checks
Commands that check lane results without a model, one per line. Delete if none.

## Business lanes
Flows an attacker can abuse (payments, credits, promotions, data exports, quota...). Per flow: services, sources, value units, owner. Delete if none.

## Change
Code and IaC locations, dry-run commands, git rules (who commits, pushes, applies), rollout order.

## Owners
Incident owner, support, external providers.

## Output
Work root, incidents folder, report language, reporting currency, writing style.
```
