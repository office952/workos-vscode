# Build — ACM shell Finish Contract in Intake v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Track** | Dual-track A (Finish ACM Intake — broad) |
| **Boundary** | Capture + confirm shell foil on AcmPanel; no CostEngine; no 641/8500/RAL; not letter finishes |

## Delivered

- Types: `frontend/src/lib/intakeV6/acmPanel/shellFinish.ts` (`acm_shell_finish_v1`)
- Persist: `buildAcmPanelShellFinishPatch` → `acm_panel_instance.shell_finish`
- UI: `IntakeV6AcmShellFinishPanel` in AcmPanel inspector „Material și finisaj”
- Face ≠ volume: stock / Oracal 651 / print+lam
- Foil strategies 1–3; XOR paint screws; colant after frame teaching
- Confirm operator (`operator_confirmed`)

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/acmPanel/shellFinish.test.ts
```

## Out of scope

CostEngine · task_rules materialization · segmented Analyzer · Composer (Track B separate)
