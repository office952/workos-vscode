# MONTAJ AUTHORITY SPLIT CANONICAL RUNTIME RESTORE REPORT

## 1. Verdict

**PASS**

## 2. Mini decizia agentului

Stopped only orphan spawn workers tied to ghost `:8003` listen PIDs; started canonical BE from `C:\w\psiso` HEAD `184b9dc` on `:8003` without `--reload`; re-pointed FE proxy to `:8003`; matched `:8013` proof; stopped temporary `:8013`. No app code changes.

## 3. Git state

- Branch: `feature/product-system-active-path-isolation-v1`
- HEAD: `184b9dc51b1d9fb4cf449f01954bb909d9a0871c` (`184b9dc`)
- Staged at start: none
- Foreign WIP: present, untouched

## 4. Process inventory before

See `PROCESS_INVENTORY.md`. FE on `:3000` with `BACKEND_PORT=8013`. `:8003` ghost listeners + orphan workers. `:8013` live proof BE.

## 5. Port 8003 stale-process identity

Ghost listen PIDs `25988/27664/30868/11388/34884` (dead). Serving orphans:

| Orphan PID | Dead parent | Started |
|------------|-------------|---------|
| 35220 | 25988 | 2026-07-19 13:41:35 |
| 23792 | 27664 | 2026-07-19 18:56:43 |
| 29460 | 30868 | 2026-07-19 18:54:32 |
| 40616 | 11388 | 2026-07-19 18:56:59 |
| 32180 | 34884 | 2026-07-19 18:56:14 |

CMD pattern: `spawn_main(parent_pid=<ghost>)` via system Python 3.12.

## 6. Port 8013 temporary-process identity

Parent `17828` = `C:\w\psiso\backend\.venv\Scripts\python.exe -m uvicorn ... --port 8013`; worker `17840`. Started 2026-07-19 19:00:55.

## 7. Root cause

Uvicorn reload parents died; orphaned multiprocessing workers retained sockets and kept serving **pre-184b9dc** composition. Netstat attributed LISTENING to dead parent PIDs (“ghost listeners”).

## 8. Actions performed

1. Pre-flight inventory + ACM API delta  
2. Stopped five mapped orphans only  
3. Confirmed `:8003` closed  
4. Started canonical BE on `:8003`  
5. Restarted FE with `BACKEND_PORT=8003`  
6. Compared `:8003` vs `:8013` (match)  
7. Stopped `:8013`  
8. Tests + UI screenshots + docs  

## 9. Canonical backend start

```
cwd: C:\w\psiso\backend
exe: C:\w\psiso\backend\.venv\Scripts\python.exe
args: -m uvicorn main:app --host 127.0.0.1 --port 8003
env: APP_ENV=development; ENVIRONMENT=development;
     DATABASE_URL=sqlite+aiosqlite:///./dev.db;
     JWT_SECRET_KEY=<local-dev-secret-redacted>
reload: NO
parent PID: 8844
listen worker PID: 34480
```

## 10. Frontend proxy proof

Parent cmdline contains `BACKEND_PORT=8003`. FE PD == direct `:8003` PD (`confirmed`, `[]`).

## 11. Database/config comparison

Same `dev.db` under `C:\w\psiso\backend`; identical workspace `updated_at` across ports before restore → prior mismatch was code/process, not data.

## 12. API truth on 8003

PD confirmed, blockers `[]`, ACM included, Aggregate conflicts `[]`.

## 13. Comparison 8003 vs 8013

After restore: finish/PD/Agg **match**. Then `:8013` stopped.

## 14. ACM + mounting none

PASS.

## 15. Segmented status

API `CONFIRMED` / UI `Confirmat` after reload.

## 16. Service-corner authority

No Aggregate `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED`; Confirmare clean of that code.

## 17. Template inactive policy

`mounting_template_enabled=true` persisted; UI legacy inactive note present; template enable control absent under scope none.

## 18. Accessories pricing warning

Logical-list contains Consumabile producție label; not “Accesorii montaj”.

## 19. Confirmare truth

No `MOUNTING_SCOPE_INACTIVE` in Confirmare UI.

## 20. Save/reload

Reload Montaj keeps fundal authority + Confirmat (navigation/reload only).

## 21. Tests

Backend **31 passed**; FE related **51 passed**.

## 22. Runtime evidence

`docs/qa/intake-v6-montaj-authority-split-runtime-restore-2026-07-19/` (JSON + screenshots).

## 23. Processes after

- `:3000` Vite with `BACKEND_PORT=8003`  
- `:8003` canonical uvicorn (8844/34480)  
- `:8013` none  

## 24. Port 8013 final status

**Stopped** after successful parity with restored `:8003`.

## 25. Files modified

Docs/worklog/QA evidence only under:

- `docs/qa/intake-v6-montaj-authority-split-runtime-restore-2026-07-19/**`
- `docs/worklog/realignment/2026-07-19_montaj_authority_split_runtime_restore.md`

## 26. Files intentionally not modified

All application source, DB, seeds, migrations, foreign WIP.

## 27. Foreign WIP

Untouched.

## 28. Worklog

`docs/worklog/realignment/2026-07-19_montaj_authority_split_runtime_restore.md`

## 29. Commit

Docs-only commit (this pack).

## 30. Metoda de lucru si logica abordarii

Identify before kill → map ghost listen PIDs to living orphan children → surgical stop → start canonical no-reload BE → rebind FE proxy → parity vs proof port → retire `:8013`.

## 31. Roadmap awareness checkpoint

Unblocks accepting `184b9dc` as functional baseline on the documented local topology. No feature work performed.

## 32. Dead pieces check

Temporary `:8013` retired. Ghost orphans removed. Do not reintroduce `--reload` on Windows without orphan monitoring.

## 33. Cat sunt in directia stabilita

Cat sunt in directia stabilita: **98/100%**

## 34. Can 184b9dc become accepted functional baseline?

**DA** — restored `:8003` + FE `:3000` proxy return repaired authority truth matching the `:8013` proof for ACM WS; suites green; foreign WIP untouched.

## 35. Can implementation continue?

Only after owner review.
