# Documentation handoff input package (25 documents)

Structured evidence-backed inputs for `DOCUMENTATION_HANDOFF_COMPLETE`.
**Do not write the full prose package in this build.**

Shared freeze facts:

```text
Lab stop = production cost / EIC
CPP = reconciliation only
MAT-LED-PSU-12V = VARIANT_SELECTOR (no generic price)
Critical gaps = []
VL EIC 923.2 · CPP 1061 · reconcile OK
Analyzer = desktop I/O only
Authoring = Option 2
UI Lab ≠ Platform
FREEZE/DEV = contract frozen, impl deferred
Supplier Import deferred
```

Canonical APIs:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/product-system/reference-complete` | Final closure matrix + handoff stubs |
| `GET .../reference-finish-line/contract` | Finish-line package |
| `GET .../form-field-ownership-map` | 26 VL fields |
| `GET .../analyzer-io-contract` | Analyzer I/O |
| `GET .../critical-materials` | Critical classification |
| `GET /api/v1/pricing/material-market-prices` | Purchase truth registry |
| `POST .../templates/{code}/price-breakdown` | EIC/CPP breakdown |

Evidence roots:

- `docs/qa/product-system-reference-complete/`
- `docs/qa/active-template-critical-material-fill-v1/`
- `docs/qa/product-system-reference-finish-line-v1/`
- `docs/qa/material-market-price-registry-v1/`
- `docs/qa/product-price-breakdown-v1/`

Accepted commits (chain tip before this build): `7bdd9f61` · finish-line `8aac9eda` · market `f67d56a7` · breakdown `a243dd69`.

---

## 1. WORKFLOW_ADV_PRODUCT_SYSTEM_OVERVIEW

| Field | Value |
|-------|--------|
| Canonical facts | Laboratory/reference Product System closed at production cost; modular root/child; not Platform UI |
| Source code | `backend/data/product_system_reference_complete_v1.py`, finish-line data |
| Source API | `GET .../reference-complete` |
| Fixture | VL `TPL-VOLUMETRIC-LETTERS_v2` / `vl_letters_demo_v1` |
| Screenshot | `screenshots/01_reference_complete_status.png` |
| Accepted build / commit | REFERENCE_COMPLETE / (this) · CRITICAL_FILL `7bdd9f61` |
| Limitations | Lab UI badges; Logo incomplete; ACM deferred |
| Do-not-transfer | Lab UI as Platform; offer/Execution as finish line |
| Open ADV decision | Platform vs Lab repository split |

## 2. DOMAIN_MODEL

| Field | Value |
|-------|--------|
| Canonical facts | Product Template · child composition · PD · PT · quantity/formula · catalog resources · EIC |
| Source code | finish-line + identity boundary services |
| Source API | finish-line contract + reference-complete matrix |
| Fixture | VL root + Volum Aluminiu child |
| Screenshot | 01 |
| Limitations | No ComponentTemplate parallel entity required |
| Do-not-transfer | Local pseudo-resources as authority |
| Open ADV decision | Operational-process catalog persistence shape |

## 3. PRODUCT_TEMPLATE_AUTHORING

| Field | Value |
|-------|--------|
| Canonical facts | Option 2: update composition links in UI; add-child via API/seed |
| Source code | finish-line authoring decision |
| Source API | finish-line contract `authoring_decision` |
| Fixture | VL composition |
| Limitations | No full visual factory |
| Do-not-transfer | Hardcoded template-code page copies as extension model |
| Open ADV decision | Visual authoring factory scope |

## 4. CHILD_TEMPLATE_COMPOSITION

| Field | Value |
|-------|--------|
| Canonical facts | Child owns technical truth/inputs/quantities/materials; parent does not duplicate |
| Source code | Volum Aluminiu ownership proofs |
| Source API | child price-breakdown |
| Fixture | Volum Aluminiu |
| Limitations | Add-child UI deferred |
| Do-not-transfer | Parent-owned cant/material duplication |
| Open ADV decision | Broader child catalog beyond VL pilot |

## 5. FORM_SCHEMA_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | Reusable field contract frozen; VL 26-field map complete; source/destination/validation/visibility/formula impact explicit |
| Source code | finish-line form map builders |
| Source API | `GET .../form-field-ownership-map` |
| Fixture | Intake V6 VL |
| Screenshot | prior finish-line form shots (reuse) |
| Limitations | Generic Form Builder deferred |
| Do-not-transfer | VL-only UI as universal Form Generator |
| Open ADV decision | Form Builder productization |

## 6. PRODUCT_DEFINITION_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | PD = configuration intent + operator input + Analyzer proposals; versioned; not Product Truth |
| Source code | product definition preview paths |
| Source API | PD preview endpoints (prior) |
| Limitations | Lab surfaces only |
| Do-not-transfer | Treating PD as confirmed truth |
| Open ADV decision | PD versioning UX |

## 7. PRODUCT_TRUTH_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | PT = confirmed facts + provenance + revision/hash; feeds quantities/cost; Analyzer cannot silently rewrite |
| Source code | product truth confirmation services |
| Source API | PT audit/confirm paths (prior) |
| Limitations | Full audit UI polish deferred |
| Do-not-transfer | Analyzer → PT without confirmation |
| Open ADV decision | Hash/revision storage hardening |

## 8. QUANTITY_AND_FORMULA_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | Declared quantity keys; one formula owner; FE does not recalculate; parent/child not duplicated |
| Source code | price breakdown / labor recipe |
| Source API | `POST .../price-breakdown` |
| Fixture | VL + Volum Aluminiu |
| Screenshot | 03 |
| Limitations | — |
| Do-not-transfer | Frontend recalculation authority |
| Open ADV decision | Formula authoring UX |

## 9. INVENTORY_AND_MATERIAL_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | Templates reference canonical Inventory only; JIT catalog growth; no invented local materials |
| Source code | material market registry + selector policy |
| Source API | material-market-prices · critical-materials |
| Screenshot | 04 |
| Limitations | Optional consumables unpriced |
| Do-not-transfer | Template-local material invention |
| Open ADV decision | Consumable fill policy |

## 10. MATERIAL_PRICE_SOURCE_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | Purchase truth OWNER_CONFIRMED / provenance; VARIANT_SELECTOR has no raw price; concrete variants priced |
| Source code | `material_variant_selector_policy`, market registry |
| Source API | material-market-prices |
| Accepted build / commit | CRITICAL_FILL `7bdd9f61` · MARKET `f67d56a7` |
| Screenshot | 04 |
| Limitations | Supplier Import deferred |
| Do-not-transfer | Invented generic selector prices |
| Open ADV decision | Supplier Import Workflow-ADV only |

## 11. OPERATIONAL_PROCESS_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | Processes are first-class (CNC/Laser/Print/Lamination/Edge/Painting); Product System references + quantity; catalog owns rates |
| Source code | `OPERATIONAL_PROCESS_CONTRACT` in reference-complete data |
| Source API | reference-complete frozen contracts |
| Limitations | Full catalog UI deferred — boundary only |
| Do-not-transfer | Reducing processes to generic price lines |
| Open ADV decision | Process catalog schema persistence + UI |

## 12. LABOR_AND_SERVICE_RECIPE_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | Labor/services owned by recipe contracts; JIT creation when required |
| Source code | Labor Recipe Contract build |
| Source API | labor recipe / breakdown lines |
| Limitations | — |
| Do-not-transfer | Invented labor rates inside templates |
| Open ADV decision | Broader labor catalog |

## 13. AI_OPERATIONAL_DEFAULTS_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | AI defaults carry provenance; propose/ask; never write Product Truth/Pricing authority |
| Source code | AI Operational Defaults build |
| Source API | AI defaults endpoints (prior) |
| Limitations | Assistant not productionized |
| Do-not-transfer | AI silent writes into PT/cost |
| Open ADV decision | Assistant UX |

## 14. PRODUCTION_COST_BREAKDOWN_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | materials+processes+labor+services+consumables+packaging = EIC; no markup/offer in reference |
| Source code | price breakdown service |
| Source API | price-breakdown |
| Fixture | VL EIC 923.2 · CPP 1061 |
| Screenshot | 03 |
| Accepted build / commit | PRICE_BREAKDOWN `a243dd69` |
| Limitations | CPP shown for reconciliation only |
| Do-not-transfer | CPP as offer completion |
| Open ADV decision | Commercial markup path outside lab |

## 15. READINESS_AND_LIFECYCLE

| Field | Value |
|-------|--------|
| Canonical facts | Readiness scoped; activation honesty; critical materials no longer block VL reference |
| Source code | template activation + critical fill |
| Source API | activation + critical-materials |
| Limitations | Logo incomplete readiness |
| Do-not-transfer | False critical blockers on selectors |
| Open ADV decision | Lifecycle state machine for ADV |

## 16. ANALYZER_DESKTOP_INTEGRATION_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | Desktop separate; versioned I/O; observed/proposed; operator confirms; no parser in WorkOS |
| Source code | analyzer I/O contract in finish-line |
| Source API | `GET .../analyzer-io-contract` |
| Contract version | `workflow_adv_analyzer_io_contract_v1` |
| Limitations | Desktop app not built here |
| Do-not-transfer | Parser/geometry in central platform |
| Open ADV decision | Desktop Analyzer repo + production-file assistance |

## 17. REQUEST_TO_COST_FLOW

| Field | Value |
|-------|--------|
| Canonical facts | VL request → form → PD → PT confirm → quantities → catalog resources → EIC |
| Source code | Intake V6 + Product System path |
| Source API | form map + PD/PT + breakdown |
| Fixture | VL demo |
| Screenshot | 01 + 03 |
| Limitations | Offer not included |
| Do-not-transfer | Skipping operator confirmation |
| Open ADV decision | Offer after documentation |

## 18. API_CONTRACTS

| Field | Value |
|-------|--------|
| Canonical facts | Closure + finish-line + market + breakdown APIs listed above |
| Source code | routers under `backend/routers/product_system_*` |
| Source API | see table |
| Limitations | Freeze subsystem not implemented as write API |
| Do-not-transfer | Ad-hoc undocumented endpoints as authority |
| Open ADV decision | Versioned public API surface |

## 19. UI_INFORMATION_ARCHITECTURE

| Field | Value |
|-------|--------|
| Canonical facts | Lab UI diagnostics; Platform operator actions; Admin freeze/audit; Dev experimental |
| Source code | `UI_MODE_DISTINCTION` contract |
| Source API | reference-complete |
| Screenshot | 01/02 |
| Limitations | Current app is Lab UI |
| Do-not-transfer | Badge-heavy Lab as final Platform |
| Open ADV decision | Platform IA rebuild |

## 20. TEMPLATE_EXAMPLES

| Field | Value |
|-------|--------|
| Canonical facts | Complete: VL root; working child: Volum Aluminiu; incomplete: Logo |
| Fixtures | VL v2, Volum Aluminiu, Logo |
| Limitations | Logo not reference-complete path |
| Do-not-transfer | Treating Logo as complete reference |
| Open ADV decision | Additional template pilots |

## 21. TEST_FIXTURES

| Field | Value |
|-------|--------|
| Canonical facts | `vl_letters_demo_v1`; PSU 100W concrete; pytest RC/fill/finish-line |
| Source code | `backend/tests/test_product_system_reference_complete_v1.py` (+ chain) |
| Runtime | `runtime/SUMMARY.json` |
| Limitations | Incomplete pytest DB may lack golden totals — live :8020 required |
| Do-not-transfer | Weakening assertions to greenwash |
| Open ADV decision | CI proof DB seeding |

## 22. DEV_TO_IMPLEMENTATION_PROMOTION_CONTRACT

| Field | Value |
|-------|--------|
| Canonical facts | DEV MODE on draft/version only; promote then FREEZE ON |
| Source code | `DEV_MODE_CONTRACT` |
| Limitations | Implementation deferred to Workflow-ADV |
| Do-not-transfer | Mutating frozen operational version in place |
| Open ADV decision | Promotion tooling |

## 23. FREEZE_AND_VERSION_GOVERNANCE

| Field | Value |
|-------|--------|
| Canonical facts | FREEZE ON = immutable accepted operational version; owner-only unfreeze; Frozen v1 → DEV v2 → validate → promote → FREEZE |
| Source code | `FREEZE_GOVERNANCE_CONTRACT` |
| Source API | documented in reference-complete (no global write API) |
| Limitations | Global freeze subsystem not implemented in this lab |
| Do-not-transfer | Seed/agent/admin mutate frozen v1 |
| Open ADV decision | First-class freeze control plane |

## 24. WORKFLOW_ADV_MIGRATION_AND_HANDOFF

| Field | Value |
|-------|--------|
| Canonical facts | Transfer contracts + evidence, not Lab UI chrome; stop feature expansion in this laboratory |
| Source code | this package + do-not-transfer list |
| Screenshot | 01/02 |
| Limitations | Documentation prose next build |
| Do-not-transfer | Entire dirty-tree unrelated labs |
| Open ADV decision | Target repo/layout for Platform |

## 25. DEAD_AND_LEGACY_PATHS

| Field | Value |
|-------|--------|
| Canonical facts | WorkIntake V1 parallel; hardcoded VL page copies; ghost :8000 envs; invented selector prices; offer-as-finish-line misconceptions |
| Source code | AGENTS.md protected areas + do-not-transfer |
| Limitations | Dead paths may still exist in repo — not authority |
| Do-not-transfer | Legacy paths as Workflow-ADV baseline |
| Open ADV decision | Explicit deletion vs quarantine policy |
