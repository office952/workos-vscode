# WorkOS App Integrity Before Next GO — Worklog

**Date:** 2026-07-31  
**Mode:** READ-ONLY / reporting  
**Canonical repo:** `C:\w\psiso`  
**SHA:** `a1c28854`

---

## Timeline

| Step | Action | Result |
|------|--------|--------|
| 0 | Repo identity on `C:\w\psiso` vs `C:\Users\offic\workos_app_vs` | Canonical = **psiso**; workos_app_vs detached stale `82a713e0` |
| 1 | `git status` / branch / log / dirty classify | Branch `feat/capacity-batch-20d-scoped-b-92401` @ `a1c28854`; employee WIP unrelated; capacity QA docs expected untracked |
| 2 | Read AGENTS.md, CI preflight gate, Batch 20B–20E handoff reports, 20E evidence + QA mirrors | Done; `project_sources/*` **missing** |
| 3 | Workspace folders + worktree signals | `backend`/`frontend`/`docs/qa`/`exports` present; live detached stack metadata present |
| 4 | Runtime probes `:8000`/`:3000`, local-compatibility, log tails | Healthy; authorize false; intake_v5 svgpathtools WARN |
| 5 | DB read-only + GET plan 92401/973010 | ops 18 / 12; sessions 0; reality scoped 0; hashes match 20E |
| 6 | Boundary + product-direction greps / prior 20E checks | Pricing⊥time hold; no 92401 UI hardcode; 973010 default WARN carry |
| 7 | CI preflight: lint, test:ci, build, 4-file pytest | All exit 0 |
| 8 | Write reports | See file list below |

---

## Commands (representative)

```powershell
cd C:\w\psiso
git rev-parse --show-toplevel
git status --short
git branch --show-current
git rev-parse --short HEAD
git log --oneline -10

# Runtime
Invoke-WebRequest http://127.0.0.1:8000/health
Invoke-WebRequest http://127.0.0.1:3000/
Invoke-WebRequest http://127.0.0.1:8000/api/v1/system/local-compatibility -Headers @{Authorization='Bearer __DEV_BYPASS_TOKEN__'}
Invoke-WebRequest http://127.0.0.1:8000/api/v1/execution/plan/92401 -Headers @{Authorization='Bearer __DEV_BYPASS_TOKEN__'}
Invoke-WebRequest http://127.0.0.1:8000/api/v1/execution/plan/973010 -Headers @{Authorization='Bearer __DEV_BYPASS_TOKEN__'}

# DB (read-only python sqlite3 on backend/dev.db)

# Preflight
cd frontend; pnpm run lint; pnpm run test:ci; pnpm run build
cd backend; $env:APP_ENV='test'; $env:ENVIRONMENT='test'
.\.venv\Scripts\python.exe -m pytest -q tests/test_dashboard_kpi_metrics.py tests/test_operational_data_gaps.py tests/test_pricing_registry.py tests/test_cost_engine_config.py --ignore=tests/manual
```

**Not run (forbidden / out of scope):** POST materialize, execute controls, migrations, product edits, full Vitest, full backend pytest.

---

## Kickoff / preflight gate ticks

- [x] Frontend lint
- [x] Frontend test:ci
- [x] Frontend build
- [x] Backend targeted pytest
- [x] Runtime health API/UI
- [ ] Screenshot proof — N/A (no UI GO; integrity reporting only)
- [x] Persistent worklog (this file)
- [~] GitHub Actions — not re-polled this session; prior PR #37 stamped green in 20D/20E

---

## Outputs

- `WORKOS_REPO_IDENTITY_CHECK_REPORT.md`
- `WORKOS_APP_INTEGRITY_BEFORE_NEXT_GO_REPORT.md`
- `WORKOS_APP_INTEGRITY_BEFORE_NEXT_GO_WORKLOG.md` (this file)
- `C:\w\psiso\docs\qa\app-integrity-before-next-go\*.md` (6 integrity chapters + ephemeral `_tmp_*.txt` logs)

---

## Final stamp (this batch)

**PASS WITH WARNINGS**  
**Direction:** 88/100%  
**Next:** Owner review → dispose HR dirty WIP separately → choose next single-purpose Owner GO (RO operator review of 92401 recommended before any new authorize/execute).
