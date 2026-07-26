# WorkOS E2E — Implementation Operating Model

**Task:** `WORKOS_E2E_CONTROLLED_IMPLEMENTATION_ORCHESTRATION_V1`  
**Program:** `WORKOS_E2E_MASTER_ALIGNMENT_AND_FINALIZATION_V1`  
**Model baseline HEAD:** `fe6c6f7` (when model was accepted)  
**Living phase / Accepted HEAD:** `WORKOS_E2E_STATUS.md` (may show hold lifted and waves closed)  
**Canonical root:** `docs/master/workos-e2e/`  
**Figma MASTER:** `911Q6oRKcEursrRoT4Qj0h` nodes `14:2`–`14:15`  
**Verdict at model creation:** `WORKOS_E2E_IMPLEMENTATION_MODEL_READY_FOR_WAVE_1`  
**B2:** Outside Important Documents unless owner promotes.

This document is the **execution discipline contract** for Waves 1–7 (coordinator, lanes, gates). It does not replace living STATUS for which wave is open. Where lane reservations conflict with later STATUS closures, STATUS + DECISION_LOG win for progress; this model still governs how new lanes may open.

---

## 1. Implementation principles

1. **One connected truth** — A change is incomplete until downstream consumers are proven, not merely until local tests pass.
2. **Serialize on shared spine** — Files, reducers, and contract surfaces that define the same canonical truth are single-lane unless independence is demonstrated in writing.
3. **Coordinator owns integration** — Subagents may investigate or implement reserved lanes; they may not redefine architecture, wave order, or canonical ownership.
4. **No silent compatibility** — Temporary aliases, badges, fallbacks, and diagnostics require a registered temporary-debt record with removal task and test.
5. **No audit sprawl** — Routine work updates status, issues, worklog, and task evidence only. New general audits require owner GO (see §15).
6. **Contradiction stops the lane** — If runtime/code contradicts canonical docs, record the contradiction and halt affected work until owner truth is established.
7. **Wave gates are explicit** — Task PASS does not open the next wave. Only the cross-wave opening gate does.

---

## 2. Wave coordinator

| Role | Owner | Responsibilities |
|------|-------|------------------|
| **Wave Coordinator** | Active Cursor session (parent agent) | Active-wave truth, lane reservations, overlap decisions, merge integration, regression orchestration, canonical status, wave closure |
| **Lane worker** | Subagent or same session scoped task | Implement or investigate within reservation only |
| **Owner** | Human | P-001/P-003, D-010, wave-opening GO, contradiction resolution |

**Coordinator MUST:**

- Maintain the resume block (§14) at start and end of every session
- Approve or deny parallel lanes using §3 criteria
- Run wave integration gate before marking wave complete
- Reject commits that introduce unregistered temporary debt
- Update `WORKOS_E2E_STATUS.md` and issue registry on every task closure

**Coordinator MUST NOT:**

- Allow two lanes to edit the same reserved file without explicit serialization
- Declare wave complete on task tests alone
- Create new master documents or audit folders during routine implementation

---

## 3. Controlled parallelism

A lane may run **in parallel** only when independence is demonstrated across **all** of:

| Dimension | Independence test |
|-----------|-------------------|
| Canonical truth | Different truth owner or read-only consumer |
| Files | No overlap on write paths |
| Reducers / state | No shared derive function or workspace payload field |
| Schemas | No same Pydantic model or TS contract type |
| API contracts | No same router response shape |
| State transitions | No same status enum derive path |
| Tests | No same fixture mutation or shared snapshot file |
| Runtime records | No same workspace/request fixture ID during proof |
| Figma surfaces | No same MASTER page under edit |

If any dimension fails → **serialize**.

**Default for WorkOS E2E:** Waves 1–5 are **spine-serial** with narrow parallel exceptions documented per wave.

---

## 4. Reservation model

Before a lane starts, the coordinator publishes a **Lane Reservation** in the task worklog:

```yaml
lane_id: W1-L-SPINE
wave: 1
systems: [Intake V6, FormSystem capture]
canonical_truths: [mounting_solution, readiness_status, capture_blockers, handoff_policy]
contracts: [workspace GET/PATCH, runtime capture read model, pricing preview handoff]
files_write:
  - backend/services/form_system_runtime_capture_read_model_service.py
  - backend/services/form_system_contract_backbone_service.py
  - backend/services/intake_v6_workspace_service.py
  - backend/services/intake_v6_canonical_readiness_service.py
  - frontend/src/lib/intakeV6/intakeV4Readiness.ts
  - frontend/src/components/workos/intake-v6/*blocker*
tests_write:
  - backend/tests/test_form_system_contract_backbone.py
  - backend/tests/test_form_system_contract_mapping_adapter.py
  - frontend/src/components/workos/intake-v6/IntakeV6ReviewOperatorBlockerBanner.test.tsx
start_HEAD: fe6c6f7
integration_point: W1-INT-01
collision_risk: HIGH
parallel_allowed: false
```

**Conflict prevention:**

- Second lane requesting overlapping `files_write` → blocked until first lane merges and releases reservation
- Coordinator maintains reservations in session resume block
- Integration task owns final merge and regression at `integration_point`

---

## 5. Three-level gates

### Level 1 — Task gate (lane closure)

Required for every implementation task:

- Targeted pytest and/or Vitest per task contract
- Runtime proof on declared routes (screenshots for UI)
- Issue registry updated (TE2E IDs)
- `WORKOS_E2E_STATUS.md` active task / next task updated
- Isolated commit at lane `start_HEAD` descendant
- Temporary debt register empty or all items documented
- Task worklog complete (before/during/after sections)

**Task PASS does not imply wave open.**

### Level 2 — Wave integration gate

Run once per wave before wave closure:

| Wave | Integration gate |
|------|------------------|
| 1 | IR-MRJS4VIK workspace step 2–3: zero false ready; mounting_solution gate; capture blockers ⊆ readiness; handoff preview merges policy; screenshots |
| 2 | PD preview + aggregate GET consistent; composition Cases A–D deterministic tests |
| 3 | Single cost authority recorded (D-010); pricing registry trace |
| 4 | Quote create dry-run; order snapshot byte-stable |
| 5 | Execution tasks from frozen snapshot only |
| 6 | Operator UI audit vs MASTER 07/08 |
| 7 | Full same-scenario spine + owner sign-off |

### Level 3 — Cross-wave opening gate

Next wave opens only when:

- Prior wave integration gate PASS
- `WORKOS_E2E_STATUS.md` records wave closure
- No open P1 issues owned by the prior wave (or owner explicit accept)
- Owner decision gates satisfied (e.g. D-010 before Wave 4 cost-dependent work)

**Wave 2 opening gate (explicit):** Intake handoff safe — see §11.

---

## 6. Regression ownership map

| Canonical truth | Owner | Direct consumers | Indirect consumers | Tests | Runtime routes | Visual evidence | Freeze check |
|-----------------|-------|------------------|--------------------|-------|----------------|-----------------|--------------|
| `mounting_solution` | Intake finish_setup | FormSystem capture, PD composition, Aggregate | Cost, Offer scope | `test_form_system_contract_backbone.py`, composition tests | Intake step 2 | Step 2 screenshot | N/A until Order |
| `readiness_status` | Intake workspace derive | UI badges, handoff CTA | Offer policy, quotes list | workspace persistence tests, Vitest readiness | step 2–3 | Step 3 confirm | Offer accept |
| `capture blockers` | FormSystem read model | Readiness merge, handoff | Pricing preview | mapping adapter tests | capture API | Step 2 rail | handoff |
| `finish_setup` fields | Intake finish | Capture, PD, Aggregate | Cost BOM | finish truth tests | step 2 | finish panel | Order snapshot |
| `product graph` | PD builder | Aggregate | Cost, Offer, Execution | composition contract tests | PD preview API | PD surface | Order snapshot v2 |
| `commercial price` | Calcul (D-010 TBD) | Offer | Order freeze | cost trace tests | quote wizard | Offer totals | snapshot immutable |
| `order snapshot` | Order service | Execution plan | Reconciliation | snapshot immutability | order view | order page | PATCH rejected |
| `execution tasks` | Plan compiler | Shop floor | Reconciliation | execution tests | `/execution` | board | frozen graph |

**Downstream regression owner:** Wave Coordinator runs consumer proofs listed in the active wave integration gate. Lane worker proves direct owner tests only.

---

## 7. Temporary-debt control

Any temporary warning, badge, fallback, compatibility alias, feature flag, or diagnostic surface **requires**:

| Field | Required |
|-------|----------|
| `debt_id` | TD-### |
| owner | system |
| reason | TE2E or defect ID |
| creation_task | W*-T* |
| removal_condition | measurable |
| removal_task | W*-T* |
| test | proves removal |
| deadline_gate | wave or task |

**Forbidden without registration:** hiding blockers in UI only, dual-path cost authority, `support_type` fallback when `mounting_solution` is canonical (D-005).

Wave 6 owns removal of TE2E-005, 020, 021 diagnostics — not Wave 1 badge hiding.

---

## 8. Task lifecycle contract

Every implementation task worklog MUST contain:

### Before work

- canonical owner, root cause, input/output contract
- upstream dependencies, downstream consumers
- touched states, collision risk, alternatives, chosen rationale
- lane reservation YAML

### During work

- unexpected repository truth, scope changes, contradictions
- temporary compatibility introduced (TD-###)
- tests added, runtime behavior notes

### After work

- exact truth changed, files touched, tests run
- runtime evidence, downstream regression result
- screenshots (UI), issue updates, status update
- isolated commit SHA, remaining risk, next allowed action

---

## 9. Wave 1 — Deep orchestration (derived from code, not copied)

### 9.1 Root-cause clustering

| Cluster | Issues | Shared spine | Shared files |
|---------|--------|--------------|--------------|
| **A — Readiness truth spine** | TE2E-001, 002, 014, 015 | `mounting_solution` vs `support_type`; `_derive_readiness_status` ignores capture; `merge_policy_findings` unwired | `intake_v6_workspace_service.py`, `form_system_runtime_capture_read_model_service.py`, `form_system_contract_backbone_service.py`, `intake_v6_canonical_readiness_service.py`, handoff callers, frontend readiness/blocker |
| **B — Finish persistence** | TE2E-003 | `finish_setup` write path vs capture overlay | finish save services, capture FIELD_SPECS |
| **C — Cant/return contract** | TE2E-006 | return/cant truth mappers | `returnCantTruthFields*`, finish_setup |
| **D — Vector edge** | TE2E-007 | analyzer edge case | isolated analyzer tests |

**Symptoms exposed by A (not separate root causes):** false ready badge, SUPPORT_TYPE with ACM saved, handoff confidence, policy banner inputs (TE2E-005 is Wave 6 surface symptom).

### 9.2 Serialization order (implementation)

```
W1-INT-00  Orchestration hold lift + reservation publish
    ↓
W1-L-SPINE  Canonical readiness truth spine (SERIAL — one lane)
    ↓
W1-INT-01   Wave 1 spine integration proof
    ↓
W1-L-FINISH Finish truth persistence (SERIAL — shares finish_setup + capture)
    ↓
W1-L-CANT   Cant/return contract (SERIAL — shares finish_setup)
    ↓
W1-INT-02   Wave 1 integration gate (full)
    ↓
W1-L-VECTOR Vector analyzer edge (may parallel ONLY after W1-INT-02 if files independent)
```

### 9.3 Parallel lanes in Wave 1

| Lane | Parallel? | Condition |
|------|-----------|-----------|
| W1-L-SPINE | **NO** | HIGH collision — core derive + capture |
| W1-L-FINISH | **NO** | After spine — shares finish_setup |
| W1-L-CANT | **NO** | After finish — shares finish_setup |
| W1-L-VECTOR | **MAYBE** | Only after W1-INT-02; read-only analysis may run during spine |
| W1-L-TESTS-DRAFT | **MAYBE** | Coordinator reserves test names; no production code until spine merges |

**Answer:** Wave 1 may use multiple lanes for **investigation and test drafting only**. **Implementation parallelism on Intake truth is forbidden.**

### 9.4 W1-L-SPINE scope (replaces naive W1-T01-only framing)

**Task ID:** `W1-L-SPINE` — `INTAKE_V6_CANONICAL_READINESS_TRUTH_SPINE_V1`

**Delivers:**

1. `mounting_solution` is the mounting validation source per D-005 (retire `support_type` as gate in capture/backbone for volumetric path)
2. `_derive_readiness_status` incorporates capture fatal blockers (D-006)
3. Workspace status cannot be `ready_for_quote_preview` when capture blockers > 0 (TE2E-002)
4. Wire `merge_policy_findings` / `collect_canonical_readiness_findings` into handoff pricing preview path (TE2E-014, 015)
5. Frontend blocker channel reflects merged truth (not UI-only hide)

**Explicitly NOT in spine:** finish field persistence (W1-L-FINISH), cant/return (W1-L-CANT), Wave 6 diagnostic relocation.

### 9.5 Wave 1 integration owner

**Owner:** Wave Coordinator (parent session) at **W1-INT-01** and **W1-INT-02**.

### 9.6 Wave 2 opening gate

Wave 2 opens when **W1-INT-02 PASS**:

- Fixture `IR-MRJS4VIK` / workspace `80570a4a-a806-4305-a39c-b34a72092694`
- Step 2: no SUPPORT_TYPE_MISSING when `mounting_solution` ACM saved
- No ready badge with active capture blockers
- Handoff preview: `is_ready_for_quote` false when blockers present
- PD `build_preview` callable without handoff contradiction (TE2E-010 unblocked for entry)

---

## 10. Waves 2–7 orchestration outlines

### Wave 2 — Product Definition and Aggregate

| Field | Value |
|-------|-------|
| Entry truth | Safe Intake handoff; mounting_solution confirmed |
| Exit truth | Composition Cases A–D deterministic; aggregate no re-inference |
| Sequential spine | W2-L-PD-CONTRACT → W2-L-AGG-HANDOFF → W2-L-PD-UI |
| Parallel | None on builder + aggregate services |
| Collision | `product_definition_builder_service`, `product_aggregate_service`, composition contract |
| Integration gate | PD preview ≡ aggregate GET for fixture |
| Owner decision | PD standalone route vs embedded (W2-L-PD-UI) |
| Regression | Cost preview consumes aggregate graph |

### Wave 3 — Cost authority

| Field | Value |
|-------|-------|
| Entry truth | Stable aggregate graph |
| Exit truth | **D-010 resolved** — single traceable authority |
| Sequential spine | W3-L-AUTHORITY-DECISION → W3-L-REGISTRY |
| Parallel | Forbidden until D-010 recorded |
| Collision | `commercial_price_proposal`, `estimated_internal_cost`, CostEngine |
| Integration gate | One cost trace document in decision log |
| Regression | Offer totals trace to chosen authority |

### Wave 4 — Offer and Order

| Field | Value |
|-------|-------|
| Entry truth | Singular cost authority |
| Exit truth | Order snapshot immutable |
| Sequential spine | W4-L-OFFER-READINESS → W4-L-ORDER-FREEZE |
| Parallel | None on quote orchestrator + snapshot |
| Integration gate | Snapshot byte-stable on reload |
| Regression | Execution plan inputs frozen |

### Wave 5 — Execution and Actuals

| Field | Value |
|-------|-------|
| Entry truth | Frozen order snapshot |
| Exit truth | Tasks from snapshot; actuals captured |
| Sequential spine | W5-L-PLAN → W5-L-TASKS |
| Parallel | W5-L-AUTH (TE2E-023) may run if no shared auth middleware edit conflict |
| Integration gate | Dashboard row for seeded order |
| Regression | No live template rebuild (MASTER 11) |

### Wave 6 — Operator UI

| Field | Value |
|-------|-------|
| Entry truth | Waves 1–5 logic stable |
| Exit truth | MASTER 07/08 parity; diagnostics off operator path |
| Sequential spine | W6-L-INTAKE-SURFACE → W6-L-COMMERCIAL-SURFACE → W6-L-TERMINOLOGY |
| Parallel | W6-L-PS-TABS (TE2E-012) if no intake file overlap |
| Integration gate | UI audit checklist |
| Regression | No reintroduction of false ready |

### Wave 7 — Final E2E acceptance

| Field | Value |
|-------|-------|
| Entry truth | Waves 1–6 + **P-003 owner GO on seed** |
| Exit truth | 20 gates PASS; owner sign-off D-020 |
| Sequential spine | W7-L-SEED → W7-L-SPINE-TEST → W7-L-RECONCILE → W7-L-SIGNOFF |
| Parallel | Forbidden on fixture spine |
| Integration gate | Same-scenario ID chain per ACCEPTANCE_PLAN |

---

## 11. High collision risk — truths and files

| Risk | Files / surfaces |
|------|------------------|
| **CRITICAL** | `intake_v6_workspace_service.py` (`_derive_readiness_status`), `form_system_contract_backbone_service.py`, `form_system_runtime_capture_read_model_service.py` |
| **HIGH** | `intake_v6_canonical_readiness_service.py`, `intake_v4_pricing_input_service.py`, frontend `intakeV4Readiness.ts`, blocker banner components |
| **HIGH** | `product_definition_builder_service.py`, `product_aggregate_service.py` (Wave 2) |
| **HIGH** | `commercial_price_proposal_service.py`, `estimated_internal_cost_service.py` (Wave 3) |
| **MEDIUM** | Quote orchestrator, snapshot v2 (Wave 4) |

---

## 12. Session resume block

Copy at session start; update at session end:

```yaml
workos_e2e_resume:
  accepted_HEAD: fe6c6f7
  program: WORKOS_E2E_MASTER_ALIGNMENT_AND_FINALIZATION_V1
  active_wave: 1
  active_task: null  # set on P-001 YES
  active_lanes: []
  reserved_truths: []
  reserved_files: []
  completed_gates: [W0-doc, W0-figma]
  open_blockers: [TE2E-001, TE2E-002, TE2E-003, TE2E-010, TE2E-014, P-001]
  implementation_hold: LIFT_HOLD_FOR_WAVE_1_ONLY_PENDING_P001
  next_allowed_action: Owner P-001 YES then W1-L-SPINE reservation
  canonical_root: docs/master/workos-e2e/
  operating_model: docs/master/workos-e2e/WORKOS_E2E_IMPLEMENTATION_OPERATING_MODEL.md
  figma_master: 911Q6oRKcEursrRoT4Qj0h nodes 14:2-14:15
  fixture: IR-MRJS4VIK / 80570a4a-a806-4305-a39c-b34a72092694
```

---

## 13. Documentation control

| Event | Update |
|-------|--------|
| Task start/close | Task worklog + `WORKOS_E2E_STATUS.md` |
| Defect state change | `WORKOS_E2E_ISSUE_REGISTRY.md` |
| Owner/architecture choice | `WORKOS_E2E_DECISION_LOG.md` |
| Wave closure | `WORKOS_E2E_STATUS.md` + roadmap task graph if sequencing changed |
| Task proof | `docs/qa/<task-id>/` or task worklog attachments — **not** new master doc |
| Contradiction found | Decision log + status blocker; **no** new audit folder |
| New general audit | Owner GO only — see §15 |

**Forbidden during routine implementation:** new `docs/qa/workos-e2e-*-audit*` folders, duplicate master dossiers, rewriting Figma MASTER without dedicated doc task.

---

## 14. Required decisions — answers

| # | Question | Answer |
|---|----------|--------|
| 1 | Can Wave 1 use multiple implementation lanes? | **Investigation/test-draft yes; implementation no** on shared Intake spine |
| 2 | Which Wave 1 items share root cause? | **TE2E-001, 002, 014, 015** share readiness spine (cluster A) |
| 3 | Which must serialize? | **SPINE → FINISH → CANT**; VECTOR after wave integration |
| 4 | What may parallel? | Read-only analysis, test drafting with reserved names, post-W1-INT-02 vector if file-independent |
| 5 | Who owns Wave 1 integration? | **Wave Coordinator** at W1-INT-01 / W1-INT-02 |
| 6 | What gate opens Wave 2? | **W1-INT-02 PASS** — handoff safe per §9.6 |
| 7 | High collision truths/files? | See §11 — intake derive + form system backbone |
| 8 | Temporary badge/warning removal? | **TD-### register** + removal task in Wave 6; forbidden to hide in Wave 1 |
| 9 | Downstream regression owner? | **Wave Coordinator** at integration gates |
| 10 | Session resume? | **§12 resume block** in every worklog session |
| 11 | When is another audit justified? | Owner GO; contradiction unresolved; post-W7 only for release — not per task |
| 12 | Prevent local optimization breaking E2E? | **Integration gates + downstream consumer proofs** |
| 13 | Prevent parallel authority? | **Reservation model + serialize on shared files + D-010 single owner** |
| 14 | First implementation task? | **`W1-L-SPINE` — `INTAKE_V6_CANONICAL_READINESS_TRUTH_SPINE_V1`** |
| 15 | Is W1-T01 scope correct? | **Direction correct; scope too narrow** — must include readiness merge + handoff wire, not mounting-only |

---

## 15. When another audit is justified

- Owner explicitly requests re-audit
- Unresolved canonical contradiction after code inspection
- Post-W7 release certification gap

**Not justified:** per-task completion, single-system fix, UI polish, test addition.

---

## 16. Contradictions found (code vs docs)

| ID | Observation | Resolution |
|----|-------------|------------|
| C-01 | Task graph lists W1-T04 ∥ W1-T02 after T01 | **Overridden** — W1-T02 shares finish_setup with spine; serialize after W1-INT-01 |
| C-02 | `merge_policy_findings` exists but grep shows no callers | **Confirmed** — TE2E-015; wire in W1-L-SPINE |
| C-03 | Capture FIELD_SPECS still gate `support.support_type` not `mounting_solution` | **Confirmed** — TE2E-001; D-005 not implemented in capture |
| C-04 | `_derive_readiness_status` has no capture blocker check | **Confirmed** — TE2E-002 |

No blocker contradictions between master dossier and Figma MASTER.

---

## 17. Implementation hold recommendation

**`LIFT_HOLD_FOR_WAVE_1_ONLY`** — pending owner **P-001 YES** after approving this operating model.

Full program remains held until Waves 1–7 complete.

---

## 18. Delivery footer

| Field | Value |
|-------|-------|
| Task | `WORKOS_E2E_CONTROLLED_IMPLEMENTATION_ORCHESTRATION_V1` |
| Verdict | `WORKOS_E2E_IMPLEMENTATION_MODEL_READY_FOR_WAVE_1` |
| Application code changed | NO |
| DB changed | NO |
| Implementation started | NO |
| First task | `W1-L-SPINE` / `INTAKE_V6_CANONICAL_READINESS_TRUTH_SPINE_V1` |
| Commit | NO |
| Push | NO |
