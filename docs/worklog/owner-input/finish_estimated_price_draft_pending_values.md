# FINISH estimated price draft — pending values (post owner decision)

Status: **OWNER_ACCEPTED** — `finish_owner_price_values_decision_v1.md` (2026-07-10)  
Mode: readonly draft — **no activation**

---

## Evidence keys — evidence_only (not FINISH pricing authority)

| Key | EUR/mp | Classification |
|-----|--------|----------------|
| MAT-ORACAL-641 | 6.50 | evidence_only |
| MAT-ORACAL-651 | 9.00 | evidence_only |
| MAT-ORACAL-8500 | 20.00 | evidence_only |
| MAT-VINYL-PRINT-LAMINATED | 10.00 | evidence_only |
| MAT-VINYL-PRINT | 1.50 | evidence_only |
| LARGE_FORMAT_PRINT | 8.50 | evidence_only |
| LAMINATION | 5.00 | evidence_only |
| FACE_VINYL_APPLICATION_LABOR | 5.00 | evidence_only (face + artwork draft) |
| WC_VINYL_APPLICATION | — | legacy_runtime_evidence (Intake V4 only) |

---

## Draft row status after owner decision

| Draft row | Status | Blocker |
|-----------|--------|---------|
| Face Oracal / print rows | evidence_only | activation |
| Artwork Oracal rows | evidence_only | mp_artwork_area handoff |
| artwork_print_laminate_draft | evidence_only | handoff + activation |
| artwork_print_only_draft | source_inventory_audit_required / blocked | no Intake V4 print_only runtime |
| artwork_none_raw_plexi | not_applicable | — |

---

## Remaining blockers (unchanged)

- `pricingActive: false`
- `readyForPricing: false`
- ProductSystem geometry handoff (`mp_artwork_area` / `artwork_instances`)
- Intake V4 `artwork_print_only` runtime
- No owner-confirmed live FINISH price authority

---

## Next step

**FINISH_PRODUCT_TRUTH_HANDOFF_SPEC_V1**
