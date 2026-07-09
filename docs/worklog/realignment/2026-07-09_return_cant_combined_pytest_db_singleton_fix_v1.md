# RETURN_CANT_COMBINED_PYTEST_DB_SINGLETON_FIX_V1

Status: PASS

Scope:
- fix only the shared backend test infrastructure issue that broke `return_cant` during combined pytest runs
- preserve Product Truth writer, dry-run, planner, and `return_cant` business behavior exactly as-is
- no runtime feature change
- no business logic change

HEAD before:
- `d30ba12`

Failing command before fix:
- `cd backend`
- `\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py tests/test_return_cant_product_truth_bridge.py -q`

Failure before fix:
- result:
  - `29 passed`
  - `2 errors`
- failing tests:
  - `test_finish_setup_save_persists_product_truth_runtime_bridge`
  - `test_svg_replacement_clears_stale_return_cant_product_truth`
- traceback summary:
  - `backend/tests/test_return_cant_product_truth_bridge.py:251`
  - `seeded_db` called `seed_build4_templates()`
  - `backend/seeds/seed_build4_templates.py:1060`
  - `async with db_manager.async_session_maker() as session:`
  - `TypeError: 'NoneType' object is not callable`

Exact failure cause:
1. `backend/tests/_db_fixture.py` patches the global `core.database.db_manager` once for the session fixture
2. writer / planner suites use `TestClient` fixtures from `backend/tests/conftest.py`
3. app lifespan shutdown in `backend/main.py` calls `await close_database()`
4. `backend/services/database.py` forwards that to `await db_manager.close_db()`
5. `backend/core/database.py` resets `db_manager.async_session_maker = None`
6. later, `backend/tests/test_return_cant_product_truth_bridge.py` module fixture `seeded_db` runs seed helpers that call `db_manager.async_session_maker()` directly
7. in a combined pytest session, the singleton can therefore be unset before the `return_cant` seed helpers run

Files touched:
- `backend/tests/_db_fixture.py`
- `backend/tests/test_return_cant_product_truth_bridge.py`
- `docs/worklog/realignment/2026-07-09_return_cant_combined_pytest_db_singleton_fix_v1.md`

Fix summary:
1. added `patch_global_db_manager()` to `IsolatedDBFixture`
2. this helper re-binds `db_manager.engine`, `db_manager.async_session_maker`, and `_initialized` to the fixture-owned test database
3. updated `seeded_db` in `backend/tests/test_return_cant_product_truth_bridge.py` to call `db_fixture.patch_global_db_manager()` before running the seed helpers
4. switched the fixture seeding calls to `db_fixture.run(...)` so the same fixture-owned event loop drives the seed helpers consistently

Why this is the minimum safe fix:
1. it stays inside test infrastructure only
2. it does not touch writer code
3. it does not touch dry-run code
4. it does not touch planner code
5. it does not touch `return_cant` business logic
6. it restores the already intended test DB binding rather than introducing a new test-only database path

Tests run:
1. standalone `return_cant`
   - `\.venv\Scripts\python.exe -m pytest tests/test_return_cant_product_truth_bridge.py -q -vv`
   - result: `11 passed`

2. combined adjacent run
   - `\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py tests/test_return_cant_product_truth_bridge.py -q`
   - result: `31 passed`

3. writer regressions
   - `\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer.py -q`
   - result: `3 passed`

4. dry-run regressions
   - `\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py -q`
   - result: `7 passed`

5. planner regressions
   - `\.venv\Scripts\python.exe -m pytest tests/test_product_truth_promotion_planner_service.py tests/test_product_truth_promotion_planner_endpoint.py -q`
   - result: `13 passed`

Confirmation no business logic changed:
- no Product Truth writer behavior change
- no Product Truth dry-run behavior change
- no planner behavior change
- no `return_cant` business rule change
- no payload target change
- no `confirmed_snapshot_v1` behavior change

Forbidden scope confirmation:
- no ProductDefinition
- no Pricing
- no Quote/Order
- no Execution
- no ProductAggregate / TaskGraph
- no DB migration
- no seed live
- no UI
- no worktree cleanup
- no skip / xfail masking

Next recommended prompt:
- `TASK — PRODUCT_TRUTH_WRITER_BACKEND_V1_POST_FIX_VALIDATION_NOTE_V1`
- Goal: record the accepted writer PASS status together with the resolved combined pytest infrastructure fix, and confirm there is no remaining blocker on the Product Truth writer backend lane
- Boundary: docs / validation note only unless a new owner-approved backend slice is opened