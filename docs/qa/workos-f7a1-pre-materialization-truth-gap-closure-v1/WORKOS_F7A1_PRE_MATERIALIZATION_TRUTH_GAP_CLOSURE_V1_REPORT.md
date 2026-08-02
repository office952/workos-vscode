# WORKOS F7A.1 — Pre-materialization truth gap closure v1

## Verdict

```text
F7A.1 PRE-MATERIALIZATION TRUTH GAP CLOSURE = PASS
WORKCENTER REGISTRY FIDELITY = PASS
PREMOUNT HARD POLICY = PASS
FIXTURE DAG = PASS
POST MATERIALIZE = NOT EXECUTED
DEC-009 RECOMMENDATION = B (Owner written GO still required; F7B not started)
PUSH = NOT EXECUTED
```

## Identity

`C:\w\psiso` · `feat/capacity-batch-20d-scoped-b-92401` · baseline `5a477310` · remote `0c8a76cd`

## Workcenter matrix (controlled fixture)

| Operație canonică | Cod emis upstream | Cod registry | Alias oficial | Snapshot | Preview | Verdict |
| ----------------- | ----------------- | ------------ | ------------- | -------- | ------- | ------- |
| CNC routing (`face_cnc_cut`) | `WC_CNC_ROUTING` | `WC_CNC_ROUTING` | none (`WC_CNC` = non_canonical conflict) | frozen Aggregate op | projected | PASS |
| Letter forming (`side_forming`) | `WC_LETTER_FORMING` | `WC_LETTER_FORMING` | — | frozen | projected | PASS |
| Metal / bond (`return_face_bonding`) | `WC_METAL_FAB` | `WC_METAL_FAB` | — | frozen | projected | PASS |
| Assembly / painting / packaging | `WC_ASSEMBLY` | `WC_ASSEMBLY` | packaging ORR → WC_ASSEMBLY | frozen | projected | PASS |

Registry owner: `seeds/seed_operational_workforce_registry.py` + `data/operational_workcenters.py` (code identity).  
`WC_CNC` remains listed as **non_canonical** (parity VALUE_CONFLICT); preview warns `WORKCENTER_CODE_NON_CANONICAL` if stamped.

## Premount (DEC-002=A)

- No activation signal in repo (`premount_activation_signal_present` → always false).
- Hard ban in: dossier `_build_task_contract`, modular `_rules_from_resolved`, `collect_effective_task_rules` (dossier + synthetic), preview `_is_non_operational_rule`.
- BOM op may remain on Aggregate `operations[]`; never task_rule / planned_task / audit candidate without signal.

## DAG

Fixture preview-native: bond ← face + side; `DAG_PROCESS_DEPENDENCIES_UNRESOLVED` absent. Legacy linear fallback remains only on non-V2 frozen-graph preview route.

## Tests

```text
123 passed — F7A.1 + F7A + golden DAG + step9 audit + DEC-009 + preview + bridge + quote accept
s56 tip test — still FAIL (preexisting hygiene; unrelated)
```

## Protected baseline

`973019` / plan `21` / `2d412e6e1234ae44` / `847.5` — no drift.

## DEC-009

Recommend **B** for a future controlled F7B pilot on the F7A.1 fixture only — **do not start F7B** until Owner writes GO. Minutes remain null (scheduling still blocked).
