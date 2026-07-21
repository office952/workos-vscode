# VL Pre-Publication E2E — Shared Map (CP0)

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `520f3f01` (reconfirmed) |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Parent | `TPL-VOLUMETRIC-LETTERS_v2` — **KEEP UNPUBLISHED** |
| Child | `TPL-VOLUM-ALUMINIU_v1` active=true, published=false (id=10) |
| Mode | Pre-publication E2E proof — no parent publish |

## Six NOT_TESTED (accepted baseline)

| # | System | Prior reason | Close path |
|---|--------|--------------|------------|
| 1 | `product_truth` | static skips job revision | `runtime_dry_run` + confirmed workspace |
| 2 | `cpp` | readiness never exercises formulas | runtime preview↔qty ml proof (no CostEngine dup) |
| 3 | `eic` | same | runtime INT_VOL_V2_RETURN_ML / qty overlay proof |
| 4 | `quote_snapshot` | static skips freeze | runtime freeze-gate on confirmed PT |
| 5 | `order_snapshot` | no order create | preview provenance enrich + convert helpers (no live Order) |
| 6 | `execution_preview` | no materialization | frozen-snapshot preview only (`no_write`) |

## Fixture lineage (one primary)

| Key | Value |
|-----|--------|
| Label | `VL_PREPUB_E2E_FIXTURE_v1` |
| Template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Return | Cant din aluminiu / `TPL-VOLUM-ALUMINIU_v1` / `modelare_cant` |
| Confirmed perimeter | **12.5 m** (operator_confirmed) |
| Depth | **60 mm** |
| Finish | `white_aluminum` (Stock) |
| Groups | `pseudo:maria` (+ optional `pseudo:soare` for multi) |
| Evidence perimeter | aligned 12.5 m (bridge) / negative tests use diverge |
| Persistence | pytest isolated workspace only; named `IV6-VL-PREPUB-*` |
| Forbidden | SVG/DWG/DXF parse; live customer Quote/Order |

## Identity spine (must preserve)

```
TPL-VOLUMETRIC-LETTERS_v2
  └─ required_module TPL-VOLUM-ALUMINIU_v1
       BOM: comp_volum_aluminiu_module
       Aggregate key: modelare_cant (once)
       Pricing stub alias: comp_lateral_litere → modelare_cant
       CPP line: modelare_cant_aluminiu / VOL_V2_RETURN_PROFILE_ML
       EIC rule: INT_VOL_V2_RETURN_ML
       PT container: product_truth.components.return_cant
```

## Path + checkpoints

| CP | Systems | Evidence mode |
|----|---------|---------------|
| CP0 | Freeze map/allowlist | docs only |
| CP1 | Intake + Product Truth | RO helpers + isolated confirm fixture |
| CP2 | Product Definition | workspace preview, revision pin |
| CP3 | Aggregate + Quantity | same revision/hash; perimeter qty |
| CP4 | CPP + EIC | preview qty == product-total; ml; anti-hourly |
| CP5 | Quote Snapshot V2 | freeze gate dry assessment (no customer quote) |
| CP6 | Order Snapshot | provenance enrich only; **no live order** if unsafe |
| CP7 | EP preview | `build_execution_preview_from_frozen_snapshot` only |

## Approved endpoints (dry / preview)

| Endpoint / API | Write? |
|----------------|--------|
| GET e2e-readiness/{code}/static | no |
| POST e2e-readiness/{code}/runtime-dry-run | no (`write_performed=false`) |
| separate-calculation-preview | no (`persist=false`) |
| ConfirmJobProductTruth (test fixture only) | yes — isolated test workspace |
| EP from frozen snapshot | no materialization |

## RO vs write-required

| Evidence | Mode |
|----------|------|
| Catalog/components/intake/PD/Agg static | RO |
| Separate calc / perimeter authority | RO |
| Readiness static | RO |
| PT confirm + runtime readiness | Write to **isolated** intake_v6 workspace only |
| Quote/Order live customer | **FORBIDDEN** |
| Parent/child publish | **FORBIDDEN** |

## Warning ownership (non-blocking expected)

- Aggregate dossier metadata-only warnings
- Premount optional trigger_field mismatches
- Static mode retains NOT_TESTED for unproven stages by design until runtime

## Publication gate

- `publication_status` parent remains null / unpublished
- Recommendation only at end: GO / GO_WITH_CONDITIONS / NO-GO / INSUFFICIENT_EVIDENCE
- Never execute publish

## Non-effects / forbidden writes

No logo-return activation; no relationship/pricing/formula redesign; no schema migration; no Execution materialization; no employee assignment; no `git add -A` / dirty-tree reset; no push/PR.

## Agents (after CP0)

| Agent | Scope |
|-------|-------|
| A | Fixture / Intake |
| B | PT + PD |
| C | Agg + Qty |
| D | CPP + EIC |
| E | Snapshot + Order boundaries |
| F | EP preview |
| G | Readiness / UI / QA report |

## Stop conditions

Publication required to exercise flow; schema/pricing redesign; Snap/Order needs live customer data; EP needs materialization; conflicting PT authority; double-count; quote_geometry independent again; inseparable dirty tree.
