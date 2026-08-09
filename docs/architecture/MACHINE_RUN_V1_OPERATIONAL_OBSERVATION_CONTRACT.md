# MACHINE_RUN V1 — Operational Observation Contract

**Status:** FINALIZED · manual observation only  
**Date:** 2026-08-09  
**Mode:** `HARDEN_AND_OBSERVE`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_V1_HARDEN_AND_OBSERVE_BASELINE`  
**Worklog:** `docs/worklog/realignment/2026-08-09_machine_run_v1_harden_and_observe_baseline.md`

No telemetry framework. No analytics tables. No silent retries. No auto-release.  
Evidence sources: workshop notes · owner feedback · existing audit/history · bounded QA notes.

---

## V1 frozen scope (included)

```text
CREATE · candidate discovery · multi-plan/multi-order grouping
ADD · REMOVE (HELD)
CONFIRM · RESCHEDULE · START · COMPLETE · RELEASE · CANCEL
list · detail
task → active MachineRun lookup
ExecutionDetail + Ops-Graph context links
read / manage / execute separation
light/dark operator UI
```

## Explicitly not V1

```text
PAUSE · RESUME
post-start reassignment / handoff / transfer / takeover  (= reassignment Phase E)
Employee Session coupling · auto task-state propagation
auto-batch · machine recommendation · Capacity activation
machine telemetry · Utilaje MachineRun home · Employee Mobile MachineRun controls
```

---

## Terminology (resolved)

| Name | Canonical meaning |
| ---- | ----------------- |
| **Reassignment Phase B** | Pre-start reassignment/unassignment backend — Wave 11 **VERIFIED** |
| **Reassignment Phase E** | Post-start operational transfer — **NOT_AUTHORIZED** |
| **MachineRun “PHASE_B” (docs)** | Future MachineRun→R6 guard coupling for reassignment CLEAR — **NOT_AUTHORIZED**; **not** post-start transfer |

```text
POST_START_TRANSFER_CANONICAL_PHASE = REASSIGNMENT_PHASE_E
TERMINOLOGY_DRIFT = YES
  (some MachineRun docs say “Phase B transfer/handoff” — incorrect synonym for Phase E)
```

Do not rename broad architecture in this baseline; use the table above in new writing.

---

## What to observe

### A. CREATE / grouping

| Signal | Why | Informs |
| ------ | --- | ------- |
| How often runs are created | Adoption | whether V1 is used |
| Multi-plan grouping frequency | Core value of MachineRun | candidate UX sufficiency |
| Unexpected empty candidate list | Discovery/eligibility friction | candidate UX — not auto-batch |
| Operator cannot find expected task | Same | eligibility honesty vs UX |

**Does not justify:** AI ranking, auto-grouping, machine recommendation.

### B. RELEASE friction

| Signal | Why | Informs |
| ------ | --- | ------- |
| COMPLETED left RESERVED | Commitment not released | RELEASE UX |
| Forgotten RELEASE | Usability | reminder / attention indicator (later) |
| Time COMPLETE → RELEASE | Workflow clarity | whether explicit RELEASE is understood |

**Does not justify:** auto-RELEASE without evidence.

Possible *future* options only if evidence appears: inline reminder · completed-reserved attention · workflow change.

### C. Temporary stops

| Signal | Why | Informs |
| ------ | --- | ------- |
| Stop while run stays RUNNING | Reality vs status | PAUSE/RESUME |
| Reason / duration / workaround | Severity | same |
| Early COMPLETE used instead | Acceptable? | same |

**PAUSE/RESUME candidate only when:**

```text
temporary stops occur repeatedly
AND leaving RUNNING materially misrepresents reality
AND early COMPLETE is not acceptable
```

Otherwise: `PAUSE_RESUME = KEEP_DEFERRED`.

### D. Employee / operator change

| Signal | Why | Informs |
| ------ | --- | ------- |
| Who operates machine during RUNNING | Labor vs machine clocks | session relation |
| Whether assignment/session already handles it | Existing systems enough? | coupling need |

**Does not justify:** MachineRun START → auto start employee session.

Coupling candidate only when separate systems cannot represent machine + labor provenance correctly.

### E. Post-start transfer

| Signal | Why | Informs |
| ------ | --- | ------- |
| Need to reassign after start | Frequency / blocker | reopen Phase E? |
| Workaround used | Severity | same |

**Candidate only when:**

```text
real responsibilities need transfer after start
AND pre-start-only policy blocks normal work
AND ownership boundary can be defined safely
```

Otherwise: `POST_START_TRANSFER = KEEP_DEFERRED` (canonical phase = **E**).

### F. CAS / concurrency

| Signal | Why | Informs |
| ------ | --- | ------- |
| `cas_stale` frequency | Contention | UX refresh adequacy |
| Which actions | Hot spots | same |

**Does not justify:** silent mutation retries.

---

## Bulk lookup watch

Current accepted pattern: one `GET …/by-task` per unique `(plan_id, task_key)` with page cache (~1–20 tasks typical).

```text
bulk lookup = LATER
if actual plan sizes materially increase
or browser request volume becomes problematic
```

No invented numeric threshold without evidence.

---

## Observation exit

```text
OBSERVATION_EXIT =
owner reviews enough real workshop evidence
to decide whether a concrete operational blocker exists
```

When reviewing, compare again:

```text
PAUSE_RESUME
POST_START_TRANSFER   (Phase E)
EMPLOYEE_SESSION_RELATION
NO_CHANGE             ← default until evidence
```

```text
NEXT_FEATURE_DOMAIN = UNSELECTED
NEXT_TASK = NOT_AUTHORIZED
```
