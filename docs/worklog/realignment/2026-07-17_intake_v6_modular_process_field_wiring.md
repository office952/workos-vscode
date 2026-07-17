# Worklog — Intake V6 modular process field wiring

| Field | Value |
|-------|-------|
| Task | INTAKE_V6_MODULAR_PROCESS_FIELD_WIRING |
| Owner GO | explicit single coherent build |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `08fc832` |
| Feature commit | `4ccfba6` |
| Worklog commit | `670d7c5` |
| End HEAD | `670d7c5` |
| Initial | `INTAKE_V6_MODULAR_PROCESS_FIELD_WIRING_IN_PROGRESS` |
| Final | `INTAKE_V6_MODULAR_PROCESS_FIELD_WIRING_COMPLETE_WITH_GUARDS` |

## Lineage verified

- `8c98dae` — Build 4A.1
- `46bfc9b` / `ea923c1` — Build 4C
- `6fe5c50` / `baec7a9` — process contract + resolver
- `96343cd` / `08fc832` — live Aggregate bridge

## Objective

Wire typed process configuration from Intake V6 / ProductDefinition into the active modular resolver path. Stop treating ghost keys in `finish_setup` as the only authority for cable / service corner / screw finish.

## Authority decisions (single SoT per field)

| Semantic | Authority | Transport |
|----------|-----------|-----------|
| support_type | `mounting_solution` (typed) → adapter map; legacy `mounting_system` fallback | PD + finish_setup |
| cant_finish_mode | existing `return_finish_type` | PD + finish_setup |
| mains_cable_length_m | typed `finish_setup.mains_cable_length_m` → PD canonical | PD wins |
| power_supply_service_corner | typed field; required only Alucobond cased | PD wins |
| service_screw_finish | typed field; default NATURAL when unset | PD wins |
| installation_template | existing `mounting_template_enabled` | unchanged |

Chosen architecture: **A + C minimal** — reuse existing mounting/cant/template fields; add three typed finish_setup fields (JSON document, no DB migration) projected via form bindings into ProductDefinition.

Rejected as permanent authority: generic `finish_setup` bag for process options (legacy fallback only).

## finish_setup classification

| Key | Class |
|-----|-------|
| return_finish_type, return_depth_mm, face_*, lighting_*, backing_* | KEEP_IN_FINISH_SETUP |
| mounting_solution, mounting_system, mounting_template_* | KEEP_IN_FINISH_SETUP (existing typed) |
| mains_cable_length_m, power_supply_service_corner, service_screw_finish | ADD_MINIMAL_TYPED_FIELD (now on schema + bindings) |
| screw_finish / transformer_service_corner / cable_length_m | LEGACY_ONLY read fallback |
| commercial_inputs | KEEP_IN_FINISH_SETUP (pricing boundary — untouched) |

## Implementation

1. Schema: `IntakeV4FinishSetup` typed fields (no migration).
2. Form contract: bindings + writable paths in `intake_v6_modular_form_contract_service.py`.
3. Adapter: typed PD → typed finish → mounting_solution → legacy mounting_system; never invent 5 m cable.
4. Bridge / workspace compose: pass `product_definition_canonical_values`; observability `config_source`.
5. FE Intake V6 Review Montaj: cable (metal/ACM), service corner (ACM only), screw finish; clears inactive fields on solution change.
6. Tests: `test_intake_v6_modular_process_field_wiring.py` + bridge unpack fix.

## Tests run

```text
pytest tests/test_intake_v6_modular_process_field_wiring.py
     tests/test_product_process_live_aggregate_bridge.py
     tests/test_product_process_contract_resolver.py
     tests/test_intake_v6_modular_form.py
     tests/test_frozen_modular_graph_build4a.py
     tests/test_execution_preview_from_frozen_build4c.py
→ 148 passed
```

## Runtime / UI proof (owner verification)

| Item | Value |
|------|-------|
| Route | Intake V6 Review → tab **Montaj** |
| URL | `http://127.0.0.1:3000/intake-v6/<workspaceId>` (backend `:8001`) |
| Template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Metal | Soluție = bare metalice → `intake-v6-mains-cable-length-m`; note no service corner |
| Alucobond | Soluție = ACM casetat → cable + `intake-v6-power-supply-service-corner` |
| No support | Soluție = none → cable/corner cleared; screw + șablon remain as before |
| Aggregate | `task_contract.process_graph_source=modular_resolver`; warning details include `config_source` / cable |

## Live calculation / CPP boundary (no change)

- `WIRE_SUPPLY_ML_PER_JOB = 5.0` in `intake_v4_consumables_adhesive_wiring_service.py` remains hardcoded for commercial consumable estimate.
- Typed `mains_cable_length_m` is process-path only in this build.
- Gap for owner: GO CPP cable / channel / template wiring (separate build).

## Guards remaining

- CPP / pricing formulas unchanged.
- FE Generate Plan still V1 write path.
- Sequence fallback still exists for snapshots without edges.
- Pre-existing logo composition suite noise unrelated to this wiring.
- `intake_v6_pilot_contract_seed.py` still broken import (pre-existing dead piece; not used by live form contract).

## Next safe step

**Option 1 — OWNER REVIEW OF INTAKE FIELD WIRING**

Then optionally Option 2 read-only owner process proof, or Option 3 CPP cable/channel/template after GO.
