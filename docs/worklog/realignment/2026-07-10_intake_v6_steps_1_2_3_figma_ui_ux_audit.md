# Worklog — Intake V6 Steps 1–3 UI/UX Audit (Figma)

**Date:** 2026-07-10  
**Status:** COMPLETE — audit only  
**Build boundary:** No code changes. Documentation + screenshots + Figma proposal only.

---

## Scope

Audit UI/UX pentru Intake V6:
- Pas 1 (Straturi / `layers`)
- Pas 2 (Review / `review`) — taburi Finisaje, Iluminare, Montaj
- Pas 3 (Confirmare / `confirm`) — layout vertical, accordions
- Inventar badge-uri și collapsibles
- Propunere vizuală controlată în Figma

**Out of scope:** implementare frontend/backend, DB, seed, pricing, ProductDefinition, ProductAggregate.

---

## Runtime verificat

| Service | Status |
|---------|--------|
| Frontend :3000 | 200 |
| Backend :8000 | 200 |
| `/intake` | 200 (Work Intake list) |
| Intake V6 workspace | 200 |

---

## URL / rute

| Ruta | Rol |
|------|-----|
| http://127.0.0.1:3000/intake | Inbox cereri (canonical entry) |
| http://127.0.0.1:3000/intake-v6/:workspaceId/operator | Workspace operator Intake V6 |
| http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator | Workspace auditat |

Legacy `/intake/:id` redirectează către Intake V6 (confirmat din `IntakeLegacyRoute.tsx`).

---

## Workspace / test data

| Field | Value |
|-------|-------|
| Workspace UUID | `22ef834d-f2d0-453b-a7a7-118928c98a39` |
| UI code | IV6-189D2F12 |
| Template | Litere volumetrice (`TPL-VOLUMETRIC-LETTERS_v2`) |
| SVG | gradi-curat.svg (6 straturi, artwork + litere) |
| E2E reference | `frontend/e2e/intake-v6-step1-smoke.spec.ts` folosește același workspace |

---

## Fișiere inspectate (read-only)

### Routing & shell
- `frontend/src/App.tsx`
- `frontend/src/pages/IntakeV6OperatorWorkspaceApp.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6OperatorWorkspace.tsx`
- `frontend/src/lib/intakeV6/intakeV6Contracts.ts`
- `frontend/src/lib/intakeV6/intakeV6ProductPlugin.ts`

### Steps
- `frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx`

### Tabs & collapsibles
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewTabNav.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/components/workos/intake-v6/atoms/IntakeV6TechnicalDetailsAccordion.tsx`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.tsx`

### Badges
- `frontend/src/components/workos/intake-v6/atoms/intakeV6Presentation.tsx` (`AtomsBadge`)
- `frontend/src/components/workos/intake-v6/IntakeV6ComponentQuestionBadges.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LayerCardCollapsedHeader.tsx`

---

## Capturi realizate

**Folder:** `docs/qa/intake-v6-ui-ux-audit-2026-07-10/screenshots/`  
**Count:** 24 PNG + `capture_manifest.jsonl`

| Grup | Fișiere |
|------|---------|
| Pas 1 | `01`–`07` (full, scroll, expanded layers, metrics, composition) |
| Pas 2 | `10`–`16` (initial, 3 tabs top/bottom, cards expanded, technical collapsed/expanded, form-system) |
| Pas 3 | `20`–`24` (initial, operator summary collapsed/expanded, technical collapsed/expanded) |

**Script captură:** `docs/qa/intake-v6-ui-ux-audit-2026-07-10/capture-audit-screenshots.mjs` (Playwright, read-only pe UI)

---

## Pagini / frame-uri Figma

| Item | Value |
|------|-------|
| File | [WorkOS Intake V6 — UI Audit](https://www.figma.com/design/911Q6oRKcEursrRoT4Qj0h) |
| Key | `911Q6oRKcEursrRoT4Qj0h` |
| Pagini | 00 Audit Overview … 10 Before / Proposed Comparison |
| Frames populate | 00 overview + findings; 07 proposed Step 2; 09 tabs & status system |

### Anotații numerotate (sample)

| ID | Problema | Severitate |
|----|----------|------------|
| P1-01 | Triplu semnal complet Pas 1 | High |
| P1-02 | Chip-uri Atenție analiză redundante | Medium |
| P2-TAB-01 | 3 surse paralele probleme Pas 2 | High |
| P2-COL-01 | Blockers ascunse în Detalii tehnice | Critical |
| P2-COL-02 | Badge 651 COLORED redundant | Medium |
| P3-01 | Badge De completat x3 Pas 3 | High |
| BADGE-01 | ~47 badge-uri max simultan | High |

---

## Findings (summary)

Vezi raport complet: `docs/qa/intake-v6-ui-ux-audit-2026-07-10/INTAKE_V6_STEPS_1_2_3_UI_UX_AUDIT_V1.md`

**Verdict:** PASS_AUDIT_COMPLETE  
**Overall score:** 5.7/10

---

## Recomandarea principală

**Status la nivel de secțiune, nu la nivel de câmp:**
- Banner unic blocker sub tab bar
- Tab status: pending count / check discret (fără ON pill)
- Collapsed summary: titlu + valoare + 1 secundar + stare
- Diagnostics (form-system) collapsed by default, redenumit „Diagnostic tehnic”

---

## Badge reduction summary

- ~52 instanțe identificate
- ~45% reducere recomandată
- Keep: pending Finisaje count, footer issues, blocker banner
- Remove/Merge: ON pill, 651 COLORED, per-layer check when 100%, Handoff x2, De completat x3 → 1 mesaj

---

## Collapsible content summary

| Clasificare | Secțiuni |
|-------------|----------|
| A (deschis implicit dacă blockers) | Detalii tehnice când blockers > 0; primul artwork neconfirmat |
| B (collapsed + sumar bun) | Layer cards Finisaje |
| C (discret collapsed) | Calcul live details |
| F (advanced/debug) | Form-system backbone, metrici tehnice |

---

## Fișiere modificate

| File | Change |
|------|--------|
| `docs/worklog/realignment/2026-07-10_intake_v6_steps_1_2_3_figma_ui_ux_audit.md` | Created |
| `docs/qa/intake-v6-ui-ux-audit-2026-07-10/INTAKE_V6_STEPS_1_2_3_UI_UX_AUDIT_V1.md` | Created |
| `docs/qa/intake-v6-ui-ux-audit-2026-07-10/capture-audit-screenshots.mjs` | Created |
| `docs/qa/intake-v6-ui-ux-audit-2026-07-10/screenshots/*.png` | Created (24) |

**Nu s-a modificat cod aplicație.**

---

## Confirmare fără implementare

- [x] Nu am modificat frontend
- [x] Nu am modificat backend
- [x] Nu am modificat DB
- [x] Nu am creat seed-uri
- [x] Nu am creat migrări
- [x] Nu am schimbat business logic
- [x] Nu am schimbat taxonomia owner
- [x] Nu am modificat ProductDefinition/ProductAggregate
- [x] Nu am modificat pricing
- [x] Nu am implementat recomandările
- [x] Nu am introdus mock data în app
- [x] Nu am atins Employee Mobile
- [x] Am creat worklog persistent
- [x] Am furnizat dovezi vizuale
- [x] Am folosit Figma doar pentru audit/propunere controlată

---

## Teste / validări

| Command | Result |
|---------|--------|
| Runtime HTTP :3000/:8000 | PASS |
| Playwright capture script | PASS (24 screenshots) |
| Frontend/backend tests | Not run (no code changes) |

---

## Blocaje

None — runtime disponibil, workspace funcțional.

---

## Owner decisions necesare

1. Promovare blockers din form-system în banner operator?
2. GO pentru reducere badge-uri (~45%)?
3. Calcul live — permanent sidebar sau collapsible?
4. Acces „Diagnostic tehnic” — operator vs admin?

---

## Next step recomandat

Owner review al auditului și selectarea explicită a recomandărilor care primesc GO pentru implementare.

---

## Scor direcție

| Metric | Score |
|--------|-------|
| Audit completeness | 10/10 |
| Roadmap alignment | 9/10 |
| Implementation readiness | 8/10 (pending owner GO) |
