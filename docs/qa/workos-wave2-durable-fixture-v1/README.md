# Wave 2 durable QA fixture (`880750`)

Local non-production fixture for Finalization Wave 2 runtime/UI proof.

| Field | Value |
| ----- | ----- |
| Order | `880750` / `ORD-WAVE2-QA-880750` |
| Plan | `23` |
| Snapshot | `QSN2-WAVE2-880750` (DB quote_snapshot_v2 id `23`) |
| Environment | `APP_ENV=development`, `backend/dev.db`, `127.0.0.1` |
| Materialize | **exercised Wave 3** (`DEC-009=B` scoped next-dry) — `operational_tasks=13`, `execution_tasks_created=true`; assignment/sessions still closed |

Create/recreate (does not materialize; does not touch `880811` / `973019`):

```powershell
cd C:\w\psiso\backend
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
.\.venv\Scripts\python.exe ..\docs\qa\workos-wave2-durable-fixture-v1\_create_wave2_durable_fixture.py
```

UI: `http://127.0.0.1:3000/execution/880750`

Worklog: `docs/worklog/realignment/2026-08-03_wave2_durable_qa_fixture_and_wave3_readiness_pack.md`
