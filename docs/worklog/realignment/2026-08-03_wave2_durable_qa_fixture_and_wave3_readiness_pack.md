# Wave 2 Durable QA Fixture + Wave 3 Readiness Pack

| Field | Value |
| ----- | ----- |
| Date | 2026-08-03 / runtime 2026-08-04 01:12 EEST |
| Mini decision | Create one durable non-production Wave 2 QA fixture; runtime + light/day UI proof; docs-only commit; Wave 3 Readiness Pack. **No Wave 3.** |
| Worktree | `C:\w\psiso` |
| Git common dir | `C:\Users\offic\workos_app_vs\.git` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `5868dc97` |
| Ancestors verified | `788171b4` (Wave 2 impl), `f6dfe4e3` (docs reconcile) |
| Final HEAD | docs-only commit after this worklog |
| Limits | `DEC-009=A`, MATERIALIZATION CLOSED, SCHEDULING HOLD, EMPLOYEE_MOBILE FROZEN_FINAL_FINAL |

## Preflight

```text
PREFLIGHT = PASS
HEAD = 5868dc97
tracked clean except prior untracked QA leftovers (untouched)
stack restarted via scripts/dev-detached.ps1 (worktree C:\w\psiso)
```

## Non-production proof

| Check | Evidence |
| ----- | -------- |
| APP_ENV | `development` |
| ENVIRONMENT | `development` |
| DATABASE_URL | `sqlite+aiosqlite:///./dev.db` |
| DB file | `C:\w\psiso\backend\dev.db` |
| Host | `127.0.0.1:8000` / `:3000` |
| UI badge | Staging · Sistem disponibil / BUILD_25 STAGING |

## Controlled durable fixture manifest

| Field | Evidence |
| ----- | -------- |
| Fixture name | `WAVE2-DURABLE-QA-880750` |
| Order ID | **880750** |
| Order code | `ORD-WAVE2-QA-880750` |
| Quote ID | 880750 |
| Quote Snapshot V2 ID | **23** |
| Snapshot code | `QSN2-WAVE2-880750` |
| Snapshot sha256 | `dc998518d7fb7a8ea755f75969962c5e6765245ff20b791104a1427b8332643e` |
| Accepted commercial total | 1925.0 RON (fixture-local; not a protected baseline) |
| Execution Plan ID | **23** |
| Planned tasks | 13 |
| Planned operations | 18 |
| Operational tasks | **0** |
| execution_tasks_created | **false** |
| Materialization | `blocked_needs_owner_go`; `post_materialize_allowed=false` |
| Persist | first `persisted`, second `already_exists` (idempotent) |
| Created by | `docs/qa/workos-wave2-durable-fixture-v1/_create_wave2_durable_fixture.py` |
| Evidence JSON | `docs/qa/workos-wave2-durable-fixture-v1/fixture-evidence.json` |

### Ownership / DAG / WC (fixture)

- Alias ops absent: `RETURN_PROFILE_*`, `PAINTING`
- Parents present: `side_forming`, `return_face_bonding`, `painting`
- Foil: `vinyl_application` depends on `assembly_letters` + `return_face_bonding`
- LED / electrical / mounting_template present
- Premount present as operation metadata only (no task_rule)
- SVG geometry non-operational / excluded from planned
- Workcenters resolved via live ORR stamp at Aggregate build (`operation_resource_requirements:…|orr/v1`)
- Minutes null on planned tasks

## Runtime evidence (selected)

| Method | URL | Status | Side effects |
| ------ | --- | ------ | ------------ |
| POST | `/api/v1/execution/plan-v2/preview/880750` | 200 | none (`no_write=true`) |
| POST | `/api/v1/execution/plan-v2/from-order/880750` | 200 | idempotent `already_exists` plan 23 |
| GET | `/api/v1/execution/plan-v2/from-order/880750/materialization-audit` | 200 | none; ops=0; post_allowed=false |
| POST materialize | — | **not called** | — |

## Protected baselines (before = after)

| Order | total | sha256 prefix | plan |
| ----- | ----- | ------------- | ---- |
| 880811 | 1847.5 | `a59b6c44` | 22 |
| 973019 | 847.5 | `2d412e6e` | 21 |

`protected_unchanged = true` in fixture evidence.

## Visual proof (official light/day)

Theme: `localStorage workos-theme=light` via official `ThemeContext` (no CSS invent).

| Viewport | Theme | URL | Result |
| -------- | ----- | --- | ------ |
| 1920 | light | `/execution/880750` | PASS — ORD-WAVE2-QA-880750, plan 23, 13 planned tasks, DRAFT/NOT_MATERIALIZED, DEC-009 banner, no Materialize/Assign/Start |
| 1366×768 | light | same | PASS — same signals |
| dark | official supported | — | not used as substitute |

Screenshots local QA temp only — not committed.

## F7I

Constants unchanged: debitare_spate 15 / LED 1.5 / PSU 35 / ambalare 20 EUR.

## Documentation updates

- This worklog
- Minimal pointer in `21_WORKOS_IMPLEMENTATION_ROUTE.md` that durable Wave2 fixture `880750` exists for readiness evidence
- QA folder evidence + create script (reproducible non-prod seed; does not materialize)

## Wave 3 Readiness Pack

```text
WAVE_2_IMPLEMENTATION_STATUS = COMPLETE (788171b4)
DOCUMENTATION_TRUTH = RECONCILED
CONTROLLED_WAVE_2_FIXTURE = VERIFIED (durable runtime 880750)
LIGHT_DAY_1920 = PASS
LIGHT_DAY_1366 = PASS
WAVE_3_READINESS_PACK = READY_FOR_OWNER_REVIEW
DEC_009 = A
MATERIALIZATION = CLOSED
```

`READY_FOR_OWNER_REVIEW` does **not** authorize Wave 3. Only Owner may set `DEC-009=B` with a separate GO.

### Proven for Owner review before DEC-009=B

1. Canonical ownership stable; no RETURN/painting duplicates on fixture
2. Workcenters frozen/stamped upstream (ORR) and visible in Step 9B
3. Finish-aware foil DAG valid on fixture
4. Snapshot + plan IDs stable; persist idempotent
5. Audit GET; operational_tasks empty; materialize not called
6. Protected baselines unchanged
7. No commercial rate regression

## Scores

```text
direction alignment score = 93/100
operational completion score = 36/100
```

(Shop floor still closed by DEC-009=A.)

## Exact next step

```text
Do not start Wave 3.
Return Readiness Pack to Owner.
Keep DEC-009=A / MATERIALIZATION=CLOSED / SCHEDULING=HOLD / EMPLOYEE_MOBILE=FROZEN_FINAL_FINAL.
Next authorized build only after Owner GO:
FINALIZATION_WAVE_3 = controlled materialization + idempotency + audit trail + fixture validation + zero sessions + zero assignment
```
