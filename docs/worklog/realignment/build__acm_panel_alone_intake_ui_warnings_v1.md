# Build — ACM panel-alone Intake UI warnings + construction form v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Workspace proof** | `IV6-FEA75D2C` / `doar-panou.svg` |
| **Boundary** | Auto-role Contur suport; construction fold UI; single-panel dims; Review chrome ACM-only; no CostEngine |

## Fixes

1. **Auto-role** — stroke pe layer „Alucobond Casetat” nu mai vira la Logo; `alucobond`/`casetat` → `support_panel` (fără match greșit pe `bond`→backing)
2. **Instantiate** — panou singur primește rând `panels[]` cu W×H (CUT/V deduction)
3. **Construcție UI** — select 1/2 întoarceri, L1/L2/grosime, CTA „Confirmă construcția panoului”
4. **Review ACM-only** — tab Montaj only; ascunde avertizarea Cant litere

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/svgAnalyzer/analyzer/remusDoarPanouSupportRole.test.ts `
  src/lib/intakeV6/acmPanel/acmPanelOnlyComposition.test.ts `
  src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelInspector.commitSemantics.test.tsx
```
