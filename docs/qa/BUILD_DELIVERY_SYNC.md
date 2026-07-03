# BUILD-DELIVERY-SYNC

## Audit finding

P0/P1 from intake-to-quote audit: delivery type appeared in multiple places with inconsistent terrain gating.

## Canonical semantics

Central helper: `frontend/src/lib/intakeDeliverySemantics.ts`

| Delivery | Terrain audit | Notes |
|----------|---------------|-------|
| unset | No | Label: Livrare nealeasă |
| pickup / courier / standard / express | No | Teren N/A |
| delivery_install + work type known | Yes | Terrain panel + blockers |
| delivery_install + Stage 0 unresolved | No | Neutral install note only |

Key exports: `requiresTerrainAudit`, `getDeliveryLabel`, `getDeliveryStageNote`, `filterReadinessMissingForDisplay`, `INTAKE_DELIVERY_OPTIONS`.

## UI behavior

- **Stage 0 generic**: delivery informational; install → neutral note; no terrain
- **Volumetric non-install**: `TerrainRequirementPanel` shows N/A compact label; terrain blockers filtered from display
- **Volumetric install**: full terrain section; terrain blockers visible
- **Delivery change away from install**: site audit data preserved; note in side panel

## Code audit summary

| File | reads | writes | action |
|------|-------|--------|--------|
| `intakeDeliverySemantics.ts` | — | — | **new** canonical source |
| `IntakeDetail.tsx` | yes | yes | uses `requiresTerrainAudit`, `showTerrainGates` |
| `VolumetricLettersWorkspace.tsx` | yes | via callback | filters readiness display |
| `RequestContextPanel.tsx` | yes | yes | canonical labels + stage note |
| `NewIntakeDialog.tsx` | yes | yes | `INTAKE_DELIVERY_OPTIONS` |
| `intakeActionSummary.ts` | yes | — | filtered `readinessMissing` |
| `intakeReadiness.ts` | yes | — | unchanged policy |

## Tests / lint

```text
intakeDeliverySemantics.test.ts — 9 PASS
IntakeDetail.deliverySync.test.tsx — 4 PASS
IntakeDetail.unresolvedWorkType.test.tsx — 6 PASS
IntakeDetail.volumetricShell.test.tsx — 12 PASS
VolumetricLettersWorkspace.test.tsx — 6 PASS
intakeGateStages.test.ts — 2 PASS
intakeActionSummary.test.ts — 3 PASS
```

## Browser validation

- `IR-MQ3E7K2V`: neutral install note, no terrain
- `IR-MQ3C869E`: volumetric workspace + vector intact
- `WI-SMOKE-P001`: baseline preserved via volumetric shell tests

## Counts

| | Before | After |
|---|--------|-------|
| intakes | 22 | 22 |
| quotes | 7 | 7 |
| orders | 8 | 8 |

No intakes modified during smoke.

## Confirmations

- No pricing / CostEngine / quote calculation changes
- No quote or order created
- No Reference Catalogs started
- Readiness policy unchanged (display filter only)
- `Product001IntakeSpecEditor` unchanged
- SVG/vector flow preserved
- WI-SMOKE-P001 baseline preserved

## Commit

`25fa94a` — fix: synchronize delivery terrain gates
