# QA — WorkOS Atoms Reproducible Demo Environment V1

**Owner GO:** `AUTHORIZE_WORKOS_ATOMS_REPRODUCIBLE_DEMO_ENVIRONMENT_V1`  
**Verdict:** `PASS`  
**Worklog:** `docs/worklog/realignment/2026-08-10_workos_atoms_reproducible_demo_environment_v1.md`

## Proofs

| Item | Evidence |
|------|----------|
| Architecture | Option A — wipe-and-rebuild `backend/demo/workos_demo.db` + seed |
| Guard tests | `pytest tests/test_atoms_demo_db_guard.py tests/test_atoms_demo_bootstrap_safety.py` → 10 passed |
| Bootstrap / rebuild | `.\scripts\demo-bootstrap.ps1` → PASS (repeat proven) |
| Seed summary | `seed_summary.json` |
| API smoke | `api_smoke_results.json` (TestClient vs demo DB) |
| Route smoke §23 | `ROUTE_SMOKE.md` + `route_smoke.json` + `screenshots/` |
| PII scan | `PII_SCAN.md` → PASS |
| Ops doc | `docs/operations/WORKOS_ATOMS_DEMO_ENVIRONMENT.md` |

## DEMO commercial totals (real CPP)

- EUR gross **862.65** · net **712.93** · VAT **149.72**
- Quote code `DEMO-QUOTE-EUR-001` · Order `DEMO-ORDER-001`

## Ports used for UI proof

Owner live stack stayed on `:8000`/`:3000`. UI route smoke used isolated:

```powershell
$env:BACKEND_PORT='8010'
$env:VITE_PORT='3010'
$env:VITE_API_BASE_URL='http://127.0.0.1:8010'
.\scripts\demo-start.ps1
```

## Rebuild

```powershell
.\scripts\demo-bootstrap.ps1
```

Wipe-and-rebuild dedicated demo DB only — never `backend/dev.db`.
