# Worklog — Intake V6 vocabulary and residual UI noise cleanup

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Initial HEAD:** `fc9c21b` (`refactor(intake-v6): realign page two operator flow`)  
**Commit message (target):** `refactor(intake-v6): clean operator vocabulary and mounting noise`

## Research tracks (reconciled)

1. **Raw enum / OWNER_GATE** — primary offenders in ACP local modules panel + ReviewStep profile/manual confirmation strings; segmented electrical already had RO labels.
2. **Operator Romanian copy** — mapping layer `intakeV6OperatorVocabulary.ts`.
3. **Commercial mounting** — `intake-v6-mounting-site-section` + mains cable service fields moved into `intake-v6-montaj-commercial-cluster`.
4. **Advanced demotion** — ownership notes stay under Avansat; Finisaje ownership wrapped in technical accordion; ACP raw readiness under module advanced.
5. **Severity vocabulary** — documented in audit §36; owner decision ≠ technical failure tone.
6. **Accessibility** — accordion toggle `aria-label` with expanded/collapsed state.
7. **Figma** — frame on `0CDPIuqoaZ1OQgNnvNyl1F` node `74:3`.
8. **Regression** — placement source guards + CASE 1 segmented E2E + electrical unit tests + screenshot E2E.

## Vocabulary map

See `docs/architecture/INTAKE_V6_COMPLETE_UI_UX_AND_FLOW_AUDIT.md` §36.

## Moved content

| Content | From | To |
|---------|------|-----|
| Montaj la locație | Sibling after Avansat | Inside Montaj comercial |
| Lungime cablu alimentare (serviciu) | Avansat | Montaj comercial |
| Finisaje ownership dump | Primary Finisaje | Technical accordion (collapsed) |
| ACP readiness raw tokens | Primary module card | Module advanced accordion |

## Remaining technical labels (intentional)

- Avansat ownership notes (`MOUNTING → …`)
- Template ID lines labeled „Detaliu tehnic · ID șablon”
- Advanced module `readiness_raw` / gate paths
- Option values in selects (internal codes) — not visible as primary status badges

## Figma

- File: `0CDPIuqoaZ1OQgNnvNyl1F`
- Page: `00 — Cover & Index`
- Frame: `Intake V6 — Page 2 Montaj (runtime sync 2026-07-19)` (`74:3`)
- Screenshot: `docs/qa/intake-v6-vocabulary-residual-ui-cleanup-2026-07-19/screenshots/14_figma_montaj_runtime_sync.png`
- Intentionally not updated: pixel-perfect component library / other pages
- Remaining diff: Figma is structural IA mirror; runtime visual tokens/spacing differ

## Tests

- Vitest: `intakeV6OperatorVocabulary`, `intakeV6MontajPlacement.vocab`, accordion, `segmentedElectrical`, `IntakeV6SegmentedElectricalPanel` — PASS
- Playwright CASE 1 segmented live E2E (`:3001`/`:8003`) — PASS
- Playwright vocab screenshots + placement assertions — PASS

## Screenshots

`docs/qa/intake-v6-vocabulary-residual-ui-cleanup-2026-07-19/screenshots/` (01–14)

## Regressions checked / fixed

- Site outside commercial → moved in
- Raw OWNER_GATE in ACP primary → mapped RO + advanced raw
- Finisaje ownership competing with operator decisions → demoted
- Accordion a11y labels improved
- Foreign WIP untouched

## Next step

Single coherent build: **Intake V6 Finisaje ownership + residual Page-1/composition technical dumps demotion** (copy-only), or operator polish on sticky blocker severity colors — **not** pricing/Execution.
