# BUILD — PROD FLEX COLLABORATION PHASE 3

**Purpose:** Integrated Operator/Execution + Employee Mobile V2 human collaboration loop.  
**Boundary:** Thin capability projections only; no DB migration; no Phase 2 redesign; Mobile V1 unchanged; no Product System / pricing / mock collab.

## Feature flag
- Frontend: `VITE_FEATURE_FLEX_COLLAB_UI` (default off)
- Backend: existing `FLEX_COLLAB_PHASE2_ENABLED`

## Owner verification (local)
1. Backend `:8001` with Phase 2 flag on; frontend `:3000` with UI flag on.
2. Open `http://127.0.0.1:3000/execution/23099` (or suitable local order).
3. Scroll to **Colaborare flex** — Request Help only when backend `can_request_help`.
4. Create broadcast help → OPEN chip.
5. Open `http://127.0.0.1:3000/employee-app-v2/tasks` as eligible helper → **Ajutor solicitat** → Acceptă.
6. Open helper task work room → **Pornește ajutorul** / **Oprește sesiunea mea** (no Complete for helper-only).
7. On Execution, active workers update after start; after stop, operation remains incomplete.
8. Principal completes via existing Complete when `can_complete_operation`.

## Runtime proof script
```powershell
cd backend
.\.venv\Scripts\python.exe scripts\phase3_runtime_loop_proof.py
```

## Rollback
Unset/disable `VITE_FEATURE_FLEX_COLLAB_UI` — existing Execution and Mobile V2 flows remain; no migration.
