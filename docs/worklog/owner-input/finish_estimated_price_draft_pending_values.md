# FINISH estimated price draft — pending owner values / audit

Status: **audit complete (PARTIAL)** — `FINISH_SOURCE_INVENTORY_CROSS_REFERENCE_AUDIT_V1`  
Prior slice: readonly draft only (`FINISH_ESTIMATED_PRICE_DRAFT_V1` @ `c6b06d7`)

See full audit: `docs/worklog/realignment/2026-07-09_finish_source_inventory_cross_reference_audit_v1.md`

---

## Evidence keys — source found (still evidence_only, not FINISH pricing authority)

| Key | Evidence EUR/mp | Classification | Source location |
|-----|-----------------|----------------|-----------------|
| MAT-ORACAL-641 | 6.50 | evidence_only | `seed_volumetric_owner_confirmed_prices.py`, Intake V4 artwork Oracal |
| MAT-ORACAL-651 | 9.00 | evidence_only | Same |
| MAT-ORACAL-8500 | 20.00 | evidence_only | Same |
| MAT-VINYL-PRINT-LAMINATED | 10.00 | evidence_only | Combined material only — face + artwork Intake V4 |
| MAT-VINYL-PRINT | 1.50 | evidence_only | Material only — face + artwork Intake V4 |
| FACE_VINYL_APPLICATION_LABOR | 5.00 | evidence_only | `seed_volumetric_workcenter_rates.py` — face-labeled |
| LARGE_FORMAT_PRINT | 8.50 | evidence_only | Workcenter service rate |
| LAMINATION | 5.00 | evidence_only | Workcenter service rate |

These are **not** owner-confirmed FINISH pricing authority in Product System. Do not activate.

---

## Audit outcomes by draft row

| Draft row | Prior status | Post-audit status | Notes |
|-----------|--------------|-------------------|-------|
| `artwork_print_laminate_draft` | source_inventory_audit_required | **evidence_only (keys found)** — UI label unchanged until cleanup slice | Same MAT-VINYL-PRINT / PRINT / LAMINATION keys as face; labor conflict remains |
| `artwork_print_only_draft` | source_inventory_audit_required | **still audit_required** | `print_only` not in Intake V4 `PRINT_ARTWORK_EXECUTION_TYPES` — no runtime path |

---

## Open owner decisions (do not invent)

### 1. Artwork application labor key

- FINISH draft references: `FACE_VINYL_APPLICATION_LABOR` (5 EUR/mp)
- Intake V4 artwork print/lam application rows use: `WC_VINYL_APPLICATION` workcenter (legacy fallback 3 EUR/mp)
- **Owner must choose** mapping before price values or activation.

### 2. Artwork print only variant

- Canonical `artwork_print_only` exists in Product System
- Intake V4 does not process `execution_type=print_only` for artwork breakdown
- **Owner must decide:** add runtime support or defer variant

### 3. mp_artwork_area handoff

- Rule owner_confirmed; Intake V4 produces area via `quote_geometry.artwork_boxes`
- Product System component-first: runtime source **not wired**
- Spec/handoff slice recommended before pricing

### 4. Seed naming

- `MAT-VINYL-PRINT` / `MAT-VINYL-PRINT-LAMINATED` seed names say “față litere” but Intake V4 reuses keys for artwork
- Document-only acceptable unless owner wants rename

---

## Explicitly not FINISH (no owner price needed here)

- `RETURN_CANT_VINYL_APPLICATION_LABOR` — RETURN-CANT only
- `MAT-ACP-FATA-LITERE` — FACE base material
- RAL 100 lei minimum — RETURN-CANT commercial policy

---

## Activation blockers (unchanged)

- `pricingActive: false`
- `readyForPricing: false`
- No Product Truth live write
- No Pricing Registry write
- No ProductDefinition bridge

---

## Next recommended step

**FINISH_OWNER_PRICE_VALUES_DECISION_V1** (after owner answers labor + print_only questions)

Alternative: **FINISH_PRODUCT_TRUTH_HANDOFF_SPEC_V1** for `mp_artwork_area` / `artwork_instances`
