# Build — ACM panel-alone calc honesty (adeziv / V-groove / cadru) v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Boundary** | No new ACM adhesive/frame commercial rates; honesty only; no CostEngine rewrite |

## Problem

Pe panou ACM singur (Remus `doar-panou`): UI cerea adeziv cant litere, V-groove lipsea la cantități, cadrul era read-only / neclar.

## Fixes

1. **Live-calc filter** — `support_only` / ACM-only: elimină rânduri VL (adeziv, cant, față plexi, LED) din logical list + material breakdown, chiar sub scope legacy; păstrează `acm_*`.
2. **V-groove qty** — envelope W×H când `panels[]` e gol (`source=envelope`); operator confirm/edit sincronizează `panels[0]` din geometrie.
3. **Cadru interior** — toggle în inspector + copy „tehnic / neprețuit în CPP”.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_acm_assembly_extent.py tests/test_intake_v6_acm_panel_only_capture_filter.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/intakeV6/acmPanel/assemblyExtent.test.ts `
  src/lib/intakeV6/acmPanel/operatorPatch.test.ts
```
