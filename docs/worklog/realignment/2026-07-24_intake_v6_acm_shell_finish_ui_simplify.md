# Intake V6 — simplify ACM shell Oracal / finish UI

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Boundary** | Display / IA only — no CostEngine, CPP rates, or new commercial calc |
| **Owner ask** | Reduce text; Oracal = cum aplici folia + bife față/cant; restul atelier |

## Before (operator story)

Material și finisaj showed a long essay (641/8500/RAL), duplicate Față/Volum editors (Cod Oracal, Lățime rolă), Strategie folie multi-bucăți + Nr. bucăți + Client informat, and a dense status line. Panou Alucobond form also carried lab jargon (bbox, capabilități, CUT/V-groove footnotes).

## After (operator story)

1. **Cum aplici folia** — După cadru / Fără colant  
2. **Unde aplici** — checkboxes Față · Cant (volum); short Oracal 651 hint  
3. **Detalii atelier** (collapsed) — zone kinds, cod, lățime, strategie folie  
4. Shorter construction labels (Pliuri, Confirmă construcția) and leaner rezumat in flat workbench  

Persistence contract `acm_shell_finish_v1` unchanged.

## Files

- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmShellFinishPanel.tsx`
- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmShellFinishPanel.test.tsx`
- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelInspector.tsx`
- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelConfigRegion.tsx`
- `frontend/src/components/workos/intake-v6/acm-panel/AcmPanelProductionGeometryBlock.tsx`
- `frontend/src/lib/intakeV6/acmPanel/shellFinish.ts`
- `frontend/src/lib/intakeV6/acmPanel/shellFinish.test.ts`

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/acmPanel/shellFinish.test.ts src/components/workos/intake-v6/acm-panel/IntakeV6AcmShellFinishPanel.test.tsx src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelConfigRegion.blueprint.test.tsx
```
