# Build 3 — Operator UI closeout (compact runtime status + sticky layout)

| Field | Value |
|-------|-------|
| Task | BUILD 3 UI CLOSEOUT — COMPACT RUNTIME STATUS + STICKY LAYOUT CORRECTION |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `ce63b76` |
| End HEAD | *(filled after commit)* |
| Feature commit (prior closeout) | `f96ad0b` |
| Verdict | `BUILD3_OPERATOR_UI_CLOSEOUT_COMPLETE_WITH_GUARDS` |

## Root cause

App-shell `EnvironmentBanner` previously occupied a full-width strip under the topbar. Staging/environment context was visually dominant. Severity already came from backend/DB truth (`deriveSeverity`) — staging ≠ critical — but presentation treated informational states like a persistent alert band.

## Runtime severity map (unchanged meaning)

| Backend / DB truth | Banner severity | Presentation |
|--------------------|-----------------|--------------|
| loading/checking | neutral | Compact chip „Se verifică” |
| healthy + DB confirmed | positive | Compact „{Env} · Sistem disponibil” |
| warning / unknown / DB unverified / stale / demo | warning | Compact amber „Stare sistem: necesită verificare” (demo: „Mod demo”) |
| unavailable / critical | critical | Red chip „Stare sistem” + dismissible critical strip + details |

No `if staging then hide`. No severity remapping.

## Chosen presentation

1. Compact chip in `workos-desktop-topbar` (`data-presentation="compact"`).
2. Expandable `RuntimeStatusDetails` panel.
3. Link „Deschide Control Center” → `/modules`.
4. Critical: visible strip with „Detalii stare sistem” + „Ascunde”; chip remains critical after collapse.

## Sticky analysis

- `IntakeV6OperatorWorkspaceFooter`: sole `sticky bottom-0 z-10` authority.
- `IntakeV6ReviewSaveFooter`: `relative z-0 mb-20` (already corrected in `f96ad0b`).
- Runtime E2E confirmed: `workspace_sticky=true`, `save_relative=true`.
- Live calc: `lg:sticky lg:top-4` shell — opposite edge, no footer fight.

## Calculator analysis

Desktop right panel remains readable; not covered by footer. Values unchanged (no CPP/formula edits).

## Real SVG path

`C:/Users/offic/Desktop/fisiere-teste-svg/gradi-curat.svg`  
Upload: UI `data-testid="intake-v6-svg-input"` only.  
Hash: `593c4d43…6cf1` · layers 6 · ~5087×600 mm.

## Workspaces (this pass)

| Scenario | Workspace ID |
|----------|--------------|
| Full product | `b4502ac6-ce5e-4f96-b67f-5a3cb55388db` |
| FACE | `9e3743be-ee44-41c5-9d93-0cb5803c5ff3` |
| CANT | `ada11273-2f45-426b-822f-7e691c7e0bb3` |
| FACE+CANT | `101b0cb3-96e2-48bb-9fd2-9fa13e1bc20d` |

## Tests

- Vitest `EnvironmentBanner`: 7 passed (healthy / warning / critical dismiss / Control Center / staging≠critical).
- Pytest Build 1/2/3: 37 passed.
- Playwright closeout E2E: PASS four scenarios + responsive 1440/1280/1024/768.

## Adversarial + fix pass

- Not CSS-only hide — remount + compact presentation + label matrix.
- Staging remains warning when DB unverified; not forced healthy; not critical.
- Critical strip dismissible; chip severity persists.
- Fix pass: `mkdirSync` for `08_payloads` before write (ENOENT false FAIL).
- Sticky already correct — no second sticky change.

## Files changed (this pass)

- `frontend/src/components/workos/EnvironmentBanner.tsx`
- `frontend/src/components/workos/EnvironmentBanner.test.tsx`
- Evidence + e2e under `docs/audits/_evidence/2026-07-17_intake_v6_build3_operator_ui_closeout/`
- This worklog

Prior closeout (`f96ad0b`): `App.tsx`, `IntakeV6ReviewSaveFooter.tsx`.

## Exclusions

No schema/migration/seed · no PD/Aggregate/CPP/formula/price/active-scope · no Build 4.

## Next step

Owner visual review. **STOP.**
