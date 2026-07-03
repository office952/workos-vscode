# FACE-BACK-PREP ProductSystem Contract — Pre-Registry Integration Audit

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `9acc668` (`fix(volumetric): apply CNC pass counts to face-back prep draft`)  
**Mode:** read-only audit — no code, registry, CostEngine, UI, quote/order, tasks, or stock changes  
**Build label:** `AUDIT_FACE_BACK_PREP_PRODUCTSYSTEM_CONTRACT_BEFORE_REGISTRY_INTEGRATION`

---

## 1. Verdict scurt

**`tpl_volumetric_face_back_prep_productsystem_contract.py` este un contract Python local canonic** — metadata, componente, operații, material mappings, task order, exclusions — **nu** este încă registry ProductSystem complet funcțional.

Există deja un **seed parțial** (`seed_tpl_volumetric_face_back_prep_template.py`, commit `30f746b`) care scrie rând inactiv în `product_templates`, dar **lanțul ProductSystem complet** (dossier, CostEngine, quote handoff, production task rules) **lipsește**.

Cost draft service **consumă parțial** contractul (constante, keys, vector perimeter keys) dar **redefinește** pass-count runtime, labels, task draft structure și perimeter resolution logic.

**Recomandare:** păstrează contractul ca sursă de adevăr; refactor incremental ca service + seed să citească pass-count, labels, task order și vector keys exclusiv din contract (sau din helpers exportați de contract); reconciliază semantic divergența Forex 10 mm față de `shared_cnc_operation_model.py`.

---

## 2. Scope

| In scope | Out of scope |
|----------|--------------|
| Ce este contractul existent | Implementare registry complet |
| Dublări față de cost draft / CNC shared model | Modificări cod |
| Starea registry ProductSystem la HEAD | CostEngine / quote / production |
| Plan următor build | UI Intake V4 |

---

## 3. Surse citite

### Cod (read-only)

| File | Rol |
|------|-----|
| `backend/services/tpl_volumetric_face_back_prep_productsystem_contract.py` | Contract canonic Python |
| `backend/services/tpl_volumetric_face_back_prep_cost_draft_service.py` | Consumer Intake V4 cost draft |
| `backend/seeds/seed_tpl_volumetric_face_back_prep_template.py` | Seed `product_templates` (inactive) |
| `backend/schemas/intake_v4.py` | Template code constants + response schemas |
| `backend/services/intake_v4_cnc_router_pass_policy_service.py` | Pass-count depth rules |
| `backend/services/shared_cnc_operation_model.py` | CNC preview rules (TPL-VOLUMETRIC-LETTERS) |
| `backend/seeds/seed_build4_templates.py` | BUILD4 registry pattern (6 templates) |
| `backend/scripts/seed_sync_all.py` | Pipeline seed |
| `backend/tests/test_tpl_volumetric_face_back_prep_cost_draft.py` | Cost draft tests |
| `backend/tests/test_tpl_volumetric_face_back_prep_productsystem_registry.py` | Contract + seed tests |

### Docs (read-only)

| File | Rol |
|------|-----|
| `docs/architecture/TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CONTRACT.md` | Product intent + CNC rules |
| `docs/architecture/TPL_VOLUMETRIC_FACE_BACK_PREP_PRODUCTSYSTEM_INTEGRATION.md` | Integration architecture (build `30f746b`) |
| `docs/qa/FIX_TPL_VOLUMETRIC_FACE_BACK_PREP_CNC_PASS_COUNTS_AND_VECTOR_PERIMETER_TRUTH.md` | Pass-count fix QA |
| `docs/architecture/PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md` | Full onboarding lifecycle |

---

## 4. Ce este contractul ProductSystem existent

### Răspuns la întrebările obligatorii

| Question | Answer |
|----------|--------|
| Template key? | **Da** — `TEMPLATE_METADATA["key"]` = `TPL-VOLUMETRIC-FACE-BACK-PREP` (importă constanta din `schemas/intake_v4.py`) |
| Componente? | **Da** — `PRODUCTSYSTEM_COMPONENTS` (`FACE_PLEXI`, `BACK_FOREX`) |
| Operații? | **Da** — `PRODUCTSYSTEM_OPERATIONS` (7 operații V1) |
| Pass-count rules? | **Da** — `FACE_CNC_CUT_PASS_COUNT=1`, `FACE_CNC_SHANFREN_PASS_COUNT=1`, `BACK_FOREX_CNC_CUT_PASS_COUNT=3`, `BACK_FOREX_CNC_SHANFREN_PASS_COUNT=2` |
| Material mappings? | **Da** — `MATERIAL_REGISTRY_BY_LOGICAL_KEY` |
| Task draft order? | **Da** — `task_draft_order(shanfren_forex_enabled=…)` |
| Folosit de service? | **Parțial** — importă keys, registry codes, vector perimeter key tuples; **nu** folosește pass constants, `task_draft_order`, `get_operation_spec`, `PRODUCTSYSTEM_OPERATIONS` labels |
| Folosit de endpoint? | **Indirect** — router → cost draft service → contract constants |
| Folosit de teste? | **Da** — ambele suite pytest importă contractul |
| ProductSystem registry sau contract local? | **Contract local Python** + seed DB parțial; **nu** dossier / CostEngine / quote-ready registry |

### Clasificare

```txt
tpl_volumetric_face_back_prep_productsystem_contract.py =
  început de model ProductSystem (canonical Python module)
  + constante + catalog declarativ
  NU = registry runtime complet
  NU = înlocuitor product_templates JSON loaded at quote time
```

Funcții helper exportate: `task_draft_order`, `get_operation_spec`, `is_template_excluded_capability`, `productsystem_template_notes`.

**Notă tehnică:** `ProductSystemOperationSpec` referă `ComponentKey` în TypedDict dar tipul `ComponentKey` **nu este definit** în fișier (latent bug — nu remediat în acest audit).

**Notă:** `PRODUCTSYSTEM_OPERATIONS` descrie `unitPrice` per ml **fără** `pass_count` — pass-count există ca constante separate, nu pe fiecare operație în catalog.

---

## 5. Ce folosește cost draft service

### Importuri din contract

```txt
CNC_RATE_EUR_PER_ML (importat, nefolosit direct — service folosește DEFAULT_CNC_RATE_EUR_PER_ML_PASS)
MATERIAL_KEY_*, OP_CNC_*, REGISTRY_* codes
TASK_* keys
TEMPLATE_METADATA (importat, nefolosit)
VECTOR_FACE/BACK_PERIMETER_KEYS
```

### Logică proprie (nu din contract)

| Concern | Unde |
|---------|------|
| Pass-count runtime | `face_plexi_cnc_passes()` / `forex_backing_cnc_passes()` din `intake_v4_cnc_router_pass_policy_service.py` |
| CNC rate aplicat | `DEFAULT_CNC_RATE_EUR_PER_ML_PASS` (pass policy), nu `CNC_RATE_EUR_PER_ML` din contract |
| Operation labels | String literals hardcoded în `_operation_row` calls |
| Task draft graph | `_build_task_drafts()` — structură manuală, nu `task_draft_order()` |
| Vector perimeter resolution | `_resolve_vector_perimeter_ml()` duplică key lists din contract |
| Workspace geometry / backing / shanfren | Intake V4 services (`backing_mode`, finish setup) |
| Material cost | Area-based cu fallback față→spate (permis doar material) |
| Response assembly | `schemas/intake_v4` Pydantic models |

### Endpoint

```txt
GET /api/v1/intake-v4/workspaces/{id}/volumetric-face-back-prep/cost-draft
```

Consumator read-only; **nu** citește `product_templates` row la runtime — aplică contract Python + workspace payload.

---

## 6. Ce există deja ca ProductSystem registry

### Pattern canonical (BUILD4 — referință)

| Artifact | Location | Face-back prep |
|----------|----------|----------------|
| Template definitions | `seed_build4_templates.TEMPLATE_DEFINITIONS` (6 templates) | **Nu inclus** — seed separat |
| DB row | `product_templates` | **Da** — via `seed_tpl_volumetric_face_back_prep_template` |
| Active commercial scope | `seed_active_template_scope` | **Nu** — doar `TPL-VOLUMETRIC-LETTERS` activ |
| Blueprint dossier | `ProductBlueprintDossier` | **Lipsește** |
| CostEngine mapping | dossier `costengine_mapping_json` | **Lipsește** |
| Production task rules | dossier `task_rules_json` | **Lipsește** |
| Pricing input adapter | `docs/intake-v3/templates/TPL-VOLUMETRIC-LETTERS/09_*` | **Lipsește** pentru face-back prep |
| Intake V4 binding | `PILOT_V4_TEMPLATE_CODE = TPL-VOLUMETRIC-LETTERS` | Workspace pilot pe template complet |

### Seed existent (commit `30f746b`)

- Scrie `components_json`, `operations_json`, `required_materials_json` derivate din contract
- `active=False`, notes `cost_draft_only=true`
- Operațiile seed folosesc `calculation_type: draft_fixed_ml` **fără** `pass_count` în JSON
- Pipeline: `seed_sync_all.py` step `tpl_volumetric_face_back_prep` (după BUILD4)

### Concluzie registry

Registry **DB parțial există**; integrarea **completă** (playbook secțiuni 3–29) **nu**.

---

## 7. Dublări găsite

| Concern | Contract | Cost draft service | Pass policy | shared_cnc_operation_model | Seed JSON |
|---------|----------|-------------------|-------------|---------------------------|-----------|
| Template key | `TEMPLATE_METADATA` + import schema | `schemas/intake_v4` constants | — | — | `template_code` |
| Material mappings | `MATERIAL_REGISTRY_BY_LOGICAL_KEY` | import registry codes | — | material_key strings | `_mat_formula` codes |
| Operation keys | `operation_key` + `OP_CNC_*` aliases | import aliases | — | `cnc_*_plexiglas_3mm` etc. | `productsystem_operation_key` |
| Pass counts | constants 1/1/3/2 | **pass policy functions** | depth-based ceil | Forex cut **5 passes single row** | **absent** |
| Unit price 1.5 | `CNC_RATE_EUR_PER_ML` | `DEFAULT_CNC_RATE_EUR_PER_ML_PASS` | same value | via preview builder | `unit_price_eur` |
| Task draft order | `task_draft_order()` | `_build_task_drafts()` duplicate | — | — | sequence in components |
| Vector perimeter keys | `VECTOR_*_PERIMETER_KEYS` | `_resolve_vector_perimeter_ml` copy | `resolve_cnc_cutting_perimeter_ml` (face, broader keys) | basis_key strings | — |
| Operation labels | `PRODUCTSYSTEM_OPERATIONS[].label` | hardcoded în service | — | `display_name` | label in seed |

### Divergență critică — Forex 10 mm

| Model | Semantics |
|-------|-----------|
| Face-back prep (owner V1) | `CUT_BACK` 3 passes + optional `SHANFREN_BACK` 2 passes = 5 total |
| `forex_backing_cnc_passes()` | Aligned: cut=3, bevel=2 when enabled |
| `shared_cnc_operation_model` `VOLUMETRIC_BACKING_CUTTING_RULE` | **Single row passes=5** (`FOREX_10MM_CUTTING_PASSES_OWNER`) for TPL-VOLUMETRIC-LETTERS CostEngine preview |

Aceeași cheie shared CNC (`cnc_backing_cutting_forex_10mm`) mapată în contract, dar **pass semantics diferite** între agregat (5 pe un rând) vs split (3+2). Risc de double-count sau formulă diferită la compoziție cu `TPL-VOLUMETRIC-LETTERS`.

---

## 8. Sursa de adevăr recomandată

| Concern | Single source of truth (target) | Current state |
|---------|--------------------------------|---------------|
| Template identity | ProductSystem contract → `product_templates` row | Contract + schema constants (dual) |
| Component model | Contract `PRODUCTSYSTEM_COMPONENTS` → seed `components_json` | Aligned at seed time; service uses partial imports |
| Operation model | Contract `PRODUCTSYSTEM_OPERATIONS` | Labels duplicated in service |
| Pass-count | Contract constants **sau** shared helper owned by contract wrapping pass policy | **Pass policy called directly in service**; contract constants unused at runtime |
| Material mapping | Contract `MATERIAL_REGISTRY_BY_LOGICAL_KEY` | Service imports — OK |
| Task draft order | Contract `task_draft_order()` + optional dependency metadata | Service `_build_task_drafts()` reimplements |
| Vector perimeter rules | Contract `VECTOR_*_PERIMETER_KEYS` + documented exclusions | Duplicated resolver in service |
| V1 exclusions | Contract `TEMPLATE_EXCLUDES` | Not enforced in service runtime |

**Principiu confirmat pe cod:**

```txt
ProductSystem contract/registry = sursa de identitate și catalog
Cost draft service = consumer (geometry + prices + contract catalog)
Intake V4 endpoint = consumer al service-ului, nu sursă de adevăr
```

---

## 9. Ce trebuie alimentat în ProductSystem (următorul build)

1. **Enrich contract operations** — adaugă `passCount` pe fiecare operație CNC în `PRODUCTSYSTEM_OPERATIONS`; exportă `get_pass_count(task_key, shanfren_forex_enabled)`.
2. **Service refactor** — service citește labels, pass_count, task order din contract; elimină string literals duplicate; folosește `CNC_RATE_EUR_PER_ML` sau un singur import rate.
3. **Seed alignment** — persist `pass_count` în `operations_json`; optional `vector_perimeter_basis_key` per CNC op.
4. **Reconciliere shared CNC model** — documentează mapping explicit: split rows (face-back prep) vs aggregated row (full letters CostEngine); evită 3+2+5 double count la compoziție.
5. **Blueprint dossier** (playbook) — `ProductBlueprintDossier` pentru partial template sau module reference inside volumetric dossier.
6. **Fix `ComponentKey` TypedDict** — definește tipul lipsă.
7. **Template docs pack** — `docs/intake-v3/templates/TPL-VOLUMETRIC-FACE-BACK-PREP/` (scope, material intent, operation catalog) mirror letters pack.
8. **Runtime registry read** (optional phase) — `resolve_product_template_or_raise("TPL-VOLUMETRIC-FACE-BACK-PREP")` în cost draft pentru validare identitate DB vs contract.
9. **Teste** — assert service pass_count == contract; assert seed JSON pass_count; cross-test vs pass policy; guard against shared_cnc 5-pass aggregate mismatch.

### Ce NU mai trebuie (deja făcut parțial)

- Creare fișier contract — **există**
- Seed idempotent `product_templates` — **există** (`30f746b`)
- Pipeline seed — **există**

---

## 10. Cum se integrează cu TPL-VOLUMETRIC-LETTERS

```txt
TPL-VOLUMETRIC-LETTERS (full, active commercial)
  may include / reference:
    TPL-VOLUMETRIC-FACE-BACK-PREP (partial module, draft_internal)
```

| Aspect | Reuse direct | Rămâne specific full template | Nu duplica |
|--------|--------------|------------------------------|------------|
| Face plexi 3 mm material | `MAT-ACP-FATA-LITERE` mapping | cant, vinyl, lighting | pass-count formulas în 3 locuri |
| Back Forex 10 mm | `MAT-SPATE-PVC-LITERE` | mounting, PSU, assembly | Forex cost ca 1+1 ml rows |
| Shared CNC keys | `cnc_face_cutting_plexiglas_3mm`, bevel, backing cut/bevel | edge forming, LED routes | `FOREX_10MM_CUTTING_PASSES_OWNER=5` vs 3+2 split |
| Vector perimeter | same geometry keys in workspace | letter depth, LED pockets | bbox/nesting perimeter |
| Operations | prep, cut, shanfren, clean, pack | side_forming, wiring, QC gates | task_rules_json from full dossier |

### Perimetru vectorial sfânt

Ambele template-uri trebuie să consume **aceleași chei geometry** (`cnc_cutting_perimeter_ml`, `backing_cnc_cutting_perimeter_ml`). Modulul partial **nu** trebuie să relaxeze regula față de full template.

### Evitarea a două formule Forex

La compoziție viitoare, alege **un model canonical**:

- **Option A (recommended for partial):** split rows 3 + 2, total 5 ml-pass equivalent
- **Option B (full letters today):** single backing cut row with passes=5

Documentează transformarea B→A sau un adapter CostEngine care nu sumează ambele.

---

## 11. Riscuri

| Risk | Severity | Mitigation |
|------|----------|------------|
| Pass-count dual source (contract constants vs pass policy vs shared_cnc 5-pass) | **High** | Single helper; tests lock values |
| Seed JSON fără pass_count | **Medium** | Extend seed + contract |
| Service labels drift from catalog | **Medium** | Read labels from `OPERATION_BY_KEY` |
| `ComponentKey` undefined | **Low** | Fix TypedDict |
| `TEMPLATE_METADATA` / `CNC_RATE` unused imports | **Low** | Use or remove |
| Partial template counted in BUILD4 "6 templates" tests | **Low** | Already separate seed — keep separate |
| Full letters CostEngine + partial draft both price same CNC keys | **High** | Composition boundary doc + integration tests |
| Registry row inactive — operators assume "registered = quote ready" | **Medium** | status metadata + UI boundary |

---

## 12. Pași recomandați pentru următorul build

**Build label sugerat:** `BUILD_TPL_VOLUMETRIC_FACE_BACK_PREP_PRODUCTSYSTEM_CONTRACT_CONSUMPTION_AND_PASS_ALIGNMENT`

1. Extend contract: `passCount` on operations; fix `ComponentKey`; export `resolve_pass_counts(shanfren_forex_enabled)`.
2. Refactor cost draft service to consume contract for labels, pass counts, task order, rate.
3. Update seed JSON to include `pass_count` on CNC operations.
4. Add reconciliation doc section: face-back prep split vs volumetric letters aggregate Forex rule.
5. Add dossier stub or module reference in volumetric blueprint (read-only, no task creation).
6. Tests: contract ↔ service ↔ seed parity; no regression on vector perimeter protection.
7. Optional: Intake V4 workspace binding awareness of partial template code (still no UI scope creep).

---

## 13. Ce nu se face acum

- Modificări cod / registry / CostEngine / UI
- Quote / order / real tasks / ExecutionPlan / `tasks_json`
- Stock consumption
- Commit / push
- Activare commercial `active=true` pentru partial template
- Oracal / print / laminare / policromie

---

## Audit checklist

| Item | Status |
|------|--------|
| Pre-flight HEAD `9acc668` | PASS |
| Tracked clean (untracked externe OK) | PASS |
| Contract classified | Local canonical Python module |
| Registry state documented | Partial DB seed only |
| Duplications listed | PASS |
| Truth source recommended | Contract → registry → consumers |
| TPL-VOLUMETRIC-LETTERS relation | Documented |
| No code changes | PASS |
| No commit/push | PASS |
