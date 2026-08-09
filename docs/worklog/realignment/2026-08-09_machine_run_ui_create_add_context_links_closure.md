# MachineRun UI CREATE / ADD / context links closure

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_UI_CREATE_ADD_AND_CONTEXT_LINKS_CLOSURE`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `a162dca7`  
**Verdict:** **PASS** · `MACHINE_RUN_V1_E2E = CLOSED`

---

## Scope delivered

1. **CREATE MachineRun UI** on `/execution/machine-runs` (`+ Rulare utilaj`) — machine picker → `GET …/candidates` → multi-plan checkbox groups → reservation window → `POST` → navigate to canonical detail. Min 2 participants client-side; backend remains authority.
2. **ADD participant UI** on detail when `HELD` + `execution.machine_run.manage` — `GET …/candidate-participants`, respects `mutation_allowed`, single-task add, refetch.
3. **ExecutionDetail** WorkPanel context chip via `GET …/by-task`.
4. **Ops-Graph** task-row context chip via same lookup.
5. No frontend eligibility reconstruction; no Capacity / PAUSE / Phase B / Mobile; QA writes = 0; no push.

---

## N+1 / request-volume decision

| Surface | N tasks | Lookup GETs | Decision |
| ------- | ------- | ----------- | -------- |
| ExecutionDetail (proof order 880755) | 1 | 1 | ACCEPTABLE |
| Ops-Graph (same) | 1 | 1 | ACCEPTABLE |

Hook `useActiveMachineRunByTasks` dedupes keys and caches per mount. At typical ~10–20 tasks/page this is **VERIFIED_ACCEPTABLE**; bulk lookup **not** required for V1.

---

## Evidence

`docs/qa/machine-run-ui-v1-closure/` — screenshots (light/dark CREATE/ADD/chips), `network_proof.json`, `browser_capture_report.json`, `console_proof.json`.

Isolated runtime: `:3010` + `:8010` + `_isolated_s67_closure.db` (gitignored).

QA `backend/dev.db` `machine_runs` count after closure: **0**.

---

## Files (primary)

| Area | Path |
| ---- | ---- |
| API client | `frontend/src/api/machineRuns.ts` |
| Flags / copy helpers | `frontend/src/lib/machineRunUi.ts` |
| CREATE dialog | `frontend/src/components/machine-run/MachineRunCreateDialog.tsx` |
| ADD panel | `frontend/src/components/machine-run/MachineRunAddParticipantPanel.tsx` |
| Context chip | `frontend/src/components/machine-run/MachineRunContextChip.tsx` |
| Lookup hook | `frontend/src/hooks/useActiveMachineRunByTasks.ts` |
| List / detail | `MachineRunsListPage.tsx` / `MachineRunDetailPage.tsx` |
| Chips hosts | `WorkPanel.tsx` / `MaterializedOpsGraph.tsx` |
| Modules/gov truth | `currentTruthControlCenter.ts` |

---

## Still deferred (not V1)

```text
PAUSE_RESUME = DEFERRED
AUTO_BATCH = NOT_IMPLEMENTED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
EMPLOYEE_MOBILE = NO_CHANGE
UTILAJE_MACHINE_RUN_HOME = LATER
```

---

## Operator summary

- **Creează rulare:** Producție → Rulări utilaj → **Rulare utilaj** → alege utilaj → bifează ≥2 taskuri eligibile (pot fi din comenzi diferite) → interval → Creează.
- **Adaugă task:** deschide o rulare în **Grupare (HELD)** → **Adaugă participant** → alege un candidat → Adaugă.
- **Vede apartenența:** pe task în ExecutionDetail / Ops-Graph apare chip **Rulare utilaj MR-…** cu status + **Deschide** (doar dacă există membership activ).
- **V1 închis E2E** = write + read + candidates + by-task + list/detail + CREATE + ADD/REMOVE + lifecycle + context chips pe fluxul actual — fără PAUSE/RESUME sau Phase B.
