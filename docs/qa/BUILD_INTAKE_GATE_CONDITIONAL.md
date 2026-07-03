# BUILD-INTAKE-GATE-CONDITIONAL

## Audit finding addressed

P0 from `de783a5` — generic unresolved intakes showed terrain audit, fiscal/CUI, template CTAs, and quote readiness blockers before work type selection.

## Gate model

| Stage | Condition | UI |
|-------|-----------|-----|
| **0** | `product_family` empty | Client context, delivery (info), **Alege tip lucrare** |
| **1** | Work type known | Template workspace, spec, conditional terrain |
| **2** | Quote estimate ready | Preliminary simulation |
| **3** | Commercial quote ready | Final quote gate |

Code: `frontend/src/lib/intakeGateStages.ts`, `docs/architecture/INTAKE_GATE_STAGES.md`.

## Sections hidden (Stage 0)

- `IntakeActionSummary` (terrain 1/3, Confirmă template, readiness list)
- `IdentitySection` (CUI/SmartBill)
- `AuditTerenSection` (Detalii Tehnice Client)
- Marchează Gata pt. Ofertă + readiness blockers
- Install delivery blocker → neutral note only

## Sections preserved

- Volumetric workspace (`TemplateWorkspaceRouter`) unchanged
- `Product001IntakeSpecEditor` untouched
- SVG/vector pathway untouched
- `/quotes` generic QuoteWizard untouched

## Tests / lint

```text
vitest: intakeGateStages.test.ts, IntakeDetail.unresolvedWorkType.test.tsx,
        IntakeDetail.routing.test.tsx, IntakeDetail.volumetricShell.test.tsx — PASS
eslint: IntakeDetail.tsx, intakeGateStages.ts, IntakeActionSummary.tsx — warnings only (pre-existing hooks)
```

## Browser validation

### A. Generic unresolved `IR-MQ3E7K2V`

- Visible: Tip lucrare — nespecificat, Alege tip lucrare, client summary
- Hidden: terrain 1/3, Mergi la teren, CUI panel, quote blockers
- Install note: neutral “Montajul va fi verificat…”

### B. Volumetric `IR-MQ3C869E`

- Workspace + vector pathway preserved

### C. `WI-SMOKE-P001`

- Simulation baseline 844,41 EUR preserved (volumetric shell test)

### D. `/quotes`

- Ofertă nouă → generic QuoteWizard (unchanged)

## Counts

| | Before | After |
|---|--------|-------|
| intakes | 22 | 22 |
| quotes | 7 | 7 |
| orders | 8 | 8 |

## Confirmations

- No pricing / CostEngine / quote calculation changes
- No quote or order created
- No Reference Catalogs started
- Readiness policy (`intakeReadiness.ts`) unchanged — display filter only
- `Product001IntakeSpecEditor` unchanged
- SVG/vector flow untouched
- WI-SMOKE-P001 baseline preserved

## Commit

`5643dfb` — fix: stage unresolved intake gates
