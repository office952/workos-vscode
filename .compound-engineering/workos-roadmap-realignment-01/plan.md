# WORKOS-ROADMAP-REALIGNMENT-01 — Decision Plan

**Task:** WORKOS-ROADMAP-REALIGNMENT-01-AFTER-BACKUP-AND-FLEX-FOUNDATION  
**Mode:** PLAN MODE — read-only realignment; docs-only write  
**Starting HEAD:** `e92d135`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Worktree:** `C:\w\psiso`  
**Created:** 2026-07-15  
**Artifact type:** Roadmap realignment decision support (not implementation-ready code plan)

---

## Goal Capsule

Reconstruct the real WorkOS position after backup/restore, runtime recovery, UI-truth foundation, parity work, FLEX-01/A/B, and RUNTIME-FRESHNESS-04A/04B. Decide whether FLEX-02 is the correct next product step or whether the program must return to another canonical lane. Close the runtime tooling lane definitively before any further application code.

---

## Problem Frame

After a dense 2026-07-15 session (22 commits from backup baseline `deb5d69` to `e92d135`), the program has:

- A **complete frozen commercial→execution spine** (Wave 7 closed; order `23099` proven)
- A **FLEX detour** that delivered read-only collaboration truth (FLEX-01) and completion semantics (FLEX-01A)
- A **runtime tooling lane** now complete through RUNTIME-FRESHNESS-04B
- **Stale canonical docs** (`WORKOS_E2E_STATUS.md` accepted HEAD still `695c78c`, not `e92d135`)
- **Paused parallel tracks** (APP-AUTH-06G Sandu evidence, UI-TRUTH-01B–01E banner)

The risk is accelerating FLEX-02 (participant persistence) because it appears "next" in the task graph, when pre-FLEX canonical work and owner-paused tracks may carry higher immediate value.

---

## Source-of-Truth Order (applied)

1. Real runtime (health probe `:8001` healthy at audit time; full stack proof anchored to 04B worklog)
2. Current code (`App.tsx` routes, FLEX-01 service, freshness scripts)
3. DB read-only evidence (fixture order `23099`, QSN2-2026-0001)
4. OpenAPI manifest (`scripts/workos-canonical-openapi-paths.json` — 5 routes)
5. Accepted worklogs and commits (`deb5d69..e92d135`)
6. Canonical status docs (`WORKOS_E2E_STATUS.md`, `WORKOS_E2E_TASK_GRAPH.md`)
7. Roadmap/task graph and session ledger
8. Archive/reference docs

---

## Integrated Verdict

**`WORKOS_ROADMAP_REALIGNMENT_01_COMPLETE`**

The program is **on the frozen-spine trajectory** but **temporarily misaligned on "what's next"** because:

- Task graph declares **PROD-FLEX-ARCH-02** (architecture only)
- **FLEX-02 implementation is NOT authorized and NOT needed by any current consumer**
- **Pre-FLEX canonical next was APP-AUTH-06G** (paused)
- **Runtime tooling lane is CLOSED** — no further freshness work

---

## Key Technical Decisions (realignment)

### KTD-1: Runtime tooling lane — CLOSED

RUNTIME-FRESHNESS-04A + 04B complete at `e92d135`. Owner decision: close definitively. No further startup-contract or process-ownership work unless a new runtime regression is proven.

### KTD-2: FLEX-02 — NOT next for implementation

FLEX-02 (participant persistence writes) is **blocked** by OWNER-DECISION-07. No frontend consumer calls `task-collaboration-read`. Mobile individual flow works without FLEX-02. `participants_json` is **deferred**, not canonical.

**Required gate before any FLEX-02 code:** `PROD-FLEX-ARCH-02-PARTICIPANT-PERSISTENCE-BOUNDARY` (plan/docs only; owner GO).

### KTD-3: Recommended primary lane — PROD-FLEX-ARCH-02 (plan only)

Highest **program-authoritative** next step. Bounded (no code/DB/UI). Unblocks the collaboration frontier (D6 helper-join debt, MOBILE-INT-02) without violating gates.

**Alternative if owner redirects to pre-FLEX track:** APP-AUTH-06G (Sandu observe-only evidence) — requires explicit unpause.

### KTD-4: Frozen spine — do not reopen

Order Snapshot → Execution Plan → materialized operational tasks path is **complete**. Next work is collaboration architecture and trust surfaces, not re-plumbing W5.

### KTD-5: Canonical docs refresh — required follow-up

Update `WORKOS_E2E_STATUS.md` and `WORKOS_E2E_TASK_GRAPH.md` accepted HEAD to `e92d135`; record runtime tooling CLOSED and FLEX-01A/01B/04 complete.

---

## Workstream Synthesis

### A — Runtime/product truth

| Surface | Status |
|---------|--------|
| Intake V6 → Quote → Order → Execution (`23099`) | **Operational** |
| Employee Mobile v2 (individual tasks) | **Operational** |
| FLEX-01 `task-collaboration-read` | **Shipped** (read-only) |
| Product System planned tabs (components…advanced) | **Preview-only** |
| `/modules`, `/governance` | **Shell/static** |
| `/shop-floor`, global `/operator` | **Partial** (mock fallback) |
| Collaborative execution / help / join | **Not implemented** |

### B — Commit history (`deb5d69..e92d135`)

| Class | Count | Examples |
|-------|-------|----------|
| Application behavior | 3 | UI-TRUTH-01A hook; FLEX-01 endpoint; FLEX-01A completion semantics |
| Dev runtime/tooling | 3 | RUNTIME-CONFIG-03; RUNTIME-FRESHNESS-04A/04B |
| Docs/evidence/governance | 16 | Backup, parity plans, FLEX audit/arch/OD gates |

**Pre-FLEX canonical next:** APP-AUTH-06G (Sandu evidence). FLEX opened at `02b5981` as parallel workforce audit, not replacement of parity track.

### C — FLEX relevance

- FLEX-01 enables read-only collaboration projection + operation_completed semantics
- FLEX-02 necessity: **PAUSE** (not YES — no consumer; not NO — future waves depend on persistence decision)
- Dependencies: PROD-FLEX-ARCH-02 → FLEX-02 → FLEX-03 (split pools, D6 guard) → FLEX-05+ (UI)

### D — Lane comparison (summary)

| Lane | Maturity | Next action |
|------|----------|-------------|
| Order→Plan→Materialize | Complete | Maintenance only |
| Execution Reality (individual) | Complete | Collaboration gaps remain |
| FLEX-02 persistence | Blocked | Wait for ARCH-02 |
| Employee eligibility | Observe-only | APP-AUTH-06G paused |
| UI truth banner | 01A done; 01B paused | Owner GO required |
| Workcenter/utilaje routing | Partial | PROD-ARCH-01 blocked |
| Product System active path | Mostly complete | Audit-only closeout |
| **PROD-FLEX-ARCH-02** | Not started | **Primary recommendation** |

---

## Scope Boundaries

### In scope (this task)

- Read-only audits across runtime, commits, FLEX, lanes
- Decision artifacts: this plan + worklog final report
- Optional docs-only commit

### Out of scope / forbidden

- Code, DB, migrations, seeds, UI changes
- Runtime tooling changes
- FLEX-02, `participants_json`, participant persistence
- Product System edits, snapshot edits, materialization
- Employee Mobile changes, dead-piece cleanup
- Push, PR

### Deferred to follow-up work

- STATUS/TASK_GRAPH accepted HEAD refresh to `e92d135`
- Owner GO for PROD-FLEX-ARCH-02 or unpause APP-AUTH-06G / UI-TRUTH-01B
- FLEX-02 implementation (after ARCH-02 + owner GO)

### Paused lanes (owner decision)

| Lane | Status |
|------|--------|
| Runtime tooling (RUNTIME-FRESHNESS-04+) | **CLOSED** |
| FLEX-02–FLEX-09 implementation | **BLOCKED** |
| APP-AUTH-06G (Sandu evidence) | **PAUSED** |
| UI-TRUTH-01B–01E (banner rendering) | **PAUSED** |
| PROD-ARCH-01 (intelligent dispatch) | **BLOCKED** |
| MOBILE-INT-02 | **BLOCKED** (awaits collaborative model) |
| Parity enforcement / Sandu auto-fix | **NOT AUTHORIZED** |

---

## Recommended Next Steps (post-realignment)

### 1. Primary lane (continue)

**`PROD-FLEX-ARCH-02-PARTICIPANT-PERSISTENCE-BOUNDARY`**

- Deliverable: architecture decision package comparing persistence options (normalized record vs event projection vs JSON extension vs session-only)
- Mode: plan/docs only — **no writes, no migration, no UI**
- Stop for owner GO before FLEX-02

### 2. Smallest safe next **implementation** slice (after ARCH-02 GO)

**`FLEX-02` participant write foundation** — only after ARCH-02 approves persistence shape. Paired likely with FLEX-03 split-pool work for D6 debt.

If owner redirects away from FLEX track: **`UI-TRUTH-01B`** (frontend banner; owner must lift pause) or **`APP-AUTH-06G`** (observe-only Sandu evidence).

### 3. Owner-visible verification target (current truth — no new code)

| Field | Value |
|-------|-------|
| URL | `http://127.0.0.1:3000/execution/23099` |
| Page | Execution Detail |
| Section | Task list + production release strip + blocker resolution |
| Fixture | Order `23099` (`ORD-W5INT02-GATE`) |
| Expected | 13 materialized tasks; start/complete flow; `task-collaboration-read` returns `execution_task_collaboration_read/v1` on `:8001` when stack running |

After **UI-TRUTH-01B** (if unpaused): Environment banner shows separated runtime truths (not auth→LIVE/DB misleading segment).

After **PROD-FLEX-ARCH-02**: Owner verifies by reading decision doc — no visual product change.

---

## Risks

1. **Doc drift** — STATUS at `695c78c` misleads agents/owners about FLEX-01A/04 completion
2. **FLEX-02 premature start** — would violate OD-07 and waste effort without persistence shape
3. **Mock surfaces as truth** — `/shop-floor`, global `/operator` mock fallback misleads operators
4. **D6 collaboration debt** — `_has_active_session_by_other` blocks helper join until FLEX-03
5. **Sandu eligibility discrepancies** — 20 observe-only parity gaps; enforcement blocked until OD-02/06G

---

## Owner Decisions Required

1. **Confirm runtime tooling lane CLOSED** (recommended: YES)
2. **Authorize PROD-FLEX-ARCH-02** as next bounded work (plan only)
3. **OR redirect to pre-FLEX track:** unpause APP-AUTH-06G and/or UI-TRUTH-01B
4. **Persistence shape** (at ARCH-02): normalized vs event-derived vs session-only — reject auto-accepting `participants_json`
5. **Refresh canonical STATUS/TASK_GRAPH** to `e92d135` (docs-only)

---

## Roadmap Awareness Checkpoint

| Metric | Value |
|--------|-------|
| Roadmap alignment score | **8/10** |
| Current position | Wave 7 closed; frozen spine complete; collaboration architecture frontier |
| Dead pieces check | WorkIntake V2 removed from router; `/modules`/`/governance` static; PS planned tabs placeholder |
| Forbidden scope confirmed | No FLEX-02, no runtime tooling, no DB/UI in this realignment |
| Cat sunt in directia stabilita | **78%** |

**Honest opinion:** The FLEX detour was **justified** for runtime recovery and read-model foundation but **mistimed as "the" roadmap** — it ran parallel while APP-AUTH-06G was canonical next. FLEX-02 is **not** the right immediate implementation; ARCH-02 (plan) is. Runtime tooling is done — stop investing there. Highest **operational** value already delivered (frozen spine + mobile individual). Highest **forward** value is collaboration persistence **decision**, not implementation yet.

---

## Artifacts

| Artifact | Path |
|----------|------|
| This plan | `.compound-engineering/workos-roadmap-realignment-01/plan.md` |
| Final report worklog | `docs/worklog/realignment/2026-07-15_workos_roadmap_realignment_01_after_backup_and_flex_foundation.md` |
| Session ledger | `docs/worklog/session/2026-07-15_session_master_backup_runtime_parity_governance_alignment.md` |
| E2E status | `docs/master/workos-e2e/WORKOS_E2E_STATUS.md` |
| Task graph | `docs/master/workos-e2e/WORKOS_E2E_TASK_GRAPH.md` |

---

## Definition of Done (this task)

- [x] Four parallel read-only workstreams completed
- [x] Integrated conclusion answers all 14 prompt questions
- [x] Plan written to `.compound-engineering/workos-roadmap-realignment-01/plan.md`
- [x] Worklog final report with 21 sections + delivery footer
- [x] No code/DB/UI/runtime tooling changes
- [ ] Optional docs-only commit (owner choice)
