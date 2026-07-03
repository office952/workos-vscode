# Form System Flow

**Current status:** PARTIAL

---

## 1. Purpose

Describe **which Intake fields exist**, how they map to mini-modules and ProductDefinition keys, and module activation semantics — derived from ProductSystem registry, not ad-hoc per-screen hardcoding (target).

---

## 2. Current status

**PARTIAL** — read-only form contract for pilot template; hardcoded `VOLUMETRIC_FIELD_BINDINGS` plus registry modules.

---

## 3. Pages / UI surfaces

> Modularization plan: [15_FORM_SYSTEM_MODULARIZATION_PLAN.md](./15_FORM_SYSTEM_MODULARIZATION_PLAN.md) · Roles: [14](./14_APP_ROLES_AND_PAGE_RESPONSIBILITIES.md).

| Route/Page | Component/File | Primary role | Secondary roles | Role of page | Reads | Writes | Status | Risk |
| ---------- | -------------- | ------------ | --------------- | ------------ | ----- | ------ | ------ | ---- |
| Intake V6 steps | `IntakeV6ModularFormAwarenessPanel`, steps | Intake operator | Configurator | **Form presentation** — maps fields to workspace | GET form-contract | workspace PUT | PARTIAL | UI partly hardcoded |
| `/product-system` admin | `FormSystemAdminPanel` | Product configurator | Admin | **Registry admin** — not operator intake | mini-modules API | — | PARTIAL | Not order flow |

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Reads | Writes | Status | Risk |
| ------ | ----- | ----------- | ------- | ----- | ------ | ------ | ---- |
| GET | `/api/v1/intake-v6/form-contract/{template_code}` | `intake_v6_modular_form.py` | Modular contract | mini-module registry | — | VALIDATED | Pilot only |
| GET | `/api/v1/product-system/mini-modules*` | `product_system_mini_modules.py` | Module registry | `mini_module_registry` data | — | VALIDATED | — |

---

## 5. Services / schemas / models

| File | Role | Input | Output | Status | Notes |
| ---- | ---- | ----- | ------ | ------ | ----- |
| `intake_v6_modular_form_contract_service.py` | Build contract | template_code | `IntakeV6ModularFormContract` | PARTIAL | `PILOT_TEMPLATE` constant |
| `schemas/intake_v6_modular_form.py` | Field bindings, sections | — | DTOs | VALIDATED | — |
| `data/mini_module_registry_volumetric_v2.py` | Module defs | — | registry | VALIDATED | Source for activation |

---

## 6. Data contract

**Response:** `modules[]`, `field_bindings[]`, `trigger_alignments[]`

**Binding fields:** `canonical_key`, `workspace_path`, `module_codes[]`, `product_definition_keys[]`, `field_role`, `operational_status`

**Example paths:** `finish_setup.return_depth_mm` → module `modelare_cant`; `quote_geometry.letter_count` → commercial geometry keys.

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| ProductSystem | mini-module codes | Form contract | registry + bindings | STRONG | Hardcoded volumetric bindings |
| Form contract | workspace_path | Intake V6 UI | reducer reads payload | MEDIUM | Not all UI generated from contract |
| Form contract | product_definition_keys | ProductDefinition | builder `_get_by_path` | STRONG | Generalization needed |

---

## 8. Source of truth

| Aspect | Source |
| ------ | ------ |
| Module catalog | **mini-module registry** + dossier alignment |
| Field → workspace mapping | **form contract service** (pilot: hardcoded list + registry) |
| Runtime values | **Intake workspace `payload_json`** |

---

## 9. What must not happen

- Duplicate field definitions per product without registry backing.
- Form contract silently defaulting missing required fields (fail-closed in PD builder instead).
- Using form contract as pricing truth.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| Hardcoded pilot bindings | MEDIUM | `VOLUMETRIC_FIELD_BINDINGS` | New templates | Generalize from registry |
| UI not fully generated from contract | MEDIUM | Many Intake components | Drift | Step 11+ refactor GO |
| Trigger field mismatches | LOW | `TRIGGER_FIELD_MISMATCHES` in aggregate | Wrong module activation | Owner align triggers |

---

## 11. Owner decisions

None currently known.

---

## 12. Verification checklist

```powershell
GET /api/v1/intake-v6/form-contract/TPL-VOLUMETRIC-LETTERS_v2  # read-only when stack up
Select-String -Path backend\services\intake_v6_modular_form_contract_service.py -Pattern "VOLUMETRIC_FIELD_BINDINGS"
```

---

## 13. Next safe step

Keep form contract read-only; extend bindings only with owner GO for new template activation.
