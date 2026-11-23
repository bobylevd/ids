# Report

File: `incident-<date>-<slug>.md` in the incidents folder, next to the work dir `<date>-<slug>/`. `ledger` writes it from the records after each merge. Do not edit it by hand: change the records. The headings and the status words are English; the text of the records is in the report language of `config.md`.

## What the ledger writes

| Part | From |
|---|---|
| Header table | the incident fields below |
| 2. Impact, 6. Root cause, 7. Current exposure | confirmed and candidate findings of the sections `impact`, `cause`, `exposure` |
| 4. Key timeline, Appendix A | `timeline` findings (`key` for section 4) |
| 8. Action items, cleanup table | actions with the scope `incident`, resources |
| 10. Open questions | units with their answers |
| Appendix B, C, D, E | indicators, `detail` findings, `closed` findings, deferred units |
| `<work dir>/README.md` | the index of the extracts that the records link to |

A section without records is not in the file. A triage that finds no attack gives a short file: the header, the summary, the timeline and the actions. Rejected findings, `elsewhere` findings and `elsewhere` actions are not in the report.

## Text fields

The `report` lane writes these in `"incident": {...}`:

| Field | Content |
|---|---|
| `severity` | `SEV<n>: <one-line reason>`; `none` for a triage with no attack |
| `status` | OPEN, CONTAINED, RESOLVED, CLOSED or NOT AN ATTACK |
| `exposure` | `STILL EXPOSED: <what>` or `CLOSED on <date> by <change>` |
| `owner` | incident owner |
| `first_activity`, `detected`, `contained` | UTC time and what, how, by whom |
| `activity` | ACTIVE, DORMANT or UNCLEAR, with the time of the last check |
| `systems` | the systems in scope |
| `notification` | customer, partner, regulator or none; owner; deadline (UTC); status |
| `summary` | Section 1. One paragraph of 5 to 8 sentences: who, what, how, impact, status. A second short paragraph: what is needed now and from whom (the top 3 actions by ID) |
| `what_happened` | Section 3. Short paragraphs in time order: preparation, entry point, actions, result, response |
| `detection` | Section 5. How it was detected, missed signals, response steps, logging or access gaps |
| `well`, `badly`, `lucky` | Section 9. Three lists of short sentences |

## Rules for the text

- Section 1 alone tells what happened, the impact, the status and who must act.
- Each number, time, IP and account in the text is in a confirmed finding, an indicator or an answered unit. Cite the record ID in brackets: `(F12)`. No record: leave the fact out, or mark it "Inferred:" with the reason.
- Full IDs always. Shorten only secrets, and say so. Accounts as `<term> <id> (<tenant>)`.
- Value: amount, currency, unit. Separate confirmed loss, attacker gain and at risk now.
- Write in the language and the style of `config.md` (Output).

## Severity

| Level | Meaning |
|---|---|
| SEV1 | Confirmed loss or personal-data breach, or an attack that is still active |
| SEV2 | Exploited exposure that gave the attacker value or data access, with no confirmed loss |
| SEV3 | Exploited exposure without value gained, or an open exposure with high impact |
| SEV4 | Attempt or probe only |
