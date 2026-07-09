# FACE Price Registry Alignment Owner Decision v1 — Worklog

**Date:** 2026-07-09  
**Task:** `FACE_PRICE_REGISTRY_ALIGNMENT_OWNER_DECISION_DOC_V1`  
**Mode:** DOCS / OWNER DECISION ONLY  
**HEAD before:** `e87f043`

---

## What was decided

Owner signed alignment between FACE owner estimate drafts and existing Inventory/Pricing sources:

- Plexiglas 3 mm: **16 EUR/mp** via `MAT-ACP-FATA-LITERE` = registry authority; draft 15 superseded conceptually
- Plexiglas 5/10 mm: **draft-only** (25 / 50 EUR/mp); no MAT-* keys
- CNC commercial: **contour EUR/ml** (1.00 / 1.50 / 2.50) — not pass model for offer
- `CNC_ROUTER` 1.5 EUR/ml/pass: **internal only**
- 50 lei CNC minimum: **owner commercial policy** (not registry)
- FACE pricing activation: **blocked until future GO**

---

## What was not changed

- No frontend/backend/seed/migration/DB
- No Pricing Registry write
- No code value update 15 → 16 (deferred to `FACE_PRICE_DRAFT_ALIGN_3MM_TO_REGISTRY_V1`)
- No FINISH workshop
- No new MAT-* keys

---

## Files created

| File | Purpose |
|------|---------|
| `docs/worklog/owner-input/face_price_registry_alignment_owner_decision_v1.md` | Signed owner decision |
| `docs/worklog/realignment/2026-07-09_face_price_registry_alignment_owner_decision_v1.md` | This worklog |

---

## Next recommended slice

**`FACE_PRICE_DRAFT_ALIGN_3MM_TO_REGISTRY_V1`** — update readonly FACE draft 15 → 16 EUR/mp per owner decision; still no Pricing Registry activation.

Alternative: **`FINISH_COMPONENT_TRUTH_WORKSHOP_V1`** only if owner postpones draft align.
