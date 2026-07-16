# WorkOS E2E — Master Dossier

**Program:** `WORKOS_E2E_MASTER_ALIGNMENT_AND_FINALIZATION_V1`  
**Role:** BASELINE program narrative for connected-flow E2E (not a substitute for living STATUS)  
**Worktree:** `C:\w\psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Evidence baseline HEAD:** `fe6c6f7` (TRUE E2E audit era)  
**Living status:** See `WORKOS_E2E_STATUS.md` for Accepted HEAD, wave closure, and implementation hold  
**Maturity sections below:** May lag STATUS — treat open-blocker lists as baseline evidence unless STATUS/ISSUE_REGISTRY supersede them

**Companion docs:** SYSTEM_MAP, ROADMAP, TASK_GRAPH, ACCEPTANCE_PLAN, DECISION_LOG, STATUS, DOCUMENT_INDEX, ISSUE_REGISTRY

**B2 / Important Documents:** Outside B2 unless owner promotes.

---

## A. Executive truth

### What WorkOS is

WorkOS is an operational ERP for volumetric signage production: commercial intake through execution, with Product System as the template and module authority.

### Current maturity

| Area | Maturity |
|------|----------|
| Intake V6 operator path | **Functional but canonically broken** at Step 2 |
| Product System catalog | Operational (readonly) |
| Product Definition | **Paused** — Figma + API only |
| Commercial spine (Offer→Order→Execution) | **PROVEN_V1** same-scenario Letters (`DETERMINISTIC_LOCAL_SCENARIO`; not universal) |
| Operator UI coherence | **Poor** on Intake Step 2 (debug overload) |
| Documentation | **Fragmented** until this master program |

### Current blockers

1. TE2E-001/002/014/015 — mounting/readiness/handoff split
2. TE2E-003 — finish truth persistence
3. TE2E-013 — **closed** (`SAME_SCENARIO_REQUEST_TO_POST_JOB_PROVEN_V1`; residuals TE2E-028)
4. TE2E-025 — dual cost authority
5. Owner approval pending for Wave 1 (historical — Wave 1 complete; retained for audit trail)

### Target state

One product truth from Cerere to Reconciliere; frozen commercial truth after Order; operator UI with single primary action per page; diagnostics in Admin/QA only.

### Final success definition

All 20 gates in `WORKOS_E2E_ACCEPTANCE_PLAN.md` green + owner sign-off.

### Audit verdict (evidence)

`WORKOS_TRUE_E2E_BLOCKED_MULTIPLE_INDEPENDENT_FAILURES` — first break Intake Step 2; 12 independent downstream defects catalogued.

---

## B. Canonical connected flow

| # | Stage | Operator route | Maturity |
|---|-------|----------------|----------|
| 1 | Cerere | `/intake` | OK |
| 2 | Intake V6 | `/intake-v6/:id/operator` | **BLOCKED** canonical truth |
| 3 | Definire produs | embedded / API | PAUSED |
| 4 | Product System | `/product-system/products` | Catalog OK; tabs stub |
| 5 | Product Aggregate | API only | STATIC proven |
| 6 | Calcul | Intake step 2 rail | PARTIAL (20/21) |
| 7 | Ofertă | `/quotes` | Empty UI OK; debug banner |
| 8 | Comandă | `/orders` | Empty UI OK |
| 9 | Plan de execuție | APIs + code | **PROVEN_V1** same-scenario (plan `8` / 18 tasks on order `92402`) |
| 10 | Execuție efectivă | `/execution` | **PROVEN_V1** partial (session closed; `vector_prep` Finalizat) |
| 11 | Reconciliere | `/execution/:id` Post-Job | **PROVEN_V1** W7-T02 breadth (matched/partial/variance on `92402`/`92403`) |

Product System runs parallel as **configuration authority**, not required operator stop.

---

## C. System ownership

See `WORKOS_E2E_SYSTEM_MAP.md` for full matrix.

**Critical owner corrections needed:**

| Truth | Current broken owner | Canonical owner |
|-------|---------------------|-----------------|
| Mounting decision | `support_type` adapter | `mounting_solution` + operator confirm |
| Readiness | `_derive_readiness_status` alone | merged with runtime capture |
| Finish flags | UI incomplete write | `finish_setup` persisted fields |
| Commercial readiness | UI + policy partial | backend merged policy |
| Cost graph | CostEngine + 7G/7H parallel | **TBD Wave 3** single authority |

---

## D. Canonical product truth trace

| Checkpoint | Field examples | Owner stage | Status @ fe6c6f7 |
|------------|----------------|-------------|------------------|
| Request identity | IR-MRJS4VIK | Cerere | OK |
| Workspace | 80570a4a-... | Intake | OK |
| Root template | TPL-VOLUMETRIC-LETTERS_v2 | Intake/PS | OK |
| Child templates | ACM, premount optional | Intake montaj | **Broken gate** |
| Layer roles | Vector Litere, Logo | Intake Step 1 | OK |
| Finishes | face/cant/back | Intake Step 2 | **Incomplete persist** |
| Mounting | mounting_solution | Intake | **Blocked by support_type** |
| Composition graph | Cases A–D | PD builder | PAUSED |
| Aggregate modules | structura_suport, volum | Aggregate API | API OK |
| Cost lines | 20/21 preview | Calcul | gap |
| Offer | quote snapshot | Ofertă | NOT_CREATED |
| Order freeze | order snapshot v2 | Comandă | **PROVEN_V1** observed (`92402` from `QSN2-2026-0002`; TE2E-022 immutability gate still open) |
| Execution tasks | from frozen ops | Execution | **PROVEN_V1** (18 tasks on plan `8`) |
| Actuals | shop floor capture | Execution | **PROVEN_V1** partial (one closed session) |

---

## E. State machines (summary)

### Intake workspace readiness (target)

```
draft → configuring → blocked | ready_for_preview → handed_off
```

**Invalid today:** `ready_for_preview` while capture blockers active (TE2E-002).

### Offer

```
draft → sent → accepted → converted_to_order
```

### Order

```
created → in_execution → completed → reconciled
```

**Freeze boundary:** Order creation — snapshot immutable after.

### Execution task

```
planned → in_progress → done | blocked
```

Full matrix: `docs/qa/workos-e2e-operational-coherence-audit-v1-true-e2e/matrices/state-machine-matrix.md` (SUPPORTING).

---

## F. Terminology dictionary (operator)

| Approved (RO) | Technical | Avoid |
|---------------|-----------|-------|
| Cant | return_finish / cant edge | Cant / volum |
| Panou ACM casetat | mounting_panel / ACM template | support_type (operator) |
| Structura premontaj | premount_structure | structura_suport (operator) |
| Pregătit | readiness clear | Ready with blockers |
| Definire produs | product_definition stage | Dev column names on PD01 |
| Cost intern | 7H / internal cost | Mixed with commercial |
| Preț comercial | 7G / commercial proposal | UI policy prose |

Full matrix: SUPPORTING `matrices/terminology-matrix.md`.

---

## G. UI/UX operating model

### Per-page contract

| Page | Purpose | Primary action | Center of attention | Status |
|------|---------|----------------|---------------------|--------|
| Intake Step 1 | Layer roles | Confirm layers | SVG role cards | OK |
| Intake Step 2 | Configure product | Confirm montaj/finish | **FAIL** — warning stack | FIX Wave 1+6 |
| Intake Step 3 | Confirm handoff | Next commercial | Mixed readiness | PARTIAL |
| PS catalog | Pick template | Open detail | Bucket catalog | OK |
| Offers empty | List offers | + Ofertă nouă | **Policy banner competes** | FIX Wave 6 |
| Orders empty | List orders | Mergi la Oferte | Empty guidance | OK |

### Warning rules

- Max one primary blocker channel per page
- No raw capture codes in page-wide banners
- Badges must match backend state exactly

### Diagnostic rules

| Surface | Destination |
|---------|-------------|
| Runtime capture accordion | MOVE_TO_ADMIN |
| Promotion planner | MOVE_TO_ADMIN |
| Offers policy banner | MOVE_TO_ADMIN |
| Header 2 critical | MOVE_TO_ADMIN |
| Cant inline (when logic fixed) | CONTEXTUAL_INLINE |

### Typography / density

- Minimum 12px operator body; 11px only in admin tables
- Step 2 must fit primary CTA above fold after Wave 6

---

## H. Current defects

**Living registry:** `WORKOS_E2E_ISSUE_REGISTRY.md` (authoritative open/closed counts).  
**Living wave outcomes:** `WORKOS_E2E_STATUS.md`.

Baseline note (TRUE E2E era): P1 originally included TE2E-001, 002, 003, 010, 014 — confirm against ISSUE_REGISTRY before treating as still open.

---

## I. Architecture risks (unproven vs confirmed)

| Risk | Class | Evidence |
|------|-------|----------|
| Dual cost path | CONFIRMED code | TE2E-025 |
| Same-scenario spine | **PROVEN_V1** (Letters deterministic local; IR-BUILD1→92402) | TE2E-013 closed; TE2E-028 residuals |
| Order freeze immutability | STRONG_INFERENCE | code only |
| ARCH Figma drift | NOT_AUDITED | TE2E-027 |
| Session gate on /execution | CONFIRMED intermittent | TE2E-023 |

---

## J. Missing product surfaces (planned, not defects)

| Surface | Wave | Issue |
|---------|------|-------|
| PD operator page | 2 | TE2E-010 |
| PS Components–Advanced tabs | 6 gating | TE2E-012 |
| Figma MASTER 00–13 | 0 spec | TE2E-027 |

---

## K. Implementation roadmap

See `WORKOS_E2E_IMPLEMENTATION_ROADMAP.md` — Waves 0–7.

**First code task after approval:** W1-T01 `INTAKE_V6_CANONICAL_MOUNTING_BLOCKER_ALIGNMENT_V1`

---

## L. Final acceptance

See `WORKOS_E2E_ACCEPTANCE_PLAN.md`.

---

## Figma MASTER diagram program

**File:** `911Q6oRKcEursrRoT4Qj0h`  
**Section to create:** `WORKOS E2E MASTER` (do not destructively edit ARCH/PD pages)  
**Physical pages created:** **0/14** — specifications below for owner/Figma work  
**Existing ARCH/PD:** mark as supporting reference per frame

| Page | Node ID | Purpose | Current state | Target state | Owner | Impl dep | Acceptance gate |
|------|---------|---------|---------------|--------------|-------|------------|-----------------|
| MASTER 00 | TBD | E2E flow map Cerere→Reconciliere | NOT_CREATED | Canonical flow diagram | PD UX | Wave 0 | Owner approves diagram |
| MASTER 01 | TBD | System ownership map | NOT_CREATED | owns/reads/writes/freeze | PD UX | Wave 0 | Matches SYSTEM_MAP |
| MASTER 02 | TBD | Product truth lifecycle | NOT_CREATED | One product trace | PD UX | Wave 2 | Matches aggregate API |
| MASTER 03 | TBD | Decision ownership | NOT_CREATED | propose/confirm/freeze | PD UX | Wave 1 | Matches D-005,006 |
| MASTER 04 | TBD | State machines | NOT_CREATED | Valid transitions only | PD UX | Wave 1 | No ready+blockers |
| MASTER 05 | TBD | Data/contract handoffs | NOT_CREATED | API boundaries | PD UX | Wave 4 | Handoff tests pass |
| MASTER 06 | TBD | Operator navigation | NOT_CREATED | Pages + next action | PD UX | Wave 6 | 3s primary action test |
| MASTER 07 | TBD | Admin/Advanced surfaces | NOT_CREATED | Removed from operator | PD UX | Wave 6 | No capture on step 2 |
| MASTER 08 | TBD | Warning/diagnostic destination | NOT_CREATED | 5 destination classes | PD UX | Wave 6 | UI audit pass |
| MASTER 09 | TBD | Product composition A–D | NOT_CREATED | 4 composition chains | PD UX | Wave 2 | Cases A–D tests |
| MASTER 10 | TBD | Cost & commercial truth | NOT_CREATED | internal vs commercial vs freeze | PD UX | Wave 3 | W3-T01 decision |
| MASTER 11 | TBD | Execution truth | NOT_CREATED | plan/actual/reconcile | PD UX | Wave 5 | W5 complete |
| MASTER 12 | TBD | Implementation roadmap visual | NOT_CREATED | Wave dependency graph | PD UX | Wave 0 | Matches ROADMAP |
| MASTER 13 | TBD | Final acceptance map | NOT_CREATED | 20 gates | PD UX | Wave 7 | ACCEPTANCE_PLAN |

**Existing frame marking (non-destructive):**

| Frame set | Mark as |
|-----------|---------|
| PD01–12 (partial exports) | supporting reference — target incomplete |
| ARCH 00–12 | supporting reference — not audited in repo |

---

## WORKOS Agent Operating Contract

### Before every task

Read in order:

1. `WORKOS_E2E_STATUS.md`
2. `WORKOS_E2E_MASTER_DOSSIER.md` (this file)
3. `WORKOS_E2E_IMPLEMENTATION_ROADMAP.md`
4. `WORKOS_E2E_TASK_GRAPH.md`
5. `WORKOS_E2E_DECISION_LOG.md`
6. Relevant issue in `WORKOS_E2E_ISSUE_REGISTRY.md`
7. Last worklog for active task

### During every task

Report: current task, HEAD, files touched, scope, dependencies, tests, runtime, screenshots, blockers, unresolved questions.

### After every task

Update: issue status, STATUS.md, worklog, commit (if implementation), next step in TASK_GRAPH.

### Forbidden behavior

- Do not invent architecture outside DECISION_LOG
- Do not infer owner silently
- Do not create parallel truth or new canonical docs
- Do not add warnings instead of validation fixes
- Do not expose debug on operator UI
- Do not modify unrelated systems
- Do not auto-start next task
- Do not declare E2E complete before Wave 7

---

## UI cleanup policy (Wave 6)

Every warning/badge/debug maps to: KEEP_PRIMARY | CONTEXTUAL_INLINE | MOVE_TO_DETAIL | MOVE_TO_ADMIN | MOVE_TO_ISSUE_REGISTRY | MOVE_TO_RUNTIME_LOG | REMOVE | REPLACE_WITH_VALIDATION.

No badge without: owner, meaning, source state, removal condition, test.

---

## Documentation supersession plan

See `WORKOS_E2E_DOCUMENT_INDEX.md`. Headers on old docs only after owner approval.

---

*End of Master Dossier.*
