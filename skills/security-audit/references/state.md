# STATE.md

```markdown
# Orchestrator state: <title>

Work dir: `<work dir>`
Report: `<incidents folder>/incident-<YYYY-MM-DD>-<slug>.md`
Step: <1–5>. Round: <N>. Last update: <UTC time>.

## Lane ledger
| Lane | Agent id | Model | Started (UTC) | Status (RUNNING / DONE / STOPPED) | Output file | Open gaps |
|---|---|---|---|---|---|---|

## Rounds
| Round | Ended (UTC) | New indicators | Lanes started for them |
|---|---|---|---|

## Report runs
| Run (DRAFT / FINAL) | Time (UTC) | check-masking |
|---|---|---|

## Cleanup
| Resource (access grant / worktree / paid-scan resource / credential cache) | Created (UTC) | Removed (UTC) or command for the user |
|---|---|---|

## Waiting for the user
| Item (approval / script to run / decision) | Asked (UTC) | Answer |
|---|---|---|
```
