# Report

Write `incident-<date>-<slug>.md` (plus `.<lang>.md` per extra language in `config.md`, same numbers) to the incidents folder, with masked evidence files in `<date>-<slug>/`. The date is the first confirmed attacker activity.

## Rules

- Body is 2–4 pages; detail goes to appendices. Section 1 alone tells what happened, impact, status and who must act.
- Every fact links to its evidence file. No evidence: remove it, or mark it "Inferred:" with the reason.
- Full IDs always. Accounts as `<term> <id> (<tenant>)`.
- Value: separate confirmed loss, attacker gain and at risk now.
- Severity: SEV1 confirmed loss, data breach or active attack; SEV2 attacker gained value or data access; SEV3 exploited without gain, or high-impact open exposure; SEV4 attempt only.

## Skeleton

```markdown
# INC-<date>-<slug>: <title>
Severity · Status (OPEN/CONTAINED/RESOLVED) · Exposure (STILL EXPOSED/CLOSED) · Owner · First activity · Detected · Contained

## 1. Summary          (one paragraph + top 3 actions)
## 2. Impact           (area | confirmed | attacker gain | at risk | evidence)
## 3. What happened    (short paragraphs in time order)
## 4. Timeline         (max 20 rows: time UTC | event | evidence)
## 5. Detection and response (incl. missed signals, logging gaps)
## 6. Root cause       (file:line, deployed version; contributing factors)
## 7. Current exposure
## 8. Action items     (ID | action | owner | P0–P3 | status)
## 9. Lessons learned
## 10. Open questions  (question | status | owner)
## Appendices: full timeline, indicators, detailed findings, checked and closed, data files
```
