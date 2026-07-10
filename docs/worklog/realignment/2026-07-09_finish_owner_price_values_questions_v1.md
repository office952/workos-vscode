# FINISH_OWNER_PRICE_VALUES_DECISION_V1 — Questions Prep Worklog

**Date:** 2026-07-09  
**Task:** `FINISH_OWNER_PRICE_VALUES_DECISION_V1`  
**Mode:** QUESTIONS PREP ONLY (no `OwnerDecision` block in context)  
**HEAD before:** `542fff6` — Audit FINISH source inventory cross references  
**Verdict:** PASS (questions prepared; stopped for owner chat)

---

## Purpose

Prepare owner-facing decision questions about FINISH draft/source values and blockers identified in source inventory cross-reference audit. No answers invented. No pricing activation.

---

## Worktree gate

| Check | Result |
|-------|--------|
| Expected HEAD | `542fff6` |
| Actual HEAD | `542fff6` |
| Tracked dirty (unrelated) | `.gitignore`, QA smoke PNGs |
| Tracked dirty (prior slice) | `docs/worklog/realignment/2026-07-09_finish_estimated_price_draft_v1.md` — single line: `HEAD after: c6b06d7` (not included in this commit; owner may fix separately) |
| Unrelated untracked | QA folders, capture scripts — not touched |

---

## Files read

- `docs/worklog/realignment/2026-07-09_finish_source_inventory_cross_reference_audit_v1.md`
- `docs/worklog/owner-input/finish_estimated_price_draft_pending_values.md`
- `docs/worklog/owner-input/finish_component_truth_owner_decision_v1.md`
- `docs/worklog/realignment/2026-07-09_finish_estimated_price_draft_v1.md`
- `frontend/src/features/product-system/componentFirstFinishEstimatedPriceDraft.ts`
- `frontend/src/features/product-system/componentFirstFinishTruthWorkshop.ts`
- `frontend/src/features/product-system/canonicalFinishEnumMap.ts`
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py` (read-only audit)
- `backend/seeds/seed_volumetric_workcenter_rates.py` (read-only audit)
- `backend/services/intake_v4_material_breakdown_service.py` (read-only audit)
- `frontend/src/lib/svgArtworkContracts.ts`

---

## Files changed

- `docs/worklog/owner-input/finish_owner_price_values_decision_pending.md` (new)
- `docs/worklog/realignment/2026-07-09_finish_owner_price_values_questions_v1.md` (this file)

No frontend/backend/seed changes.

---

## Owner questions prepared (A–G)

See `docs/worklog/owner-input/finish_owner_price_values_decision_pending.md` for full detail.

| Question | Decision needed | Recommended answer |
|----------|-----------------|-------------------|
| A — Face labor | FACE_VINYL_APPLICATION_LABOR vs WC_VINYL_APPLICATION | FACE_VINYL_APPLICATION_LABOR evidence_only in FINISH draft |
| B — Artwork labor | Same as face or new key | Same as face evidence_only |
| C — Artwork print+lam | Shared vs artwork keys | Accept evidence_only (same as face) |
| D — Artwork print only | Block / hide / implement | Keep visible as blocked |
| E — mp_artwork_area handoff | When to unblock | Blocked until ProductSystem handoff spec |
| F — Seed EUR/mp | Evidence vs owner draft values | Seeds evidence_only only |
| G — Boundary | Reconfirm all NO | ACCEPT unchanged |

---

## Draft row impact (recommendations only — not applied)

| Draft row | Before | Recommendation | Blocker |
|-----------|--------|----------------|---------|
| Face Oracal / print rows | evidence_only | unchanged | activation |
| Artwork Oracal rows | evidence_only | unchanged | geometry handoff |
| artwork_print_laminate_draft | source_inventory_audit_required | → evidence_only (after APPLY) | labor + handoff |
| artwork_print_only_draft | source_inventory_audit_required | stay audit_required / blocked | no Intake V4 handler |
| artwork_none_raw_plexi | not_applicable | unchanged | — |

---

## Boundary preserved

- No pricing activation
- No Product Truth write
- No Pricing Registry write
- No ProductDefinition bridge
- No backend/seed/DB changes
- No quote/order/execution changes

---

## Tests / checks

```powershell
git diff --check
```

Docs-only — no frontend tests run.

---

## Next step

**STOP for owner chat** → owner answers A–G → rerun `FINISH_OWNER_PRICE_VALUES_DECISION_V1` with `OwnerDecision` block → APPLY mode.

Likely follow-on after APPLY: `FINISH_PRODUCT_TRUTH_HANDOFF_SPEC_V1` (question E).

---

## Cat sunt in directia stabilita

**96/100%** — Questions prepared; owner answers required before draft metadata cleanup or any path toward activation.
