# Product System Flow

**Current status:** PARTIAL

---

## 1. Purpose

Define **what is technologically possible** for a product family: parent template, blueprint dossier, linked module templates, operations, materials, resources, and dossier `task_rules` — upstream of ProductDefinition/Aggregate.

---

## 2. Current status

**PARTIAL** — volumetric letters v2 dossier + modules active; parent template row often thin (`components_json=[]`); dossier carries operational truth.

---

## 3. Pages / UI surfaces

> ProductSystem is a **technical library**, not a runtime task board. Template detail: [16](./16_VOLUMETRIC_LETTERS_TEMPLATE_MODULARIZATION.md).

| Route/Page | Component/File | Primary role | Secondary roles | Role of page | Reads | Writes | Status | Risk |
| ---------- | -------------- | ------------ | --------------- | ------------ | ----- | ------ | ------ | ---- |
| `/product-system` | Product system hub | Product configurator | Admin | **Template/module/dossier admin** | product_templates | CRUD (owner GO) | PARTIAL | Not shop runtime |
| `/product-system/blueprint-dossier` | Dossier editor | Configurator | Admin | **task_rules + sections source** | dossier service | dossier rows | PARTIAL | Affects future freezes |
| `/inventory/pricing` | `Pricing` | Admin / Finance | — | **Legacy registry hub** | pricing registry | admin | DEAD_LEGACY_RISK | Not CPP canonical |

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Reads | Writes | Status | Risk |
| ------ | ----- | ----------- | ------- | ----- | ------ | ------ | ---- |
| GET | `/api/v1/product-system/mini-modules*` | `product_system_mini_modules.py` | Module registry | data files | — | VALIDATED | — |
| GET | `/api/v1/product-system/aggregate/{template}` | `product_system_aggregate.py` | Aggregate preview | templates, dossier, links | — | VALIDATED | — |
| GET | `/api/v1/product-system/product-definition/{template}` | `product_system_product_definition.py` | PD preview | workspace + template | — | VALIDATED | — |
| GET | `/api/v1/product-system/cost-bom-preview/{template}` | `product_system_cost_bom_preview.py` | BOM preview | aggregate adapter | — | IMPLEMENTED_PREVIEW_ONLY | — |
| GET | `/api/v1/product_system/validate/{id}` | `product_system_validate.py` | Linkage validation | templates | — | VALIDATED | — |
| POST | `/api/v1/intake-v6/product-system/templates/volumetric-letters-v2` | intake router | Dev seed template | — | DB seed | VALIDATED | Dev only |

**Models:** `product_templates`, `product_blueprint_dossier`, `product_template_module_links`

---

## 5. Services / schemas / models

| File | Role | Input | Output | Status | Notes |
| ---- | ---- | ----- | ------ | ------ | ----- |
| `product_aggregate_service.py` | Merge parent+dossier+modules | template_code, workspace | `ProductAggregate` | VALIDATED_WITH_GUARDS | task_rules from dossier |
| `product_blueprint_dossier_service.py` | Dossier CRUD/read | template | dossier JSON | PARTIAL | task_rules_json |
| `product_template_module_links_service.py` | Module links | parent template | linked children | VALIDATED | e.g. TPL-VOLUM-ALUMINIU |
| `mini_module_registry_service.py` | Module metadata | module_code | contract | VALIDATED | — |

---

## 6. Data contract

**Dossier (typical):** `sections_json`, `task_rules_json.rules[]`, `costengine_mapping_json` (audit)

**task_rule row:** `task_name`, `task_type`, `priced_operation`, `sequence`, `trigger_condition`

**Linked module:** child `template_code` → expanded operations in aggregate (duplicate lateral risk — DEC-003/004)

**Pilot:** `TPL-VOLUMETRIC-LETTERS_v2`, modules e.g. `debitare_fata`, `modelare_cant`, `sistem_led`

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| Intake V6 | `template_code` | ProductSystem | template row + dossier | STRONG | — |
| ProductSystem | dossier + links | ProductDefinition | builder activation rules | STRONG | Parent thin |
| ProductSystem | merged graph | ProductAggregate | expand service | STRONG | Duplicate module ops |
| ProductSystem | task_rules | ExecutionPlan | via frozen aggregate snapshot | MEDIUM | WC null on parent ops |

---

## 8. Source of truth

| Aspect | Source |
| ------ | ------ |
| Possible modules/ops | **Dossier + linked module templates** (not empty parent alone) |
| task_rules for execution | **Dossier `task_rules_json`** → aggregate `task_contract` |
| Commercial rules | **Separate** — `commercial_rules_volumetric_v2` (not dossier alone) |

---

## 9. What must not happen

- Treat empty parent `components_json` as full BOM.
- Materialize module duplicate ops alongside parent task_rules (DEC-003/004).
- Use dossier CE mapping as client commercial price.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| Parent template thin | HIGH | audit: `components_json=[]` | CE legacy path | Aggregate merge (done); enrich parent WC |
| Duplicate lateral module | HIGH | TPL-VOLUM-ALUMINIU ops | Double execution | DEC-003/004; Faza 2 |
| task_rules note stale in code | LOW | "V3 catalog" comment in aggregate | Doc confusion | Docs + code comment sync |
| ACM / other templates | HIGH | Not wired in V6 | Scale | Owner GO per template |

---

## 11. Owner decisions

| Decision ID | Topic | Options | Recommended | Status |
| ----------- | ----- | ------- | ----------- | ------ |
| DEC-003 | RETURN lateral canonical | parent vs module | parent canonical | PENDING_OWNER |
| DEC-004 | painting canonical | parent vs module | parent canonical | PENDING_OWNER |
| DEC-001 | svg_geometry_analysis | non-op vs task_rule | non-operational | PENDING_OWNER |
| DEC-002 | premount_bar_preparation | BOM vs task | BOM default | PENDING_OWNER |

---

## 12. Verification checklist

```powershell
GET /api/v1/product-system/aggregate/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=...
Select-String -Path backend\services\product_aggregate_service.py -Pattern "task_rules"
```

---

## 13. Next safe step

Owner DEC-003/004 before changing dossier/task_rules for materialization; read-only aggregate audit on fixture.
