# Intake V6 — Three-Step Final Confirmation E2E Smoke Alignment V1

| Field | Value |
|-------|-------|
| Task | `INTAKE_V6_THREE_STEP_FINAL_CONFIRMATION_E2E_SMOKE_ALIGNMENT_V1` |
| Verdict | **PASS** |
| Accepted HEAD | `c5c93c2` |
| Branch | `main` |
| Prior task | `INTAKE_V6_RETURN_CANT_READINESS_SINGLE_FINAL_CONFIRMATION_V1` (PASS) |

## Accepted operator flow

Pas 1 Straturi → Pas 2 Configurare → Pas 3 Confirmare. Single final confirmation (`internal_draft_quote_confirmed`) only on Pas 3. No removed workspace status badge.

## E2E debt before

| File | Issue |
|------|-------|
| `intake-v6-step1-smoke.spec.ts` | Required `intake-v6-workspace-status-badge`; expected header “Review” |
| `intake-v6-runtime-capture-read-model.spec.ts` | Header copy `/Review/i`; panel not expanded from technical accordion |
| (none) | No primary three-step → confirm smoke |

## Stale assertions replaced

| Old | New |
|-----|-----|
| `intake-v6-workspace-status-badge` visible | `toHaveCount(0)` via `assertNoRemovedWorkspaceStatusBadge` |
| Header `/Review/i` | `Configurare` / `Confirmare` via `assertHeaderStepLabel` |
| Step1-only navigation | Full A→D flow in `intake-v6-three-step-final-confirmation-smoke.spec.ts` |
| Runtime capture panel always visible | Expand `intake-v6-review-technical-details-toggle` first |

## Aligned assertions

- Three progress steps with labels Straturi / Configurare / Confirmare
- Pas 3 separate (`intake-v6-step-confirm`, review step count 0)
- Summary collapsed by default (`data-expanded=false`)
- Final checkbox only on Pas 3 (`intake-v6-confirm-internal-draft` count 0 on Pas 2)
- Persisted defaults visible: `Alb · 60 mm`, `Print + laminare`
- False legacy warnings absent: `Verifică lățimea cantului.`, `RETURN_CANT_COMPONENT_CONFIRMATION_MISSING`, `Artwork neconfirmat în Review.`
- Real blockers: footer primary reason visible; create draft disabled on confirm step
- Technical diagnostics secondary: runtime capture under review technical accordion

## Fixture / runtime

| Workspace | Use |
|-----------|-----|
| `22ef834d-f2d0-453b-a7a7-118928c98a39` | Primary three-step smoke (IV6-189D2F12) |
| `668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c` | Runtime capture read-model panel |

**Limitation:** Full checkbox persistence + handoff enablement not E2E-mutated — PUT `/internal-draft-quote-confirmation` requires authenticated session; smoke stops before quote/order creation per task boundary.

## Blocked vs ready scenarios

| Scenario | Coverage |
|----------|----------|
| Blocked | Final action disabled; primary reason visible; no false cant-width copy |
| Ready boundary | Final checkbox enabled, unchecked, single instance on Pas 3 only |

## Selectors

Stable `data-testid`: progress steps, step-review/confirm, final summary toggle, confirm-internal-draft, create-internal-draft, footer-primary-action-reason, review-technical-details-toggle.

## Tests

```powershell
$env:PW_SKIP_WEB_SERVER='1'
cd frontend
npx playwright test e2e/intake-v6-three-step-final-confirmation-smoke.spec.ts e2e/intake-v6-step1-smoke.spec.ts e2e/intake-v6-runtime-capture-read-model.spec.ts
```

| Result | Detail |
|--------|--------|
| E2E | **5 passed** (6.9s, Chromium headless, exit 0) |
| Vitest batch | 31 passed (prior task subset) |
| Backend bridge | 11 passed |

## Artifacts

- `docs/qa/intake-v6-three-step-final-confirmation-e2e-smoke-alignment-v1/E2E_INDEX.md`
- `docs/qa/intake-v6-three-step-final-confirmation-e2e-smoke-alignment-v1/three-step-smoke-pass.png`

## Files changed

- `frontend/e2e/helpers/intakeV6ThreeStepSmoke.ts` (new)
- `frontend/e2e/intake-v6-three-step-final-confirmation-smoke.spec.ts` (new)
- `frontend/e2e/intake-v6-step1-smoke.spec.ts`
- `frontend/e2e/intake-v6-runtime-capture-read-model.spec.ts`

## Application regression check

No `BLOCKED_APPLICATION_REGRESSION`. Three steps visible; Confirmare reachable; 60 mm + print/laminare shown; false cant-width / legacy confirmation copy absent. Note: generic `intake-v6-return-cant-blocked-operator-message` may still appear when product-truth operator_readiness is blocked for non-depth reasons — not asserted as false positive in this smoke (specific audit false warnings are what we gate).

## Forbidden scope

No application code, backend, DB, seed, pricing, or fixture business data changes.

## Honest opinion

E2E was the missing contract layer after the functional fix. Auth-gated final confirmation persistence deserves a dedicated dev-auth fixture helper in a follow-up; this smoke correctly stops before mutation.

## Remaining debt

- E2E auth helper for full confirm → enable handoff path
- Optional npm script `test:e2e:intake-v6-three-step-smoke`
- Generic return/cant operator banner vs product-truth operator_blockers alignment on IV6-189D2F12

## Next functional roadmap step

Dev-auth Playwright fixture for confirm persistence smoke; then leave confirmation/UI loop.

## Direction score

**94/100**

## Commit

Message: `Align Intake V6 final flow E2E smoke`
