# Form System Selected Layer Refs Test Setup Repair V1

Verdict: PASS

HEAD before implementation:
- `4902944`

Scope:
- repair focused backend test setup for `tests/test_selected_layer_refs_runtime_capture.py`
- no runtime capture rewrite
- no Product Truth logic change
- no UI
- no Pricing
- no DB migration/schema change
- no seed live behavior change
- no endpoint
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph

Root cause:
- the selected-layer persistence test used module-local seeding through `seed_build4_templates()` / related seeds, and those seed functions resolve sessions through the global `core.database.db_manager`
- when this module ran after another runtime-capture module in the same pytest process, the module fixture assumed `db_manager.async_session_maker` was still bound to the session `db_fixture`
- that assumption was unstable across module ordering, so the second module sometimes hit `db_manager.async_session_maker = None` during fixture setup
- the failing symptom was:
  - `TypeError: 'NoneType' object is not callable`
  - at `seeds/seed_build4_templates.py` on `db_manager.async_session_maker()`

Repair:
- kept the existing persistence coverage intact
- kept the existing seed functions intact
- repaired only the test fixture
- `tests/test_selected_layer_refs_runtime_capture.py` now explicitly rebinds `core.database.db_manager` to the already-created isolated `db_fixture` before invoking the seed helpers
- the module now also runs the seed coroutines on `db_fixture.run(...)`, so the same isolated event loop and sessionmaker are used as the green backend test setup

Why this is the minimal safe fix:
- no production code changes were required
- no live seed behavior changed
- no runtime truth behavior changed
- no skip or coverage reduction was introduced
- the change only removes hidden order-dependence from the selected-layer test module

Tests run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_selected_layer_refs_runtime_capture.py -q
```

Expected:
- selected-layer persistence slice green

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_contract_mapping_adapter.py tests/test_form_system_contract_backbone.py tests/test_finish_target_runtime_capture.py tests/test_intake_v4_finish_truth.py tests/test_selected_layer_refs_runtime_capture.py -q
```

Expected:
- full focused runtime-capture slice green without setup-order failure

Files changed:
- `backend/tests/test_selected_layer_refs_runtime_capture.py`
- `docs/worklog/realignment/2026-07-09_form_system_selected_layer_refs_test_setup_repair_v1.md`