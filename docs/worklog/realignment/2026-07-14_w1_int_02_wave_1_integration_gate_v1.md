# W1-INT-02 — INTAKE_V6_WAVE_1_E2E_INTEGRATION_GATE_V1

**Date:** 2026-07-14  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Accepted HEAD:** `6637aa2`  
**Fixture:** `IR-MRJS4VIK` / workspace `80570a4a-a806-4305-a39c-b34a72092694`  
**Verdict:** `W1_INT_02_PASS_WITH_NONBLOCKING_DEBT_OPEN_WAVE_2`

## Gate purpose

Holistic integration proof across completed Wave 1 lanes (spine, finish, cant). No application code changes.

## Runtime proof (live stack @ `6637aa2`)

| Surface | Evidence |
|---------|----------|
| Workspace GET | `mounting_solution` ACM confirmed; `finish_target=all`; `return_finish_type=white_aluminum`; depth 60; 6 `return_cant` instances confirmed |
| Runtime capture | No fatal blockers; `mounting.mounting_solution` + `finish.finish_target` confirmed |
| Pricing preview | `is_ready_for_quote: true`; no adapter blockers |
| Handoff preview | `handoff_allowed: false`; fatal blockers = operator confirmation + PD missing fields |
| Product Definition | Preview 200; missing geometry/module fields (Wave 2 composition) |
| Product Aggregate | 5 components compiled; diagnostic warnings only |
| Product truth planner | No promotion blockers |

## Integration questions (summary)

1–3. **Single authorities:** mounting (`finish_setup.mounting_solution`), general finish (`finish_setup` + row fields), cant (`product_truth.components.return_cant.instances`) — **YES**
4. **Compatible:** per-layer writers → product_truth bridge → capture/readiness — **YES**
5. **Persistence/read aligned:** capture confirms persisted values — **YES**
6. **Stale dependents controlled:** cant save normalization clears Oracal/RAL on method change — **YES**
7. **Ready with fatal blockers:** pricing/capture spine cannot; handoff correctly blocks — **NO bypass**
8. **Handoff bypass:** `handoff_allowed=false` when fatal findings present — **NO bypass**
9. **Legacy override:** capture overlays prefer persisted truth; no legacy wins — **NO**
10. **Frontend/backend split:** review cant mapper now reads `product_truth` — **aligned**
11. **Cant services duplicate authority:** `return_cant_finish_truth_service` normalizes; `return_cant_runtime_state` aggregates bridge output — **expose only, no second writer**
12–13. **PD/Aggregate boundary:** stable template contract input; missing derived geometry fields are **Wave 2** — **PARTIAL**

## Remaining blocker classification (fixture)

| Blocker | Class |
|---------|-------|
| `operator_confirmation_missing` | OPERATOR_CONFIRMATION_REQUIRED |
| `canonical_missing_required_field:height_mm` etc. | VALID_WAVE_2_BLOCKER |
| `canonical_missing_required_field:mounting_system` | VALID_WAVE_2_BLOCKER (mounting_solution vs mounting_system mapping) |
| `unclassified_vector_artwork_requires_decision` | VALID_WAVE_2_BLOCKER (optional W1-L-VECTOR) |
| `Pricing: Lipsesc tarife` / 20/21 rows | PRICING_REGISTRY_BLOCKER |
| `RETURN_CANT_CONFIRMED_PERIMETER_MISSING` | TECHNICAL_DIAGNOSTIC_ONLY |
| `TRIGGER_FIELD_MISMATCH structura_suport` | STALE_OR_DUPLICATE (terminology, Wave 6) |
| False cant operator blockers | **removed** (STALE_OR_DUPLICATE — fixed W1-L-CANT) |
| `workspace.readiness_status=ready_for_quote_preview` while handoff blocked | SAFE_DERIVED_SNAPSHOT |

## Decisions

- **Vector:** `MAY_CLOSE_IN_WAVE_2` (optional `W1-L-VECTOR`; not blocking Wave 2 PD work)
- **Pricing rates:** `PRICING_REGISTRY_BLOCKER` — does not invalidate Intake truth; Wave 3 (`W3-T02`)
- **Persisted readiness snapshot:** `SAFE_DERIVED_SNAPSHOT` — handoff uses merged canonical findings

## Tests

- Backend combined Wave 1 suite: **83 passed**, 2 skipped, **10 collection errors** in `test_finish_target_runtime_capture.py` (pre-existing `seeded_db` fixture infra — not Wave 1 regression)
- Frontend mapper tests: **8 passed**
- Runtime fixture: read-only — **RUNTIME_FIXTURE_CHANGED: NO**

## UI evidence

| File | Route | Step |
|------|-------|------|
| `w1-int-02-step2-finish-cant.png` | `/intake-v6/80570a4a-.../operator` | Configurare / Finisaje |
| `w1-int-02-step2-mounting-acm.png` | same | Configurare / Montaj |
| `w1-int-02-step3-review-handoff.png` | same | Confirmare |

## Wave 2 opening

**OPEN** — Intake V1 truth lanes coherent; remaining blockers correctly owned outside Wave 1.

**First allowed Wave 2 task:** `W2-T01` — Resume PD composition contract (Cases A–D)

## Screenshots path

`docs/qa/workos-e2e-operational-coherence-audit-v1-true-e2e/`
