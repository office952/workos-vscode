# INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1 — Plan

**Phase:** PLAN COMPLETE  
**Plan verdict:** **READY_FOR_BOUNDED_IMPLEMENTATION**  
**All 7 DEC decisions:** **CLOSED**  
**Accepted HEAD:** 0df2c79  
**Branch:** main

---

## 1. Root cause

Per segment, three parallel producers emit the same physical artwork concepts:

1. **Face child** (`TPL-VOLUMETRIC-LOGO-FACE_v1`) — erroneously declares `print_media`, `laminate_media`, `logo_face_print`, `logo_face_laminate` alongside substrate + CNC.
2. **Finish child** (`TPL-VOLUMETRIC-LOGO-FINISH_v1`) — correctly declares media + `logo_finish_application`; missing print/lam **operations** today.
3. **Parent dossier `mapping_only`** — injects all keys again as `linked_segment::{segment}` via `product_aggregate_service.build`.

`product_aggregate_workspace_composition_service._dedupe_*` keys on `component_ref` — no semantic collapse.  
`aggregate_cost_bom_adapter` treats **all** rows as costable — ignores `status=mapping_only`.

**Quantity per segment is correct.** Cardinality and ownership are wrong.

---

## 2. Canonical owners (CLOSED — owner preferred direction)

| Module | Owns |
|---|---|
| **logo face** (`comp_logo_face`) | `logo_face_material`, `logo_face_cnc_cut` |
| **logo finish** (`comp_logo_finish`) | `print_media`, `laminate_media`, `logo_face_print`, `logo_face_laminate`, `logo_finish_application` |
| **dossier mapping_only** | Metadata only — **not costable** when linked child exists |

---

## 3. Selected remediation layer (DEC-DEDUPE-LAYER CLOSED)

| Layer | Role |
|---|---|
| **A — Seed/template realign** | **REQUIRED** — move print/lam ops to finish; remove artwork from face child |
| **B — Workspace composition** | Ownership classifier; drop non-canonical rows from composed costable set |
| **C — Cost BOM guard** | Defense: skip `mapping_only` + non-canonical owners |

**Rejected:** EIC dedupe (D); generic `material_code` / `operation_code` dedupe; cross-segment collapse.

---

## 4. Implementation sequence (future `/ce-work` only)

1. **`seed_tpl_volumetric_logo_v1.py`** — face child: keep substrate + CNC only; finish child: add print/lam ops + keep media + application.
2. **`logo_artwork_cost_ownership.py`** (new) — ownership contract constants + `is_canonical_costable_row(...)`.
3. **`product_aggregate_workspace_composition_service.py`** — filter after namespace.
4. **`aggregate_cost_bom_adapter.py`** — skip non-canonical + mapping_only with explicit `CostBomSkippedItem` reasons.
5. **Tests** — cardinality contract; update workspace BOM + EIC tests for `comp_logo_finish::` op refs.
6. **Probe re-run** — verify 1/1/1/1/1 per segment.
7. **Do not** touch EIC rate resolver or 35 RON/m² values.

---

## 5. Application scope (logo_print_finish)

| Source | Print | Lam | App | Bundled? |
|---|---|---|---|---|
| BOM (target) | Separate ops on finish | Separate | Separate | NO |
| Task `logo_print_finish` | — | — | priced op = application | Task label only |
| Owner intent | Machine processing | Laminator | Physical apply | Additive after dedupe |

Application rate (35 RON/m²) remains disabled until parent catalog re-audit.

---

## 6. Downstream impact

| Consumer | After fix |
|---|---|
| ProductAggregate | Canonical rows; mapping_only informational |
| Cost BOM | 1 row per concept per segment |
| EIC materials | 1 print + 1 lam per segment |
| EIC logo ops | 1 per op on `comp_logo_finish::` |
| ProductDefinition | Unchanged |
| CPP / Quote / Execution | Unchanged |

---

## 7. Files proposed

| File | Change |
|---|---|
| `backend/seeds/seed_tpl_volumetric_logo_v1.py` | CHILD_SPECS realign |
| `backend/services/logo_artwork_cost_ownership.py` | New ownership contract |
| `backend/services/product_aggregate_workspace_composition_service.py` | Filter |
| `backend/services/aggregate_cost_bom_adapter.py` | BOM guard |
| `backend/tests/test_logo_artwork_bom_ownership_dedupe.py` | New |
| `backend/tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py` | Cardinality |
| `backend/tests/test_estimated_internal_cost_workspace_linked_logo.py` | Finish-owned refs |
| `backend/tests/test_estimated_internal_cost_logo_operations.py` | `comp_logo_finish::` refs |
| `backend/tests/test_seed_tpl_volumetric_logo_v1.py` | Seed structure |

**Forbidden:** EIC rates, CPP, Quote, DB migration, frontend.

---

## 8. Test plan

- Per-segment: 1 print media, 1 lam media, 1 print op, 1 lam op, 1 app op — all on `comp_logo_finish::{segment}`
- Face: 1 substrate, 1 CNC — no artwork on face
- mapping_only never in `costable_*`
- Two segments independent
- Partial finish → 0 artwork rows
- EIC rates still `INTERNAL_OPERATION_RULE_MISSING`
- Letters-only unchanged

---

## 9. Runtime probe

Before: 3/3/2/2/2 per segment. After: 1/1/1/1/1.  
Command: see `cardinality-contract.md` §5.

---

## 10. Rollback

Revert seed + composition + BOM guard → restores 0df2c79 cardinality.

---

## 11. Plan review gate

| Check | Pass |
|---|---|
| One owner per concept | YES |
| All 7 DEC closed | YES |
| mapping_only ≠ cost truth | YES |
| No generic code dedupe | YES |
| No cross-segment collapse | YES |
| Quantities unchanged | YES |
| EIC not primary fix | YES |
| Rates disabled | YES |
| Preferred direction demonstrated | YES (seed gap documented + closed via Option A) |

**Verdict:** **READY_FOR_BOUNDED_IMPLEMENTATION**

---

## 12. Next command

```
/ce-work mode:return-to-caller .compound-engineering/intake-v6-linked-logo-artwork-bom-ownership-dedupe-v1/plan.md
```

Then re-run artwork duplication audit → parent rate catalog `/ce-work`.
