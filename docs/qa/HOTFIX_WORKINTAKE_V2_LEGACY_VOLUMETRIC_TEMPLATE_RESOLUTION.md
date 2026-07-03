# HOTFIX: WorkIntake V2 Legacy Volumetric Template Resolution

**Date:** 2026-06-08  
**Status:** **PASS**  
**Route:** `/intake-v2/:id`  
**Example intake:** `IR-MQ51B998`

---

## Root cause

After **Template Intake Modularity Foundation**, `WorkIntakeV2Flow` resolves config only via `resolveWorkIntakeTemplateConfig(confirmedTemplateCode)`. Page routing (`shouldUseVolumetricIntakePage`) already allowed `litere_volumetrice` family without a confirmed template, but the Flow resolver did not — legacy intakes reached V2 and hit `work-intake-v2-unsupported-template`.

## Missing mapping

| Layer | Before hotfix |
|-------|----------------|
| Page gate (`volumetricIntakeRoute.ts`) | `family = litere_volumetrice` → V2 allowed |
| Flow resolver (`resolveWorkIntakeTemplateConfig.ts`) | Only `confirmedTemplateCode === TPL-VOLUMETRIC-LETTERS` |

Gap: routing vs config resolution.

## Fallback rule implemented

Priority in `resolveWorkIntakeTemplateConfig({ confirmedTemplateCode, productFamily })`:

1. `confirmedTemplateCode === TPL-VOLUMETRIC-LETTERS` → `volumetricLettersTemplateConfig` (explicit).
2. Missing / null / `---` / `—` template **and** `isLitereVolumetriceFamily(productFamily)` → same config, `resolvedViaLegacyFamily: true`.
3. Any other non-empty unknown code (e.g. `TPL-ACM-CASSETTED-PANEL`) → `null` (unsupported).

**Not allowed:** inferring volumetric from missing template alone.

Readiness, handoff, and `volumetricReadinessStrategy` unchanged. Legacy intakes still show **Confirmă template** until `confirmed_template_code` is persisted.

## UI

When resolved via family fallback, header shows badge `TPL-VOLUMETRIC-LETTERS` plus note `rezolvat din familia litere_volumetrice` (`work-intake-v2-template-legacy-family-note`).

## Files modified

- `frontend/src/lib/workIntakeV2/templateConfig/resolveWorkIntakeTemplateConfig.ts`
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.tsx`
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2OperationalHeader.tsx`
- `frontend/src/lib/workIntakeV2/templateConfig/templateConfig.test.tsx`

## Tests

| Case | Expected |
|------|----------|
| `TPL-VOLUMETRIC-LETTERS` confirmed | Volumetric config |
| `null` / `undefined` + `litere_volumetrice` | Volumetric config (legacy flag) |
| `null` + unknown family | Unsupported |
| `TPL-ACM-CASSETTED-PANEL` | Unsupported |
| `IR-MQ51B998`-style flow render | No unsupported screen |

```bash
cd frontend
npx vitest run src/lib/workIntakeV2/templateConfig/templateConfig.test.tsx
```

## Boundary

| Area | Touched? |
|------|----------|
| CostEngine / Pricing / Inventory | No |
| Backend | No |
| WorkIntake V1 | No |
| QuoteWizard | No |
| ACM activation | No |
| Readiness / handoff rules | No |

---

## PASS

Legacy volumetric family intakes enter WorkIntake V2 volumetric flow; unknown templates remain unsupported; tests pass.
