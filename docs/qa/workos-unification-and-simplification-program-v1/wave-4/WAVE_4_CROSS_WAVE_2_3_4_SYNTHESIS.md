# Wave 4 — cross-wave 2 / 3 / 4

Volumetric letters fixture:

| Lens | Value |
|------|--------|
| DEFINED AS | `TPL-VOLUMETRIC-LETTERS_v2` + child modules (PS catalog) |
| CONFIGURED AS | V6 workspace IR/IV6 split |
| AGGREGATED AS | PA graph + task_contract (workspace compose) |
| PRICED AS | V6 preview 725,25 EUR (not official quote) |
| SOLD AS | Frozen `ORD-IV6-V2-1786318810-31` |
| FROZEN AS | Order snapshot copies PD/cost/quote; no recompile |
| EXECUTED AS | `/execution/973024` 18 tasks; Atelier live = other job |

| Flag | |
|------|--|
| DEFINITION_DRIFT | YES — confirm blocked vs frozen order |
| AGGREGATE_DRIFT | PARTIAL — multi-root nodes visible, intended |
| COMMERCIAL_DRIFT | YES — EUR vs RON vs preview (Wave 2 C2) |
| EXECUTION_DRIFT | YES — UI projection, not PS compile |
| IDENTITY_DRIFT | YES — IR / IV6 / ORD / 973024 |
| GRANULARITY_DRIFT | YES — commercial line ≠ CNC job ≠ operator card |
| OWNERSHIP_DRIFT | YES — PS catalog vs V6 job truth vs FLUX |
| NO_DRIFT_PROVEN | PARTIAL — 973024 task ids match template graph |

**CROSS_WAVE_2_3_4_MODEL = PARTIAL**

Gap closure: ProductAggregate → Execution task ids are **PROVEN** on 973024 (`node:root_product:TPL-VOLUMETRIC-LETTERS_v2:*`, `node:volum_aluminum:TPL-VOLUM-ALUMINIU_v1:*`). UI still hides that grain. Architectural answer unchanged: compiler spine, not commercial/shop backbone. PD having no page is accepted as healthy. Unregistered 12+9 retracted as Level-1 systems.
