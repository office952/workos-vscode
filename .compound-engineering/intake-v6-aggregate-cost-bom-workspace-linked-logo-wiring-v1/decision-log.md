# INTAKE_V6_AGGREGATE_COST_BOM_WORKSPACE_LINKED_LOGO_WIRING_V1 — Decision Log

**Phase:** PLAN  
**Accepted HEAD:** bee9757

## Resolved (plan recommendation)

### DEC-CBOM-ARCH-01 — Adapter architecture

| Field | Value |
|---|---|
| Problem | How to wire workspace-composed PA into Cost BOM |
| Evidence | Adapter already accepts PA object; builder is the gap |
| Selected | **Option B/C hybrid** — fix `AggregateCostBomBuilderService.build_preview` + bounded adapter module-activation helpers |
| Rejected | Binding read, recommendation read, PA rebuild inside adapter, new parallel product graph |
| Risk | LOW |
| Blocked until GO | NO |

### DEC-CBOM-01 — Endpoint shape

| Field | Value |
|---|---|
| Problem | Public API surface for workspace Cost BOM |
| Evidence | `GET /api/v1/product-system/cost-bom-preview/{template_code}?workspace_id=` already exists |
| Options | A) Extend existing endpoint (recommended), B) New aggregate/cost-bom route, C) internal-only |
| **Recommended** | **Option A** — no new public route |
| Risk | LOW — backward compatible when `workspace_id` omitted |
| Blocked until GO | NO |

### DEC-CBOM-02 — Internal cost totals in this slice

| Field | Value |
|---|---|
| Problem | Include EstimatedInternalCost in same implementation? |
| Evidence | `EstimatedInternalCostService.build_preview` has identical template-only aggregate gap (line ~462) |
| Options | A) BOM only (recommended), B) BOM + EIC in same PR |
| **Recommended** | **A — BOM mapping only**; EIC follow-up task |
| Risk | MED if deferred — operators see BOM but not EIC totals for logos until follow-up |
| Blocked until GO | NO (recommended path unblocks BOM) |

## Owner decisions (pending GO)

### DEC-CBOM-03 — Missing tariff semantics

| Field | Value |
|---|---|
| Problem | Missing material rate or workcenter rate for logo rows |
| Evidence | Adapter adds `missing_pricing` → `bom_status=blocked`; geometry gaps → `partial` |
| Options | A) Keep existing blocked/partial split, B) Logo missing tariff = warning-only |
| **Recommended** | **A** — preserve Step 7B semantics |
| Risk | Logo preview may show `blocked` until registry seeded |
| Blocked until GO | **NO** — default acceptable |

### DEC-CBOM-04 — Shared operation cost ownership

| Field | Value |
|---|---|
| Problem | Shared mounting/QC ops across letters + logos |
| Evidence | PA `_dedupe_operations` at composition; adapter maps each PA operation row once |
| **Recommended** | Trust PA dedupe; adapter does not second-dedupe by operation_code alone |
| Risk | LOW if PA dedupe key includes segment |
| Blocked until GO | NO |

### DEC-CBOM-05 — Partial response status vocabulary

| Field | Value |
|---|---|
| Problem | Operator-visible partial vs blocked |
| Evidence | `BomStatus = ready | partial | blocked`; PA warnings `LINKED_SEGMENT_FINISH_PARTIAL` |
| **Recommended** | Use existing `bom_status=partial` + propagated PA warnings; no new public enum |
| Mapping | `TECHNICAL_BOM_PARTIAL` → `bom_status=partial` + finish partial warning |
| Blocked until GO | NO |

### DEC-CBOM-06 — Logo module activation rule

| Field | Value |
|---|---|
| Problem | Logo `mini_module_code` not in letters `active_modules` → rows skipped |
| **Owner GO** | **ACCEPTED** — eligibility derived exclusively from workspace-composed ProductAggregate |
| Implementation | `_is_aggregate_linked_logo_{material,operation,component}` helpers |
| Blocked until GO | **NO — implemented** |

## Decision index

| ID | Status | Blocks /ce-work? |
|---|---|---|
| DEC-CBOM-ARCH-01 | Recommended | NO |
| DEC-CBOM-01 | Recommended | NO |
| DEC-CBOM-02 | Recommended (BOM only) | NO |
| DEC-CBOM-03 | Recommended | NO |
| DEC-CBOM-04 | Recommended | NO |
| DEC-CBOM-05 | Recommended | NO |
| DEC-CBOM-06 | Recommended — owner confirm | Soft — proceed with recommended default |
