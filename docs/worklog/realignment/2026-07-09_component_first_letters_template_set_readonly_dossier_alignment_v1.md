# COMPONENT_FIRST_LETTERS_TEMPLATE_SET_READONLY_DOSSIER_ALIGNMENT_V1

## Scope

- Readonly dossier alignment contract only.
- No activation.
- No seed live.
- No `seed_sync_all` change.
- No migration.
- No DB write.
- No backend change.
- No Pricing / ProductDefinition / ProductAggregate / Quote / Order / Execution change.
- No Work Intake exposure.
- No task materialization / ExecutionPlan / TaskGraph.

## HEAD before

- `addbb7b`

## Files touched

- `frontend/src/features/product-system/componentFirstReadonlyDossierAlignment.ts`
- `frontend/src/features/product-system/componentFirstReadonlyCompleteness.test.ts`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_readonly_dossier_alignment_v1.md`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_dossier_alignment_v1/*.png`

## Problem closed

After completeness guard and fixture comparison guard, the component-first set had provenance and drift detection.
This slice adds readonly dossier alignment contract readiness so each expected template maps coherently toward future Product/Component Dossier metadata without inventing runtime dossier rows.

## Helper added

`componentFirstReadonlyDossierAlignment.ts`:

- `COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE` (7 entries)
- `validateComponentFirstDossierContract()`
- `assessComponentFirstDossierAlignment(liveTemplates, { completeness?, drift? })`
- runtime link labels and alignment tones

## Dossier alignment states

| State | Meaning |
|---|---|
| `READONLY_ALIGNED` | 7/7 live inactive + 7/7 dossier contract |
| `READONLY_FALLBACK_ONLY` | 0/7 live + 7/7 dossier contract |
| `READONLY_PARTIAL` | partial live + 7/7 dossier contract |
| `BLOCKED_INVALID_LIVE_STATE` | any active expected row |
| `BLOCKED_DOSSIER_ACTIVATION_LEAK` | task materialization / execution / pricing / quote / work-intake leak signals |

Runtime dossier link states:

- `NOT_LINKED_YET` — default when catalog rows exist but no blueprint dossier linkage
- `READONLY_CONTRACT_ONLY` — 0/7 live; contract readiness only
- `PARTIAL_RUNTIME_LINK` — partial live catalog only
- `BLOCKED_RUNTIME_ACTIVATION_LEAK` — forbidden runtime wiring detected

## Relationship to existing guards

- **Completeness guard** supplies `foundRowCount`, `missingTemplateCodes`, `invalidActiveTemplateCodes`, `sourceMode`.
- **Drift guard** supplies contract-check status and live-vs-fallback drift warnings.
- **Dossier alignment** consumes both assessments and adds per-template dossier role/truth-owner contract plus runtime dossier honesty (`not linked yet`).

## UI changes

Readonly `Dossier alignment` block in component-first letters section:

- `Dossier contract: 7/7`
- `Runtime dossier rows: not linked yet` / `readonly contract only`
- `Alignment: <state>`
- truth ownership summary
- guard: no task materialization / ProductAggregate / ProductDefinition / Pricing / Quote / Order / Execution

No CTA, no activate/promote/write controls.

## Tests run

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

Result:

- `31 passed`

Coverage added:

- dossier contract exactly 7 entries
- composer = product_composer / composer_orchestration
- 6 components = component_template / component-owned truth
- 7/7 inactive => `READONLY_ALIGNED`
- 0/7 => `READONLY_FALLBACK_ONLY`
- partial => `READONLY_PARTIAL`
- active row => `BLOCKED_INVALID_LIVE_STATE`
- runtime dossier not linked => readonly readiness, not failure
- activation leak signals => `BLOCKED_DOSSIER_ACTIVATION_LEAK`
- UI dossier block rendering without activation buttons

## UI verification

URL:

- `http://127.0.0.1:3000/product-system`

Live browser proof (0/7 live rows in current DB):

- `Dossier contract: 7/7`
- `Runtime dossier rows: readonly contract only`
- `Alignment: READONLY_FALLBACK_ONLY`
- `contract check: OK`
- `drift: NO_DRIFT`
- `completeness: 0/7`

Screenshot paths:

- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_dossier_alignment_v1/product_system_overview_context.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_dossier_alignment_v1/component_first_letters_template_set_section.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_dossier_alignment_v1/component_first_dossier_alignment_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_dossier_alignment_v1/component_first_source_state_completeness_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_dossier_alignment_v1/component_first_activation_no_materialization_guard_closeup.png`

## Sincere UI opinion

- Dossier reads as contract/readiness, not runtime activation — especially with explicit `not linked yet` / `readonly contract only` copy.
- Guard line makes no task materialization explicit.
- Truth ownership line clarifies composer vs component truth split.
- Low risk of appearing offerable: INACTIVE / CANDIDATE / READONLY badges remain; no CTA.
- Still engineering-facing; dossier role names (`composer_orchestration`, `return_cant`) remain technical.

## Forbidden scope confirmation

- No seed live
- No `seed_sync_all`
- No migration
- No DB write
- No delete/cleanup
- No writer path
- No activate/promote/write button
- No Pricing
- No ProductDefinition runtime
- No ProductAggregate runtime
- No Quote / Order / Execution
- No TaskGraph / ExecutionPlan / task materialization
- No Work Intake exposure
- No `TPL-VOLUMETRIC-LETTERS_v2` change
- No LOGO activation
- No component root/quote

## Limitations

1. Dossier alignment is frontend contract only; no blueprint dossier API linkage yet.
2. Runtime dossier rows are honestly reported as not linked — no invented dossier entities.
3. Activation leak detection scans notes/operations_json shape only on component-first family rows.

## Next recommended slice

`COMPONENT_FIRST_LETTERS_TEMPLATE_SET_READONLY_OWNER_REVIEW_CARD_V1`

Suggested scope:

- owner-language summary card above engineering panel
- readonly only
- no activation
- no seed live

## Roadmap awareness checkpoint

- Spine position: blueprint → inert seed → readonly Product System → completeness → fixture comparison → dossier alignment contract → still before activation/live seed.
- Direction adherence: `99/100`.
