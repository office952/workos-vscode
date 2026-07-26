# PROD-FLEX-COLLABORATION-PHASE-2 — Closure Audit

**Task:** PROD-FLEX-COLLABORATION-PHASE-2-CLOSURE-AND-PHASE-3-PLAN  
**Date:** 2026-07-16  
**Starting HEAD:** `17af5f6`  
**Mode:** PLAN / READ-ONLY — no code, DB, or runtime mutation  
**Declared prior verdict:** `PROD_FLEX_COLLABORATION_PHASE_2_COMPLETE` (implementation claim)  
**Closure verdict:** `PROD_FLEX_COLLABORATION_PHASE_2_CORRECTION_REQUIRED`

---

## Stage A summary

| Risk | Classification |
|------|----------------|
| A1 Completion → OPEN help | `COMPLETION_CLOSURE_PARTIAL` |
| A2 Cancel authority | `CANCEL_POLICY_CORRECTION_REQUIRED` |
| A3 Cross-process concurrency | `MULTIPROCESS_CORRECTION_REQUIRED` |

**Phase 2 final acceptance:** `PROD_FLEX_COLLABORATION_PHASE_2_CORRECTION_REQUIRED`

**Stage B (Phase 3 plan):** **NOT EXECUTED** — blocked until correction lands and re-closes.

Limitations that would be “document only” are **not** enough here: cancel authorization and helper-session multiprocess races violate authorization / data-integrity bars in the closure prompt.

---

## A1 — Completion closure

### Commands that close OPEN help

| Path | Closes OPEN help? |
|------|-------------------|
| Employee Mobile `complete_my_task` | Yes — after `end_task` |
| Operator `POST .../task-action` `action=complete` | Yes — after `end_task` |
| Helper session stop | No (correct) |
| Raw `ExecutionRealityService.end_task` / execution end | No |

### Answers

1. **Which commands close OPEN help?** Mobile complete + operator complete only.  
2. **Same transaction?** **No** — `end_task` commits, then `close_open_help_for_task` commits separately.  
3. **If close fails?** Exception bubbles; completion already committed.  
4. **Completion committed, help OPEN?** **Yes, possible.**  
5. **Retry idempotent?** Closer yes (OPEN-only). Mobile `already_completed` early return **skips** closer — retry gap.  
6. **Broadcast + targeted OPEN?** Yes — all `status=OPEN` for task.  
7. **Memberships preserved?** Yes — closer does not touch participants.  
8. **Why `op_completed=false` in runtime report?** Proof called `close_open_help_for_task` **directly**; never ran real completion. Operation stayed incomplete by design of the proof script.  
9. **Actual completion runtime?** **No** — unit/hook + direct service call only.  
10. **Wording vs proof?** **Both** — report overclaimed “completion closes help”; proof incomplete for the completion path.

**Classification:** `COMPLETION_CLOSURE_PARTIAL`  
Not a missing wire (B2 was fixed), but not proven atomic / not proven end-to-end.

---

## A2 — Cancel authority

### Effective policy today

| Surface | Route gate | Service check on actor |
|---------|------------|------------------------|
| Operator cancel | `execution.production_blueprint` + linked active employee | **None** — `actor_employee_id` unused in `_close_like` |
| Employee Mobile cancel | `require_employee_self_user` | **None** — same |

**Any authenticated actor who clears the route gate can cancel any OPEN help** (broadcast or targeted), including helpers and unrelated employees. Decline is correctly target-gated; cancel is not.

Memberships are correctly preserved on cancel (`test_h7`). Who-cancels was **never locked** in Phase 2 plan (only membership preservation was).

**Classification:** `CANCEL_POLICY_CORRECTION_REQUIRED`

**Recommended policy (for correction phase):** requester-only cancel on both APIs; targeted “no” stays decline; memberships stay; optional future operator override must be explicit (not silent open cancel).

---

## A3 — Cross-process concurrency

| Operation | Protection | Multiprocess |
|-----------|------------|--------------|
| Create duplicate OPEN | Partial unique (s58) + process asyncio lock + FOR UPDATE + IntegrityError | Safe **if s58 applied**; ORM/`create_all` **omits** unique |
| Accept broadcast/targeted | Process lock + FOR UPDATE + membership unique | Product OK; locks not cross-process |
| Membership join/leave | DB unique + process lock | Multiprocess-safe on uniqueness |
| Helper session start | App pre-check only; `start_task` **no** `for_update` | **Race → duplicate own active sessions** |
| Helper session stop | Pre-check + `end_task` `for_update` | Better than start; still races with start |
| Completion → close OPEN | No task lock / no FOR UPDATE on closer | Races with accept |

Process-local `_help_locks` / `_membership_locks` must **not** be claimed as multiprocess safety.

**Classification:** `MULTIPROCESS_CORRECTION_REQUIRED`

---

## Correction scope (one coherent phase)

See: `.compound-engineering/prod-flex-collaboration-phase-2-correction/plan.md`

Do **not** start Phase 3 UI until correction is implemented, retested, and re-closed.

---

## Forbidden confirmation (this audit)

No code changes, no DB writes, no runtime mutation of order 23099, no Phase 3 artifacts created.
