# WorkOS — Roadmap re-entry and next build selection

**Date:** 2026-07-16  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Gate HEAD:** `8a266b6`  
**Runtime:** frontend `:3000` · backend `:8001`  
**Mode:** planning only — no implementation

---

## 1. Where WorkOS stands

Canonical spine:

`Intake V6 → ProductDefinition → ProductAggregate → Pricing/Cost → Quote → Order → ExecutionPlan → Execution Reality → Post-job`

| Segment | Truth |
|---------|--------|
| Intake V6 Letters operator | Strong / operational |
| Logo root | Candidate-only, fail-closed — **closed** (do not reopen) |
| Snapshot V2 Quote/Order freeze | Validated with guards |
| Post-job V1 | Accepted (nonblocking limitations) @ master Accepted HEAD `0b97f7d` |
| Same-scenario unbroken lineage | **NOT_PROVEN** — master’s stated next |
| Intake→PD before quote create | Weak — PD joins mainly at Snapshot freeze |
| Dirty tree (~252 paths) | ~docs/QA dominant; few unfinished code clusters |

Master living status (`docs/master/workos-e2e/WORKOS_E2E_STATUS.md`) still lists Accepted HEAD `0b97f7d`. Git HEAD `8a266b6` is intake truth hardening after that (Logo readiness + blocker contract + live smokes). **Not a product conflict** — master next remains same-scenario E2E.

---

## 2. Completed work — do not reopen

- Repository cleanup / preserve-valid-work batches  
- B2 Important Documents stabilization  
- Cursor/plugin research + Agent Compatibility + Figma read-only pilot  
- Master E2E dossier preservation  
- Logo candidate-only readiness + HTTP + live UI smoke  
- Blocker-banner defensive fix  
- Runtime-capture blocker normalization + live contract smoke (`8a266b6`)  
- Post-job V1 acceptance · FLEX phases closed · runtime tooling lane closed  

---

## 3. Dirty-tree classification (planning decisions)

| Group | Class | Next-build use |
|-------|--------|----------------|
| PreOrder technical preview + component task composition (services/UI/tests; **routers missing**) | Coherent unfinished | **Exclude** from recommended build (parallel-engine risk) |
| Product Truth audit view (no router) | Coherent unfinished / diagnostic | **Exclude** |
| `frontend/src/api/productDefinitionPreview.ts` composition types | Valid active | **Preserve for later** (may support Build 2 friction) |
| Architecture contracts (untracked) | Supporting docs | **Owner decision** which are canonical — not this build |
| CE probes (active-path isolation delta) | Supporting | **Preserve** |
| Bulk worklogs / QA dumps / SVG fixtures / capture scripts | Supporting or local/generated | **Exclude** / cleanup later |
| Modified finish/preserve/cleanup worklogs | Meta docs | **Exclude** |

No dirty cleanup or commits in this planning task.

---

## 4. Candidate comparison

| # | Candidate | Problem solved | Value | Risk | Agent |
|---|-----------|----------------|-------|------|-------|
| **1** | Same-Scenario Request→Post-Job E2E Truth V1 | Prove one unbroken IR→…→post-job lineage (TE2E-013) | Highest program + operator E2E | Walkthrough friction / fixture theater | **RECOMMENDED** |
| **2** | Letters+Logo → Quote/Order continuity (gradi path) | Close create/accept/convert after commercial dry-run ready | Visible commercial close | Scope creep into dossier/Aggregate | Strong alternative if owner wants smaller slice |
| **3** | PreOrder technical preview maturity (readonly) | Honest pre-order production view | Useful Review UX | Looks like parallel task engine | Last among serious options |

Rejected: Employee Mobile, W0-B6, EP rematerialize, Logo reopen, PS catalog “completion”, PD standalone page as sole next (sideways), FLEX polish.

---

## 5. Recommended next build — BUILD 1

### Objective

Execute `WORKOS-SAME-SCENARIO-REQUEST-TO-POST-JOB-E2E-TRUTH-V1`: one real `TPL-VOLUMETRIC-LETTERS_v2` (± linked logo/ACM as already allowed) journey with **stable identity** from request through post-job profitability truth.

### Scope (coherent boundary)

- Walk and record: Work Intake → Intake V6 → commercial handoff → Quote Snapshot V2 → Order Snapshot V2 → ExecutionPlan → Execution Reality → Post-job  
- Fix **only** blockers that break that one scenario’s unbroken IDs or false commercial blocks  
- Evidence pack + master STATUS / ISSUE_REGISTRY updates for TE2E-013 class  

### Systems involved

Intake V6, ProductDefinition/Aggregate (exercise, not redesign), Pricing/CPP/EIC as already wired, Quote/Order Snapshot V2, ExecutionPlan V2, Execution Reality, post-job reads.

### Expected visible result

Owner can open one workspace/order and see the **same identity** across `/intake` → quote → order → `/execution/:id` post-job — not stitched stage fixtures.

### Owner gates (explicit)

From same-scenario plan / STATUS **G1–G4** (must answer before `/ce-work`):

1. Scenario product binding (Letters root; linked logo yes/no; ACM panel yes/no)  
2. Acceptable commercial path (dry-run vs create draft vs full accept)  
3. Stock / SKU realism bar for the walk  
4. Pass definition if nonblocking PD/PA debt remains  

### Exclusions

- Logo root activation / readiness policy reopen  
- W0-B6 Documentation Center  
- Employee Mobile  
- PreOrder/TaskGraph materialization  
- New pricing catalog or CostEngine rewrite  
- Dirty-tree bulk docs commit  
- Unrelated UI polish / FLEX reopen  

### Dirty files this build may touch

- **None of the unfinished PreOrder/Truth-audit router prototypes** unless a live same-scenario blocker proves they are required (unlikely).  
- May read existing gradi-curat / snapshot evidence; may update master STATUS/ISSUE after proof.  
- May create new QA evidence under `docs/qa/` for the scenario run.

### Tests / runtime proof

- Prefer live stack proof on `:3000` / `:8001` with disposable or named scenario workspace  
- Targeted backend/frontend only if a real defect is fixed mid-walk  
- End with isolated evidence + worklog commits — not a mega-refactor commit  

### Commit boundaries

- Evidence / STATUS updates: docs commits  
- Any defect fix: one isolated product commit per real fix, only if required to finish the scenario  

### Modules / Governance (expected when executed)

| Page | Expected |
|------|----------|
| `/modules` | Likely **runtime evidence / status / source refs** update if handoffs proven; nodes unchanged unless a real contract gap is closed |
| `/governance` | **Minimal or none** unless owner gates change ownership; Important Documents only if a new canonical proof doc is promoted |

---

## 6. Why not Build 2 or 3 now

- **Build 2** is likely the *first friction inside* Build 1. Doing it alone risks another micro-fix chain without closing TE2E-013. Prefer absorbing handoff fixes **inside** same-scenario when they block the walk.  
- **Build 3** does not close Quote→Order→Execution lineage and risks parallel-engine scope.

---

## 7. Owner decision — APPROVED

**Choice:** `ALEGEM BUILDUL 1`  
**Implementation:** `GO`  
**Scenario:** Letters volumetric luminos — `TPL-VOLUMETRIC-LETTERS_v2` (real offerable template). No Logo root. No new template.  
**Data:** Deterministic local disposable/cloned scenario with cleanup. No production. No permanent seed.

### G1–G4 (binding)

| Gate | Owner answer |
|------|----------------|
| **G1** Product binding | Letters already supported; real existing template; identity preserved Intake V6 → Post-Job. No Logo root. No new template. |
| **G2** Commercial depth | Full V1: real existing pricing, Quote Snapshot, accept, Order Snapshot; frozen commercial values must not be recalculated later. |
| **G3** Stock realism | Use real availability/consumption where already supported; do not block Build 1 on advanced inventory/reservations/full physical moves. Gaps stay explicit, not simulated. |
| **G4** Pass bar | PASS only if same scenario has demonstrable lineage Request/Intake → PD → PA → Quote → Order → ExecutionPlan → Execution Reality → Post-Job, with stable IDs, tests, HTTP proof, live UI verification, and no manual bypass between stages. |

---

## 8. Sources used (priority order)

1. Live ports `:3000` / `:8001`  
2. Tracked code + tests (Intake V6, snapshot V2, logo readiness)  
3. QA: `docs/qa/logo-runtime-blocker-smoke-2026-07-16/`, logo-only live smoke, product-system E2E audit  
4. Master: `WORKOS_E2E_STATUS.md`, TASK_GRAPH, ISSUE_REGISTRY, ROADMAP (stale wave hold noted)  
5. CE: `workos-same-scenario-request-to-post-job-e2e-v1/plan.md`, post-flex reentry  
6. Dirty-tree classification (Track C)  
