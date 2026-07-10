# FINISH Owner Price Values — Owner Decision v1

> **Notă:** Decizie owner pentru surse/valori draft FINISH readonly.  
> **Nu** este sursă runtime. **Nu** activează pricing. **Nu** scrie Product Truth live.

**Date:** 2026-07-10  
**HEAD la semnare:** `a278634` — Prepare FINISH owner price value questions  
**Owner:** Alex / P-Media  
**Decision source:** OwnerDecision block — `FINISH_OWNER_PRICE_VALUES_DECISION_V1` APPLY mode

---

## 1. Status

| Field | Value |
|-------|-------|
| Decision status | **OWNER_ACCEPTED** |
| Workshop mode | readonly source/value decision |
| `readyForPricing` | **false** |
| `pricingActive` | **false** |
| Product Truth live write | **false** |
| ProductDefinition bridge | **false** |
| Pricing Registry write | **false** |

---

## 2. Decisions A–G

### A — Face labor

**ACCEPT** — `FACE_VINYL_APPLICATION_LABOR` as FINISH readonly draft evidence_only (5.0 EUR/mp seed evidence).  
`WC_VINYL_APPLICATION` remains **legacy_runtime_evidence** in Intake V4 only. No activation.

### B — Artwork labor

**ACCEPT** — Same labor model as face evidence_only. No artwork-specific labor key now. Activation blocked.

### C — Artwork print+lam

**ACCEPT** — Same evidence keys as face for readonly draft:

- `MAT-VINYL-PRINT`
- `MAT-VINYL-PRINT-LAMINATED`
- `LARGE_FORMAT_PRINT`
- `LAMINATION`
- `FACE_VINYL_APPLICATION_LABOR`

Classification: **evidence_only**. Activation blocked.

### D — Artwork print only

**ACCEPT** — Keep visible as **blocked**. No Intake V4 `print_only` runtime yet. Future implementation task allowed. Do not remove canonical variant.

### E — mp_artwork_area handoff

**ACCEPT** — Blocked until ProductSystem geometry handoff spec. Intake V4 `quote_geometry.artwork_boxes` may be referenced as evidence_only. Next: **FINISH_PRODUCT_TRUTH_HANDOFF_SPEC_V1**.

### F — Seed EUR/mp

**ACCEPT** — Seeds remain **evidence_only** only. Not owner-confirmed FINISH pricing authority. No owner draft value overrides now.

### G — Boundary

**ACCEPT** — No pricing activation · no Product Truth live write · no Pricing Registry write · no ProductDefinition bridge · no RETURN-CANT ownership · no FACE base material ownership · no RAL minimum ownership.

---

## 3. Evidence classification

| Key | Classification | Notes |
|-----|----------------|-------|
| MAT-ORACAL-641 | evidence_only | 6.5 EUR/mp seed |
| MAT-ORACAL-651 | evidence_only | 9.0 EUR/mp seed |
| MAT-ORACAL-8500 | evidence_only | 20.0 EUR/mp seed |
| MAT-VINYL-PRINT-LAMINATED | evidence_only | 10.0 EUR/mp material only |
| MAT-VINYL-PRINT | evidence_only | 1.5 EUR/mp material only |
| LARGE_FORMAT_PRINT | evidence_only | 8.5 EUR/mp service |
| LAMINATION | evidence_only | 5.0 EUR/mp service |
| FACE_VINYL_APPLICATION_LABOR | evidence_only | FINISH draft labor (face + artwork) |
| WC_VINYL_APPLICATION | legacy_runtime_evidence | Intake V4 artwork path only |
| RETURN_CANT_VINYL_APPLICATION_LABOR | return_cant_only / not_finish_scope | Excluded |

---

## 4. Draft row outcomes

| Draft row | Outcome | Activation |
|-----------|---------|------------|
| Face Oracal 641/651/8500 | evidence_only | blocked |
| Face print+lam combined | evidence_only | blocked |
| Face print+lam split | evidence_only | blocked |
| Artwork Oracal 641 | evidence_only | blocked (geometry handoff) |
| Artwork Oracal 8500 | evidence_only | blocked (geometry handoff) |
| Artwork print+lam | evidence_only | blocked (geometry handoff) |
| Artwork print only | source_inventory_audit_required / blocked | blocked (no Intake V4 runtime) |
| Artwork none/raw plexi | not_applicable | blocked |

---

## 5. Still blocked

- Pricing activation
- Product Truth live write
- Pricing Registry write
- ProductDefinition bridge
- ProductSystem `mp_artwork_area` / `artwork_instances` geometry handoff
- Intake V4 / runtime support for `artwork_print_only`
- Owner-confirmed live FINISH price authority (seeds ≠ pricing authority in Product System)

---

## 6. Owner signature

| Field | Value |
|-------|-------|
| Status | **ACCEPTED** |
| Date | 2026-07-10 |
| Source | OwnerDecision block in `FINISH_OWNER_PRICE_VALUES_DECISION_V1` |

---

## Supersedes

- `finish_owner_price_values_decision_pending.md` (questions prep)

## Encoded in (readonly)

- `frontend/src/features/product-system/componentFirstFinishEstimatedPriceDraft.ts`
- `frontend/src/features/product-system/FinishEstimatedPriceDraftPanel.tsx`
- `frontend/src/features/product-system/componentFirstFinishTruthWorkshop.ts`
