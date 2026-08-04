# Finalization Wave 7 — Auth + UI Closure Proof Only

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Task | `FINALIZATION_WAVE_7_AUTH_AND_UI_CLOSURE_PROOF_ONLY` |
| Status | **`FINALIZATION_WAVE_7 = PASS`** |
| Starting HEAD | `c6085895` |
| Final HEAD | `eca5d59d` |
| Repo / worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Production code changed | **NO** |
| Config/code commit | **NONE** (operational restart only) |
| Schema / migration | **NONE** |
| Assignment mutations | **0** additional |

## Verdict

```text
FINALIZATION_WAVE_7 = PASS
CONTROLLED_SINGLE_QA_ASSIGNMENT = VERIFIED
AUTHORIZATION =
VERIFIED_WITHIN_EXISTING_SINGLE_ORGANIZATION_MODEL
UI_READ_ONLY_E2E = VERIFIED
VITE_PROXY = VERIFIED
ADDITIONAL_ASSIGNMENT_MUTATIONS = 0
EMPLOYEE_ASSIGNMENTS_ON_PLAN_23 = 1
UNASSIGNED_OPERATIONAL_TASKS_ON_PLAN_23 = 12
SESSIONS = 0
MACHINE_ASSIGNMENTS = 0
SCHEDULING = HOLD
CAPACITY = NOT_STARTED
EMPLOYEE_MOBILE = FROZEN_FINAL_FINAL
PRODUCTION_ROLLOUT = NOT_AUTHORIZED
WAVE_8 = NOT_AUTHORIZED
```

Owner accepted Wave 7 assignment persistence as factual truth, but withheld full Wave 7 PASS until authenticated authorization + UI read-only E2E closed. This task closes those two proofs only.

## Repo identity (preflight)

| Item | Value |
| ---- | ----- |
| Repo | `C:/w/psiso` |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `c60858950e448ea4158288addfc5f4c7ae175001` |
| Tracked changes | none |
| Untracked | preexisting `docs/qa/**`, `backend/_qa_backups/`, logs — left untouched |
| Ancestry | `f68790f3` OK · `c6085895` OK · `b652d1bd` OK · `4a72025e` OK |

## Protected assignment state (before = after)

| Field | Value |
| ----- | ----- |
| order_id | 880750 |
| execution_plan_id | 23 |
| operational_tasks | 13 |
| assigned | 1 |
| unassigned | 12 |
| assigned task | `node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters` |
| assigned employee | 7 |
| assignment_source | `canonical_controlled_assign_v1` |
| assignment_actor_user_id | `dev-admin-user-00000000` (Wave 7 mutation actor; unchanged) |
| plan `updated_at` | `2026-08-04 19:16:57.407320` |
| `tasks_json` SHA-256 | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` |
| DB path | `C:\w\psiso\backend\dev.db` |
| DB SHA-256 | `b67c76f0fe87cb64e2950d680e38da2fe32cb9229bf4015904ddd24cc32f8b14` |
| DB size / mtime | `36241408` / `1785860217.413299` |
| sessions / reality | 0 |
| machine / team assignments | 0 |
| scheduling | HOLD |
| capacity | NOT_STARTED |

Sibling task fingerprints (stable, non-assignment keys): unchanged vs Wave 7 post-state
(`vector_prep`…`packaging` short digests recorded in capture; LED sibling fingerprint `bf7c7cbd1fd8b0b4`).

## DEV missing-auth bypass (documented separately — not positive proof)

```text
DEV_MISSING_AUTH_BYPASS =
  When APP_ENV/ENVIRONMENT allow dev_auth_allowed():
  missing Authorization → synthetic Bearer __DEV_BYPASS_TOKEN__
  → user id=dev-admin-user-00000000 role=admin
  (dependencies/auth.py get_bearer_token / _resolve_dev_bypass_user)
```

Positive authorization proof below uses a **signed JWT** actor, not missing credentials.

## Authenticated QA actor proof

```text
AUTH_MECHANISM = application JWT (core.auth.create_access_token / Bearer)
AUTHENTICATED_QA_ACTOR =
  sub=qa-wave7-auth-closure
  email=qa-wave7@localhost
  name=QA Wave7 Auth Closure
  role=admin
AUTHENTICATED_QA_ACTOR_PERMISSIONS =
  role admin ⊇ execution.task_assign (PERMISSION_MATRIX)
  role admin ⊇ execution.plan_generate (readiness / eligibility RO)
```

Local `users` table is empty; JWT path does not require a DB user row (claims → `UserResponse`). No roles/permissions were written to QA DB.

Runtime evidence (fresh backend with `JWT_SECRET_KEY` + `JWT_ALGORITHM=HS256`):

| Probe | Result |
| ----- | ------ |
| `GET /api/v1/auth/me` Bearer JWT admin | 200 → id `qa-wave7-auth-closure`, role `admin` |
| `GET …/assignment-readiness` JWT admin | 200 · order 880750 · plan 23 · status ok · employee_assignment_count 1 · machine 0 · sessions 0 · scheduling HOLD · capacity not_started |
| `GET …/employee-eligibility` JWT admin | 200 · order 880750 · plan 23 · 13 ops |
| `GET /api/v1/execution/plan/880750` JWT admin | 200 · plan id 23 · 1 assigned (LED→7) · 12 unassigned |
| command_contract.permission | `execution.task_assign` |
| matrix `has_permission(admin, execution.task_assign)` | True |

Scope established read-only:

```text
actor authenticated
actor has execution.task_assign (role matrix + command_contract)
actor can access order 880750
plan 23 belongs to order 880750
assigned task belongs to plan 23
employee 7 resolves in permitted existing context
  (persisted assignment + readiness candidate path; eligible_employee_ids include 7)
```

```text
AUTHORIZATION =
VERIFIED_WITHIN_EXISTING_SINGLE_ORGANIZATION_MODEL
```

No multi-tenant org model exists; strongest scope remains order → plan → task → DEC-015.

## Negative authorization (read-only / isolated)

| Case | Path | Result |
| ---- | ---- | ------ |
| invalid auth | `GET /auth/me` Bearer garbage | **401** |
| authenticated without `execution.task_assign` | JWT role=`viewer` → readiness | **403** `permission_denied` / `execution.plan_generate` |
| viewer on assign command | isolated DB pytest `test_permission_denied_for_viewer` | **401/403** (no QA DB write) |
| wrong order | readiness `order_id=999999` JWT admin | **200** `status=plan_not_found` (no leak of assignable work) |
| forged task key | readiness `task_key=forged:task:key` emp 7 | hypo `TASK_NOT_OPERATIONAL` / absent from `operational_tasks[]` |
| unknown employee | readiness emp `99999` on LED task | hypo `CANDIDATE_NOT_FOUND` |
| missing auth (dev) | no Authorization → `/me` | **200 synthetic admin** — documented bypass, **not** used as positive proof |
| missing auth (production intent) | `test_production_blocks_dev_bypass_without_credentials` | **FAILED** in this shell — classified **PRE_EXISTING / TEST_FIXTURE_DRIFT** (lifespan blocked by `DEBUG` safety when env forced to production); not used to claim Wave 7 auth pass |

No PATCH assign against QA DB. Mutation counters:

```text
ADDITIONAL_ASSIGNMENT_REQUESTS_TO_QA_DB = 0
ADDITIONAL_SUCCESSFUL_ASSIGNMENT_MUTATIONS = 0
ADDITIONAL_IDEMPOTENT_PATCH_RETRIES = 0
ADDITIONAL_CONFLICT_PATCH_REQUESTS = 0
```

## Vite proxy diagnosis

### Observed failure (before fix)

| Item | Value |
| ---- | ----- |
| Frontend port | 3000 |
| Vite PID (broken) | 16868 |
| Ancestor command | `set BACKEND_PORT=8001&& … vite --port 3000` |
| Proxy target (broken) | `http://127.0.0.1:8001` |
| Listener on 8001 | **none** (connect timeout) |
| Backend healthy | `:8000` PID 2508 — direct `/api` 200 |
| Proxy `/api/*` via `:3000` | **500** empty body |

### Classification

```text
STALE_PROCESS
PORT_MISMATCH
PROXY_CONFIGURATION
```

Not a Wave 7 frontend regression. Vite was started with `BACKEND_PORT=8001` while the live API was on `:8000`. Default `vite.config.ts` proxies `/api` → `BACKEND_PORT || 8000`.

Secondary finding on stale backend: process started with `JWT_SECRET_KEY` only → signed JWT probes returned **503 Missing JWT_ALGORITHM**. Canonical helpers (`Set-WorkOsJwtEnv` / `dev-backend.ps1`) set `JWT_ALGORITHM=HS256`.

### Operational correction (no code commit)

1. Owner-authorized stop of stale `:3000` / `:8000` via `.\scripts\stop-dev.ps1`
2. Fresh stack via `.\scripts\dev-detached.ps1`

### After fix

| Item | Value |
| ---- | ----- |
| FE | `:3000` PID 12124 · `dev-frontend.ps1` · `BACKEND_PORT=8000` · `VITE_ENABLE_DEV_AUTH=true` |
| BE | `:8000` PID 11804 · `uvicorn main:app --reload` · git_commit `c6085895` |
| Proxy `/api/v1/system/version` | **200** |
| Proxy `/api/v1/system/local-compatibility` | **200** |
| Proxy `/api/v1/execution/plan/880750` | **200** |
| `VITE_PROXY` | **VERIFIED** |

Note: `VITE_API_BASE_URL` from detached helper is absolute `http://127.0.0.1:8000` (browser may call BE directly). Vite `/api` proxy to `:8000` was still verified independently.

## Browser UI read-only proof

| Item | Value |
| ---- | ----- |
| URL | `http://127.0.0.1:3000/execution/880750` |
| Theme | official light/day (`data-shell-day=true`) |
| Viewports | 1920×1080 and ~1366×768 |
| Click steps | navigate → wait AuthGate → scroll to `[data-testid=assignment-readiness-panel]` |
| Loading | brief “Se verifică sesiunea…” then shell |
| Error state | none (compat banner absent) |
| Screenshots | local Cursor temp only — **not committed** |

### Actual UI facts

- Order `ORD-WAVE2-QA-880750` / `#880750`, plan **23**, **13** planned tasks
- Panel **Pregătire pentru atribuire**: `13 taskuri operaționale` · `12 neatribuite` · `Atribuiri: 1` · `Utilaje: 0` · `Programare: HOLD`
- Row `…:led_install_letters` → **Atribuit #7**; minutes cell **null**
- Twelve siblings **Neatribuit**
- Banner: assignment / sessions / scheduling blocked; text “Nu există acțiune Asignează / Pornește pe această suprafață” (negation, not controls)
- Work rows: **read-only** / `nepornit · durată neconfirmată`
- Absent false claims: Ready to start / Available now / Scheduled / Machine reserved / Production ready
- No Assign / Reassign / Unassign / Start / Stop / Auto-assign / Reserve / Schedule action controls introduced

```text
UI_READ_ONLY_E2E = VERIFIED
```

## Zero-mutation proof

Before and after closure work identical for:

- `tasks_json` SHA
- plan `updated_at`
- assigned task + employee 7 + audit fields
- 12 sibling fingerprints
- DB SHA / size / mtime
- sessions 0 · machine 0 · scheduling HOLD · capacity NOT_STARTED

## Tests

| Command | Suite | Passed | Failed | Skipped | DB | Classification |
| ------- | ----- | ------ | ------ | ------- | -- | -------------- |
| `pytest -q tests/test_auth_dev_impersonation.py tests/test_permissions.py tests/test_finalization_wave5_assignment_readiness_audit.py tests/test_finalization_wave6_assignment_command_hardening.py::test_permission_denied_for_viewer` | auth + readiness + permission | 42 | 1 | 0 | isolated test DB | fail = PRE_EXISTING / TEST_FIXTURE_DRIFT (`test_production_blocks_dev_bypass_without_credentials` lifespan DEBUG safety) |
| re-run permissions + `test_permission_denied_for_viewer` (DEBUG unset) | permissions + assign deny | 27 | 0 | 0 | isolated | NEW_REGRESSION none |
| `vitest run assignmentReadinessDisplay.test.ts localApiCompatibility.test.ts` | FE readiness + compat URL | 8 | 0 | 0 | n/a | pass |
| Runtime JWT + readiness + proxy probes | manual RO against QA DB | n/a | n/a | n/a | `dev.db` RO | evidence only — no mutate |

## Protected baselines / F7I

| Check | Result |
| ----- | ------ |
| 880811 | unchanged (`updated_at` 2026-08-03 00:06:15.946013) |
| 973019 | unchanged (`updated_at` 2026-08-02 16:48:17.965225) |
| 88002 | absent (unchanged absence) |
| F7I rates | `15` / `1.5` / `35` / `20` EUR still in `commercial_rules_volumetric_v2.py`; no pricing/ORR/CPP/EIC edits |

## Remaining gaps / dead pieces

- No persisted `users` row for QA JWT actor (claims-only JWT is the canonical local path).
- Readiness RO gate uses `execution.plan_generate`; assign command gate uses `execution.task_assign` (proven via matrix + isolated PATCH deny + command_contract inventory).
- FE may call absolute `:8000` via `VITE_API_BASE_URL` while Vite proxy remains correct for `/api` relative calls.
- Production missing-auth denial test remains environment-sensitive (pre-existing).

## Next step

```text
FUTURE CANDIDATE:
ASSIGNMENT_OBSERVABILITY_AND_CONTROLLED_REASSIGNMENT_POLICY_AUDIT
```

Not started. Awaiting Owner review.

## Scores

```text
Direction alignment score: 96/100
Operational completion score: 94/100
```

## Dead pieces

None introduced. Stale Vite `:3000`/`BACKEND_PORT=8001` and JWT-incomplete uvicorn process were operational debt, cleared by restart.
