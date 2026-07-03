# Product Definition Flow

**Current status:** VALIDATED

---

## 1. Purpose

**Compile** concrete product from Intake workspace + template: which mini-modules activate, canonical values, operation roles, readiness/blockers. No pricing, no execution persistence.

---

## 2. Current status

**VALIDATED** — read-only builder; fail-closed gates; consumed by aggregate, CPP, EIC, snapshot freeze.

---

## 3. Pages / UI surfaces

| Route/Page | Component/File | Role | Reads | Writes | Status | Risk |
| ---------- | -------------- | ---- | ----- | ------ | ------ | ---- |
| Intake V6 review panels | various `IntakeV6*` | Show readiness | PD preview API (optional) | — | PARTIAL | — |
| Product system UI | aggregate/PD previews | Admin/debug | GET product-definition | — | IMPLEMENTED_PREVIEW_ONLY | — |

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Reads | Writes | Status | Risk |
| ------ | ----- | ----------- | ------- | ----- | ------ | ------ | ---- |
| GET | `/api/v1/product-system/product-definition/{template_code}` | `product_system_product_definition.py` | PD preview | workspace, template, form contract | — | VALIDATED | Query: workspace_id |

---

## 5. Services / schemas / models

| File | Role | Input | Output | Status | Notes |
| ---- | ---- | ----- | ------ | ------ | ----- |
| `product_definition_builder_service.py` | Compiler | workspace_id, template | `ProductDefinitionPreview` | VALIDATED | No pricing imports |
| `schemas/product_definition.py` | DTO | — | modules, operation_roles, validation | VALIDATED | — |

**Output slices:** `active_modules[]`, `operation_roles[]`, `material_roles[]`, `validation.readiness`, `missing_fields[]`

---

## 6. Data contract

**Input:** `intake_v6_workspaces.payload_json` + `template_code` + mini-module registry

**Output (embedded in snapshots as `product_definition_snapshot`):**

| Key | Meaning |
| --- | ------- |
| `template_code` | ProductSystem binding |
| `modules[]` | Active/inactive mini-modules |
| `operation_roles[]` | `{ operation_code, label, workcenter?, component_ref }` |
| `validation.status` | NOT_READY / READY semantics |
| `provenance[]` | Compile trail |

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| Intake V6 | payload_json | ProductDefinition | builder | STRONG | Missing geometry blocks |
| Form System | field paths | ProductDefinition | activation triggers | MEDIUM | Hardcoded pilot |
| ProductDefinition | output | ProductAggregate | expand | STRONG | — |
| ProductDefinition | snapshot embed | Quote/Order V2 | freeze | STRONG | Frozen at snapshot time |

---

## 8. Source of truth

| Aspect | Source |
| ------ | ------ |
| Live compile | **Derived** from workspace + template at request time |
| Post-accept truth | **Frozen** `product_definition_snapshot` in Order Snapshot V2 |
| Upstream input truth | **Intake workspace payload** |

---

## 9. What must not happen

- ProductDefinition setting commercial price or writing quotes.
- Silent defaults on missing critical geometry (fail-closed).
- Parallel V3 catalog overriding PD for production tasks.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| operation_roles workcenter often null | HIGH | fixture order 88002 | ExecutionPlan WC | DEC-005 upstream enrich |
| Layer-1 only processes | MEDIUM | audit note | Multi-layer jobs | Owner decision |
| QuoteOrchestrator builds PD at /price | MEDIUM | legacy path | Dual truth | Freeze /price for V2 |

---

## 11. Owner decisions

None currently known beyond downstream DEC-005 (workcenter enrichment affects PD roles).

---

## 12. Verification checklist

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_product_aggregate_volumetric_v2.py -q  # if env ready
GET /api/v1/product-system/product-definition/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=...
```

---

## 13. Next safe step

Use PD preview gates in Intake before freeze; do not recompile for pricing on ExecutionPlan path (use frozen snapshot).
