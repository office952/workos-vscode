# INTAKE_V6_ESTIMATED_INTERNAL_COST_WORKSPACE_LINKED_LOGO_WIRING_V1 — Decision Log

**Phase:** PLAN  
**Accepted HEAD:** bcdd14d

## Recommended (plan default)

### DEC-EIC-ARCH-01 — Architecture

| Field | Value |
|---|---|
| Problem | EIC rebuilds template-only PA/BOM |
| Selected | **Option A/C hybrid** — `AggregateCostBomBuilderService.build_preview` as canonical BOM input |
| Rejected | EIC reads bindings; EIC expands linked templates; parallel BOM build |
| Blocked until GO | NO |

### DEC-EIC-01 — Endpoint shape

| Field | Value |
|---|---|
| Problem | Public API for workspace EIC |
| Evidence | `POST /api/v1/product-system/estimated-internal-cost-preview/{template_code}` accepts `workspace_id` |
| **Recommended** | **Option A** — reuse existing POST route |
| Blocked until GO | NO |

### DEC-EIC-02 — Cost BOM as canonical input

| Field | Value |
|---|---|
| Problem | EIC vs PA direct |
| **Recommended** | **Cost BOM via builder** — single costing graph |
| Blocked until GO | NO |

## Owner decisions (pending GO)

### DEC-EIC-03 — Logo segment material quantity

| Field | Value |
|---|---|
| Problem | `_estimate_material_quantity` uses letter_face_area_m2 for all m² materials |
| Evidence | Logo BOM rows have namespaced `component_ref`; payload has `artwork_finishes[].estimated_area_m2` |
| Options | A) Match segment key from `component_ref` suffix → artwork finish area (recommended); B) Block logo material lines with geometry blocker; C) Skip quantity (partial only) |
| **Recommended** | **A** — read segment area from payload paths already in workspace (not bindings) |
| Risk | Wrong area if payload incomplete → blocker/warning |
| Blocked until GO | Soft — default A in plan |

### DEC-EIC-04 — Logo operation internal cost (v1 scope)

| Field | Value |
|---|---|
| Problem | EIC operation lines come from letters `RULES_BY_TEMPLATE`, not BOM operations |
| Options | A) v1 logo **material** internal cost only (recommended); B) Map `bom.costable_operations` for linked logo rows (larger) |
| **Recommended** | **A for v1** — document operation debt |
| Blocked until GO | NO for v1 material path |

### DEC-EIC-05 — Partial EIC status when logo finish partial

| Field | Value |
|---|---|
| Problem | EIC `_compute_status` ignores BOM partial |
| **Recommended** | When `bom.bom_status == partial` or finish-partial warning → EIC `status=partial`; letters lines still calculated |
| Blocked until GO | NO |

### DEC-EIC-06 — Missing logo material rate

| Field | Value |
|---|---|
| Problem | Missing rate handling for logo rows |
| **Recommended** | Keep existing `INTERNAL_MATERIAL_COST_MISSING` blocker; never zero fallback |
| Blocked until GO | NO |

### DEC-EIC-07 — Overhead in v1 slice

| Field | Value |
|---|---|
| Problem | Overhead rules always applied |
| **Recommended** | Unchanged — existing overhead lines remain; no logo-specific overhead |
| Blocked until GO | NO |

## Decision index

| ID | Status | Blocks /ce-work? |
|---|---|---|
| DEC-EIC-ARCH-01 | Recommended | NO |
| DEC-EIC-01 | Recommended | NO |
| DEC-EIC-02 | Recommended | NO |
| DEC-EIC-03 | Recommended (A) | Soft |
| DEC-EIC-04 | Recommended (material-only v1) | NO |
| DEC-EIC-05 | Recommended | NO |
| DEC-EIC-06 | Recommended | NO |
| DEC-EIC-07 | Recommended | NO |
