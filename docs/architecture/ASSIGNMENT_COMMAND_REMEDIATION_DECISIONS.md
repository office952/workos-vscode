# Assignment Command Remediation Decisions

**Status:** Owner decisions **RECORDED** (2026-08-04); Wave 6 hardening **implemented** under separate Owner GO  
**Wave 5 remains:** `FINALIZATION_WAVE_5 = PARTIAL_BLOCKED` (historical readiness audit)  
**Wave 6:** see `docs/worklog/realignment/2026-08-04_finalization_wave6_minimal_safe_assignment_command_hardening.md`  
**QA fixture assignment execution:** Wave 7 single-task proof **COMPLETED** (see Wave 7 worklog).  
**Wave 8:** auth fail-closed + observability + reassignment **policy audit** COMPLETE — see `ASSIGNMENT_OBSERVABILITY_AND_REASSIGNMENT_POLICY.md`.  
**Owner reassignment decisions:** **RECORDED** — see `CONTROLLED_PRE_START_REASSIGNMENT_DECISIONS.md` (implementation still **FALSE**).

**Sources:**

- `docs/worklog/realignment/2026-08-04_finalization_wave5_assignment_readiness_audit_only.md`
- `docs/worklog/realignment/2026-08-04_assignment_command_remediation_strategy_audit_only.md`
- `docs/worklog/realignment/2026-08-04_finalization_wave7_controlled_single_qa_employee_assignment_proof.md`
- `docs/worklog/realignment/2026-08-04_finalization_wave8_assignment_auth_observability_reassignment_policy.md`
- `docs/worklog/realignment/2026-08-04_controlled_pre_start_reassignment_owner_decisions.md`

**Canonical fixture after Wave 7:** order `880750` / plan `23` / 13 `operational_tasks[]` / **exactly 1** employee assignment (LED install → employee_id `7`).

**Owner gate (post Owner reassignment decisions):**

```text
ASSIGNMENT_IMPLEMENTATION_AUTHORIZED = TRUE   # Wave 6 hardening
ASSIGNMENT_EXECUTION_AUTHORIZED = PROOF_ONLY  # Wave 7 single QA assign done
SCHEMA_CHANGE_AUTHORIZED = FALSE
MIGRATION_AUTHORIZED = FALSE
REASSIGNMENT_AUTHORIZED = FALSE               # decisions recorded; build not authorized
LEGACY_REMOVAL_AUTHORIZED = FALSE
MOBILE_ASSIGNMENT_AUTHORIZED = FALSE
WAVE_6 = COMPLETED_PASS
WAVE_7 = COMPLETED_PASS
WAVE_8 = COMPLETED_PASS
OWNER_REASSIGNMENT_DECISIONS = RECORDED
WAVE_9 = NOT_AUTHORIZED
```

---

## Resulting architecture contract

```text
1. One canonical assignment service path
2. No caller-controlled validation bypass
3. Order/plan/task/employee scoped authorization
4. Eligibility and state revalidation inside the lock
5. Compare-and-set assignment semantics
6. Same-employee retry is idempotent
7. Different-employee retry is conflict
8. No last-write-wins
9. No silent reassignment
10. No Mobile activation
11. No schema change in first hardening build
12. Stop and return to Owner if schema is required
13. Assignment audit evidence must be consistent
14. No machine assignment, scheduling or sessions
```

Targets:

```text
PUBLIC_ASSIGNMENT_BYPASS = FORBIDDEN
LEGACY_COMPATIBILITY = CONTROLLED_ADAPTER_ONLY
AUTHORIZATION_SCOPE = permission + order + execution plan + operational task + employee context
```

---

## DEC-ASSIGN-01 — Legacy `controlled=false`

| Field | Value |
| ----- | ----- |
| Decision | **`CLOSE_EXTERNAL_BYPASS`** |
| Rationale | Request body must not disable DEC-015 / controlled revalidation; public bypass is a proven security blocker. |
| Accepted constraints | Public API forbids free `controlled=false`; no FE un-controlled mode; legacy must not skip DEC-015. |
| Rejected alternatives | Keep public optional bypass; “trust UI only”; silent last-write-wins via forced `allow_reassign`. |
| Implementation implications | Future hardening must reject or hard-gate public bypass **before** first authorized QA mutation; inventory consumers first. |
| Schema implications | None for this decision. |
| Authorization implications | Bypass cannot be a permission substitute. |
| Legacy implications | Code not deleted yet; `LEGACY_COMPATIBILITY = CONTROLLED_ADAPTER_ONLY` after inventory + separate GO for removal. |
| Test implications | Legacy tests that send `controlled=false` must migrate to canonical path or controlled adapter. |
| Owner gate | Implementation / removal not authorized here. |
| Reconsider when | Proven internal consumer needs an audited, non-public adapter with separate Owner GO. |

---

## DEC-ASSIGN-02 — Authorization scope

| Field | Value |
| ----- | ----- |
| Decision | **`REQUIRE_ORDER_PLAN_TASK_SCOPE`** |
| Rationale | Permission-wide assign enables soft IDOR across orders. |
| Accepted constraints | Backend must prove: authenticated actor + assign permission + order in scope + plan belongs to order + task belongs to plan + employee in permitted org context. |
| Rejected alternatives | UI-only scoping; permission-wide as sufficient. |
| Implementation implications | Future service/route must enforce scope server-side. |
| Schema implications | None required by this decision alone. |
| Authorization implications | Admin wildcard only if explicit, audited, and still bound to tenant/context. |
| Legacy implications | Callers assuming any-order assign under role alone will break until scoped. |
| Test implications | Cross-order / cross-plan / arbitrary task+employee negative cases required in future GO. |
| Owner gate | No auth redesign in this task. |
| Reconsider when | Multi-tenant model changes require stronger/weaker boundaries with new Owner GO. |

---

## DEC-ASSIGN-03 — Idempotency strategy

| Field | Value |
| ----- | ----- |
| Decision | **`STATE_CAS_FIRST`** |
| Rationale | First safe build can use embedded state CAS without new idempotency storage. |
| Accepted constraints | Unassigned+eligible → assign once; same employee retry → idempotent; different employee → conflict unless explicit reassignment contract; stale version → conflict, no overwrite. |
| Rejected alternatives | Last-write-wins; mandatory idempotency-key table in first build. |
| Implementation implications | Compare-and-set on assignment state (+ existing checks) under lock. |
| Schema implications | Prefer none; key storage deferred. |
| Authorization implications | Reassignment remains a separate authorized contract, not default. |
| Legacy implications | Legacy overwrite via forced `allow_reassign` incompatible with this policy. |
| Test implications | Same-employee retry, different-employee conflict, stale state conflict. |
| Owner gate | No storage implementation here. |
| Reconsider when | Distributed timeout/retry SLA proves CAS insufficient → re-evaluate idempotency key. |

---

## DEC-ASSIGN-04 — Schema changes

| Field | Value |
| ----- | ----- |
| Decision | **`NO_SCHEMA_CHANGE_FOR_FIRST_HARDENING_BUILD`** |
| Rationale | Prefer minimal hardening with existing plan/task locking and CAS. |
| Accepted constraints | First build uses locks, CAS, in-lock revalidation, conflict semantics, path consolidation. |
| Rejected alternatives | Invent assignment table/migration without proof that safety requires it. |
| Implementation implications | If hardening cannot prove safety without schema → `PARTIAL_BLOCKED` + `OWNER_DECISION_REQUIRED = SCHEMA_CHANGE`. |
| Schema implications | **Forbidden** until that stop condition. |
| Authorization implications | N/A. |
| Legacy implications | N/A. |
| Test implications | Prove safety without migrations where possible. |
| Owner gate | `SCHEMA_CHANGE_AUTHORIZED = FALSE` now. |
| Reconsider when | Implementation audit proves schema is necessary. |

---

## DEC-ASSIGN-05 — Persistence model

| Field | Value |
| ----- | ----- |
| Decision | **`KEEP_EMBEDDED_ASSIGNMENT_FOR_FIRST_HARDENING_BUILD`** |
| Rationale | Keep `assigned_employee_id` on `operational_tasks[]` for first hardening. |
| Accepted constraints | Embedded model for first build only; not declared final forever. |
| Rejected alternatives | Immediate separate assignment table without demonstrated need. |
| Implementation implications | Harden writers of `tasks_json` operational tasks. |
| Schema implications | No extension now. |
| Authorization implications | N/A. |
| Legacy implications | Consumers already reading embedded field remain compatible. |
| Test implications | Assert embed fields + no dual-write drift. |
| Owner gate | Separate table needs future Owner GO. |
| Reconsider when | History, multi-role assign, uniqueness, atomic audit, or distributed concurrency require it. |

---

## DEC-ASSIGN-06 — Audit / event atomicity

| Field | Value |
| ----- | ----- |
| Decision | **`AUDIT_REQUIRED`** |
| Rationale | Successful assignment must not be reported without consistent audit evidence. |
| Accepted constraints | Future build documents: what audit exists, when written, atomicity with assign, failure if audit write fails, whether assign-without-audit or audit-without-assign can exist. |
| Rejected alternatives | Success response with silent missing audit. |
| Implementation implications | Prefer all-or-nothing; if impossible without schema redesign → stop before claiming command safety verified. |
| Schema implications | May force stop under DEC-ASSIGN-04 if atomic audit needs new storage. |
| Authorization implications | Audit should record actor identity. |
| Legacy implications | Paths without audit remain non-compliant with target. |
| Test implications | Failure injection on audit write; no success without evidence. |
| Owner gate | No audit table invented here. |
| Reconsider when | Schema GO unlocks dedicated audit store. |

---

## DEC-ASSIGN-07 — Retry behavior

| Field | Value |
| ----- | ----- |
| Decision | **`DETERMINISTIC_RETRY`** |
| Rationale | Unknown response must not produce duplicate mutation or silent reassignment. |
| Accepted constraints | Same-employee retry → return canonical current state, no duplicate mutate; different employee → conflict; stale request → conflict with state/version details. |
| Rejected alternatives | Last-write-wins. |
| Implementation implications | Align with DEC-ASSIGN-03 CAS semantics. |
| Schema implications | None for first build. |
| Authorization implications | N/A. |
| Legacy implications | Forced reassign path conflicts with this policy. |
| Test implications | Timeout/retry simulations with mocks; conflict cases. |
| Owner gate | No runtime mutation to prove here. |
| Reconsider when | Distributed clients need idempotency keys (DEC-ASSIGN-03 revisit). |

---

## DEC-ASSIGN-08 — Legacy consumers

| Field | Value |
| ----- | ----- |
| Decision | **`INVENTORY_AND_MIGRATE`** |
| Rationale | Consumers must be identified, classified, migrated, tested; temporary bridge only if active and necessary. |
| Accepted constraints | Inventory → classify → migrate → test; controlled adapter only if required. |
| Rejected alternatives | Activate/expand Mobile claim or start_from_available; declare them safe now. |
| Implementation implications | Future consolidation includes Mobile paths in inventory; **no Mobile activation now**. |
| Schema implications | None. |
| Authorization implications | Migrated callers must meet DEC-ASSIGN-02. |
| Legacy implications | `Employee Mobile = FROZEN_FINAL_FINAL`; claim / start_from_available not authorized. |
| Test implications | Consumer inventory artifact in future GO; migrate off public bypass. |
| Owner gate | `MOBILE_ASSIGNMENT_AUTHORIZED = FALSE`; `LEGACY_REMOVAL_AUTHORIZED = FALSE`. |
| Reconsider when | Separate Mobile / legacy-removal Owner GO. |

---

## Dead pieces classification (record only — nothing removed)

| Piece | Class |
| ----- | ----- |
| Public `controlled=false` request option | `ACTIVE_LEGACY` + `BYPASSABLE` (target: FORBIDDEN) |
| Direct-service `assign_plan_task` without DEC-015 RM | `ACTIVE_LEGACY` + `BYPASSABLE` |
| Legacy assignment tests using `controlled=false` | `ACTIVE_LEGACY` |
| Ops-Graph / Operator assign UI callers (`controlled:true`) | `ACTIVE_CANONICAL` (UI default); public bypass still `BYPASSABLE` at API |
| Mobile claim path | `ACTIVE_LEGACY` + `BYPASSABLE` (frozen; not activated) |
| Mobile start_from_available path | `ACTIVE_LEGACY` + `BYPASSABLE` (frozen; not activated) |
| Controlled HTTP path (`controlled=true`) | `ACTIVE_CANONICAL` (policy CLOSED until hardening GO) |

```text
Dead pieces touched: NONE
Dead pieces removed: NONE
```

---

## Future candidate (not started)

```text
CONTROLLED_PRE_START_REASSIGNMENT_IMPLEMENTATION_READINESS_AUDIT
```

Owner DEC-REASSIGN-01…08 are **recorded**. Do not implement reassignment/unassignment until the readiness audit (persistence/history/permissions) and any required schema Owner GO complete.
