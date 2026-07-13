## Runtime verification (Phase 6)

### Attempted stack start

Worktree: `C:\\w\\psiso`

1) Attempt: `npm run dev:stack`
- Result: **FAIL** (Python not found in worktree; helper could not create `backend/.venv`)

2) Attempt with existing venv python:
- Command: set `WORKOS_PYTHON=C:\\Users\\offic\\workos_app_vs\\backend\\.venv\\Scripts\\python.exe` then `npm run dev:stack`
- Result: **BLOCKED** by port 8000 ghost listener:
  - `netstat -ano | findstr :8000` shows LISTENING PID `12012`
  - PID `12012` is not discoverable by `Get-Process` / `taskkill` / CIM lookup (process “not found”)
  - Dev script reports: **BLOCKER: Port 8000 remained occupied** after stale backend stop

### Consequence

Cannot start the backend for this slice on the required ports (`8000/3000`) to validate runtime UI + API behavior.\n\nThis is a **runtime-environment blocker**; no port changes were attempted (per constraint).

### What was verified instead (bounded)

Local targeted backend tests were executed successfully using the existing venv python from the original workspace (read-only reuse):
- `backend/tests/test_template_architecture_scope.py`
- `backend/tests/test_product_system_identity_boundary.py`

### Unverified due to blocker

- Live UI behavior and screenshots for:
  - Product System catalog/details
  - Dossier operator read-only surface
  - Live API calls demonstrating 422 identity rejection

### Recommended unblock steps (operator action)

1) Identify and free port `8000` listener on `127.0.0.1:8000`.\n2) Re-run stack start with:\n   - `WORKOS_PYTHON=C:\\Users\\offic\\workos_app_vs\\backend\\.venv\\Scripts\\python.exe`\n   - `npm run dev:stack`\n3) Re-run runtime verification checklist and capture screenshots under:\n   - `docs/qa/product-system-active-path-isolation-v1/`

