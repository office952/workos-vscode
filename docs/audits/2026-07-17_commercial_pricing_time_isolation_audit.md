# WORKOS — Commercial Pricing Time Isolation Audit

**Date:** 2026-07-17  
**Repo:** `C:/w/psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD at audit:** `37a0e2f` (`docs(execution): close te2e-028a visual proof`)  
**Remote:** `https://github.com/office952/workos-vscode.git`  
**Runtime:** FE `http://127.0.0.1:3000` · BE `http://127.0.0.1:8001`  
**Scope:** Audit + focused regression proof only — **no pricing implementation**

### Owner decision (approved for follow-on isolation build)

```text
ACTIVE COMMERCIAL ENGINE = Intake V6 → CommercialPriceProposalService / 7G
ACTIVE ENGINE STATUS = ACCEPTED AND PROTECTED
LEGACY /entities/quotes/price = MUST BE ISOLATED
LEGACY QuoteWizard CALLER = MUST BE REMOVED, DISABLED OR EXPLICITLY BLOCKED
CostEngine per_hour = MUST NOT REMAIN CUSTOMER-PRICING AUTHORITY
AUDIT COMMIT = DA
IMPLEMENTATION = GO
TE2E-028B = NOT STARTED
```

Recorded audit facts accepted by owner:

- active 7G pricing is safe on the V6 spine;
- planned minutes are operational only;
- actual minutes are analysis only;
- Quote and Order snapshots are protected;
- legacy `/entities/quotes/price` is runtime-reachable (isolation approved);
- no active pricing-engine redesign is approved.

---

## 1. Verdict

`LEGACY_PRICING_PATH_REACHABLE`

**Active Intake V6 → Quote Snapshot V2 → Order Snapshot V2 spine:** operational planned/actual minutes do **not** influence customer commercial price. Differential tests pass; Post-Job write-back remains false; TE2E-028A introduced no commercial edge.

**Residual system risk:** `POST /api/v1/entities/quotes/price` + CostEngine `per_hour` + QuoteOrchestrator `total_cost × margin` remain **registered and callable** (QuoteWizard / simulate-cost). That path can still price from minutes × hourly rate. It is **not** the V6 commercial authority, but it is **runtime-reachable**.

Not a `COMMERCIAL_PRICING_BOUNDARY_BREACH` on the active spine (no active reverse write/reprice from execution). Not full `COMMERCIAL_TIME_ISOLATION_PROVEN` for the whole process surface while legacy `/price` remains reachable.

---

## 2. Mini decision

**Today, on the active commercial spine, minutes do not change customer offers.**  
Changing planned minutes (15 vs 150) or actual session minutes changes ExecutionPlan / Post-Job analysis only. Frozen `accepted_commercial_total` and Quote/Order snapshot payloads stay put.

**However:** an operator (or UI) that still calls legacy QuoteWizard `/price` can still hit CostEngine hourly logic. That is a residual reachability risk, not an execution write-back bug.

---

## 3. Repository state

| Check | Result |
|--------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `37a0e2f` — matches expected |
| TE2E-028A commits present | `3420b57`, `5640c36`, `577d43c`, `37a0e2f` |
| Ports | FE 200 · BE 200 |
| Reference data | Orders `92402`/`92403`, fixture `972901` — **read-only** |
| Commit | **NO COMMIT — WAITING FOR OWNER REVIEW** |

---

## 4. Active commercial engine

| Item | Current truth |
|------|----------------|
| Authority | `CommercialPriceProposalService.build_preview` (7G), tag `commercial_price_proposal_7g` |
| Primary V6 endpoint | `GET /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote-dry-run` |
| Direct preview | `POST /api/v1/product-system/commercial-price-preview/{template_code}` |
| Orchestration | `build_intake_v6_priced_quote_dry_run` → 7G → VAT wrap |
| Persist quote totals | `POST .../priced-quote/write` / handoff-to-offer (writes quote from dry-run; does not invent hourly math) |
| Freeze quote | `POST .../quotes/{id}/snapshot-v2` embeds 7G commercial snapshot |
| Freeze order | accept → convert → `OrderSnapshotV2.accepted_commercial_total` + `no_reprice_policy=True` |
| Pricing basis | quantity × commercial unit price (`ml` / `m2` / `piece` / `fixed` / `set`) |
| Frontend callers | Intake V6 Review / commercial spine / handoff — dry-run only for authority |
| Explicit ignores | `FORBIDDEN_HOURLY_TOKENS`: `rate_per_hour`, `estimated_minutes`, `duration_minutes`, `hours`, `per_hour`, … |

### Plain answers

| # | Question | Answer (active 7G / V6) |
|---|----------|-------------------------|
| 1 | Accept minutes? | **No** (forbidden on commercial lines; ignored as price basis) |
| 2 | Accept hours? | **No** |
| 3 | Accept labor cost? | **No** for customer commercial |
| 4 | Multiply time × rate? | **No** |
| 5 | `total_cost × margin`? | **No** for official; diagnostic cost-plus only (`diagnostic_only`) |
| 6 | Fallback internal → customer? | **No** — missing 7G blocks; does not substitute EIC |
| 7 | Frontend authoritative total? | **No** — displays dry-run; gate requires `commercial_price_proposal_7g` |
| 8 | Execution trigger after freeze? | **No** — Post-Job/plan/reality do not import or call 7G |

---

## 5. Time-field map

| Field | Owner | Current use | Commercial influence | Evidence |
|-------|-------|-------------|---------------------:|----------|
| `estimated_minutes` (aggregate/plan) | ProductAggregate / ExecutionPlan V2 | Planning minutes provenance (TE2E-028A) | **No** on V6 spine | preview/persist/materialize; CPP forbid list |
| `planning_minutes_source` | ExecutionPlan V2 / Post-Job | Provenance label | **No** | plan envelope + Post-Job planned source |
| `planned_minutes` (Post-Job) | PostJobTruth | Reconciliation display | **No** | read-only |
| `actual_minutes` / `duration_minutes` | Execution Reality | Session actuals | **No** | reality JSON only |
| `labor_minutes` | Post-Job | Variance analysis | **No** | monetary labor `excluded` |
| `rate_per_hour` / `per_hour` | CostEngine / workcenter_rates | Legacy op cost | **Yes if `/price` used** | CostEngine `line_total = rate_per_hour * hours` |
| `accepted_commercial_total` | Order Snapshot V2 | Frozen customer revenue | Protected from time | convert + Post-Job read |
| `estimated_internal_total` | EIC snapshot | Internal cost baseline | Not customer price | Post-Job planned internal |
| `write_back_performed` | Post-Job / Profitability | Always `false` | N/A | hard-coded |
| `productive_minutes` | — | Absent | — | no matches |

---

## 6. Active call graph

### Commercial (forward only)

```text
Intake V6 workspace
  → GET priced-quote-dry-run
      → CommercialPriceProposalService.build_preview (7G)
      → commercial_totals (+ VAT)
  → priced-quote/write | handoff-to-offer
      → Quotes totals (priced)
  → snapshot-v2
      → QuoteSnapshotV2.commercial_price_proposal_snapshot
  → accept → convert-to-order
      → OrderSnapshotV2.accepted_commercial_total (no_reprice_policy)
```

### Operational (no reverse commercial edge)

```text
Order Snapshot V2 (frozen commercial)
  → ExecutionPlan V2 preview/persist/materialize  (planned minutes)
  → Execution Reality start/end                   (actual minutes)
  → Post-Job / Profitability                      (READ commercial; write_back=false)
```

### Reverse edges found

**None that mutate Quote/Order commercial fields.**

### Legacy forward edge (reachable, not V6 authority)

```text
QuoteWizard / VolumetricLettersQuoteFlow
  → POST /api/v1/entities/quotes/price
      → QuoteOrchestrator → CostEngine
      → minutes/60 × rate_per_hour → total_cost × margin
```

---

## 7. Legacy path classification

| Path | Runtime reachable | Active caller | Uses time | Can affect commercial total | Classification | Action |
|------|------------------:|---------------|----------:|----------------------------:|----------------|--------|
| V6 priced-quote-dry-run → 7G | Yes | Intake V6 | No | Yes (product bases) | `ACTIVE_SAFE` | Keep |
| commercial-price-preview | Yes | Backend/API | No | Yes (product bases) | `ACTIVE_SAFE` | Keep |
| CostEngine `per_hour` via `/price` | Yes | QuoteWizard, quotes API | Yes | Yes | `LEGACY_REACHABLE` | Owner: quarantine / retire / gate |
| QuoteOrchestrator `total_cost × margin` | Yes | `/price` | Indirect | Yes | `LEGACY_REACHABLE` | Same |
| product-system/simulate-cost | Yes | Product System cost sim UI | Yes (CE) | No persist claim; cost sim | `LEGACY_REACHABLE` | Keep as internal sim; not V6 SoT |
| Post-Job write-back | No path | — | — | No | `DEAD` | Keep enforced false |
| Inventory material price-history `/price-history` | Yes | Admin inventory | No (material history) | No (not quote) | `ACTIVE_SAFE` | Out of scope |

---

## 8. TE2E-028A diff review

| Commit | Files | Pricing import? | Commercial write? | Quote/Order mutation? | Finding |
|--------|-------|----------------:|------------------:|----------------------:|---------|
| `5640c36` | aggregate, plan preview/parser, post-job source label, tests, docs, control-center evidence | **No** | **No** | Order seed in tests only; asserts `total_amount` unchanged | Planning integrity only |
| `577d43c` | `ExecutionDetail.tsx`, `execution.ts` type | **No** | **No** | **No** | Null-safe UI projection |
| `37a0e2f` | QA screenshot/SUMMARY, worklog, control-center text | **No** | **No** | **No** | Evidence only |

**Conclusion:** TE2E-028A did **not** introduce a commercial dependency or reverse edge.

---

## 9. Planned-minute differential proof

Isolated ephemeral orders (OID base `973500+`), commercial frozen at **1500.0 RON**.

| Scenario | QC planned minutes | Commercial total | Snapshot hash/total | Post-Job revenue |
|----------|-------------------:|-----------------:|---------------------|------------------|
| A | 15 | 1500.0 | unchanged after plan | 1500.0 |
| B | 150 | 1500.0 | unchanged after plan | 1500.0 |

Also: 7G `build_preview` with polluted `estimated_minutes` / `rate_per_hour` in quote_input → **same `commercial_total`** as clean input.

Test: `test_planned_minutes_15_vs_150_same_commercial_different_plan`  
Test: `test_cpp_commercial_total_ignores_quote_input_minutes`

---

## 10. Actual-minute differential proof

One frozen order; reality mutated only.

| State | Actual minutes | Variance | `write_back` | Order `total_amount` | Snapshot JSON |
|-------|---------------:|---------:|-------------:|---------------------:|---------------|
| 1 | not_captured | — | false | 1500.0 | unchanged |
| 2 | 10 | −5 vs plan 15 | false | 1500.0 | unchanged |
| 3 | 180 | +165 | false | 1500.0 | unchanged |

Test: `test_actual_minutes_states_do_not_mutate_frozen_commercial`

---

## 11. Snapshot immutability proof

| Layer | Enforcement | Evidence |
|-------|-------------|----------|
| Code | `no_reprice_policy=True` on Order Snapshot V2 convert; plan preview ignores pricing sources; Post-Job read-only | convert service + persist FORBIDDEN import list + Post-Job |
| Tests | Diff tests assert snapshot JSON / accepted total / content_hash unchanged | this audit suite + TE2E-028A preserve `total_amount` |
| Runtime | Order `972901` Post-Job revenue `1500.0`, `write_back_performed=false` | `GET /api/v1/execution/972901/post-job-truth` |
| Plan after freeze | Plan create writes `execution_plan` + readiness flags only | DB write map below |

---

## 12. Database write map

| Trigger | Service | Models/tables written | Financial field written? | Commercial side effect |
|---------|---------|------------------------|-------------------------:|------------------------|
| Plan preview | `build_execution_plan_v2_preview` | none | No | None |
| Plan persist | `create_execution_plan_v2_from_order` | `execution_plan`; `orders.readiness_snapshot` flags | No | None |
| Materialize | `materialize_execution_plan_v2_operational_tasks` | `execution_plan.tasks_json`; readiness flag | No | None |
| Task start/end | `ExecutionRealityService` | `execution_reality` sessions / actual minutes | No | None |
| Post-Job read | `PostJobTruthService.build_for_order` | **none** | No | Reads frozen revenue only |
| Post-Job refresh | same | **none** | No | None |
| 7G dry-run | CPP | none (preview) | No write | Computes commercial (product bases) |
| Legacy `/price` | QuoteOrchestrator | quote price fields | **Yes** | **Legacy commercial** |

---

## 13. UI wording result

| Surface | Finding | Class |
|---------|---------|-------|
| Intake V6 commercial / dry-run | Product-basis totals; no “price by hour” | Safe |
| Post-Job / Plan vs execuție | Shows planned/actual minutes; “minutes only”; write-back false | Internal analysis display |
| Execution detail | Planning minutes display | Operational |
| QuoteWizard | Still documents/calls `/entities/quotes/price` | **Legacy UI path** (risk if used) |
| Governance ownership | Pricing owns commercial; Post-Job read-only; freeze language | Correct substance |
| Explicit “not hourly” on `/governance` body | Stronger on `/modules` Control Center (“Orele/minutele nu sunt autoritate…”) than Governance tabs | Partial wording coverage |

No calculation defect found on V6 UI. Legacy QuoteWizard remains a reachable hourly-capable path.

---

## 14. Modules / Governance result

| Surface | Expected substance | Classification |
|---------|--------------------|----------------|
| `/modules` | Pricing owns customer price; ExecutionPlan planned; Reality actual; Post-Job read-only; minutes not commercial authority | `CURRENT_CORRECT` |
| `/governance` | UI does not own commercial cost; Quote/Order freeze; ownership matrix aligned; pricing authority owner gate | `PARTIAL` (freeze + ownership clear; explicit “not hourly” stronger on Modules/Control Center than Governance copy) |

No page updates performed (evidence-only update deferred to owner review).

---

## 15. Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest `
  tests/test_commercial_pricing_time_isolation_audit.py `
  tests/test_te2e_028a_planning_minute_source.py `
  tests/test_commercial_price_proposal_preview.py::test_estimated_minutes_not_commercial_price `
  tests/test_commercial_price_proposal_preview.py::test_no_rate_per_hour_as_price_basis `
  tests/test_quote_snapshot_v2.py::test_no_rate_per_hour_commercial_path `
  tests/test_profitability_analysis.py -q --tb=short
```

**Result:** `23 passed`

New file (uncommitted): `backend/tests/test_commercial_pricing_time_isolation_audit.py`

---

## 16. Runtime comparison

| Value | Baseline (`972901`) | Planned minutes changed (pytest A/B) | Actual minutes changed (pytest S1–S3) | Must stay equal? | Result |
|-------|--------------------:|-------------------------------------:|--------------------------------------:|-----------------:|--------|
| Commercial preview (7G) | product bases | polluted minutes ignored | N/A | YES | PASS |
| Quote / Order commercial total | 1500.0 | 1500.0 / 1500.0 | 1500.0 | YES | PASS |
| Quote Snapshot payload | frozen | unchanged | unchanged | YES | PASS |
| Order Snapshot payload | frozen | unchanged | unchanged | YES | PASS |
| Final price (`total_amount`) | 1500.0 | 1500.0 | 1500.0 | YES | PASS |
| Planned minutes (QC) | 15 | 15 vs 150 | 15 | NO | PASS (differs) |
| Actual minutes | not_captured | — | 10 → 180 | NO | PASS (differs) |
| Post-Job variance | missing_actual | — | changes | NO | PASS |
| write_back | false | false | false | YES — false | PASS |

Endpoints: `GET /api/v1/execution/972901/post-job-truth`; OpenAPI still lists `POST /api/v1/entities/quotes/price`.

---

## 17. Risks and gaps

1. **Legacy `/price` + CostEngine hourly** still registered — QuoteWizard can still price from minutes.  
2. **Shared field name** `estimated_minutes` on aggregate ops (planning) vs CostEngine ops (legacy cost) — dual-use naming hazard if templates feed CE.  
3. **Governance copy** does not state “not hourly” as explicitly as Modules/Control Center.  
4. **Labor money** remains excluded in Post-Job (intentional TE2E-028 residual) — not a commercial leak.  
5. Diagnostic cost-plus markup exists beside 7G — must stay non-authoritative (currently tagged).

---

## 18. Files created or changed

| Path | Status |
|------|--------|
| `docs/audits/2026-07-17_commercial_pricing_time_isolation_audit.md` | Created (this file) |
| `docs/worklog/realignment/2026-07-17_commercial_pricing_time_isolation_audit.md` | Created |
| `backend/tests/test_commercial_pricing_time_isolation_audit.py` | Created — **uncommitted** pending owner review |

No product/pricing implementation changes.

---

## 19. Commit status

`NO COMMIT — WAITING FOR OWNER REVIEW`

Staging left empty for this audit.

---

## 20. Owner conclusion

```text
MINUTELE INFLUENTEAZA OFERTA = NU
PLANNED MINUTES = OPERATIONAL ONLY
ACTUAL MINUTES = ANALYSIS ONLY
QUOTE SNAPSHOT = PROTECTED
ORDER SNAPSHOT = PROTECTED
INTERNAL COST = SEPARATE
HOURLY PRICING = INACTIVE
LEGACY PRICING = REACHABLE
IMPLEMENTATION REQUIRED = NU
```

Notes for owner reading of the block:

- **MINUTELE… = NU** refers to the **active V6 / 7G / Snapshot V2 spine**.  
- **HOURLY PRICING = INACTIVE** as **customer commercial authority** on that spine.  
- **LEGACY PRICING = REACHABLE** means `/price` + CostEngine hourly math still exists for QuoteWizard — residual quarantine candidate, not an automatic build in this audit.

If owner requires whole-process “unreachable legacy” before accepting isolation as absolute, next step is an **owner-approved legacy retire/gate build** (separate from TE2E-028B).

---

## 21. Metodă de lucru și logica abordării

1. Locked repo gate at `37a0e2f` — no branch switch.  
2. Separated **active commercial authority** (import + router + frontend callers) from **legacy registered** paths.  
3. Searched time/money fields and classified by authority, not by filename.  
4. Proved isolation with **differential** fixtures (15 vs 150 planned; 0/10/180 actual) while asserting snapshot immutability.  
5. AST-checked execution services for absence of pricing imports (forbidden-string lists alone are insufficient).  
6. Reviewed TE2E-028A diffs file-by-file for commercial edges.  
7. Checked Modules/Governance honesty without editing policies.  
8. **No pricing implementation** — audit only; TE2E-028A remains closed; TE2E-028B not started.

---

## 22. Next safe step

**Wait for owner review.**

Do **not** start TE2E-028B.  
Do **not** silently delete or rewire `/price` without an owner-approved build.

Optional owner choices after review:

- Accept active-spine isolation as sufficient business proof; track legacy `/price` as separate quarantine; or  
- Open a dedicated “Legacy quote `/price` retire / hard-gate” build.

---

## Roadmap awareness checkpoint

| Item | Score / note |
|------|----------------|
| Roadmap awareness | **8/10** |
| Current position | Post Wave 7 + TE2E-028A UI closed; commercial time isolation audited |
| Cat sunt in directia stabilita | **~85%** on active spine isolation; legacy `/price` prevents 100% process-wide claim |
| Dead pieces check | Post-Job write-back path dead; legacy `/price` alive |
| Forbidden scope | No pricing refactor; no TE2E-028B; no reference mutation |
| Parallel-flow check | V6 spine vs QuoteWizard `/price` — both registered |
| Wave 7 integrity | Preserved (refs RO) |
| UTF-8 integrity | Untouched |
| Current Truth Control Center | Consistent (minutes not commercial authority) |
| UI-TRUTH-01C integrity | Untouched |
| TE2E-028A closure integrity | Intact; green tests |
| Commercial-boundary confidence | **High on active spine; medium process-wide** until legacy gated |
