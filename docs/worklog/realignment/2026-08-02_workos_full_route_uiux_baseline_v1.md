# Worklog — WorkOS Full Route UI/UX Baseline V1

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Type | Documentation / baseline audit |
| Status | **PASS WITH WARNINGS** |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| HEAD at GO start | `75e31d46` |
| Worktree | `C:\w\psiso` |
| Runtime | FE `:3000` · BE `:8000` · DB `backend/dev.db` |

---

## Intent

Establish a durable, screenshot-backed inventory of WorkOS routes and UI/UX readiness **without** changing product code, theme, CSS, components, or database. Feed Wave 0 planning (App Shell + Day Mode + Role-Based Navigation).

---

## What was done

1. Extracted Route inventory from `frontend/src/App.tsx` (78 `path=` + 1 `index` = **79** Route elements; **72** product-relevant named patterns).
2. Consumed existing capture artifacts:
   - U1 core/shell inventory (12 opens)
   - U2 people/registries/admin (29 opens, all `themeClass: light`)
   - Drill results (tablet station OK; client/employee deep links inaccessible without mutation)
3. Catalogued **45** screenshot PNGs under `docs/qa/workos-full-route-uiux-baseline-v1/screenshots/`.
4. Wrote disposition table (KEEP / RENAME / MOVE / MERGE / HIDE_BY_ROLE / ADMIN_ONLY / LEGACY_LABEL / DEFER / REMOVE_CANDIDATE_ONLY).
5. Scored captured pages 0–5 honestly (~2.5 mean).
6. Recorded shell findings: day-mode sidebar mismatch, EN/RO mix, “(registry)” exposure, ops-home overlap.
7. Noted Ops-Graph **KEEP** with Track F controlled assignment emerging — no redesign.
8. Marked Employee Mobile as **DEFER / ADMIN_ONLY** visibility — out of scope for product change.

---

## Deliverables created

| Path |
|------|
| `docs/qa/workos-full-route-uiux-baseline-v1/route-inventory.md` |
| `docs/qa/workos-full-route-uiux-baseline-v1/page-scorecard.md` |
| `docs/qa/workos-full-route-uiux-baseline-v1/WORKOS_FULL_ROUTE_UIUX_BASELINE_V1_REPORT.md` |
| `docs/worklog/realignment/2026-08-02_workos_full_route_uiux_baseline_v1.md` |

Capture scripts / `_tmp*` left on disk as tooling — **not** emphasized as commit deliverables.

---

## Boundaries held

- No product code, DB, theme, CSS, or component edits.
- No commit / push.
- No shell rewrite.
- No mutation to unlock inaccessible deep links.
- No invented “% complete” product claims — production readiness = **not yet measurable**.

---

## Warnings (accepted)

- Parametric deep links not opened without mutation.
- Day mode imperfect.
- Jargon / language mix pervasive.
- Demos and lab routes still look like product peers in admin chrome.

---

## Wave 0 one-liner (next product GO, not this one)

**Unify day-mode shell tokens, Romanian-first nav (drop “registry”), and role-based visibility so each persona sees one clear ops home.**

---

## Top 3 problems (for owner skim)

1. Parallel ops homes (Control Tower / Shop Floor / Operator / Execuție / Tablet).  
2. Incomplete day mode + EN/RO + “(registry)” in primary nav.  
3. Sensitive HR/money and demo/lab surfaces visible without role hide.

---

## Related parallel work

- Track F: controlled employee assignment on Ops-Graph — baseline treats Ops-Graph as KEEP; assignment interaction emerging; do not redesign in UI baseline waves until Track F etiquette is clear.
- Capacity batches on same branch family — functional spine may advance while Wave 0 UI shell waits for explicit GO.
