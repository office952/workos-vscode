# MATERIALS_SOURCE_AND_SEMANTICS_MATRIX — Ops-Graph 92401

**Date:** 2026-08-01  
**Repo:** `C:\w\psiso`  
**Surface:** `http://127.0.0.1:3000/execution/ops-graph?orderId=92401`  
**No UI change was authorized.** Current screenshots = audited accepted state, not after-state.

---

## A. What the ops-graph UI actually shows about materials

| UI location | Task/operation | Current label | Displayed value | Unit | Source path | Frozen or live | Ownership | Real semantic | Operator interpretation | Honest? | Classification | Recommended action |
| ----------- | -------------- | ------------- | --------------: | ---- | ----------- | -------------- | --------- | ------------- | ----------------------- | ------- | -------------- | ------------------ |
| Ops-graph table columns | all 18 ops | *(no Materials column)* | *(absent)* | — | `MaterializedOpsGraph.tsx` headers SEQ/Status/Task/Process/Type/Code/WC/Min/Depends/Gaps | n/a | UNKNOWN | UNKNOWN_SEMANTIC | Operator may assume materials are not part of this screen, or that none exist | AMBIGUOUS — absence without explanation | SOURCE_GAP | Owner GO: honest empty/absence note or frozen technical materials section |
| Page body text | page | Materiale / Necesare / Consumate / Rezervate / În stoc | **0 occurrences** | — | DOM text scan | n/a | n/a | n/a | No materials vocabulary on page | N/A (nothing claimed) | CORRECT *(no false claim)* | Keep calm; do not invent labels without data |
| DEC-009 / OwnerGo banners | page | “materialize” / “already-materialized” / `operational_tasks[]` | lifecycle wording | — | `OwnerGoNotice`, capacity strip | live capacity + audit GET | UNKNOWN | IDENTIFIER_ONLY *(lifecycle, not BOM)* | Risk: “materializat” ≠ materiale fizice | AMBIGUOUS_LABEL | LABEL_ONLY_FIX *(optional)* | Optional glossary note: materialize = task envelope, not inventory |
| OR-09 label note | page | “commercial EUR/ml phrasing” | 2 task labels | EUR/ml in provenance | template `display_name` + soften helper | frozen template label | OPERATION | COMMERCIAL_PRICE *(phrasing only)* | Softened in display; hover keeps provenance | PARTIAL | PRICE_LEAKAGE | Already mitigated; upstream Product System rename remains Owner track |
| Metrics tiles | page | Ops / Sessions / Actuals | 18 / 0 / 0 | count | plan GET + audit.guards + reality GET | live read | TASK | not materials | Correct non-materials metrics | YES | CORRECT | Keep |
| Task names (incidental) | e.g. SEQ3 Forex, SEQ6 RAL, SEQ7 folie, SEQ8 LED | task process names | text only | — | operational_tasks.display_name | frozen planning labels | OPERATION | IDENTIFIER_ONLY | Mentions materials as process context, not BOM qty | YES as process labels | CORRECT | Do not treat as BOM |

---

## B. API / envelope fields present but not rendered

| UI location | Task/operation | Current label | Displayed value | Unit | Source path | Frozen or live | Ownership | Real semantic | Operator interpretation | Honest? | Classification | Recommended action |
| ----------- | -------------- | ------------- | --------------: | ---- | ----------- | -------------- | --------- | ------------- | ----------------------- | ------- | -------------- | ------------------ |
| *(not in UI)* | each of 18 ops | `material_inputs` | `[]` empty | — | `tasks_json.operational_tasks[].material_inputs` via GET `/execution/plan/{orderId}` ← parser copies from planned | frozen envelope | TASK | UNKNOWN_QUANTITY / empty PLANNED_REQUIREMENT | If shown as “none”, may falsely mean no materials needed | AMBIGUOUS if exposed without context | SOURCE_GAP | Do not render empty arrays as “0 materials needed” without Owner wording |
| *(not in UI)* | each of 18 ops | `quantity` | `1` | dimensionless plan count | hardcoded `1.0` in `execution_plan_task_parser.py` | derived at materialize | TASK | ESTIMATED_QUANTITY *(task count, not BOM)* | If labeled “Cantitate” could look like material qty | Latent risk | FALSE_ZERO *(latent)* | Never map task.quantity to material qty without explicit label |
| *(not in UI)* | plan envelope | `material_readiness_inputs` | **key absent** on plan 13 | — | preview builds it; `build_tasks_json_envelope` **does not persist** it | n/a | PRODUCT/COMPONENT | TECHNICAL_REQUIREMENT *(intended)* | Not available to ops-graph | SOURCE_GAP | READ_MODEL_FIX | Persist readiness from frozen aggregate **or** read snapshot on GET |
| Reality materials API | order | GET `/execution/reality/{id}/materials` | `materials: []`, `total_count: 0` | — | `execution_reality.materials_json` | live | INVENTORY | ACTUAL_CONSUMPTION *(empty)* | Correct: no consumption | YES | CORRECT | Keep; do not show as “0 used” without “no reality row” nuance |
| Reality row | order | GET `/execution/reality/92401` | 404 `reality_not_found` | — | `execution_reality` | live | INVENTORY | ACTUAL_CONSUMPTION absent | No actuals | YES | CORRECT | Actuals tile already shows 0 from null reality |

---

## C. Frozen Order snapshot materials (upstream truth — not on ops-graph)

Source: `orders.snapshot_v2_json.product_aggregate_snapshot.materials` for order **92401** (22 rows).  
All `quantity = null`. All `status = present` (= structural presence, **not** stock). Units: mp/ml/buc/set. Provenance: parent (12) + linked_module (10).

| UI location | Task/operation | Current label | Displayed value | Unit | Source path | Frozen or live | Ownership | Real semantic | Operator interpretation | Honest? | Classification | Recommended action |
| ----------- | -------------- | ------------- | --------------: | ---- | ----------- | -------------- | --------- | ------------- | ----------------------- | ------- | -------------- | ------------------ |
| *(not on ops-graph)* | product / face | MAT-ACP-FATA-LITERE | code+label; qty null | mp | snapshot PA materials | frozen | COMPONENT (`comp_face_litere`) | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | Would mean “needed somehow” if shown without qty honesty | Would be honest if labeled frozen requirement + qty Nespecificat | SOURCE_GAP *(not projected)* | Surface under Owner GO with honest labels |
| *(not on ops-graph)* | product / face | MAT-ORACAL-651 | duplicate code also under linked_module | mp | parent + linked_module rows | frozen | COMPONENT | TECHNICAL_REQUIREMENT | Duplicate codes ≠ auto-sum | DUPLICATION_RISK | DUPLICATION_RISK | Do not aggregate by code alone |
| *(not on ops-graph)* | product / face | MAT-VINYL-PRINT | qty null | mp | parent | COMPONENT | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | — | SOURCE_GAP | same |
| *(not on ops-graph)* | product / face | MAT-VINYL-PRINT-LAMINATED | qty null | mp | parent | COMPONENT | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | — | SOURCE_GAP | same |
| *(not on ops-graph)* | product / lateral | MAT-PROFIL-LATERAL-LITERE (+ 30/60/80/100MM variants) | qty null | ml | parent + module variants | COMPONENT | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | Variants may be alternatives vs additive | OWNER_DECISION_REQUIRED | Do not invent which variant is active without Product Truth |
| *(not on ops-graph)* | product / back | MAT-SPATE-PVC-LITERE | qty null | mp | parent | COMPONENT | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | — | SOURCE_GAP | same |
| *(not on ops-graph)* | product / LED | MAT-LED-MODULE | qty null | buc | parent | COMPONENT | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | — | SOURCE_GAP | same |
| *(not on ops-graph)* | product / LED | MAT-LED-PSU-12V | qty null | buc | parent | COMPONENT | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | — | SOURCE_GAP | same |
| *(not on ops-graph)* | product / paint | MAT-VOPSEA-RAL | duplicate parent+module | ml | parent + linked_module | COMPONENT | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | Duplicate risk | DUPLICATION_RISK | same |
| *(not on ops-graph)* | product / mounting | MAT-SABLON-HARTIE / MAT-SABLON-MONTAJ / MAT-CONSUMABILE-MONTAJ / MAT-SURUBURI-GEN | qty null | set/buc | parent/module | COMPONENT | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | — | SOURCE_GAP | same |
| *(not on ops-graph)* | module | MAT-ADEZIV-CANT-LITERE | qty null | ml | linked_module | COMPONENT | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | — | SOURCE_GAP | same |
| *(not on ops-graph)* | module | MAT-ACM-BOND-PANEL | duplicate ×2 | mp | linked_module | COMPONENT | TECHNICAL_REQUIREMENT + UNKNOWN_QUANTITY | Duplicate rows | DUPLICATION_RISK | same |
| *(not on ops-graph)* | commercial / EIC snapshots | commercial lines / estimated_material_lines | **ignored by plan** (`ignored_pricing_sources`) | money | snapshot CPP/EIC | frozen commercial/cost | PRICING | ACQUISITION_COST / COMMERCIAL_PRICE | Must not appear as ops truth | CORRECT that ops-graph ignores | CORRECT | Keep Pricing separation |

Full dump (audit tmp, not committed): `_tmp_snapshot_materials.json`.

---

## D. Summary counts

| Layer | Count / state |
|-------|----------------|
| Ops-graph materials UI rows | **0** |
| `operational_tasks` | **18** |
| `material_inputs` nonempty | **0 / 18** |
| Envelope `material_readiness_inputs` | **absent** |
| Frozen PA materials | **22** (qty all null) |
| Reality materials | **0** |
| Reality row 92401 | **0** |
| Sessions tables | **none** / N/A |
| Pricing used for tasks | **[]** (ignored commercial/EIC) |
