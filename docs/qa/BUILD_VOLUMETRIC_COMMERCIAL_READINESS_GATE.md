# BUILD-VOLUMETRIC-COMMERCIAL-READINESS-GATE

**Date:** 2026-06-07  
**Build status:** **PASS**  
**Prior builds:** BUILD_COMMERCIAL_E2E_FIXTURE, BUILD_EXECUTION_SNAPSHOT_FROM_VOLUMETRIC_QUOTE  
**Commit:** not committed (per user rule)

## Summary

Formalized TPL-VOLUMETRIC-LETTERS commercial readiness policy so **warning-only `needs_review`** no longer hard-blocks `can_create_commercial_quote`. The E2E fixture **no longer uses `FIXTURE_READINESS_RESULT` overlay**; seed + convert + execution plan **201** run on live readiness.

## Exact `needs_review` causes found (fixture)

Live `ProductReadinessService` + `evaluate_volumetric_quote_ready` for WI-E2E-COMMERCIAL-001 / QT-E2E-COMMERCIAL-001:

| Code | Section | Classification |
|------|---------|----------------|
| `vector_analysis_pending` | technical | **B** — pricing confidence; vector gate satisfied via manual review |
| `volumetric_psu_wattage_variant_pricing:MAT-LED-PSU-12V:...` | technical | **B** — variant registry reminder; satisfied when `selected_psu_watts` present |
| `volumetric_profile_depth_variant_pricing:MAT-PROFIL-LATERAL-LITERE:...` | technical | **B** — variant registry reminder; satisfied when `return_depth_mm` present |
| `volumetric_profile_return_depth_required_at_quote:MAT-PROFIL-LATERAL-LITERE` | costengine | **B** — quote-time reminder; satisfied when `return_depth_mm` in quote_input |
| `volumetric_psu_wattage_required_at_quote:MAT-LED-PSU-12V` | costengine | **B** — quote-time reminder; satisfied when `selected_psu_watts` in quote_input |
| `technical_readiness:needs_review` (legacy gate) | — | **C** — treated as blocker incorrectly before this build |
| `costengine_readiness:needs_review` (legacy gate) | — | **C** — treated as blocker incorrectly before this build |
| `ready_for_quote:false` (PRS overall) | — | **C** — PRS requires `overall==ready`; volumetric policy now computes commercial ready separately |

**Not present for fixture:** geometry blockers, vector blockers, cost blockers, section hard blockers, metadata blockers.

## Policy chosen: **Option B** (warning-only + acknowledgement when unsatisfied)

| Field | Semantics |
|-------|-----------|
| `blockers` | Hard stops only: cost, geometry, vector, metadata, capture, section `.blockers[]` |
| `warnings` | Visible, auditable; include PRS section warnings + cost warnings |
| `can_create_commercial_quote` | `true` when no hard blockers and dossier/template not blocked |
| `ready_for_quote` | Aligned with `can_create_commercial_quote` for volumetric gate |
| `requires_acknowledgement` | `true` only when acknowledgeable warnings remain **unsatisfied** at quote time |
| `classified.acknowledgement_pending` | Explicit list for conversion ack gate |

**Satisfied-at-quote warnings** (no ack required when quote_input/product_spec complete):

- `vector_analysis_pending` when vector gate satisfied
- `volumetric_*_required_at_quote:*` when depth/PSU present in quote_input
- `volumetric_*_variant_pricing:*` when depth/PSU present in quote_input

**Hard blockers unchanged:** missing geometry, vector gate failures, Oracal metadata, ACM separate template, section blockers, cost blockers.

## Overlay removed

| Before | After |
|--------|-------|
| `FIXTURE_READINESS_RESULT` forced `ready_for_quote: true` | **Removed** |
| `readiness_overlay: e2e_fixture_overlay` | `readiness_overlay: null` |
| `live_gate_can_create_commercial_quote: false` | **`true`** |
| `requires_acknowledgement` (fixture) | **`false`** (all warnings satisfied for deterministic input) |

## Files changed

| File | Change |
|------|--------|
| `backend/services/volumetric_quote_ready_policy.py` | Policy: section blockers only; ack path; `requires_acknowledgement` |
| `backend/routers/orders.py` | Conversion uses `quote_gate.can_create_commercial_quote` |
| `backend/routers/quotes.py` | Persist `policy.requires_warning_acknowledgement` from gate |
| `backend/scripts/seed_commercial_e2e_fixture.py` | Live readiness; fail seed if gate blocked; no overlay |
| `backend/tests/test_volumetric_quote_ready_policy.py` | Policy classification tests |
| `frontend/e2e/helpers/commercialFixture.ts` | Manifest fields for live gate |
| `frontend/e2e/commercial-chain-live.spec.ts` | Assert no overlay + live gate true |
| `docs/qa/BUILD_VOLUMETRIC_COMMERCIAL_READINESS_GATE.md` | This doc |

## Backend tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m unittest tests.test_volumetric_quote_ready_policy tests.test_volumetric_order_execution_snapshot -v
```

**Result:** 19/19 OK

## E2E tests

```powershell
# seed first
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
cd backend; .\.venv\Scripts\python.exe scripts/seed_commercial_e2e_fixture.py

$env:PW_SKIP_WEB_SERVER='1'
cd frontend; npm run test:e2e:commercial-live
```

**Result:** 1 passed — convert without overlay, plan **201**, `tasks.length > 0`

## Seed manifest (post-fix)

```json
{
  "can_create_commercial_quote": true,
  "live_gate_can_create_commercial_quote": true,
  "requires_acknowledgement": false,
  "readiness_overlay": null,
  "quote_gate_blockers": []
}
```

Warnings remain in `quote_gate_warnings` for operator visibility.

## Remaining blockers

1. **ProductReadinessService `ready_for_quote`** still false when `overall_status==needs_review` — volumetric gate overrides for commercial path; PRS flag unchanged globally.
2. **FigJam** sticky not added this session.
3. Quotes with **unsatisfied** acknowledgeable warnings (e.g. `operations_missing`) still require conversion acknowledgement — by design.

## No-regression checklist

- [x] Exact needs_review causes identified and classified  
- [x] Narrow volumetric policy — not global needs_review suppression  
- [x] Hard blockers still block  
- [x] Warnings visible in gate output  
- [x] E2E overlay removed  
- [x] Commercial-live E2E converts + plan 201  
- [x] Execution snapshot tests still pass  
- [x] Unsupported templates unaffected (`not_volumetric_template`)  

## Follow-up: BUILD-VOLUMETRIC-QUOTE-WIZARD-ACK-UX (2026-06-07)

**Status:** PASS — see `docs/qa/BUILD_VOLUMETRIC_QUOTE_WIZARD_ACK_UX.md`

- Quotes / QuoteWizard / VolumetricLettersQuoteFlow now render `VolumetricCommercialReadinessPanel` from backend `quote_gate`
- Convert disabled for hard blockers; proactive acknowledgement checkbox when `requires_acknowledgement`
- WARN seed variant `QT-E2E-COMMERCIAL-WARN-001` added for ack-path testing (primary E2E fixture unchanged)
- Remaining: optional Playwright warn-ack E2E spec
