# Track D — Runtime / Preflight Truth

**Mode:** READ-ONLY re-check · do not fix  
**Date:** 2026-07-31 (~23:27 local)  
**Repo:** `C:\w\psiso` @ `a1c28854`

---

## Runtime (fresh probes this discovery)

| Check | Result |
|-------|--------|
| `GET :8000/health` | **200** `{"status":"healthy"}` |
| `GET :3000/` | **200** |
| Listener :8000 | PID **28568** (python/uvicorn) |
| Listener :3000 | PID **9044** (node/Vite) |
| Stale second listeners | **None** observed |
| Detached meta | Started 23:08:51 · root `C:\w\psiso` · ports 8000/3000 |
| Compat `git_commit` | **`a1c28854`** matches HEAD |
| Authorize live | **false** |
| OD3 gate landed | **true** · identity `capacity-batch-20d/v1` |

---

## Startup warnings (still present)

| Warning | Severity |
|---------|----------|
| `Failed to import module 'routers.intake_v5': No module named 'svgpathtools'` | **WARN** (repeated on reload; V6 still loads) |
| Browserslist caniuse-lite stale (frontend) | **WARN** hygiene |

No crash loop observed on current detached session.

---

## Preflight / tests

Fresh full CI suite not re-run in this discovery (integrity GO already green minutes earlier). Evidence reused:

| Check | Evidence | Result |
|-------|----------|--------|
| Frontend lint | `app-integrity-before-next-go/_tmp_lint.txt` | **PASS** (exit 0) |
| Frontend `test:ci` | `_tmp_testci.txt` — 21 files / 198 tests | **PASS** |
| Frontend build | `_tmp_build.txt` — built in ~15.6s | **PASS** |
| Backend 4-file CI pytest | `_tmp_pytest.txt` — **28 passed** | **PASS** |

Canonical gate: handoff `CI_PREFLIGHT_GATE.md`.

---

## Verdict

**PASS WITH WARNINGS** — Runtime is **still** healthy now (not only previously). Preflight remains green per last integrity run. Named startup warnings are non-blocking.
