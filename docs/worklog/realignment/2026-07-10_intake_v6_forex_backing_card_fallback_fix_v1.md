# INTAKE_V6_FOREX_BACKING_CARD_FALLBACK_FIX_V1

**Date:** 2026-07-10
**Task:** `INTAKE_V6_FOREX_BACKING_CARD_FALLBACK_FIX_V1`
**HEAD before:** `face15e`
**Verdict:** PASS

---

## Why first visual QA was PARTIAL

`INTAKE_V6_FOREX_BACKING_FINISH_PANEL_ORDER_V1` integrated Forex inside **Vector Litere** when letter groups exist, but owner route `633b5663…` is **Logo volumetric** (no Vector Litere). Fallback `Spate litere` remained a detached mini-section under Vector Logo.

## Fix applied

**Target rule implemented in `IntakeV6ReviewStep`:**

| Condition | Placement |
|-----------|-----------|
| Vector Litere exists | `IntakeV6ReviewBackingFinishRow` last row in Vector Litere card |
| Logo only (no litere) | same row inside Vector Logo card (`IntakeV6ArtworkFinishSection`) |
| Both litere + logo | Forex only under Vector Litere (not duplicated) |
| Neither | rare `IntakeV6ReviewBackingSelect` embedded fallback |

Reuses `IntakeV6ReviewBackingFinishRow` — same grid, `REVIEW_SELECT_CLASS`, bindings unchanged (`backing_mode`, `back_bevel_enabled`).

## Files changed

- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingFinishRow.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingFinishRow.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LetterGroupFinishesSection.test.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/scripts/capture-intake-v6-forex-backing-card-fallback-fix-screenshots.mjs`

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx src/components/workos/intake-v6/IntakeV6ReviewBackingFinishRow.test.tsx src/components/workos/intake-v6/IntakeV6LetterGroupFinishesSection.test.tsx src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx
```

**Result:** 46/46 PASS

## Screenshots

- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_card_fallback_fix/01_owner_logo_card_with_forex_inside.png`
- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_card_fallback_fix/02_owner_logo_forex_alignment.png`
- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_card_fallback_fix/03_owner_logo_led_off_forex_visible.png`
- `docs/qa/screenshots/2026-07-10_intake_v6_forex_backing_card_fallback_fix/04_letter_card_with_forex_inside.png`

## Honest UI opinion

- **Owner logo-only route:** acceptable now (~90/100) — Forex is last row inside Vector Logo card, no detached block.
- **Letter fixture:** still good (~88/100) — Forex under layers in Vector Litere, no duplicate.
- Minor: empty cant column on backing row remains (same as prior slice); acceptable for global backing field.

## Scope check

No backend, DB, seed, pricing, ProductDefinition, quote/order/execution changes — **YES**.

## Commit decision

PASS on owner + letter routes → commit `Fix Intake V6 Forex backing card fallback`.

## Cat sunt in directia stabilita

**92/100%**
