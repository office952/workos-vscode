# PRODUCT_TRUTH_WRITER_BACKEND_RETURN_CANT_REGRESSION_TRIAGE_V1

Status: PASS

Scope:
- triage only for the reported `return_cant` adjacent validation failure after Product Truth writer backend V1
- determine whether the failure is a writer regression, a pre-existing test infrastructure issue, a run-context issue, or a real writer/bridge conflict
- confirm the writer does not use `payload.product_truth.components.return_cant` as a generic sink
- no feature work
- no runtime behavior change

HEAD before:
- `3231222`

Safety gate:
- `git status -sb`
- `git rev-parse --short HEAD`
- `git diff --cached --name-only`
- `git diff --check`
- result:
  - HEAD matched `3231222`
  - no staged files were present
  - noisy untracked worktree remained untouched

Files inspected:
- `docs/worklog/realignment/2026-07-09_product_truth_writer_backend_v1.md`
- `backend/services/product_truth_writer_service.py`
- `backend/services/product_truth_writer_dry_run_service.py`
- `backend/tests/test_product_truth_writer.py`
- `backend/services/return_cant_product_truth_bridge.py`
- `backend/tests/test_return_cant_product_truth_bridge.py`
- `backend/tests/conftest.py`
- `backend/tests/_db_fixture.py`
- `backend/core/database.py`
- `backend/services/database.py`
- `backend/main.py`

Tests run:
1. `cd backend`
   `\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer.py -q`
   - result: `3 passed`

2. `cd backend`
   `\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py -q`
   - result: `7 passed`

3. `cd backend`
   `\.venv\Scripts\python.exe -m pytest tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py -q`
   - result: `13 passed`

4. `cd backend`
   `\.venv\Scripts\python.exe -m pytest tests/test_return_cant_product_truth_bridge.py -q -vv`
   - result on `3231222`: `11 passed`

5. combined adjacent validation shape on `3231222`
   - command:
     `\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py tests/test_return_cant_product_truth_bridge.py -q`
   - result:
     - `29 passed`
     - `2 errors`

6. standalone `return_cant` on previous commit `06b5752` in detached worktree
   - command used current venv against detached worktree checkout
   - result: `11 passed`

7. combined adjacent validation shape on previous commit `06b5752` in detached worktree
   - same combined pytest file list as current triage
   - result:
     - `29 passed`
     - `2 errors`

return_cant failure details:
- failing tests in combined run:
  - `test_finish_setup_save_persists_product_truth_runtime_bridge`
  - `test_svg_replacement_clears_stale_return_cant_product_truth`
- failure point:
  - fixture setup in `backend/tests/test_return_cant_product_truth_bridge.py`
  - `seeded_db` calls:
    - `seed_build4_templates()`
    - `seed_tpl_volumetric_letters_dossier()`
    - `seed_tpl_volumetric_letters_v2()`
- traceback summary:
  - `tests/test_return_cant_product_truth_bridge.py:251`
  - inside `seed_build4_templates()`
  - `seeds/seed_build4_templates.py:1060`
  - `async with db_manager.async_session_maker() as session:`
  - error: `TypeError: 'NoneType' object is not callable`

Why this is not a writer regression:
1. the same combined-run failure reproduces on previous commit `06b5752`, before writer backend implementation
2. the `return_cant` suite passes standalone on `3231222`
3. the `return_cant` suite passes standalone on `06b5752`
4. the failure occurs in fixture setup before any Product Truth writer endpoint or writer service logic is invoked
5. `backend/tests/test_return_cant_product_truth_bridge.py` imports only `services.return_cant_product_truth_bridge`, not `product_truth_writer_service.py`

Likely infrastructure / ordering mechanism:
1. `tests/_db_fixture.py` patches `core.database.db_manager.async_session_maker` during `IsolatedDBFixture.setup()`
2. writer and planner suites use `TestClient` fixtures from `backend/tests/conftest.py`
3. app lifespan in `backend/main.py` calls `await close_database()` on shutdown
4. `backend/services/database.py` forwards that to `await db_manager.close_db()`
5. `backend/core/database.py` resets `db_manager.async_session_maker = None` in `close_db()`
6. the `return_cant` module-level `seeded_db` fixture later calls seed helpers that require `db_manager.async_session_maker()` directly
7. therefore a multi-module pytest session can invalidate the singleton between suites, while standalone `return_cant` still passes because its seeding happens before any prior `TestClient` shutdown in that process

Writer impact analysis:
- writer touched `return_cant` bridge files directly: no
- writer touched `backend/tests/test_return_cant_product_truth_bridge.py`: no
- writer imports `return_cant_product_truth_bridge` as generic sink: no
- writer writes `payload.product_truth.components.return_cant`: no
- writer writes only `payload_json.product_truth.confirmed_snapshot_v1`: yes
- writer computes `return_cant` before/after hashes only for proof/reporting: yes

No generic sink proof:
- `backend/services/product_truth_writer_service.py` persists only through `_ensure_snapshot()` under `payload_raw["product_truth"]["confirmed_snapshot_v1"]`
- refusal responses and success responses include `return_cant` hash comparisons but do not mutate the subtree
- `backend/tests/test_product_truth_writer.py` asserts `return_cant` subtree equality before/after write and refusal
- `backend/services/product_truth_writer_dry_run_service.py` uses `TARGET_PATH = payload_json.product_truth.confirmed_snapshot_v1`
- no writer path emits a target path under `payload.product_truth.components.return_cant`

Git evidence:
- `git show --name-only --oneline 3231222`
  - touched files only:
    - `backend/routers/intake_v6_workspaces.py`
    - `backend/schemas/intake_v6.py`
    - `backend/services/intake_v6_workspace_service.py`
    - `backend/services/product_truth_writer_dry_run_service.py`
    - `backend/services/product_truth_writer_service.py`
    - `backend/tests/test_product_truth_writer.py`
    - `docs/worklog/realignment/2026-07-09_product_truth_writer_backend_v1.md`
- `git show --stat 3231222`
  - no `return_cant` bridge file or test file touched
- `git diff 06b5752..3231222 -- backend/services/return_cant_product_truth_bridge.py backend/tests/test_return_cant_product_truth_bridge.py`
  - no diff output for those files

Verdict:
- `RETURN_CANT_TRIAGE_PASS_WRITER_UNRELATED`

Recommendation:
1. writer backend V1 can be accepted as PASS relative to `return_cant` bridge behavior
2. the failing adjacent combined validation should be tracked as a separate backend test infrastructure / fixture-ordering task
3. that follow-up task should harden the shared test DB lifecycle so suite-combined pytest runs do not leave `db_manager.async_session_maker` unset before direct seed helpers run

Forbidden scope confirmation:
- no UI
- no ProductDefinition
- no Pricing
- no Quote/Order
- no Execution
- no ProductAggregate / TaskGraph
- no DB migration
- no seed live
- no cleanup

Next recommended prompt:
- `TASK — RETURN_CANT_COMBINED_PYTEST_DB_SINGLETON_FIX_V1`
- Goal: fix the shared backend test infrastructure so combined pytest sessions that mix `TestClient` suites and direct seed-helper suites do not lose `db_manager.async_session_maker` between modules
- Boundary: no writer feature changes, no return_cant business logic changes unless the infrastructure fix proves insufficient, no UI, no Pricing/Quote/Order/Execution work

Roadmap awareness checkpoint:
- current spine position:
  - Product Truth writer backend V1 is complete
  - current step is post-implementation regression triage on an adjacent protected bridge boundary
- alignment with agreed direction: `92/100%`
- dead pieces check:
  - no dead writer code found in this triage slice
  - failing evidence points to shared test lifecycle, not abandoned writer logic
- forbidden scope confirmation:
  - no expansion into UI, ProductDefinition, Pricing, Quote/Order, Execution, ProductAggregate, TaskGraph, migration, or live seed