# WORKOS — Golden Pilot Employee Eligibility Read Model V1

**Stamp:** PASS WITH WARNINGS  
**Date:** 2026-08-02  
**Canonical repo:** `C:\w\psiso`  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`  
**Prior tip (pushed):** `d172d41e` — Establish operational planning truth  
**This build commit:** local only — `Establish employee eligibility read model`

---

## 1. Repo / runtime gate

| Signal | Value |
|--------|-------|
| Active worktree | `C:\w\psiso` |
| HEAD at start | `d172d41e` (ahead 1 → pushed → 0/0) |
| Runtime | `:8000` / `:3000` from `C:\w\psiso` · `backend/dev.db` |
| OD3 after build | `golden-pilot-eligibility-rm-v1/v1` · next_dry `973019/21` |
| Stash | `stash@{0}: wip-employee-unrelated` — intact |

---

## 2. Audit / push `d172d41e`

Audited (product + QA only; no DB/secrets). Trailing whitespace only in QA markdown (non-blocking).  
Pushed: `9714ddd8..d172d41e` → local = remote = `d172d41e`, ahead/behind **0/0**.

---

## 3. Protected baseline (IDENTICAL)

`92401`, `973010`, `973012`, `973013`, `973015`, **`973018`** — snapshot + tasks_json hashes unchanged.  
Orphans `973016`/`973017` reported, not cleaned.

---

## 4. Gate A — `montaj_led` ORR

### Cause (not “3 ORR rows”)

**ONE** ORR row `operation_code=montaj_led` with  
`allowed_workcenter_codes=["WC_LED_ASSEMBLY","WC_ASSEMBLY"]` → DEC-010 ambiguous → 3 LED tasks fail-closed.

### Candidates

| WC | Evidence |
|----|----------|
| **WC_LED_ASSEMBLY** | PROD-INT-02 matrix: Montare LED → `SK_ELECTRICIAN` → `WC_LED_ASSEMBLY` → `montaj_led`; catalog label “Electric” |
| WC_ASSEMBLY | Separate `assembly` ORR + `SK_ASSEMBLY`; physical WA-ASSEMBLY-* resources only |

### Canonical correction

```text
allowed_workcenter_codes = ["WC_LED_ASSEMBLY"]
```

- Seed: `backend/seeds/seed_operational_workforce_registry.py`  
- Live DB row updated to match seed (no schema migration)  
- Resources `WA-ASSEMBLY-*` kept as physical work areas  
- Not chosen by sort/label/rate/UI

### Frozen old / new

| Order | LED WC | Eligibility |
|-------|--------|-------------|
| **973018** (frozen before) | null + `WORKCENTER_MAPPING_AMBIGUOUS` | `blocked_ambiguous_workcenter` |
| **973019** (after) | `WC_LED_ASSEMBLY` resolved | `ready_with_warnings` (3 employees) |

No live ORR recompute repaired 973018.

---

## 5. Gate B — Employee Eligibility Read Model

| Item | Value |
|------|-------|
| Service | `employee_eligibility_read_model_service.py` |
| API | `GET /api/v1/execution/plan-v2/from-order/{id}/employee-eligibility` |
| Sources | ORR skills/mode + `employee_*_authorizations` + OEA; active `employees.status==active` only |
| Scope | `operational_tasks[]` only — no `planned_tasks[]` fallback |
| Side effects | **none** (no assign/session/actual) |
| Employee ≠ User | held |

### Fixture `973019` status distribution

| Status | Count |
|--------|------:|
| ready_with_warnings | 16 |
| blocked_no_matching_employee | 2 (`vector_prep` / WC_PREPRESS — no employee WC auth) |

LED: 3 eligible — Andrei Goghi, Costi Modelator, Vali Colantator.

---

## 6. Fixture IDs

| Field | Value |
|-------|-------|
| workspace | `59c7b3cf-5ba7-4b71-b13a-ee05c9b930be` |
| quote | 19 |
| Quote Snapshot V2 | 20 |
| order | **973019** |
| plan | **21** |
| ops / deps | 18 / 24 |
| 2nd materialize | 409 idempotent |
| assignments/sessions/actuals | 0 |

---

## 7. UI

**URL:** `http://127.0.0.1:3000/execution/ops-graph?orderId=973019`

| Screenshot | Path |
|------------|------|
| Full page | `screenshots/01-973019-full-page.png` |
| Task graph + Elig. | `screenshots/02-973019-task-graph-eligibility.png` |
| Eligible expand | `screenshots/03-973019-eligible-employees-expand.png` |
| LED WC resolved | `screenshots/04-973019-led-wc-resolved.png` |

**Honest opinion:** Day/light readable. Elig. column is compact; expand shows names without assign/claim. LED WC `WC_LED_ASSEMBLY` clear. Two PREPRESS blockers are honest registry gaps, not UI invention. No redesign needed.

---

## 8. Tests

**Green:** ORR resolution · LED before/after · eligibility unit (ambiguous/match/no planned fallback) · DEC-009 · planning minutes (27+ targeted).  
**Not run:** full pytest · full FE suite.

---

## 9. Boundaries held

No assignment · no sessions/actuals · no Mobile · no Pricing/Inventory/CostEngine · no migration · no retrospective repair of 973018 · no cleanup of 973016/973017.

---

## 10. Next Owner GO

1. Author WC_PREPRESS (and CNC) employee authorizations if those tasks should have candidates.  
2. Optional assignment vertical slice (still separate from eligibility).  
3. More planning-minute standards (warning-only today).

**Direction:** ~97/100% toward “cine poate executa fiecare task?”.
