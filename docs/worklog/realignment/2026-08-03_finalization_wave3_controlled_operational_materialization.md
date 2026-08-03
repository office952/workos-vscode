# Finalization Wave 3 — Controlled Operational Materialization

| Field | Value |
| ----- | ----- |
| Date | 2026-08-03 |
| Mini decision | `DEC-009=B` + `FINALIZATION_WAVE_3_GO=GRANTED_WITH_STRICT_SCOPE` |
| Scope | Fixture `880750` / plan `23` only — operational_tasks materialization + idempotency + durable envelope audit |
| Exclusions | assignment, sessions, scheduling, capacity, Employee Mobile, pricing/ORR, migrations, push/PR |
| Repo | `C:\Users\offic\workos_app_vs` (common git) |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `cdb6e7ac` |
| Ancestry | `788171b4`, `f6dfe4e3`, `cdb6e7ac` ⊂ HEAD |
| Verdict | `FINALIZATION_WAVE_3 = PASS` |

## Mini decision (Owner)

```text
DEC-009 = B
FINALIZATION_WAVE_3_GO = GRANTED_WITH_STRICT_SCOPE
```

Recorded at `docs/decisions/DEC-009_CONTROLLED_OPERATIONAL_MATERIALIZATION_B.md`.

## Capabilities / plugins used

- Terminal + git
- Backend pytest + frontend Vitest (targeted)
- Detached uvicorn on `:8001` (Wave 3 code) — canonical `:8000` left untouched (stale DEC-009=A listener)
- Frontend Vite `:3000` (worktree)
- Browser automation (cursor-ide-browser) for UI proof
- Read-only SQLite inspection
- No Datadog/Sentry/PostHog/Linear/Slack/etc.

## Preflight

- Worktree `C:\w\psiso`, common git `C:\Users\offic\workos_app_vs\.git`
- Branch `feat/f7i-owner-rate-activation`, start HEAD `cdb6e7ac`
- Ancestors of Wave 2 commits: PASS
- Tracked edits only from this Wave 3 work; large untracked `docs/qa/**` leftovers left untouched

## Non-production proof

| Field | Evidence |
| ----- | -------- |
| Process APP_ENV | `development` on Wave 3 uvicorn PID `25384` |
| Gate `production_environment` | `false` |
| Database | `sqlite+aiosqlite:///C:/w/psiso/backend/dev.db` (local file) |
| Backend | `C:\w\psiso\backend\.venv\Scripts\python.exe -m uvicorn … --port 8001` |
| Frontend | Vite `:3000` from `C:\w\psiso\frontend` |
| Compat label | release label may say `staging`; not production APP_ENV |
| Secrets exposed | NO |

Canonical `:8000` (PID 8508) remained stale (`live_dec009=A`, closed next-dry). Mutation used verified `:8001` without killing foreign listeners. `:8000` could still **read** the same DB after write (`ops=13`).

## Protected baselines

| Order | accepted_commercial_total | snapshot sha prefix | plan | ops before→after | created |
| ----- | ------------------------- | ------------------- | ---- | ---------------- | ------- |
| 880811 | 1847.5 | `a59b6c44…` | 22 | 5→5 | true |
| 973019 | 847.5 | `2d412e6e…` | 21 | 18→18 | true |
| 88002 | historical RO | n/a (no V2 plan) | — | unchanged | — |
| 880750 (target) | 1925.0 | `dc998518…` | 23 | 0→13 | false→true |

`PROTECTED_BASELINE_MUTATIONS = NONE`. Note: 973019 already had a historical non-null `assigned_employee_id` on one operational task before this build; Wave 3 did not mutate that order.

## Fixture identity (880750)

| Field | Value |
| ----- | ----- |
| Order | 880750 / `ORD-WAVE2-QA-880750` |
| Snapshot | id 23 / `QSN2-WAVE2-880750` / sha `dc998518…` |
| Plan | 23 / `order_snapshot_v2` |
| Planned tasks / ops | 13 / 18 |
| Audit before | `scoped_materialize_authorized`, candidates **13**, `post_materialize_allowed=true` |
| Audit plan vs order | match |

## Architecture (research → minimal change)

- **POST** `/api/v1/execution/plan-v2/materialize-tasks/{order_id}` already existed; OD3 gate was fail-closed.
- **DEC-009** = live constant + True_CONDITIONAL next-dry registry + protected set (not hardcoding fixture in product `if`).
- Materializer source = `planned_tasks[]` only → `operational_tasks[]` inside `tasks_json` (no `execution_tasks` table).
- Second POST → HTTP **409** `operational_tasks_already_materialized`.
- Added optimistic CAS on `tasks_json` for concurrent safety; envelope `materialization_audit` for durable audit without schema change.
- Audit GET now honest about `post_materialize_allowed` (false after materialize → sessions stay frozen).

### Alternatives evaluated

1. Global DEC-009=B without next-dry — rejected (unsafe).
2. Hardcode `order_id==880750` — rejected (forbidden).
3. New audit table/migration — rejected (`SCHEMA_CHANGE_REQUIRED` avoided; envelope field used).
4. Kill/restart `:8000` — rejected without Owner stop GO; used `:8001`.

## Runtime evidence

1. GET audit plan 23 + order 880750 → 13 candidates, scoped authorized
2. POST `:8001` …/materialize-tasks/880750 → `materialized`, ops=13, `execution_tasks_created=true`, warning `PLANNING_MINUTES_SOURCE_REQUIRED`
3. Readback readiness `v2_operational_ready`; reality rows=0; assignments=0; machines=0; foil deps on bonding+assembly=PASS
4. Second POST → **409** already materialized
5. Protected baselines unchanged

Evidence dir: `docs/qa/workos-wave3-controlled-materialization-v1/` (screenshots local-only; not for commit).

## UI / UX

- Route `/execution/880750` — no Materialize / Assign / Start buttons
- 1920 light/day: PASS (`screenshots/wave3-880750-1920-light-top.png` local)
- ~1366 light/day: PASS
- Dark: NOT_OFFICIALLY_SUPPORTED for this GO (light/day primary)
- Minimal honesty fix: WorkPanel session-frozen copy when already materialized; TruthPanel DEC-009=B banners

## Tests

- Backend: `test_dec009_materialize_gate`, `test_finalization_wave3_controlled_materialization`, `test_execution_plan_v2_materialize` (+ related F7A/F7C status asserts updated for B) — PASS
- Frontend targeted Vitest TruthPanel + readiness — PASS
- F7I rates unchanged: 15 / 1.5 / 35 / 20 EUR in `commercial_rules_volumetric_v2.py`

## DB / schema

- Migrations created/executed: **0**
- Schema changed: **NO**
- Reset/reseed: **NO**
- Authorized mutations: plan 23 envelope `operational_tasks[]`, `execution_tasks_created`, `materialization_audit`, readiness flag
- Unexpected mutations: **NONE**

## Dead Pieces Check

- Stale `:8000` runtime identity / closed-gate process — ACTIVE_LEGACY listener (left running)
- F7B `open_f7b_controlled_materialize_pilot` — SUPERSEDED (raises; 880811 protected)
- Dead pieces removed: **NONE**

## Scores

- Direction alignment: **88/100** (materialize direction proven; shop-floor still correctly closed)
- Operational completion: **42/100** (materialized ≠ schedulable/assignable/shop-ready)

## Exact next step

**DO NOT START ASSIGNMENT / SESSIONS / SCHEDULING / EMPLOYEE MOBILE.**

Recommended (unauthorized) Wave 4: workcenter→machine capability RO + eligibility RO + zero mutation.

## Owner GO still required

Any step toward assignment, sessions, scheduling, capacity, Employee Mobile, or production rollout.

## Honest opinion

The existing materializer was already the right engine; Wave 3 was mostly governance honesty (DEC-009=B next-dry), audit/CAS hardening, and proving the durable fixture end-to-end. Leaving `:8000` stale while mutating via `:8001` was the safe port strategy under no-kill rules — Owner may later ask to stop/restart the canonical stack so `:8000` matches Wave 3 code.
