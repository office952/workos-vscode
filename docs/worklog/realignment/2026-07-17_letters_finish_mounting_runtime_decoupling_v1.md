# Worklog — LETTERS_FINISH_MOUNTING_RUNTIME_DECOUPLING_V1

Date: 2026-07-17  
Repo: `C:/w/psiso`  
Branch: `feature/product-system-active-path-isolation-v1`  
Baseline HEAD (start): `05b5dba485f7f7d0101af0736ace75a4f4301343`

## Owner GO

```text
OPTION B = RUNTIME RESPONSIBILITY DECOUPLING WITH COMPATIBILITY ALIAS
MOUNTING_MAP_NARROWING_OWNER_GATE = APPROVED
MINI_MODULE_SPLIT_OWNER_GATE = APPROVED
PACKAGING = COMPOSITION / CONDITIONAL RESPONSIBILITY
PACKAGING SOLD CHIP = NOT APPROVED
FULL LETTERS COMPLETE OUTPUT = MUST BE PRESERVED
```

Approved plan: `docs/plans/2026-07-17_letters_finish_mounting_runtime_decoupling_v1_plan.md`

## Approved gates

| Gate | Status |
|------|--------|
| MOUNTING_MAP_NARROWING_OWNER_GATE | APPROVED |
| MINI_MODULE_SPLIT_OWNER_GATE | APPROVED |
| SOLD_CHIP_ACTIVATION_OWNER_GATE | NOT_APPROVED |
| PACKAGING_SOLD_CHIP | NOT_PLANNED |

## Compound Engineering

1. Parallel read-only research (prior plan turn)
2. Single synthesis → Option B
3. Single writer (this implementation)
4. Adversarial review via focused suites + ownership/map leakage tests
5. Fix pass (registry compatibility_rules shape; FE gate status; intake preview split)
6. E2E proof via targeted pytest + Vitest + frontend build

## Before-state ledger (pre-write baseline)

| Surface | Before |
|---------|--------|
| MOUNTING map | `{structura_suport, finisaje}` |
| FINISH map | `{finisaje}` |
| `finisaje` role | Mixed bucket (surface + șablon + ambalare) |
| Phantom Aggregate codes | `sablon_montaj`, `ambalare_livrare_montaj` (not in LETTERS_RUNTIME_MODULES) |
| Snapshot writer | `active_scope_snapshot/v1` |
| Sold FINISH/MOUNTING | Deferred / blocked |
| Responsive UI | PARTIAL |

## Responsibility moves

| Responsibility | Runtime code | Notes |
|----------------|--------------|-------|
| SURFACE_FINISH | `finisaje` | Narrowed; module **not** removed |
| INSTALLATION_TEMPLATE | `sablon_montaj` | Promoted; conditional on `mounting_template_enabled` |
| PACKAGING_LOGISTICS | `ambalare_livrare_montaj` | Composition; full Letters always_on; not from MOUNTING |
| STRUCTURE_SUPPORT | `structura_suport` | Unchanged ownership |

Legacy read path: `legacy_finisaje_aggregate_alias` expands old `finisaje` → `{finisaje, sablon_montaj, ambalare_livrare_montaj}`.

## Mapping changes

```text
FINISH   → {finisaje}
MOUNTING → {structura_suport, sablon_montaj}
```

- MOUNTING surface-finish leakage = NO  
- MOUNTING packaging leakage = NO  

## No-removal proof

- FINISH OPTIONS REMOVED = NONE (catalogs retained; return finish stays RETURN-CANT)
- FINISAJE MODULE REMOVED = NO
- Commercial suite (`test_commercial_price_proposal_preview`, measurement contract) = PASS
- Operation aliases precise for painting / template CNC / packaging

## Full-product preservation

- Full Letters composition activates `finisaje` + `ambalare_livrare_montaj` (+ `sablon_montaj` when template enabled)
- CPP commercial preview suites pass without total-regression stop
- Packaging remains composition responsibility for full product

## Snapshot / Execution

| Item | Value |
|------|-------|
| Writer version | `active_scope_snapshot/v2` |
| Known readers | v1 + v2 |
| Old snapshots mutated | NO |
| Old `finisaje` | legacy expand on read |
| Unknown version | fail-closed |
| Op aliases | `painting→finisaje`, `mounting_template_cnc_cut→sablon_montaj`, `packaging_letters→ambalare_livrare_montaj` |

## Intake / UI

- Form contract: template bindings → `sablon_montaj`; mounting_system → `structura_suport`
- Review notes: Surface FINISH / șablon / MOUNTING map narrowed
- Product detail panel: responsibility hierarchy + legacy block + responsive wrap
- Modules / Governance / Control Center: gates APPROVED for narrowing/split; sold still blocked
- Responsive: grids collapse to 1-col; codes wrap; action links sticky

## Tests run

```text
backend (136 passed): ownership, decoupling, PD active scope, offer_scope,
  execution sold-scope, snapshot freeze, aggregate active-scope filter,
  commercial preview, commercial measurement, execution plan preview,
  site installation binding

frontend Vitest (27 passed): ownership lib/panel, governance truth,
  intake module activation preview

pnpm build: (see commit summary)
```

Known pre-existing / out-of-scope: template-only Aggregate dossier-component BOM tests (dossier isolation — empty parent `components_json`); Pricing Registry PREPRESS fixture assertion unrelated to this build.

## Runtime IDs

- Template: `TPL-VOLUMETRIC-LETTERS_v2`
- Runtime codes: `finisaje`, `sablon_montaj`, `ambalare_livrare_montaj`, `structura_suport`
- Snapshot: `active_scope_snapshot/v2` (writer), `v1` (legacy reader)

## Remaining sold-activation gates

```text
FINISH SOLD ACTIVATION = BLOCKED
MOUNTING SOLD ACTIVATION = BLOCKED
PACKAGING SOLD ACTIVATION = NOT_PLANNED
```

Do not start Logo / ACM / Pricing Registry 7I / task materialization.

## Decizia memorabilă

```text
NU SCOATEM NIMIC DIN PRODUS.
DESFACEM BUCKETUL MIXT IN RESPONSABILITATI CORECTE.
FINISH RAMANE FINISH.
SABLONUL DEVINE SABLON.
AMBALAREA DEVINE LOGISTICA.
SUPORTUL RAMANE SUPORT.
VECHILE COMENZI RAMAN CITIBILE.
NOILE SNAPSHOTURI DEVIN PRECISE.
```
