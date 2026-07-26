# PRODUCT_SYSTEM_REFERENCE_COMPLETE — Compound Engineering final map

Shared map for all agents. No parallel definitions.

| axis | entity | accepted_build | accepted_commit | current_status | required_for_reference | complete | limitation | deferred_to_adv | runtime_proof | test_proof | screenshot_proof | documentation_input | freeze_input | blocker | final_action | confidence |
|------|--------|----------------|-----------------|----------------|------------------------|----------|------------|-----------------|---------------|------------|------------------|---------------------|--------------|---------|--------------|------------|
| Product System | REFERENCE_COMPLETE package | PRODUCT_SYSTEM_REFERENCE_COMPLETE | (this build) | REFERENCE_COMPLETE | yes | yes | — | no | `GET .../reference-complete` | `test_product_system_reference_complete_v1.py` | 01 | overview | freeze readiness | none | declare PASS | high |
| Modularity | root/child composition | FINISH_LINE_V1 | 8aac9eda | MODULAR_WITH_GAPS | yes | yes | Option 2 authoring | yes (visual factory) | finish-line + reference-complete | finish-line tests | — | CHILD_TEMPLATE | contract | none | accept limits | high |
| Root ownership | TPL-VOLUMETRIC-LETTERS_v2 | FINISH_LINE_V1 | 8aac9eda | COMPLETE | yes | yes | — | no | VL template + breakdown | finish-line | 01/03 | PRODUCT_TEMPLATE | ownership | none | freeze | high |
| Child ownership | Volum Aluminiu | FINISH_LINE_V1 | 8aac9eda | COMPLETE | yes | yes | — | no | child breakdown | finish-line | — | CHILD_TEMPLATE | ownership | none | freeze | high |
| Authoring | Option 2 | FINISH_LINE_V1 | 8aac9eda | REFERENCE_LIMITATION_ACCEPTED | yes | yes | no visual add-child | yes | authoring_decision | finish-line | — | PRODUCT_TEMPLATE_AUTHORING | Option 2 | none | document | high |
| Form contract | reusable field contract | FINISH_LINE_V1 | 8aac9eda | COMPLETE_REFERENCE | yes | yes | no Form Builder | yes | form-field-ownership-map | finish-line | — | FORM_SCHEMA | field contract | none | freeze | high |
| VL schema | 26-field map | FINISH_LINE_V1 | 8aac9eda | COMPLETE_REFERENCE | yes | yes | VL-specific UI separate | no | field_count=26 | finish-line + RC | — | FORM_SCHEMA | VL map | none | freeze | high |
| Product Definition | PD preview / intent | prior PD builds | — | COMPLETE_REFERENCE | yes | yes | — | no | PD preview path | PD tests (prior) | — | PRODUCT_DEFINITION | PD≠PT | none | freeze | high |
| Product Truth | confirmed facts + provenance | prior PT builds | — | COMPLETE_REFERENCE | yes | yes | — | no | PT confirmation path | PT tests (prior) | — | PRODUCT_TRUTH | Analyzer cannot rewrite | none | freeze | high |
| Quantities | declared keys | LABOR/PRICE builds | — | COMPLETE_REFERENCE | yes | yes | — | no | breakdown lines | price-breakdown | 03 | QUANTITY_AND_FORMULA | ownership | none | freeze | high |
| Formula ownership | one owner per formula | LABOR/PRICE builds | — | COMPLETE_REFERENCE | yes | yes | FE does not recalculate | no | breakdown ownership | price-breakdown | 03 | QUANTITY_AND_FORMULA | ownership | none | freeze | high |
| Inventory | canonical materials | MATERIAL_MARKET | f67d56a7 | COMPLETE_REFERENCE | yes | yes | optional consumables | no | market registry | market + fill | 04 | INVENTORY_AND_MATERIAL | JIT rule | none | freeze | high |
| Material price truth | OWNER_CONFIRMED / provenance | MATERIAL_MARKET | f67d56a7 | COMPLETE_REFERENCE | yes | yes | no invented prices | yes (Supplier Import) | registry | market + fill | 04 | MATERIAL_PRICE_SOURCE | no invent | none | freeze | high |
| Critical materials | ACTIVE_TEMPLATE_CRITICAL | CRITICAL_FILL | 7bdd9f61 | COMPLETE | yes | yes | optional consumables only | no | critical=[] | fill tests | 04 | INVENTORY | closure | none | freeze | high |
| Operational process | boundary contract | REFERENCE_COMPLETE | (this) | CONTRACT_FROZEN | yes | yes | catalog UI deferred | yes | operational_process_contract | RC data contract | — | OPERATIONAL_PROCESS | first-class | none | freeze contract | high |
| Labor/services | recipe contract | LABOR_RECIPE | — | COMPLETE_REFERENCE | yes | yes | — | no | labor recipe path | labor tests (prior) | — | LABOR_AND_SERVICE | ownership | none | freeze | high |
| EIC | production cost finish line | PRICE_BREAKDOWN | a243dd69 | COMPLETE_AND_RECONCILED | yes | yes | — | no | 923.2 reconcile | RC + fill | 03 | PRODUCTION_COST | finish line | none | freeze | high |
| CPP | reconciliation only | PRICE_BREAKDOWN | a243dd69 | RECONCILIATION_ONLY | yes | yes | not offer authority | no | 1061 reconcile | RC + fill | 03 | PRODUCTION_COST | not offer | none | freeze | high |
| Analyzer | I/O desktop contract | FINISH_LINE_V1 | 8aac9eda | CONTRACT_FROZEN | yes | yes | no parser in WorkOS | yes (desktop app) | analyzer-io-contract | finish-line | — | ANALYZER_DESKTOP | separation | none | freeze | high |
| Scalability | SCALABLE_WITH_KNOWN_LIMITS | FINISH_LINE_V1 | 8aac9eda | ACCEPTED_WITH_LIMITS | yes | yes | known limits | yes | finish-line scalability | finish-line | — | overview | limits | none | accept | high |
| UI target | Lab/Admin/Operator/Dev | REFERENCE_COMPLETE | (this) | CONTRACT_FROZEN | yes | yes | Lab ≠ Platform | yes | ui_mode_distinction | RC data | 01/02 | UI_INFORMATION_ARCHITECTURE | distinction | none | freeze contract | high |
| Freeze governance | FREEZE ON immutability | REFERENCE_COMPLETE | (this) | CONTRACT_FROZEN | yes | yes | impl deferred | yes | freeze_governance_contract | RC data | — | FREEZE_AND_VERSION_GOVERNANCE | contract | none | freeze contract | high |
| Documentation input | 25-doc package | REFERENCE_COMPLETE | (this) | READY | yes | yes | prose docs next build | no | documentation_handoff | RC endpoint | 01/02 | all 25 | READY | none | handoff | high |
