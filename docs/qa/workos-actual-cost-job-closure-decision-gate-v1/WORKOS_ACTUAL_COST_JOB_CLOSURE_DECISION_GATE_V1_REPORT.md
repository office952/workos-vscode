# WORKOS — Actual Cost & Job Closure Decision Gate V1 Report

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Track | **F2** |
| Verdict | **OWNER_DECISION_REQUIRED** (PASS as decision gate; FAIL for Profitability Complete) |
| Worktree | `C:\w\workos_actual_cost_policy_gate_v1` |
| Branch | `feat/actual-cost-job-closure-gate-v1` |
| Base | `3669ec86` |
| Dossier | `OWNER_DECISION_DOSSIER_ACTUAL_COST_JOB_CLOSURE_V1.md` |
| Runtime DB | `backend/qa-dbs/f2-gate.db` (copy; **read-only**, unused for mutations) |
| Commit message | `Define actual-cost and job-closure decision gate` |
| Push | **NOT pushed** |

---

## Status

Research + contract design only. No financial formulas. No inventory/HR/pricing writes. No dead code interfaces.

## Scope

- Audit employee cost / rate / inventory / sessions / RM / legacy analysis / lifecycle / RBAC
- Compare ≤3 labor policies
- Propose material actuals + job closed + access matrix
- Owner questions

## Research answers (summary)

See dossier. Key: RM already forbids inventing labor money; material catalog-at-read is legacy; job closed is not canonical; legacy profitability auth is weaker than `reports.view_profit`.

## Runtime / DB

No mutations. Fixture 973019 commercial/assignment baseline not altered by this track.

## Architecture

Controller serial integration after U2. F2 owns docs under `docs/qa/workos-actual-cost-job-closure-decision-gate-v1/` and worklog only.

## Files

- `docs/qa/workos-actual-cost-job-closure-decision-gate-v1/OWNER_DECISION_DOSSIER_ACTUAL_COST_JOB_CLOSURE_V1.md`
- `docs/qa/workos-actual-cost-job-closure-decision-gate-v1/WORKOS_ACTUAL_COST_JOB_CLOSURE_DECISION_GATE_V1_REPORT.md`
- `docs/worklog/realignment/2026-08-02_actual_cost_job_closure_decision_gate_v1.md`

## Tests

- Targeted profitability tests: run at controller integrate (read-only confirmation)
- Full suites: **not run**

## Screenshots

N/A (no UI in F2)

## Warnings

- Legacy `ProfitabilityAnalysis` still mounted and under-gated
- No supervisor role in backend matrix
- Historical sessions cannot monetize without effective dating decision

## Blockers

Owner decisions §10 in dossier

## Boundaries respected

No payroll, no consumption writes, no auto-close, no Profitability Complete, no Employee Mobile, no graphics parsing

## Dead-pieces check

No speculative code interfaces added

## Roadmap awareness

Next Functional GO: Owner policy → then Profitability Complete path. UI Wave 3 after Wave 2 audit. Employee Mobile = final-final.

## Opinion

Gate is the correct stop. Implementing any of A1–A3 without Owner would fake “Profitability Complete”.

## Next step

Owner answers dossier questions; then implementation CP0 for chosen policy.

## Direction

Cât sunt în direcția stabilită: **88/100%**
