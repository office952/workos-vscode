# Structural Resource Options — Authority Architecture

| Field | Value |
|-------|-------|
| Status | Design proposal (not implemented) |
| Date | 2026-07-18 |
| Owner-rules status | **PARTIAL OWNER_CONFIRMED** — materials + frame formula + crossbar spacing; **profiles DEFERRED** |
| Runtime V1 | Code registry `structural_resource_options/v1` + GET API; ACP `accepted_profile_codes=[]` |
| Related audit | `docs/audits/2026-07-18_structural_material_profile_catalog_audit.md` |
| Owner decision | `docs/decisions/STRUCTURAL_RESOURCE_OPTIONS_OWNER_DECISION.md` |
| Aligns with | `08_PRICING_REGISTRY_SEPARATION.md`, `MATERIAL_CANONICAL_NAMING_AND_ALIASES.md`, `18_GOVERNANCE_SETTINGS_POLICY.md` |

**Blocked for Registry V1 seed:** ACP initial profile list, clearance numeric policy, crossbar matrix (manual mode may unblock a **manual-guarded** registry only after materials + at least one confirmed profile).

---

## 1. Central question — where authority lives

| Concern | Authority home (proposed) |
|---------|---------------------------|
| What steel/aluminium **means** technically | Technical Resource Option — **material** |
| What a **profile section** is (shape, W, H, T) | Technical Resource Option — **profile** |
| Which materials a profile may use | Compatibility on profile ↔ material codes |
| Which options a product/component may use | **Product System** accepted_* declarations |
| Acquisition cost / supplier | **Pricing / inventory mapping** (separate) |
| Commercial markup / quote rules | Pricing Registry commercial rules (doc 08) |
| Operator selection UI | Intake consumes allowed options only |

```text
Technical Resource Options (shared)
  ├─ Structural materials (otel, aluminiu, …)
  └─ Structural profiles (SHS/RHS + dimensions)

Product System component / local config
  └─ declares accepted materials + profiles + defaults

Intake Step 2
  └─ selects from allowed set; confirms; persists codes

ProductDefinition
  └─ snapshots selected technical codes + provenance

ProductAggregate
  └─ resolves technical intent + quantity status (may be guarded)

CPP / Pricing
  └─ maps technical code → priced inventory SKU(s) → cost
```

---

## 2. Technical vs pricing boundary (firm)

```text
Technical Resource Option
→ ce material/profil poate fi folosit
→ caracteristici tehnice
→ compatibilități
→ unități
→ status / version / aliases

Pricing Material (inventory / pricing registry)
→ cost de achiziție
→ furnizor
→ monedă
→ unitate comercială
→ pierderi comerciale
→ valabilitate
```

| Question | Answer |
|----------|--------|
| 1. Technical registry separat necesar? | **Da** — typed structural identity without commercial fields |
| 2. Pricing registry poate fi extins? | **Da pentru prețuri**, **nu** ca technical allowlist |
| 3. Product System deține compatibility? | **Declarează accepted set**; catalog defines physical compatibility |
| 4. CPP doar rezolvă technical → priced? | **Da** (target) |
| 5. Mai mulți furnizori același profil? | Mapping **1 technical : N priced SKUs**; selection by supplier policy / owner default; PD snapshots chosen priced ref at commercial freeze |

**Relation example (illustrative naming only):**

```text
Technical profile:  PROFILE-SHS-30X30X1_5
Technical material: MAT-STRUCT-STEEL
Pricing mapping:    MAT-STEEL-SQUARE-TUBE-30X30X1_5  (inventory row, unit_cost)
                    + optional supplier-specific SKUs
```

Do not bake „premount” / „ACP frame” into technical codes.

---

## 3. Registry location comparison

| Criteriu | A PS RO registry | B Extend inventory as tech | C Pricing as tech | **D Shared tech + pricing map** |
|----------|-----------------:|---------------------------:|------------------:|--------------------------------:|
| Product System authority | High (owns catalog) | Low | None | High (consumes; declares accepted) |
| Reutilizare | Medium (risk PS-only) | High SKU | Low | **Highest** |
| Pricing separation | Good if no costs | **Weak** (unit_cost mixed) | **Fails** | **Strong** |
| Versioning | Needs design | Partial (row update) | Poor | Explicit on technical entities |
| Multiple suppliers | Needs map | One row≈one SKU | Confused | **Native 1:N map** |
| Intake consumption | Direct | Possible | Wrong | Via accepted filter |
| PD snapshot | Codes | Codes+price risk | Price leakage | Technical codes + optional priced snapshot at commercial gate |
| Aggregate resolution | Needs bridge | Direct MAT | Wrong | Technical → quantity → map to price later |
| Complexity | Medium | Low short-term | Low but wrong | Medium–high |

### Option notes

- **A** — Good for selection UX ownership; risk that catalog becomes Product-System-only and still needs pricing bridge.
- **B** — Inventory already exists; lacks dimensional schema; doc 08 + naming forbid usage-as-identity; extending columns helps SKUs but does not create clean Resource Option layer for families without stock rows.
- **C** — Rejected: pricing must not be product structure truth (doc 08, AGENTS.md).
- **D (recommended)** — Shared technical catalog (materials + profiles) + pricing mapping table/service; Product System stores **accepted option codes** per template/component; Intake never owns catalog.

---

## 4. Material model (minimal)

```text
code
label                    # owner-facing RO, e.g. "Oțel structural"
family                   # structural_metal
base_material            # steel | aluminium
grade_or_alloy           # optional V1
density_kg_per_m3        # optional V1
compatible_profile_families  # e.g. shs, rhs
allowed_finishes         # optional / deferred
unit_system              # metric
status                   # active | deprecated | draft
version
aliases[]
provenance
```

| Field | V1 required? |
|-------|--------------|
| code, label, base_material, status, version | **Required** |
| family, compatible_profile_families, unit_system, aliases, provenance | Recommended |
| grade_or_alloy, density, allowed_finishes | Optional / deferred |

### Proposed material codes (aligned with naming doc — **owner must confirm**)

| Owner label | Proposed code | Notes |
|-------------|---------------|-------|
| Oțel structural | `MAT-STRUCT-STEEL` | Family-level Resource Option (not a stock length SKU) |
| Aluminiu structural | `MAT-STRUCT-ALUMINIUM` | Prefer `ALUMINIUM` spelling consistency in new codes; alias `aluminum` |

**Not proposed:** `OPT-ACP-FRAME-MAT-*` (product-scoped).  
**Inox:** only if owner documents real need — **out of V1** unless proven.

---

## 5. Profile model (minimal)

```text
code
label
shape                    # shs | rhs  (V1)
width_mm
height_mm                # = width for SHS
diameter_mm              # null for SHS/RHS V1
wall_thickness_mm
compatible_material_codes[]
stock_length_mm          # optional
unit                     # mm for section; m for cut length consumption
status
version
aliases[]
capabilities[]           # e.g. cuttable, weldable — optional
provenance
```

### Shape scope V1

| Shape | Include V1? |
|-------|-------------|
| Square hollow section (SHS) | **Yes** |
| Rectangular hollow section (RHS) | **Yes** |
| Round tube / angle / channel | **No** unless owner proves live need |

---

## 6. Naming convention (single recommendation)

### Profiles — **dimension-first, material-agnostic codes**

```text
PROFILE-SHS-{W}X{H}X{T}
PROFILE-RHS-{W}X{H}X{T}
```

Examples:

```text
PROFILE-SHS-20X20X1_5
PROFILE-SHS-30X30X1_5
PROFILE-RHS-40X20X1_5
```

Rules:

- Use `X` separators; thickness decimal as `_` (`1_5` for 1.5).
- **Do not** embed material in profile code when the same section exists in steel and aluminium — compatibility list resolves that.
- Display label may include material when rendered in a filtered selector.

### Why not material-in-code for profiles?

| Variant | Pros | Cons |
|---------|------|------|
| Profile + material separate (**chosen**) | Reuse section; clear compatibility; matches owner model | Selector needs two fields |
| Combined SKU as only identity | Matches today’s MAT-PREMOUNT row | Forces duplicate rows per material; blurs RO vs stock |

### Stock / priced inventory SKUs (pricing layer — existing target pattern)

```text
MAT-STEEL-SQUARE-TUBE-{W}X{H}X{T}
MAT-ALU-SQUARE-TUBE-{W}X{H}X{T}
```

These remain **pricing/inventory identities**, mapped from `(MAT-STRUCT-*, PROFILE-SHS-*)`.

---

## 7. Compatibility model

```text
PROFILE-SHS-30X30X1_5
  compatible_material_codes: [MAT-STRUCT-STEEL, MAT-STRUCT-ALUMINIUM]

Component ACP internal_frame
  accepted_material_codes: [MAT-STRUCT-STEEL, MAT-STRUCT-ALUMINIUM]
  accepted_profile_codes:  [ … owner-confirmed subset … ]
```

Validation order:

1. Codes exist and `status=active`
2. Profile↔material compatible in catalog
3. Selection ∈ component accepted set
4. Not deprecated (or explicit override + owner gate)

---

## 8. Ownership by system

### Product System

- Owns **accepted_*** lists and defaults/recommendations per component / local config
- Owns required/optional when feature enabled
- Owns inactive isolation rules
- Owns interface: panel owns nested `internal_frame` config
- Does **not** own global profile dimensions
- Does **not** own unit prices

### Intake

- Step 1: intent markers only (e.g. `internal_frame_enabled`)
- Step 2: select from allowed options; confirm clearance; persist codes
- Must not invent profiles, compatibilities, or structural formulas

### ProductDefinition

- Persists selected technical codes + confirmation + provenance + source versions
- Optional snapshot labels for display
- Dimensional inputs (panel W/H, clearance)
- **No live prices**

### ProductAggregate

```text
material_option + profile_option + dimensions + crossbar_rule
→ technical material intent
→ process intent (from existing process catalogs only)
→ quantity status: COMPUTED | CONFIGURED_BUT_QUANTITY_GUARDED
```

No fake BOM when dimensional rules unapproved.

### CPP

```text
technical (material, profile) → priced inventory SKU(s) → cost
```

| Topic | Design |
|-------|--------|
| Mapping | 1 technical pair → 1..N priced SKUs |
| Fallback | Owner-gated missing price (no silent substitute) |
| Snapshot | At commercial freeze, store priced code + unit_cost used |
| This task | **No pricing formulas** |

### Lifecycle (future checks — not implemented here)

| State | Expected |
|-------|----------|
| Catalog invalid/missing codes | BLOCKED |
| Frame inactive | NOT_APPLICABLE, zero leakage |
| Frame active incomplete | Step2/PD BLOCKED |
| Frame active complete, qty rules missing | PD PASS; Aggregate OWNER_GATE / PREVIEW_ONLY; CPP OWNER_GATE |

---

## 9. Storage impact (design only — no schema approval)

| Maturity | Storage |
|----------|---------|
| **MVP** | Versioned JSON/config registry in repo (or settings-managed JSON) + code loaders; Product System accepted lists in dossier/contract JSON; pricing map by code |
| **Mature** | DB tables for technical materials/profiles + admin UI + audit log; soft deprecation; migration from MAT-PREMOUNT aliases |

| Needs? | MVP | Mature |
|--------|-----|--------|
| Contract in code | Yes | Yes |
| JSON/config registry | Yes | Optional mirror |
| DB table | No (unless owner chooses) | Likely |
| Seed | Only after owner GO on codes | Controlled |
| Migration | No for MVP if JSON | Yes if DB |
| Settings-managed | Attractive for owner edits | With governance |
| Admin UI | Deferred | Yes |

**This design does not approve schema/migration.**

---

## 10. Governance

| Action | Who (per doc 18) |
|--------|------------------|
| Create material / profile | Owner GO |
| Activate / deprecate | Owner GO |
| Change dimensions / compatibility | Owner GO (breaking → version bump) |
| Change pricing mapping / unit_cost | Pricing/Inventory owner under pricing policy |
| Change ACP accepted defaults | Product owner GO |
| Agent invents catalog rows | **Forbidden** |

---

## 11. Anti-patterns (forbidden)

- ACP-only material codes without reuse justification
- `bar_material: "steel"` as global technical authority
- Free-text profiles in Intake
- Hidden hardcoded `20x20x1.5` / `5 mm` without provenance
- Product Template per material
- Pricing seed as Product System allowlist
- Duplicate profile lists per product
- Invented structural formulas / crossbar counts
- Mixing letter-cant `MAT-PROFIL-LATERAL-*` into structural tube catalog

---

## 12. Migration note (future — not this task)

`MAT-PREMOUNT-BAR-STEEL` → alias of priced SKU mapped from `(MAT-STRUCT-STEEL, PROFILE-SHS-30X30X1_5)` with usage tag `premount_bar`, not as technical identity.
