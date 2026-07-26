# AI_OPERATIONAL_DEFAULTS_V1 — Runtime API Truth

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `aa0f8956` |
| Proof port | `127.0.0.1:8020` |
| FE | `127.0.0.1:3000` (proxy → 8020) |
| schema_version | **1.2.0** |
| `:8000` | ghost LISTENING — environment warning (not proof) |

## Endpoints

| Method | Path | Role |
|--------|------|------|
| GET | `/api/v1/product-system/templates/{code}/pricing` | recipe + `ai_decisions[]` + activation |
| GET | `/api/v1/product-system/ai-operational-defaults` | registry + overrides |
| PUT | `/api/v1/product-system/ai-operational-defaults/{decision_id}` | configurable override |
| DELETE | `/api/v1/product-system/ai-operational-defaults/{decision_id}` | restore default |

## Runtime summary (8020)

| Template | activation_status | ai_decisions | demoted | real_blockers | ACM |
|----------|-------------------|-------------:|---------|---------------|-----|
| VL `TPL-VOLUMETRIC-LETTERS_v2` | ACTIVE_WITH_AI_DEFAULTS | 4 | AMBALARE_COMMERCIAL_RULE, MISSING_OWNER_FORMULA, OPERATION_ONLY | — | n/a |
| Logo `TPL-VOLUMETRIC-LOGO_v1` | ACTIVE_WITH_AI_DEFAULTS | 4 | — | — | n/a |
| ACM `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | ACTIVE_WITH_WARNINGS | 2 | OPERATION_ONLY, MISSING_OWNER_FORMULA | ACM_TREATMENT_COMMERCIAL_BLOCKED | **5/0**, treat=false |
| Volum Aluminiu `TPL-VOLUM-ALUMINIU_v1` | ACTIVE_WITH_AI_DEFAULTS | 1 (packaging) | — | — | n/a |

## CPP / EIC vs Labor Closure dumps

| Template | CPP line_codes | EIC rule_codes | blocked_line_codes delta |
|----------|----------------|----------------|--------------------------|
| VL | same | same | removed `ambalare` (AI packaging demotion) |
| Logo | same | same | none |
| ACM | same | same | none |
| Volum Aluminiu | same | same | none |

Provenance notes unchanged. No duplicate CPP lines introduced.

## Precedence observed

Catalog rates (PACKAGING / ELECTRICAL / LED when registry-present) resolve as `CATALOG`; AI remains visible + configurable. Missing rates fill as `AI_DECISION` without writing `workcenter_rates`.

## Dumps

`docs/qa/ai-operational-defaults-v1/runtime/*_pricing.json`
