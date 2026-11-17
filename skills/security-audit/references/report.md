# Report

File: `incident-<date>-<slug>.md` in the incidents folder, in the language from `config.md`. Data folder: `<date>-<slug>/` with masked copies of the lane files and extracts. The date is the date of the work dir. The file exists from the start of the investigation and each lane result updates it.

## Rules

- Body (sections 1–10) is 2–4 pages; detail goes to appendices. Section 1 alone tells what happened, impact, status and who must act.
- Every fact (a number, a time, an IP, an account, a change, a verdict) links to its evidence file in the data folder: `([evidence](<date>-<slug>/<file>))`. No evidence: remove it, or mark it "Inferred:" with the reason.
- Full IDs always. Shorten only secrets, and say so. Accounts as `<term> <id> (<tenant>)`.
- Value: amount, currency, unit. Separate confirmed loss, attacker gain and at risk now.
- Prose in sections 1 and 3; tables elsewhere. Tables have a header row and no empty columns.

## Severity

| Level | Meaning |
|---|---|
| SEV1 | Confirmed loss or personal-data breach, or an attack that is still active |
| SEV2 | Exploited exposure that gave the attacker value or data access, with no confirmed loss |
| SEV3 | Exploited exposure without value gained, or an open exposure with high impact |
| SEV4 | Attempt or probe only |

## Template

```markdown
# INC-<date>-<slug>: <short title>

| Field | Value |
|---|---|
| Severity | SEV<n>: <one-line reason> |
| Status | <INVESTIGATING \| OPEN \| CONTAINED \| RESOLVED \| CLOSED> |
| Exposure | <STILL EXPOSED \| CLOSED on <date> by <change>> |
| Incident owner | |
| First attacker activity | <UTC time> ([evidence](...)) |
| Detected | <UTC time>, <how and by whom> |
| Contained | <UTC time>, <what> |
| Systems | |
| Notification | <customer / partner / regulator / none>; owner; deadline (UTC); status |
| Last update | <UTC time> |

## 1. Executive summary
<One paragraph of 5–8 sentences: who, what, how, impact, status.>
<A second short paragraph: what is needed now, and from whom (the top 3 action items by ID).>

## 2. Impact
| Area | Confirmed | Value gained by attacker | At risk now | Evidence |
|---|---|---|---|---|

## 3. What happened
<Short paragraphs in time order: preparation, entry point, actions, result, response.>

## 4. Key timeline
<At most 20 rows.>
| Time (UTC) | Event | Evidence |
|---|---|---|

## 5. Detection and response
<How it was detected, missed signals, response steps, logging or access gaps.>

## 6. Root cause and contributing factors
<Causes with file:line and the deployed version.>
| Factor | Effect | Evidence |
|---|---|---|

## 7. Current exposure
| Item | State | Since | Evidence |
|---|---|---|---|

## 8. Action items
| ID | Action | Owner | Priority (P0–P3) | Due | Status | Evidence |
|---|---|---|---|---|---|---|

## 9. Lessons learned
| What went well | What went badly | Where we were lucky |
|---|---|---|

## 10. Open questions
| Question | Status | Owner / how to close |
|---|---|---|

## Appendix A. Full timeline
## Appendix B. Indicators
| Type | Value | First seen | Last seen | Verdict | Evidence |
|---|---|---|---|---|---|
## Appendix C. Detailed findings
## Appendix D. Checked and closed
| Item | Result | Evidence |
|---|---|---|
## Appendix E. Data files and queries
| File | Content | Source / query |
|---|---|---|
```
