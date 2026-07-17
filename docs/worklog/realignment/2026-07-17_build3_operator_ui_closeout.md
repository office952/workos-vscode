# Build 3 — Operator UI closeout and multi-agent visual review

| Field | Value |
|-------|-------|
| Task | BUILD 3 OPERATOR UI CLOSEOUT AND MULTI-AGENT VISUAL REVIEW |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `7beb357` (Build 3 worklog) |
| End HEAD | `f96ad0b` (operator UI closeout) |
| Verdict | `BUILD3_OPERATOR_UI_CLOSEOUT_COMPLETE_WITH_GUARDS` |

## Owner request

Remove the persistent full-width red/staging system banner from the primary Intake V6 operator work area. Keep status accessible via compact indicator. Validate four modular scenarios with **real UI upload** of:

`C:/Users/offic/Desktop/fisiere-teste-svg/gradi-curat.svg`

## Agents

| Agent | Role |
|-------|------|
| A | Runtime UI truth |
| B | UI/UX reviewer guidance |
| C | System-status banner owner |
| D | Modular UI contract |
| E | Live calculation panel |
| F | Responsive |
| G | Regression |
| H | Adversarial UI |
| Writer | Single implementation |
| Fix | E2E locator strict-mode (duplicate svg-input) |

## UI reviewer — TOP 5

1. **Mandatory:** Full-width `EnvironmentBanner` under topbar consumes vertical space and dominates with staging/warning chrome.
2. Technical strip always visible for non-critical states.
3. Review autosave footer `sticky bottom-0` competes with workspace footer.
4. Scope summary must remain visible after banner removal.
5. Live calc panel must stay usable at 1440/1280/768.

### Mandatory fix

- Persistent full-width system banner → compact topbar chip.

### Optional (done, low risk)

- Review save footer no longer sticky (avoids overlap).
- Control Center link in details panel.

### Do not touch

- Formulas, CPP, active scope, SVG analyzer logic, PD/Aggregate filters.

## Synthesis / strategy

Root cause: App-shell `EnvironmentBanner` always mounted between topbar and `<main>` (`App.tsx`). Staging only labels text; red/`critical` comes from backend unavailable — but warning/staging still used a full-width strip.

**Chosen presentation:** compact chip inside `workos-desktop-topbar` (`data-presentation="compact"`), expandable details panel, critical one-line dismissible strip only when severity is critical. Technical details only inside expanded panel. Health hooks unchanged.

## Files changed

- `frontend/src/components/workos/EnvironmentBanner.tsx`
- `frontend/src/components/workos/EnvironmentBanner.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewSaveFooter.tsx`
- Evidence + worklog under `docs/audits/_evidence/2026-07-17_intake_v6_build3_operator_ui_closeout/`

## Four-scenario UI proof (real SVG upload)

| Scenario | Workspace | Verdict |
|----------|-----------|---------|
| Full product | `4d00bf12-8a21-441a-8b53-1be836d786d3` | PASS |
| FACE only | `1e287dc6-7eae-49ef-8b81-7b4b1a1ed063` | PASS |
| CANT only | `33761248-5a40-45b8-9aed-15de4922d9ca` | PASS |
| FACE+CANT | `e9167aa3-50f9-460c-a58f-eb124869dc52` | PASS |

Upload method: UI `data-testid="intake-v6-svg-input"` (operator panel). SVG hash `593c4d43…6cf1`.

Isolation: adhesive present on full / FACE+CANT; absent on FACE-only / CANT-only.

## System status proof

- Compact chip in topbar: PASS
- Staging shows as chip label, not full-width strip: PASS
- Details accessible via chip click: PASS
- Responsive 1440 / 1280 / 1024 / 768: PASS

## Adversarial + fix pass

- Not CSS-only hide — component remounted into topbar, presentation attribute `compact`.
- Critical strip still rendered for unavailable backend; dismissible without deleting health.
- E2E fix: duplicate `intake-v6-svg-input` nodes → prefer layers operator panel `.first()`.

## Exclusions

No schema/migration/seed, no formula/price/CPP/PD/Aggregate/active-scope changes, no Build 4.

## Next step

Owner visual review. **STOP — do not start Build 4.**
