# WORKOS F7B — Controlled product-linked materialization pilot v1

## Verdict

```text
F7B = BLOCKED BEFORE MATERIALIZATION
POST = NOT EXECUTED
DEC-009 Owner GO = B (written) but runtime gate next_dry still 973019/21
Production-code retarget required for HTTP POST on F7A.1 fixture → STOP per pilot rules
PUSH = NOT EXECUTED
Production Ready = NU
```

## Identity

| Field | Expected | Observed |
|-------|----------|----------|
| Repo | `C:\w\psiso` | match |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` | match |
| HEAD | `2ef99d6b` | match |
| Remote | `0c8a76cd` | match |
| Ahead/behind | `0 / 6` | match |
| Stash | `wip-employee-unrelated` | intact |

## Why POST was not executed

1. **No durable original F7A/F7A.1 fixture** in `backend/dev.db` — prior proofs used ephemeral pytest DBs (`8807xx` dynamic). Hit count for commercial `1847.5` / F7A markers = **0**.
2. Per Owner rule, recreation is allowed only as the sole safe path, then **STOP before POST**. Recreated: **order `880811` / plan `22`** (see `preflight-recreated-fixture.json`).
3. **DEC-009 runtime next_dry** remains **`973019` / plan `21`** (`LIVE_DEC009_STATUS=A`, True_CONDITIONAL). Evaluate:
   - `880811` → `allowed=False` (`order_or_plan_outside_scoped_b`)
   - `973019` → `allowed=True` — **must not POST** (protected commercial baseline; already has operational_tasks)
4. Retargeting next_dry to `880811/22` requires **production gate edit and/or backend restart** — pilot rules forbid mixing that fix into F7B. No HTTP register endpoint exists for in-process `register_golden_pilot_materialize_target` on the live uvicorn process.

## Recreated fixture identity (preflight only)

| Field | Value |
|-------|--------|
| order_id | `880811` |
| order_code | `ORD-F7B-880811` |
| execution_plan_id | `22` |
| template | `TPL-VOLUMETRIC-LETTERS_v2` |
| commercial total | `1847.5` |
| snapshot sha256 prefix | `a59b6c447d9e6afb` |
| planned_tasks | 5 |
| operational_tasks before | `[]` |
| execution_tasks_created | `false` |
| persist | idempotent (same plan id) |
| audit mode | `audit_only` |
| audit status | `blocked_needs_owner_go` |
| candidate count | 5 |
| candidate fingerprint | `cd03f9acb47afb139a2d849227d84a44328731fe806e674945b803517ce71ada` |

### Planned workcenter matrix (registry-valid)

| Operation | Workcenter |
|-----------|------------|
| face_cnc_cut | `WC_CNC_ROUTING` |
| side_forming | `WC_LETTER_FORMING` |
| return_face_bonding | `WC_METAL_FAB` |
| painting | `WC_ASSEMBLY` |
| packaging_letters | `WC_ASSEMBLY` |

DAG: bond ← face + side; painting ← bond; packaging ← painting. No aliases / premount / SVG in planned ops. Minutes null + `PLANNING_MINUTES_SOURCE_REQUIRED`.

## Protected baseline

| Field | Before | After preflight recreate |
|-------|--------|--------------------------|
| 973019 hash prefix | `2d412e6e1234ae44` | `2d412e6e1234ae44` |
| accepted total | `847.5` | `847.5` |
| plan 21 | untouched | untouched |

## Pre-POST tests

```text
APP_ENV=test:
  test_f7a_* + golden DAG + step9 audit + dec009 gate → 26 passed
  test_f7a1_pre_materialization_truth_gap.py → 7 passed
```

Preview suite had 2 UNIQUE `snapshot_code` flakes when run earlier under polluted env; not reclassified as F7B contract failure. Full suite not run.

## POST evidence

```text
FIRST POST = NOT EXECUTED
SECOND POST = NOT EXECUTED
```

## Owner asks to unblock F7B (separate GO)

1. Accept recreated fixture **`880811` / plan `22`** as the exact controlled pilot target (original ephemeral IDs never durable).
2. Authorize **minimal DEC-009 next_dry retarget** (`register` or static SCOPED_B → 880811/22) + **backend restart** — **not** materialize of 973019.
3. Re-run audit GET via HTTP on live process, then authorize the two controlled POSTs.

## Boundaries respected

No sessions, assignments, SVG processing, Pricing, UI, push, or POST materialize. No production-code commit for gate retarget.
