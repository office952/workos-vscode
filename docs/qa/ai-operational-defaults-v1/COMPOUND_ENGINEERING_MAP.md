# AI_OPERATIONAL_DEFAULTS_V1 — Shared Compound Map

Single system. No parallel AI default registries.

| Field | Meaning | V1 home |
|-------|---------|---------|
| decision_id | stable identity | `AiOperationalDefault.decision_id` |
| domain | packaging / electrical / led / labor | typed Literal |
| target_code | operation/catalog code | PACKAGING, ELECTRICAL_WIRING, LED_ASSEMBLY, FOLD_CASSETTE |
| formula_owner | central AI registry | `backend/data/ai_operational_defaults_v1.py` |
| quantity_key | Product Truth / physical driver | face_area, psu_count, module_count, panel_area_m2 |
| formula | resolved display formula | decision row |
| unit | EUR/produs, EUR/module, EUR/mp, EUR/buc | typed |
| default_value | AI proposal | registry |
| minimum / maximum | safety bounds | registry |
| confidence | LOW \| MEDIUM \| HIGH | registry |
| rationale | why (RO) | `rationale_ro` |
| source | AI_DECISION | always for registry rows |
| configurable | yes | overrides JSON |
| current_override | operator value | `ai_operational_defaults_overrides_v1.json` |
| precedence | MEASURED > OWNER > CATALOG > AI > LEGACY | frozen |
| readiness_effect | ACTIVE_WITH_AI_DEFAULTS / WARNINGS | compute_activation_status |
| affected_templates | VL, Logo, ACM shell, Volum Aluminiu | applies_to_templates |
| CPP_reader | template pricing commercial lines | demote AMBALARE only |
| EIC_reader | structural preview unchanged | no rule rewrite |
| review_trigger | calibration hook string | registry |
| risk | LOW/MEDIUM; ACM treatments excluded | policy |
| status | active / superseded / disabled | registry + overrides |
| confidence_in_mapping | high for qty-key formulas | MEDIUM defaults |

## Agents (execution)

| Agent | Owned |
|-------|--------|
| Lead | policy, precedence, activation |
| A Packaging | bands S/M/L + fragile |
| B Electrical/LED | min+PSU, per module |
| C Labor | OPERATION_ONLY / MISSING_OWNER eligible only |
| D Readiness | ACTIVE_WITH_* + demotion |
| E UI | Decizii operaționale AI |
| F CPP/EIC | regression |
| G QA | tests, screenshots, report |
