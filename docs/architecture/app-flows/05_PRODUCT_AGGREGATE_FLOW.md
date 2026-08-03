# Product Aggregate Flow

**Current status:** VALIDATED_WITH_GUARDS

---

## 1. Purpose

**Technical graph read model** — merged components, materials, operations, BOM hints, and **`task_contract.task_rules`** for execution planning. Not commercial price.

---

## 2. Current status

**VALIDATED_WITH_GUARDS** — expand service works; duplicate lateral module ops; parent-priced ops lack workcenter on fixture.

---

## 3. Pages / UI surfaces

| Route/Page | Component/File | Role | Reads | Writes | Status | Risk |
| ---------- | -------------- | ---- | ----- | ------ | ------ | ---- |
| Intake V6 | `IntakeV6AggregateCostTruthNotice` | BOM/readiness notice | aggregate/cost-bom APIs | — | IMPLEMENTED_PREVIEW_ONLY | — |
| `/product-system` | cost BOM preview | Admin truth | GET cost-bom-preview | — | IMPLEMENTED_PREVIEW_ONLY | — |

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Reads | Writes | Status | Risk |
| ------ | ----- | ----------- | ------- | ----- | ------ | ------ | ---- |
| GET | `/api/v1/product-system/aggregate/{template_code}` | `product_system_aggregate.py` | Full aggregate | templates, dossier, links, workspace | — | VALIDATED | — |
| GET | `/api/v1/product-system/cost-bom-preview/{template_code}` | `product_system_cost_bom_preview.py` | Expanded cost BOM | aggregate adapter | — | IMPLEMENTED_PREVIEW_ONLY | — |

---

## 5. Services / schemas / models

| File | Role | Input | Output | Status | Notes |
| ---- | ---- | ----- | ------ | ------ | ----- |
| `product_aggregate_service.py` | Builder | template, workspace | `ProductAggregate` | VALIDATED_WITH_GUARDS | `_build_task_contract` |
| `schemas/product_aggregate.py` | DTO | — | components, ops, task_contract | VALIDATED | `ProductAggregateTaskRule` |
| `aggregate_cost_bom_adapter.py` | Cost BOM view | aggregate | expanded BOM | IMPLEMENTED_PREVIEW_ONLY | EIC input |

---

## 6. Data contract

**`ProductAggregate` key sections:**

| Section | Content |
| ------- | ------- |
| `components[]` | comp_face_litere, comp_lateral (module), etc. |
| `materials[]` | rolled-up with provenance |
| `operations[]` | `{ code, workcenter?, priced, provenance: parent\|linked_module }` |
| `task_contract.task_rules[]` | `{ task_name, task_type, priced_operation, sequence, mini_module_code }` |
| `modules` | linked module summary |

**Canonical vs alias (execution):**

| Role | Codes |
| ---- | ----- |
| **Canonical (planned tasks)** | Parent `priced_operation`: `side_forming`, `return_face_bonding`, `painting`, … |
| **Aggregate alias only (DEC-003/004)** | Module: `RETURN_PROFILE_*`, `PAINTING` |

**Frozen copy:** `order.snapshot_v2_json.product_aggregate_snapshot`

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| ProductDefinition | workspace context | ProductAggregate | expand | STRONG | — |
| ProductAggregate | geometry + modules | CPP / EIC | preview services | STRONG | — |
| ProductAggregate | task_rules | ExecutionPlan V2 | preview reads frozen snapshot | MEDIUM | 5 orphan ops, WC null |
| ProductAggregate | snapshot embed | Quote/Order V2 | freeze | STRONG | — |

---

## 8. Source of truth

| Aspect | Source |
| ------ | ------ |
| Expanded technical graph | **ProductAggregateService** read model |
| Execution task list driver | **`task_contract.task_rules`** (not all `operations[]`) |
| Post-order | **Frozen** aggregate inside Order Snapshot V2 |

---

## 9. What must not happen

- Using all `operations[]` rows as operational tasks (orphans exist).
- Materializing module duplicate ops when parent task_rule exists.
- Treating aggregate BOM as client commercial offer.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| Duplicate lateral ops (historical 88002) | CLOSED on F7A/Wave 2 path | alias collapse DEC-003/004 | — | Keep bridge owner |
| Ops without task_rule / orphans | MEDIUM | planned_operations audit context | Operator expectation | Keep non-operational separation |
| Parent op workcenter null (historical 88002) | CLOSED on new freeze path | Wave 2 ORR compile stamp DEC-005=E | — | Do not rewrite historical snapshots |
| Durable Wave 2 QA fixture for browser | HIGH for Wave 3 readiness | pytest ephemeral `880700–880899` only | DEC-009=B evidence pack | Owner GO for durable QA fixture |
| Stale code note "V3 catalog" | LOW | aggregate `_build_task_contract` notes | Doc drift | Comment sync (Step 12) |

---

## 11. Owner decisions

| Decision ID | Topic | Recommended | Status |
| ----------- | ----- | ----------- | ------ |
| DEC-001 | svg_geometry_analysis | non-operational | **A — RECORDED** |
| DEC-002 | premount | BOM-only default | **A — RECORDED** |
| DEC-003 | RETURN lateral | parent canonical | **A — RECORDED** |
| DEC-004 | painting | parent canonical | **A — RECORDED** |
| DEC-005 | workcenter source | ORR compile → freeze → EP frozen | **E — RECORDED (Wave 2)** |
| DEC-006 | estimated minutes | null + warning | **A — RECORDED** |
| DEC-007 | dependency DAG | finish-aware | **B — RECORDED (Wave 2)** |
| DEC-009 | POST materialize | remain blocked | **A — REMAIN BLOCKED** |

---

## 12. Verification checklist

```powershell
# Historical fixture 88002 remains regression evidence only.
# Wave 2 controlled fixture is pytest-ephemeral (_f7a_oid 880700–880899, excludes 880811/973019).
Select-String -Path backend\services\execution_plan_v2_preview_service.py -Pattern "task_contract"
cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_finalization_wave2_upstream_task_contract.py -q
```

---

## 13. Next safe step

Wave 2 upstream enrichment is complete at `788171b4`. Next: Owner Wave 3 readiness review; keep DEC-009=A until a separate Owner GO authorizes durable QA fixture evidence and sets DEC-009=B.
