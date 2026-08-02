# Commit audit — `4ec3d384..b23cf5ed` (+ C3 corrective)

## Commit 1 — `2430fa8a` Prove multi-type actual-cost pilot families

| Check | Result |
|-------|--------|
| Scope | F6 service-level multi-type pilot |
| Ownership | Profitability read model + QA + tests |
| Files | `profitability_actual_read_model_service.py`, F6 test, profitability mock, F6 QA pack |
| Tests | `test_f6_multi_type_actual_cost_pilot.py` |
| Runtime proof | Isolated pytest fixtures (orders 880061–880063); not persisted in `dev.db` |
| Documentation | F6 QA pack under `docs/qa/workos-f6-multi-type-actual-cost-pilot-v1/` |
| Side effects | None on 973019 / Pricing / UI |
| Forbidden scope | Clean |
| Quality | Atomic, message matches body |
| Independently acceptable | YES |

## Commit 2 — `4ce9f769` Publish post-U5 application UI scorecard

| Check | Result |
|-------|--------|
| Scope | U6 read-only application scorecard |
| Ownership | QA evidence only — no frontend code |
| Files | U6 report, matrices, screenshots, `u6-capture-results.json` |
| Tests | None required (audit) |
| Runtime proof | Captures on FE `:3043` / BE `:8023` / `qa-dbs/u6-scorecard.db` |
| Side effects | None |
| Forbidden scope | Clean (helpers `_u6_capture.mjs` untracked, not committed) |
| Independently acceptable | YES |

## Commit 3 — `b23cf5ed` Record F6 pilot and U6 scorecard worklog

| Check | Result |
|-------|--------|
| Scope | Realignment worklog only |
| Files | `docs/worklog/realignment/2026-08-02_f6_multi_type_pilot_and_u6_scorecard.md` |
| Independently acceptable | YES |

## Commit 4 — C3 corrective (this round)

| Check | Result |
|-------|--------|
| Scope | Fix mojibake in F6/U6/worklog evidence + add C3 owner-review package |
| Code | None |
| Independently acceptable | YES |
