# BUILD_INTAKE_V4_STAGE_AUDIT_AND_REAL_TASK_CREATION_DECISION

## 1. Branch / HEAD / working tree

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD (local = remote) | `383112dc27151d4c0076ee33ff820d7903586eaa` |
| Audit type | **Read-only decision record** — no runtime mutations |

### Last 10 commits (V4 series on branch)

```txt
383112d feat(intake-v4): add order-bound task generation readiness guard
8539061 feat(intake-v4): add task generation dry-run contract for review step
1449fca feat(intake-v4): add TPL-VOLUMETRIC-LETTERS template option contract adapter
1234c7f feat(intake-v4): add read-only production handoff preview for review step
335f12f feat(intake-v4): improve sheet nesting material split by role and placement
98f1c88 fix(intake-v4): align material breakdown prices with inventory pricing BLK-18 bridge
77538e6 fix(intake-v4): fail-closed draft quote on analysis hash mismatch
4700e45 feat(intake-v4): add nesting-preferred quote material costing
c6bf6a7 test(intake-v4): add commercial handoff e2e and fix quote pytest seed
f82bf6a feat(intake-v4): lock analyzer boundary and add pilot e2e
```

### Git status (grouped)

| Group | Status |
|-------|--------|
| **Committed V4 (remote)** | Analyzer → readiness chain through `383112d` |
| **Dirty V2/V3** | `intake-v3/*`, `intake_v3_*` services/tests, `AuthContext`, `WorkIntakeV2/*` — **not touched by this audit** |
| **Untracked** | `docs/audit/`, `BUILD_INTAKE_V4_ATOMS_*`, operator-workspace components, `shared/` |
| **tmp/** | Local scripts only — **not touched** |
| **E2E off-scope** | `intake-v4-pbl-complex-desktop.spec.ts`, `intake-v4-svg-open-after-bootstrap.spec.ts` — **not touched** |

**Audit confirmation:** this build created/edited **only this QA doc**. No commits, no push, no runtime code changes.

---

## 2. V4 chain map

| Stage | What it does | Implementation | Data produced | Blockers | Read-only? | Could become real mutation | Risks |
|-------|--------------|----------------|---------------|----------|------------|---------------------------|-------|
| **SVG Analyzer** | Upload + client-side parse; layer discovery | `POST …/svg`; frontend analyzer; `intake_v4_analysis_boundary_service` | `svg_source`, `svg_analysis_json`, `path_geometry_summary`, `layer_role_setup` draft | Missing/invalid SVG, parse failures, hash sync | Upload writes workspace payload | Re-upload invalidates downstream snapshots | Stale analysis vs quote snapshot |
| **analysis-bundle** | Persist analyzed bundle + hash | `PUT …/analysis-bundle` | Full analysis bundle, `file_hash` | Boundary blockers, incomplete layers | **Write** (workspace) | Snapshot refresh on quote | Hash mismatch vs linked quote |
| **Layer roles / finish setup** | Operator confirms roles + finishes | `PUT …/layer-roles`, `PUT …/finish-setup` | `layer_role_setup`, `finish_setup` | Incomplete roles, unconfirmed finish, artwork undecided | **Write** (workspace) | Drives pricing + production preview | Finish change → fingerprint change |
| **Material breakdown** | Nesting-aware material quantities + BLK-18 bridge | `GET …/material-breakdown`; `intake_v4_material_breakdown_service` | Material lines, totals, costing policy metadata | Missing nesting, missing pricing registry rows | **Read-only GET** | Could feed stock reservation (out of scope) | Wrong material split if nesting stale |
| **Pricing BLK-18** | `quote_input_payload` preview for QuoteWizard | `GET …/pricing-input-preview`; `intake_v4_pricing_input_service` | `quote_input_payload`, operation flags, finish summary | Template out of scope, geometry missing | **Read-only GET** | QuoteWizard commercial pricing (separate module) | Not automatic final price |
| **Commercial draft quote** | Guarded draft quote creation | `POST …/create-draft-quote`; `intake_v4_commercial_quote_service` | `Quotes` row, `intake_code=IV4-{ws}`, `intake_v4_linkage_v1` snapshot | Handoff blockers, duplicate quote, hash mismatch | **Write** (quote only) | Accept/convert (not implemented for V4) | Draft quote without pricing review completion path |
| **QuoteWizard** | Human pricing review + commercial spine | Frontend `IntakeV4ConfirmStep` → navigate to quote detail | Priced line items (manual), quote status in generic Quotes UI | Operator pricing, commercial policy | **External** to V4 router | Quote status transitions (generic) | No V4-specific accept/convert guard |
| **Production handoff preview** | Material jobs + operation groups preview | `GET …/production-handoff-preview` | Handoff jobs, operation groups, warnings | Analysis boundary, material breakdown blockers | **Read-only GET** | Source for task dry-run | Catalog doc codes ≠ dossier keys 1:1 |
| **Task generation dry-run** | Task candidates + deps + idempotency plan | `GET …/task-generation-dry-run` | `task_candidates`, `idempotency_plan`, `source_fingerprint` | Always `can_generate_tasks=false`; `dry_run_only_no_order` | **Read-only GET** | **Future** execution_plan write | Schema ≠ ExecutionPlanService output |
| **Order-bound readiness** | Quote/order/commercial/dry-run gate | `GET …/order-bound-task-readiness` | `can_generate_real_tasks=false`, blockers, future contract | quote_missing, order_missing, pricing review, owner_confirmation | **Read-only GET** | Enables next build decision only | False confidence if order path missing |

---

## 3. Quote → Order audit

### Findings

| # | Question | Answer |
|---|----------|--------|
| 1 | Draft quote from V4 | `POST /api/v1/intake-v4/workspaces/{id}/create-draft-quote` → `create_guarded_draft_quote_from_intake_v4_workspace` |
| 2 | V4 linkage storage | `quotes.intake_code = IV4-{workspace_id}`; `notes.intake_v4_linkage_v1` with `snapshot`, `quote_input_payload`, `requires_pricing_review: true` |
| 3 | V4 accept flow | **Does not exist.** IV3 accept (`accept_iv3_priced_draft_*`) rejects `NOT_IV3_QUOTE` for `IV4-*` intake codes |
| 4 | V4 convert-to-order flow | **Does not exist.** IV3 convert requires `intake_v3_linkage_v1` + `IV3-*` prefix |
| 5 | Can V4 reach real Order today? | **No end-to-end V4 path.** Operator can create draft quote only; no V4 pricing-review completion, accept, or convert APIs |
| 6 | Order snapshot fidelity | IV3 convert freezes `snapshot_line_items` on Order — **no V4 equivalent**; V4 snapshot lives in quote notes only until a V4 convert build exists |
| 7 | Order-bound readiness finds Order? | Yes **if** an Order exists with matching `quote_id` (generic lookup via `check_existing_order_for_iv3_quote`); in normal V4 flow **no Order is created** |
| 8 | Safe target Order for V4 task gen? | **No** — readiness always reports `order_missing` in typical V4-only flow |

### Mandatory conclusion

```txt
V4 NU are încă flow complet quote → order.
```

V4 are: **workspace → draft quote → QuoteWizard (manual pricing)**.  
V4 nu are: **pricing review completion (V4-native) → accept → convert → locked Order with frozen V4 snapshot**.

---

## 4. ExecutionPlan / tasks_json audit

| # | Topic | Finding |
|---|-------|---------|
| 1 | What is ExecutionPlan? | ORM row per order: planned production tasks (write-once from order snapshot) |
| 2 | Definition | `backend/models/execution_plan.py` |
| 3 | `tasks_json` | JSON **string** array of task dicts on `execution_plan.tasks_json` |
| 4 | Who writes today? | `POST /api/v1/execution/plan/from-order/{order_id}` → `ExecutionPlanService.from_order(order)` → persist row. Also assignment service **mutates** `tasks_json` for `assigned_employee_id` |
| 5 | Real task structure | `task_id`, `name`/`display_name`, `layer_id`, `process_type`, `machine_type`, `estimated_time_minutes`, `quantity`, optional `process_id`, `instructions`, `documents`, `assigned_employee_id` — derived from **order `snapshot_line_items` product_definition**, not V4 material jobs |
| 6 | Idempotency / duplicate | Router returns **409** if plan exists; gate writer evaluates `plan_already_exists`; **no** V4 idempotency_key storage |
| 7 | Audit log | HTTP access logs + `prepared_by_user_id` on plan row; **no** dedicated intake_v4 task generation audit table |
| 8 | Owner confirmation | Execution plan generation requires permission `execution.plan_generate`; **no** Intake V4 owner confirmation wired to plan write |
| 9 | Rollback / regeneration | Write-once invariant; regeneration not designed — would need explicit new build/policy |
| 10 | Employee Mobile | `employee_mobile_tasks_service` reads `execution_plan.tasks_json`; requires `task_id`, `process_id`, `process_type` — **V4 dry-run candidates use different keys** (`task_key`, `operation_key`, `idempotency_key`) |
| 11 | Required fields for production usefulness | `task_id`, display name, process routing fields, time estimate, assignment — V4 candidates **do not match** this schema today |

### Mandatory conclusion

```txt
Este NESIGUR să scriem în execution_plan.tasks_json din Intake V4 dry-run acum.
```

**Why:**

1. **No V4 Order target** in normal flow.  
2. **Schema mismatch** — V4 dry-run ≠ `ExecutionPlanService` / Employee Mobile contract.  
3. **No idempotency persistence** — dry-run keys are preview-only.  
4. **No owner approval** before production write.  
5. Existing writer reads **frozen order snapshot**, not workspace payload — bypass would break execution layer invariants.

---

## 5. Owner / operator approval audit

| Capability | Exists? | Where |
|------------|---------|-------|
| Owner confirmation for draft quote | Partial | `IntakeV4ConfirmStep`: checkboxes `confirm_create_draft_only`, `confirm_no_order`, `confirm_no_execution`, `confirm_no_inventory` + `decision_reason` |
| Production manager confirmation | **No** | — |
| Acknowledge blockers | Display only | Review panels (handoff, dry-run, readiness) — no persist |
| Accept material warnings | **No** persisted ack | — |
| Acknowledge provisional tasks | **No** | — |
| Create production tasks button | **No** | `future_generation_contract.next_action_enabled=false` |
| Disable button when blockers | N/A | No button |
| Audit confirmation | Partial | Quote snapshot `owner_decision` on draft create only |

### Mandatory conclusion

```txt
NU avem owner approval flow suficient pentru real task creation.
```

Readiness marks `owner_confirmation_required=true` as a **blocker marker only** — no API/UI to record approval for production task write.

---

## 6. Idempotency / duplicate prevention audit

| Mechanism | Dry-run today | Real write needs |
|-----------|---------------|------------------|
| `idempotency_key` | `intake-v4:{ws}:{template}:{task_key}` — **excludes analysis hash** (anti double-click) | DB uniqueness constraint or compare-before-insert per order |
| `source_fingerprint` | Hash of analysis + finish + contract version — **signals regeneration** | Stored last-write fingerprint on order/plan; block or require explicit regen |
| Existing plan detection | Readiness checks `ExecutionPlan` count | Enforced at write (409 exists in execution router) |
| Duplicate task prevention | Policy string only: `do_not_create_duplicate; require explicit regeneration` | Task-level dedupe by `task_id` / idempotency key |
| Reupload regeneration | Fingerprint changes → manual interpretation | Invalidation policy + UI |
| Finish change | Fingerprint changes | Same |
| Order change | Not modeled | Re-bind to order snapshot version |
| Double-click | Key stable per task_key | Server-side idempotency token |
| Tasks already exist | Readiness blocker `order_already_has_execution_plan` | 409 on write |

### Mandatory conclusion — minimum before real creation

1. **V4-native idempotency store** (order_id + idempotency_key + source_fingerprint + created_at).  
2. **Explicit regeneration contract** (when fingerprint changes after reupload/finish).  
3. **Adapter** V4 task candidate → ExecutionPlan task dict (`task_id`, `process_type`, etc.).  
4. **Single-flight / 409** on plan row (reuse execution gate).  
5. **Owner confirmation record** bound to fingerprint at write time.

---

## 7. Template contract readiness

| Topic | Status |
|-------|--------|
| Template-backed candidates | Most material-job seeds map to dossier `operation_key` when handoff is complete; tests expect keys like `cnc_face_cutting`, `return_side_forming`, `led_module_install` |
| Provisional candidates | `production_preview_not_template_backed` warning propagates; candidates with missing dossier mapping marked `provisional=true` |
| Critical blockers | Only `unsupported_template` is blocking for non-pilot templates; pilot template uses **warnings** for gaps |
| vs TPL-VOLUMETRIC-LETTERS | Partial alignment: face/return finish partial maps, mounting not in V4 form, assembly `assembly_letters` partial, catalog doc codes ≠ dossier keys |
| Operation groups vs dossier keys | Handoff uses catalog doc codes; dry-run maps via `CATALOG_TO_DOSSIER_OPERATION` adapter |
| Assembly provisional | `assembly_letters` marked partial in canonical matrix |
| Oracal multi-color | Warning when multiple letter groups with different finishes |
| LED pitch divergence | `led_strip` not dossier-backed; multi-PSU array vs single `selected_psu_watts` |
| Mounting / back bevel gaps | `mounting_system` not captured in V4 form; `back_bevel_enabled` dossier variant not wired |

### Mandatory conclusion

```txt
Template contract NU este suficient pentru task generation real fără alignment pack suplimentar.
```

Usable for **preview and dry-run**; not sufficient as sole source of truth for production-grade `tasks_json` without schema adapter + closing partial/provisional gaps.

---

## 8. Risk matrix

| # | Risk | Severity | Current guard | Missing guard | Recommended next build |
|---|------|----------|---------------|---------------|------------------------|
| 1 | Duplicate tasks | **High** | Readiness `order_already_has_execution_plan`; execution 409 | V4 write path + task-level idempotency store | `BUILD_INTAKE_V4_CONTROLLED_EXECUTION_PLAN_WRITE_PACK` (after A) |
| 2 | Tasks without Order | **Critical** | Readiness `order_missing`; dry-run `dry_run_only_no_order` | V4 convert-to-order | **`BUILD_INTAKE_V4_QUOTE_TO_ORDER_AND_OWNER_APPROVAL_PACK`** |
| 3 | Tasks on draft quote | **Critical** | `quote_not_accepted`, `quote_status_not_ready`, `requires_pricing_review` | V4 pricing review + accept APIs | **Option A** |
| 4 | Stale analysis | **High** | Hash sync blockers, `quote_snapshot_hash_mismatch` | Order snapshot bind + regen policy | Option A + idempotency pack |
| 5 | Missing template mapping | **High** | Provisional flags, warnings | Block write if any provisional; alignment pack | **`BUILD_TPL_VOLUMETRIC_OPERATION_KEYS_ALIGNMENT_PACK`** |
| 6 | No pricing review | **Critical** | `requires_pricing_review` blocker | V4 pricing review completion (not IV3) | **Option A** |
| 7 | No owner approval | **Critical** | Marker blocker only | Persisted approval UI + API | **Option A** |
| 8 | No assignment | **Medium** | N/A at preview | Assignment after plan write (existing PATCH) | Post-write operational step |
| 9 | Wrong materials | **Medium** | Material breakdown + handoff preview | Order snapshot material truth at convert | Option A |
| 10 | Invisible in Employee Mobile | **Critical** | N/A | Schema adapter to plan task shape | Controlled write pack |
| 11 | No audit trail | **Medium** | `prepared_by_user_id` on plan | V4 generation audit event | Controlled write pack |
| 12 | No invalidation/regen | **High** | `source_fingerprint` in dry-run only | Stored fingerprint + regen workflow | Idempotency pack |

---

## 9. Decision

### Selected option: **Option A**

```txt
Next build: BUILD_INTAKE_V4_QUOTE_TO_ORDER_AND_OWNER_APPROVAL_PACK
```

### Secondary (before controlled write): **Option C**

```txt
BUILD_TPL_VOLUMETRIC_OPERATION_KEYS_ALIGNMENT_PACK
```

Run **after or in parallel with A**, before any `execution_plan.tasks_json` write.

### Not selected now

| Option | Why not |
|--------|---------|
| **B** — Controlled execution plan write | Preconditions missing: no V4 Order, no approval, schema mismatch, no idempotency store |
| **D** — Live E2E only | Useful validation layer but does not remove structural blockers |

---

## 10. Why we do NOT do real task generation yet

1. **V4 has no quote → order commercial spine** — IV3 accept/convert/pricing-review APIs reject `IV4-*` quotes.  
2. **No persisted owner approval** for production task creation.  
3. **Dry-run task shape ≠ execution_plan.tasks_json shape** — Employee Mobile would not consume V4 candidates as-is.  
4. **Idempotency is preview-only** — no storage, no regeneration policy.  
5. **Template contract has provisional/partial mappings** — unsafe as production source without alignment.  
6. **Existing execution writer** is order-snapshot-bound — Intake V4 must freeze snapshot on Order first, not skip straight from workspace.

---

## 11. Conditions that would change decision to Option B

All must be true:

1. V4 **pricing review completion** + **accept** + **guarded convert to order** with frozen snapshot on Order (`workspace_id`, `analysis_hash`, `quote_input_payload`, template context).  
2. **Owner/production confirmation** persisted and bound to readiness fingerprint.  
3. **Task schema adapter** V4 candidate → plan task dict validated against Employee Mobile reader.  
4. **Idempotency store** + regeneration rules implemented and tested.  
5. Template contract: **zero blocking provisional tasks** for target workspace profile (or explicit operator ack with audit).  
6. Readiness endpoint returns `can_generate_real_tasks=true` only when all above satisfied (still separate write build).

---

## 12. Tests

No tests run for this audit/decision build (read-only doc).  
Prior build verification remains valid:

```powershell
pytest tests/test_intake_v4_order_bound_task_readiness.py -q   # 18 passed
pytest tests/test_intake_v4_task_generation_dry_run.py tests/test_intake_v4_production_handoff_preview.py -q  # 17 passed
```

Combined pytest module run may hit module-scope event-loop fixture conflict — **harness issue, not build failure**.

---

## 13. Result

| Criterion | Status |
|-----------|--------|
| No runtime mutations | **PASS** |
| No real tasks / execution plan writes | **PASS** |
| Clear readiness answer | **PASS** — **NOT ready** for real task creation |
| Real blockers identified | **PASS** |
| Next build recommended | **PASS** — Option A (+ C before B) |
| Risks documented | **PASS** |
| V2/V3 dirty untouched | **PASS** |

### **Verdict: PASS** (audit/decision build)

---

## 14. Commit recommendation

Recommend committing **only this doc** after owner review:

```txt
docs(qa): add Intake V4 stage audit and real task creation decision
```

No push until explicitly approved.
