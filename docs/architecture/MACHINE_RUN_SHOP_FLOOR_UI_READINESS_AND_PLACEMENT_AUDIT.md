# MACHINE_RUN — Shop-Floor UI Readiness & Placement Audit

**Task:** `MACHINE_RUN_SHOP_FLOOR_UI_READINESS_AND_PLACEMENT_AUDIT`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_SHOP_FLOOR_UI_READINESS_AND_PLACEMENT_AUDIT`  
**Date:** 2026-08-07  
**Status:** **PASS** · audit/read-only · **no frontend implementation · no QA writes**  
**Starting HEAD:** `94b4223b`  
**Worklog:** `docs/worklog/realignment/2026-08-07_machine_run_shop_floor_ui_readiness_and_placement_audit.md`

```text
MACHINE_RUN_SHOP_FLOOR_UI_READINESS_AND_PLACEMENT_AUDIT = PASS
PRIMARY_UI_LOCATION =
  /execution/machine-runs
  (Planificare / Producție — dedicated Machine Runs workspace)
SECONDARY_CONTEXT_LINKS =
  ExecutionDetail task row chip (participant)
  + Ops-Graph task chip (Open run)
  · Utilaje current/upcoming = LATER
NEW_PAGE_REQUIRED = YES
OPERATOR_JOURNEY = FINALIZED
ACTION_MATRIX = FINALIZED
START_UI_SEMANTICS = FINALIZED
COMPLETE_UI_SEMANTICS = FINALIZED
RELEASE_UI_SEMANTICS = FINALIZED
PARTICIPANT_UI = FINALIZED
RESCHEDULE_UI = FINALIZED
PERMISSION_UI = FINALIZED
ERROR_UX = FINALIZED
CAS_UX = FINALIZED
MACHINE_RUN_READ_API = PASS
UI_BLOCKER = CLEARED_BY_OPERATOR_READ_API
MODULES_IMPACT = UPDATED_IN_OPERATOR_READ_API_GO
GOVERNANCE_IMPACT = UPDATED_IN_OPERATOR_READ_API_GO
FRONTEND_IMPLEMENTATION = PASS
  (2026-08-09 · MACHINE_RUN_SHOP_FLOOR_UI_IMPLEMENTATION)
CREATE_UI = VERIFIED
ADD_UI = VERIFIED
CANDIDATE_DISCOVERY_API = PASS
TASK_TO_ACTIVE_MACHINE_RUN_LOOKUP = PASS
SECONDARY_CONTEXT_LINKS = VERIFIED
MACHINE_RUN_V1_E2E = CLOSED
QA_MUTATIONS = 0
NEXT_IMPLEMENTATION_SCOPE = NOT_AUTHORIZED
PAUSE_RESUME = DEFERRED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Why UI readiness now

```text
Backend capability exists and is otherwise unusable by operator.
```

Commands already PASS: CREATE · ADD/REMOVE · CONFIRM · RESCHEDULE · START · COMPLETE · RELEASE · CANCEL.  
Frontend has **zero** `MachineRun` references. Operator cannot see or operate the lifecycle.

---

## 2. Starting state (confirmed)

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
starting HEAD = 94b4223b
CODE_ALEMBIC = s67_machine_run_execution_status
QA_ALEMBIC = s67_machine_run_execution_status
QA SHA = bee5f5f74c428fd03cf30ffd7377db00be3fa64716a29ce2652ae9f93b161322
machine_runs / participants / transitions / reservations = 0
TASK_STATE_COUPLING = NOT_IMPLEMENTED
EMPLOYEE_SESSION_COUPLING = NOT_IMPLEMENTED
PAUSE_RESUME = DEFERRED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## 3. Pages / routes audited (live browser)

| Route | Title / role | MachineRun today |
| ----- | ------------ | ---------------- |
| `/execution` | **Execuție** — order list + capacity strip | absent |
| `/execution/:order_id` | **Rezultat execuție** — dense order workspace | absent |
| `/execution/ops-graph` | **Ops graph** — employee assign audit | absent (assignment only) |
| `/shop-floor` | **Atelier** — WC monitor / Machine State | absent (monitor ≠ MachineRun) |
| `/utilaje` | **Utilaje și capacitate** — registry + util% honesty | absent · Capacity noise |
| `/modules` | **Harta sistemelor** | no MachineRun system row → **STALE** |
| `/governance` | **Guvernanța sistemului** | ExecutionPlan / Reality only → **STALE** |

Nav groups observed: Lucrări · Producție (Atelier, Planificare, Ops-Graph, Acțiune task, Stații) · Oameni · Resurse (Utilaje) · Management · Administrare (Harta, Guvernanță).

---

## 4. Existing UI hierarchy (facts)

### `/execution` (Planificare)
- Flux strip: Comenzi → Execuție → Atelier → Control producție
- Order-centric table (23 comenzi)
- Capacity strip (read-only util%) already above fold
- Next-step pushes operator into an **order** detail

### `/execution/:id` (Rezultat execuție)
Vertical stack already heavy above the fold:
1. Execution Plan truth  
2. Situație operațională  
3. Necesită atenție  
4. Pregătire resurse (capability readiness — *not* reservation)  
5. Candidați eligibili  
6. Pregătire pentru atribuire  
7. **Lucru în execuție** (task session Start/Finalizează — often FROZEN)  
8. Plan și realizat · costs · closure · post-job  

Post-job already admits: `machine_usage_not_logged_in_execution_reality`.

### Atelier
Explicit copy: *monitorizare*; *Start/Complete rămân pe Acțiune task / Stații* — meaning **employee task** actions, not MachineRun.

### Utilaje
Title mixes **capacity**; util% / GAP / Batch gates dominate. Wrong home for shop-floor START/COMPLETE.

---

## 5. Placement decision

### Compared options

| Option | Fit | Verdict |
| ------ | --- | ------- |
| A. Execution Plan level only | Order-scoped; multi-plan run does not belong to one plan | reject as primary |
| B. Task level only | Implies one-task ownership — false | reject as primary |
| C. Dedicated Machine Runs page | Matches shared machine execution object | **accept** |
| D. Utilaje page | Registry + Capacity honesty; premature dual surface | **LATER** for read-only current/upcoming |
| E. Hybrid list + context links | Needed for discoverability | **accept as pattern** |

### Singular verdict

```text
PRIMARY_UI_LOCATION =
  /execution/machine-runs
  under Planificare (Producție)
  list + detail of MachineRun as its own operational object

SECONDARY_CONTEXT_LINKS =
  1) ExecutionDetail — on participant tasks: chip
     "Rulare utilaj · MR-{id} · {status} · {machine} · Deschide"
  2) Ops-Graph — same chip (read-only open)
  Utilaje current/upcoming MachineRun = LATER (not NOW)

NEW_PAGE_REQUIRED = YES
```

**De ce pagină nouă acum:** existing Execution surfaces are **order/task scoped**. MachineRun is a **shared machine context** that can span multiple ExecutionPlans/Orders. Hosting primary controls inside one order’s `Rezultat execuție` would teach the wrong ownership and fight an already dense stack. A dedicated workspace under Planificare keeps START/COMPLETE away from employee task Start/Finalizează and away from Utilaje capacity %.

**De ce nu Atelier ca primary:** Atelier is monitoring; it already routes “Start/Complete” mentally to task actions. MachineRun verbs must not reuse that language on that page first.

---

## 6. Operator audience

| Role | Read | Manage (CREATE/CONFIRM/…) | Execute (START/COMPLETE) |
| ---- | ---- | --------------------------- | ------------------------ |
| admin | yes | yes | yes |
| manager | yes | yes | yes |
| operator | yes (recommended) | no | yes |
| sales / other | no | no | no |

Backend facts:
- `execution.machine_run.manage` → admin, manager  
- `execution.machine_run.execute` → admin, manager, operator  

UI convention in Execution: **hide** unavailable actions (WorkPanel omits Start when sessions frozen; management panels return null). Prefer **hide** over disabled for missing permission. Disable only when permission exists but state forbids (e.g. START visible only in RESERVED).

---

## 7. Information hierarchy (operator-facing)

Primary card (decision leads):

1. Status chip (RO copy)  
2. Machine identity (code/name)  
3. Capability (if present on machine registry join)  
4. Time window (reservation start–end)  
5. Primary action  

Assist / details:

6. Participants ACTIVE (plan/order/task labels — not raw node dumps as hero)  
7. Actual timing (`started_at` / `completed_at` / derived duration)  
8. Versions (for CAS / support — secondary)  
9. REMOVED participants → **Istoric** only  

Never show as MachineRun effects: task started/completed, employee working, Capacity %, PAUSE/RESUME, Phase B transfer.

---

## 8. Status copy (Romanian)

Avoid raw enums. Avoid colliding with existing **“Pregătire resurse”** readiness vocabulary for HELD.

| Backend | Operator label | Short hint |
| ------- | -------------- | ---------- |
| HELD | **Grupare** | Se decid participanții; utilajul nu e încă rezervat ferm |
| RESERVED | **Rezervat** | Intervalul pe utilaj e angajat |
| RUNNING | **În lucru pe utilaj** | Rularea a început efectiv |
| COMPLETED | **Lucru utilaj finalizat** | Tăierea/prelucrarea s-a terminat; utilajul încă nu e liber |
| RELEASED | **Eliberat** | Intervalul s-a închis; utilajul e liber din punct de vedere rezervare |
| CANCELLED | **Anulat** | Rularea nu se mai face |

---

## 9. Action matrix

| State | Primary | Secondary | Danger / forbidden |
| ----- | ------- | --------- | ------------------ |
| HELD | **Confirmă** | Adaugă participant · Elimină participant · Reprogramează | **Anulează** · START/COMPLETE forbidden |
| RESERVED | **Pornește utilajul** (START) | Reprogramează · Eliberează | **Anulează** · COMPLETE forbidden |
| RUNNING | **Finalizează lucrul pe utilaj** (COMPLETE) | — | CANCEL/RESCHEDULE/ADD/REMOVE/START forbidden · no PAUSE |
| COMPLETED | **Eliberează utilajul** (RELEASE) | — (inline hint: încă rezervat) | START/COMPLETE/CANCEL/RESCHEDULE forbidden |
| RELEASED | — (read-only) | — | all mutations forbidden |
| CANCELLED | — (read-only) | — | all mutations forbidden |

CREATE remains a managed action from the list (“Creează rulare utilaj”) — not a status action on an existing run.

---

## 10. START / COMPLETE / RELEASE UX

### START
```text
Label: Pornește utilajul
Meaning: utilajul începe efectiv această rulare
≠ Start task · ≠ Start sesiune angajat · ≠ Start comandă
Confirm modal: NOT required by default (direct action + server wait)
Sets: started_at (server)
UI after success: status → În lucru pe utilaj; reservation remains Rezervat
```

### COMPLETE
```text
Label: Finalizează lucrul pe utilaj
Meaning: lucrarea pe utilaj pentru această rulare s-a terminat
≠ Finalizează task · ≠ Închide comandă · ≠ Release
Confirm modal: NOT required by default
Sets: completed_at (server); duration = completed_at − started_at (display only)
UI after success: Lucru utilaj finalizat + short hint
  "Utilajul rămâne rezervat până la Eliberează."
```

### RELEASE
```text
Label: Eliberează utilajul
COMPLETE ≠ RELEASE (must stay visible in COMPLETED state)
From RESERVED (no start): secondary; confirm recommended
  ("Eliberezi rezervarea fără a rula utilajul?")
From COMPLETED: primary; light confirm optional
  ("Eliberezi utilajul după finalizarea lucrului?")
Does not clear started_at/completed_at audit
```

---

## 11. Participant UX

- List default = **ACTIVE** only  
- Show: order code · plan id · task display name (human) · capability if useful  
- Multi-plan / multi-order: explicit badge “Mai multe comenzi” when >1 distinct order  
- ADD/REMOVE only in **Grupare (HELD)**  
- REMOVED → under **Istoric participanți** (collapsed)  
- Never imply the run “belongs” to the first participant alone  

---

## 12. Reschedule UX

```text
Fields: new start · new end
Timezone: hide if single org timezone; send backend default from server/config
Forbidden in same dialog: machine change · participant mutation
Allowed states: HELD · RESERVED only
```

---

## 13. Error UX (operator messages)

| Code | Message | Next action |
| ---- | ------- | ----------- |
| cas_stale | Run-ul a fost modificat între timp. | Reîncarcă datele înainte să continui. |
| invalid_transition | Această acțiune nu e permisă în starea actuală. | Reîncarcă; verifică statusul. |
| overlap_conflict | Intervalul se suprapune cu altă rezervare pe utilaj. | Alege alt interval (Reprogramează) sau alt utilaj (CREATE nou — later). |
| minimum_participants_violation | Trebuie cel puțin doi participanți activi. | Adaugă participant. |
| task_already_in_active_machine_run | Taskul e deja într-o rulare activă. | Deschide rularea existentă. |
| participant_capability_mismatch | Taskul nu se potrivește cu capabilitatea utilajului. | Alege alt task sau alt utilaj. |
| domain_disabled | Rezervările pe utilaj sunt dezactivate. | Contactează administratorul. |
| permission_denied | Nu ai dreptul pentru această acțiune. | — |
| run_reservation_state_mismatch | Datele run/rezervare nu coincid. | Reîncarcă; nu continua pe date vechi. |
| idempotency_payload_conflict | Cererea conflictă cu una anterioară. | Reîncearcă cu o acțiune nouă. |

No raw code as primary text. Map via shared error helper later.

---

## 14. CAS / concurrency UX

```text
On cas_stale: show conflict · refresh run · keep list/scroll context
NO silent retry of mutation
NO optimistic status flip for START/COMPLETE/RELEASE
server-confirmed transitions only
```

---

## 15. Permission UX

| Action | Permission |
| ------ | ---------- |
| CREATE, ADD/REMOVE, CONFIRM, RESCHEDULE, RELEASE, CANCEL | `execution.machine_run.manage` |
| START, COMPLETE | `execution.machine_run.execute` |
| Read list/detail | new read permission or reuse execute/manage read — decide in READ API GO |

Pattern: **hide** unauthorized buttons. Do not show disabled START to sales.

---

## 16. Read API sufficiency — blocker

### Command APIs present (POST only)
```text
POST …/resource-state/machine-runs
POST …/machine-runs/{id}/confirm|release|start|complete|cancel|reschedule
POST …/machine-runs/{id}/add-participant|remove-participant
```

Command response (`CreateMachineRunResult`) has enough fields **after a mutation**, but UI cannot:

- list open runs  
- open a run by id without prior create response  
- refresh after navigation / CAS  
- show chips on tasks without a read join  

### Existing reads are insufficient
- R6 `GET …/resource-state/plans/{plan_id}/tasks?task_key=` → domain CLEAR/ACTIVE only; **no MachineRun payload**  
- `GET …/plans/{plan_id}/resource-requirements` → demand projection only  
- No `GET …/machine-runs` · no `GET …/machine-runs/{id}`  

```text
MACHINE_RUN_READ_API = INSUFFICIENT
UI_BLOCKER = MACHINE_RUN_READ_MODEL/API_MISSING
NEXT_BACKEND_SLICE = MACHINE_RUN_OPERATOR_READ_API
```

Do **not** build frontend over indirect introspection.

### Read model minimum (for next backend GO)

```text
run id, status, version
reservation id/status/version, window, timezone
machine id + display fields
participants ACTIVE (+ optional include_removed)
started_at, completed_at
list filters: status, machine_id, plan_id/order_id, open-only
optional: participant task → machine_run_id for chips
```

`allowed_actions[]`: **not required in first read slice**. Prefer FE derive from `status + role permissions` to avoid duplicating state machine in two places. Revisit only if FE drift becomes real.

---

## 17. Full-page visual hierarchy (recommended workspace)

```text
Above fold:
  title "Rulări utilaj"
  filters (status / machine / open)
  list rows: status · machine · window · participant count · primary CTA

Detail (route or split pane — not a giant banner on ExecutionDetail):
  status + machine + window
  primary action
  participants ACTIVE
  timing actual
  secondary actions / danger in menu

Diagnostics below / collapsed:
  versions, transition ids, reservation id
```

Rule: operator decision leads; diagnostics assist. Do not inject a large MachineRun panel into the already crowded `Rezultat execuție` stack.

---

## 18. Navigation audit

| Surface | Finding |
| ------- | ------- |
| Sidebar Planificare | Natural parent for `/execution/machine-runs` |
| Atelier | Keep monitor-only for now; no MachineRun START buttons |
| Acțiune task / Stații | Employee task verbs — keep separate naming |
| Utilaje | No MachineRun controls NOW; LATER read-only link |
| Dead links | none found for MachineRun (surface missing entirely) |
| Duplicate | avoid second “runs” UI on Utilaje until LATER |

---

## 19. `/modules` impact

```text
MODULES_IMPACT = STALE_NEEDS_MACHINE_RUN_OWNERSHIP_ROW
```

Spine today: … → ExecutionPlan → Execution Reality → PostJob.  
Missing official system: **MachineRun** (shared machine execution) and clarity that Reservation ≠ MachineRun ≠ Session.

Documented change needed (future GO / modules data update — **not this audit**):

```text
MachineRun — owns shared machine execution lifecycle
Reservation — owns machine commitment/window
ExecutionPlan task — demand/provenance participant
Employee Session — employee actual work
Capacity — IMPLEMENTED_INACTIVE
```

---

## 20. `/governance` impact

```text
GOVERNANCE_IMPACT = STALE_NEEDS_OWNERSHIP_BOUNDARY_ROWS
```

Ownership matrix lists ExecutionPlan + Execution Reality; resource boundary still “partial” (Utilaje / Angajați / Pontaj). Needs MachineRun / Reservation ownership rows when Control Center is updated — **not in this audit**.

---

## 21. Figma

```text
NO_FIGMA_BLOCKER
```

No MachineRun shop-floor Figma found as operational authority. Visual reference optional later; API/runtime remain truth.

---

## 22. Component map (structural only — not implemented)

| Piece | Role |
| ----- | ---- |
| MachineRunList | open/recent runs under `/execution/machine-runs` |
| MachineRunSummary | header: status, machine, window, primary CTA |
| MachineRunParticipantList | ACTIVE participants + multi-order badge |
| MachineRunStatus | RO chip + COMPLETED hint |
| MachineRunActions | primary/secondary/danger from matrix + permissions |
| MachineRunTiming | planned window + actual start/end/duration |

No generic execution framework. No Gantt. No scheduler.

---

## 23. Operator journey

1. Operator opens **Planificare → Rulări utilaj** (`/execution/machine-runs`)  
2. Selects run · verifies machine + ACTIVE participants (multi-order visible)  
3. If Grupare → adjust participants → **Confirmă** → Rezervat  
4. **Pornește utilajul** → În lucru pe utilaj (`started_at`)  
5. Sees RUNNING; reservation still Rezervat; tasks/sessions unchanged  
6. **Finalizează lucrul pe utilaj** → Lucru utilaj finalizat (`completed_at`)  
7. **Eliberează utilajul** → Eliberat · R6 CLEAR  

Variants: Reprogramează (HELD/RESERVED) · Anulează (HELD/RESERVED) · participant correction only while Grupare · direct RELEASE from Rezervat without START.

---

## 24. Overengineering check

**De ce UI acum?** Backend is real; operator loop is incomplete without visibility/actions.

**Ce NU construim acum:**

```text
scheduler / Gantt
capacity dashboard / util% on MachineRun UI
machine telemetry
auto-batching
PAUSE/RESUME
employee sessions coupling
task propagation from START/COMPLETE
Utilaje dual home (NOW)
allowed_actions engine (unless later proven needed)
Employee Mobile
Post-start transfer/handoff UI (reassignment Phase E — not MachineRun V1)
```

---

## 25. Implementation status (2026-08-09)

```text
MACHINE_RUN_SHOP_FLOOR_UI_IMPLEMENTATION = PASS
PRIMARY_ROUTE = /execution/machine-runs
NAV_LABEL = Rulări utilaj (Producție)
CANDIDATE_DISCOVERY_API = PASS (2026-08-09)
TASK_TO_ACTIVE_MACHINE_RUN_LOOKUP = PASS (2026-08-09)
CREATE_UI / ADD_UI = VERIFIED (2026-08-09 closure)
SECONDARY_CONTEXT_LINKS = VERIFIED (ExecutionDetail + Ops-Graph)
MACHINE_RUN_V1_E2E = CLOSED
Evidence = docs/qa/machine-run-shop-floor-ui/
Closure evidence = docs/qa/machine-run-ui-v1-closure/
Worklog = docs/worklog/realignment/2026-08-09_machine_run_shop_floor_ui_implementation.md
Closure worklog =
docs/worklog/realignment/2026-08-09_machine_run_ui_create_add_context_links_closure.md
Candidate/lookup worklog =
docs/worklog/realignment/2026-08-09_machine_run_candidate_discovery_and_task_lookup_read_api.md
```

---

## 26. Boundaries respected

```text
FRONTEND_CHANGED = YES (MachineRun shop-floor only)
QA_MUTATIONS = 0
PAUSE_RESUME = DEFERRED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
EMPLOYEE_MOBILE = NO CHANGE
NO_PUSH = YES
```
