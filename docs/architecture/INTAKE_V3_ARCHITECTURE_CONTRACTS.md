# Intake V3 Architecture Contracts

**Date:** 2026-06-17  
**Build:** `INTAKE_V3_ARCHITECTURE_CONTRACTS`  
**Status:** Contract foundation (no UI, no DB migration)

---

## 1. Purpose

Define the greenfield architectural foundation for **Intake V3** as versioned, testable contracts — independent of Intake V1/V2 UI, without changing commercial or production runtime behavior.

Intake V3 is:

- **greenfield** — not a refactor of WorkIntake V2;
- **product-first** — pilot template `TPL-VOLUMETRIC-LETTERS`;
- **contract-driven** — Atoms V6 is design reference only, not implementation source;
- **output-compatible** — future adapters map to `quote_input`, `product_spec_json`, Quote → Order → Execution → Employee Mobile.

---

## 2. What Intake V3 is NOT

| Not V3 | Reason |
|--------|--------|
| Atoms HTML/CSS/JS copy | Design reference only |
| WorkIntakeV2 refactor | V2 remains until explicit migration |
| SVG parser implementation | Future `INTAKE_V3_VECTOR_AND_LETTER_MODEL` |
| Execution plan generator | Real plan: Quote → Order → ExecutionPlanService |
| CostEngine / pricing | Adapter emits `quote_input`; no price computation |
| Inventory / StockMovement | `MaterialIntent.inventory_mutation_allowed = false` |
| Employee Mobile executor | `EmployeePreviewSeed.non_executable = true` |
| DB migration (this build) | Contracts + in-memory validation only |

---

## 3. WorkOS placement

Intake V3 owns **page workspace content only** inside the existing WorkOS App Shell. Process tabs (Context, Vector, Litere, Finisaje, Materiale, Iluminare, Handoff) are **internal workflow navigation**, not global routes.

This build defines contracts only — no `/intake-v3` route yet.

---

## 4. Contract inventory

| Contract | Module | Role |
|----------|--------|------|
| `ClientRequest` | `schemas/intake_v3.py` | Client/job context, dimensions |
| `ProductSelection` | same | Template choice, pilot scope |
| `VectorAsset` | same | Upload metadata (not confirmed letters) |
| `RawSvgAnalysis` | same | System auto-detection only |
| `ConfirmedProductionModel` | same | Operator-confirmed production truth |
| `LetterModel` | same | Real letters + grouping |
| `CutContourModel` | same | CNC contours + inner holes |
| `FinishAssignment` | same | all / group / letter_custom finishes |
| `MaterialIntent` | same | Roll/sheet/LED/PSU estimates |
| `ReadinessReport` | same | Unified blockers/warnings/CTA eligibility |
| `PricingInput` | same | Adapter toward `quote_input` |
| `ProductionHandoff` | same | Preview task seed (`preview_only=true`) |
| `EmployeePreviewSeed` | same | Mobile preview (`non_executable=true`) |
| `IntakeV3Workspace` | same | In-memory aggregate root |

**Constants / owner rules:** `data_models/intake_v3_contracts.py`  
**Readiness skeleton:** `services/intake_v3_readiness_service.py`  
**Frontend types:** `frontend/src/lib/intakeV3/contracts.ts`

---

## 5. RawSvgAnalysis ≠ ConfirmedProductionModel

| Layer | Owner | Example (HUB MEDIA PRODUCTION) |
|-------|-------|--------------------------------|
| `RawSvgAnalysis` | System | 27 closed contours detected |
| `ConfirmedProductionModel` | Operator | 18 litere reale, 27 contururi, 9 goluri |

Rules:

- Inner holes are **not** separate letters.
- CNC cut contours **include** inner holes.
- `letter_count` is **not** auto-derived from `closed_contour_count`.
- Readiness may warn when raw ≠ confirmed, but does **not** block quote once operator confirms.

---

## 6. FinishAssignment

Modes: `all` | `group` | `letter_custom` (advanced, not pilot default).

Blockers:

- Face Oracal 8500 / vinyl active → `face_vinyl_roll_width_mm` required (`MISSING_FACE_VINYL_ROLL_WIDTH`).
- Return Oracal 651 / vinyl active → `return_depth_mm` required (`MISSING_RETURN_DEPTH`).
- Active group without operator confirmation → `MISSING_FINISH_ASSIGNMENT`.

---

## 7. MaterialIntent vs Inventory

Materials in Intake V3 are **estimates for quoting and preparation**:

- Roll: `estimated_ml`, `estimated_m2`, `roll_width_mm`
- Sheet: `estimated_sheet_count`, `estimated_m2`, `estimated_remaining_area_m2` (**Rest placă estimat**)

Forbidden in V3 contracts:

- inventory write;
- StockMovement;
- nesting final;
- terminology „pierdere” as contract label.

`inventory_mutation_allowed` is hard-validated to `false`.

---

## 8. ReadinessReport

Unified readiness with:

- `status`: draft → blocked_for_quote → ready_for_quote → …
- `blockers` / `warnings` as structured `ReadinessIssue`
- `can_create_quote`, `can_generate_production_handoff`
- `completion_by_section` per process tab

Implemented blockers (skeleton):

| Code | Condition |
|------|-----------|
| `MISSING_FACE_VINYL_ROLL_WIDTH` | Face vinyl active, roll width missing |
| `MISSING_RETURN_DEPTH` | Return vinyl active, depth missing |
| `UNCONFIRMED_LETTER_MODEL` | Production model not confirmed |
| `MISSING_DIMENSIONS` | width/height missing |
| `MISSING_FINISH_ASSIGNMENT` | Active finish group not confirmed |

---

## 9. ProductionHandoff and EmployeePreviewSeed

**ProductionHandoff**

- `preview_only = true` (validated, cannot be false)
- `task_seed` — candidate tasks for operator review
- Does **not** create `execution_plan`, `execution_reality`, or work sessions

**EmployeePreviewSeed**

- `non_executable = true` (validated)
- Shows how tasks **would** appear in Employee Mobile
- No start-task actions

Real execution path remains:

```
Quote → Order → ExecutionPlanService → Employee Mobile
```

---

## 10. Owner operational rules (documented, not enforced in execution)

These are encoded in `OWNER_OPERATIONAL_RULE_DETAILS` and `REFERENCE_TASK_ORDER_NO_SHARED_SUPPORT` for future build:

**AUDIT/FIX — Volumetric execution task order and electrical source handling**

| Rule | Summary |
|------|---------|
| Face vinyl after assembly/back | Colantare fețe **după** asamblare + montaj spate |
| Return vinyl before forming | Colantare cant **înainte** de modelare cant |
| No shared support | Fără bare/ACM/casetă → surse la **Ambalare/predare**, nu task cablare pe suport |
| Shared support | Cu structură comună → cablare/surse pe suport poate fi task separat |

Reference order (no shared support) — 12 steps — see `REFERENCE_TASK_ORDER_NO_SHARED_SUPPORT`.

**Current WorkOS execution plan does not yet enforce these rules.** Gap documented; no changes in this build.

---

## 11. Compatibility with existing flows

| Existing artifact | V3 relationship |
|-------------------|-----------------|
| `product_spec_json` | Future: namespace `intake_v3.*` superset (no migration now) |
| `quote_input` | Via `PricingInput` adapter (future build) |
| `VolumetricQuoteReadyResult` | V3 `ReadinessReport` is parallel unified contract |
| WorkIntake V2 | Unchanged; may inform field mapping only |
| CostEngine | Untouched |
| ExecutionPlanService | Untouched |

---

## 12. Persistence strategy (this build)

- **No Alembic migration**
- Recommended future approach: `intake_schema_version=3` + `intake_v3` JSON namespace inside existing `intake_requests`
- Owner decision pending before persistence build

---

## 13. Future builds (recommended order)

1. `INTAKE_V3_VECTOR_AND_LETTER_MODEL` — Raw/Confirmed flow, 18/27/9 UX logic
2. `INTAKE_V3_FINISH_AND_MATERIAL_WORKFLOW`
3. `INTAKE_V3_PRICING_INPUT_ADAPTER`
4. `INTAKE_V3_PRODUCTION_HANDOFF_ADAPTER`
5. `AUDIT/FIX — Volumetric execution task order and electrical source handling`
6. `INTAKE_V3_UI_SHELL` — only after contracts + adapters

---

## 14. Boundary (this build)

- No UI routes/components
- No SVG parser
- No execution plan / electrical runtime changes
- No CostEngine / inventory / StockMovement
- No DB writes / migrations
- No commit/push in agent report phase
