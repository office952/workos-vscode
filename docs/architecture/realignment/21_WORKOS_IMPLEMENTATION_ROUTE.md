# 21 — WorkOS Implementation Route

**Version:** 1.0.1  
**Status:** Controlled implementation route synced to current validated runtime/doc truth  
**Date:** 2026-06-30  
**Branch context:** `feature/step-7g-commercial-price-proposal` — HEAD `1e32692`  
**Source audits:** Full Flow Alignment Audit (`2026-06-30_full_flow_alignment_audit.md`); Step 9 semantic alignment + owner review worklogs  
**Verdict accepted:** `ALIGNED_MAP_COMPLETE_WITH_GAPS`

**Related:** [20_ROADMAP_STEPS_7G_TO_12.md](./20_ROADMAP_STEPS_7G_TO_12.md) (step definitions) · [00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md](./00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md) (target architecture)

---

## 1. Purpose

This document defines the **controlled implementation route** for WorkOS from the current validated V2 spine forward to operational shop reality, Employee Mobile, and post-job profitability.

It is **not**:

- a generic roadmap (see doc 20 for step catalog);
- a task manager or sprint board;
- permission to implement without explicit **owner GO** per phase.

It **is**:

- the ordered sequence of phases, gates, and forbidden paths derived from code + runtime audits;
- the interconnection map between systems at each handoff;
- the checklist for when materialization, assignment, sessions, and Employee Mobile become safe.

**Owner rule:** No phase marked “Owner GO required” may start runtime work until owner confirms in writing.

---

## 2. Current validated spine

Canonical V2 chain (pilot: `TPL-VOLUMETRIC-LETTERS_v2`; fixture order `88002`, snapshot `QSN2-2026-0003`, plan `id=2`):

```
Intake V6 workspace
  → Form contract / mini-modules
  → ProductDefinition builder
  → ProductAggregate + task_rules
  → CommercialPriceProposal preview
  → EstimatedInternalCost preview
  → Quote Snapshot V2 freeze
  → Accept + Owner gates
  → Order Snapshot V2
  → ExecutionPlan V2 preview/persist
  → Materialization audit GET
  → operational_tasks / sessions (later)
  → ProfitabilityAnalysis
```

| Layer | Status | Evidence / notes |
| ----- | ------ | ---------------- |
| **Intake V6 workspace** | **VALIDATED_WITH_GUARDS** | `intake_v6_workspaces.payload_json`; routes `/api/v1/intake-v6/*`; FE `/intake-v6/:id/operator` |
| **Form System** | **PARTIAL** | `GET /api/v1/intake-v6/form-contract/{template}`; pilot template only; registry-derived bindings |
| **ProductSystem (template/dossier/modules)** | **PARTIAL** | Parent row often thin; dossier + linked modules carry truth; volumetric v2 wired |
| **ProductDefinition builder** | **VALIDATED** | `product_definition_builder_service.py`; read-only compile; fail-closed gates |
| **ProductAggregate + task_rules** | **VALIDATED_WITH_GUARDS** | `product_aggregate_service.py`; `task_contract.task_rules` from dossier; duplicate lateral ops open (DEC-003/004) |
| **CommercialPriceProposal (7G)** | **IMPLEMENTED_PREVIEW_ONLY** | `commercial_price_proposal_service.py`; mp/ml/buc rules; preview implemented, not canonical default path |
| **EstimatedInternalCost (7H)** | **IMPLEMENTED_PREVIEW_ONLY** | `estimated_internal_cost_service.py`; separate from CPP; no CE/QO on V2 path |
| **Quote Snapshot V2** | **VALIDATED_WITH_GUARDS** | Freeze/accept/convert validated; snapshot `QSN2-2026-0003` |
| **Order Snapshot V2** | **VALIDATED** | `orders.snapshot_v2_json`; `no_reprice_policy=True`; no plan at convert |
| **ExecutionPlan V2 preview** | **VALIDATED** | `POST .../execution/plan-v2/preview/{order_id}`; 12 tasks / 17 ops |
| **ExecutionPlan V2 persist draft** | **VALIDATED_WITH_GUARDS** | Plan `id=2`; idempotency; HTTP fresh persist verified: POST `from-order/88002` returned `already_exists` for plan id=2; no duplicate plan, no execution_tasks, no sessions (worklog `2026-06-30_step9_http_fresh_persist_verification.md`; commit `e9f8033`; 107 pytest) |
| **Materialization audit GET** | **IMPLEMENTED_PREVIEW_ONLY** | `GET .../materialization-audit`; dry-run only |
| **ExecutionTasks / operational_tasks** | **BLOCKED_NEEDS_OWNER_GO** | `operational_tasks[]` empty; POST materialize not exercised |
| **Workcenters on planned tasks** | **PARTIAL** | All 12 tasks: `workcenter` null on fixture (DEC-005) |
| **estimated_minutes on planned tasks** | **PARTIAL** | All null; `PLANNING_MINUTES_SOURCE_REQUIRED` (DEC-006) |
| **Employees / skills / eligibility** | **PARTIAL** | Foundation registries exist; not linked to planned graph |
| **ExecutionActuals / sessions** | **FROZEN** | Step 11+; guards block on `v2_not_materialized` |
| **ProfitabilityAnalysis** | **PARTIAL** | MVP GET + ExecutionDetail panel; `actual_margin_*` null |
| **UI labels (Step 11)** | **PARTIAL** | Step 9B read-only truth layer and some doc/runtime labels are aligned; broader labeling sweep still pending |
| **Legacy `/price` path** | **DEAD_LEGACY_RISK** | Callable; cost-plus / per_hour — not canonical V2 |
| **Pricing Registry separation (7I)** | **NOT_STARTED** | Unified hub still active for legacy |
| **Step 12 cleanup** | **FROZEN** | After canonical route stable; per-piece owner GO |

---

## 3. System interconnection map

| From | To | Link mechanism | Evidence | Strength | Current gap |
| ---- | -- | -------------- | -------- | -------- | ----------- |
| Intake V6 | Form System | `template_code` → `IntakeV6ModularFormContractService` | `GET /intake-v6/form-contract/{template}` | **STRONG** (pilot) | Only volumetric v2 fully bound |
| Form System | ProductDefinition | Field bindings → workspace paths → module activation | `VOLUMETRIC_FIELD_BINDINGS`; PD builder reads workspace | **MEDIUM** | Hardcoded pilot bindings |
| ProductDefinition | ProductAggregate | PD output + parent template + dossier + module links | `ProductAggregateService.build()` | **STRONG** | Parent `components_json` empty; dossier merge |
| ProductAggregate | CommercialPriceProposal | Geometry keys + active modules + `commercial_rules_volumetric_v2` | `CommercialPriceProposalService.build_preview()` | **STRONG** | Not sole path if `/price` used |
| ProductAggregate | EstimatedInternalCost | BOM adapter + internal rules + inventory | `EstimatedInternalCostService.build_preview()` | **STRONG** | WC blockers reclassified in docs; legacy conflates |
| CPP + EIC + PD + Aggregate | Quote Snapshot V2 | `QuoteSnapshotV2Service.build_preview()` / freeze | `POST .../quote-snapshot-v2/*` | **STRONG** | Template scope limited |
| Quote Snapshot V2 | Order Snapshot V2 | Accept gate + `convert_accepted_quote_snapshot_v2_to_order` | Intake V6 commercial spine | **STRONG** | New quotes only on V2 path |
| Order Snapshot V2 | ExecutionPlan V2 | Frozen `product_aggregate_snapshot.task_contract.task_rules` | `execution_plan_v2_preview_service.py` | **MEDIUM** | WC/minutes null; linear deps |
| ExecutionPlan V2 | Materialization Audit | Dry-run from `planned_tasks[]` in persisted envelope | `execution_plan_v2_materialization_audit_service.py` | **STRONG** (read-only) | POST materialize blocked |
| ExecutionPlan V2 | ExecutionTasks (`operational_tasks[]`) | `POST .../materialize-tasks/{order_id}` | `execution_plan_v2_materialize_service.py` | **MISSING** (blocked) | Owner GO + upstream fixes |
| ExecutionTasks | Workcenters | `machine_requirement.workcenter` on task dict | Preview resolves from aggregate op / PD role | **WEAK** | All null on live fixture |
| ExecutionTasks | Employees | `execution_task_assignment_service.assign_plan_task` | Requires materialized `operational_tasks[]` | **MISSING** | No eligibility model on planned graph |
| Workcenters | Machines / utilaje | Foundation registry + `/utilaje` UI | `foundation_workcenters`; capacity boundary doc 14 | **PARTIAL** | Not wired to frozen snapshot ops |
| ExecutionActuals | ProfitabilityAnalysis | Session minutes vs quoted/estimated baselines | `profitability_analysis_service.py` | **MISSING** (runtime) | Actuals null in MVP |
| Order / Quote snapshots | ProfitabilityAnalysis | `accepted_commercial_total`, `estimated_internal_total` | GET profitability endpoint | **MEDIUM** | Revenue side only today |
| UI | Backend read models | Intake V6, ExecutionDetail, product-system panels | `App.tsx` routes | **MEDIUM** | Labels incomplete (Step 11) |

**Link rule:** Each downstream layer must treat upstream **frozen JSON** as authority. ExecutionPlan must not re-read live Intake or reprice from registry at plan time.

---

## 4. Implementation phases from here

Phases are **sequential with explicit gates**. Parallel work is allowed only where noted and must not violate forbidden paths.

### Faza 0 — Owner decision cleanup before materialization

Resolve open semantic decisions from Step 9 owner review:

| ID | Topic |
| -- | ----- |
| **DEC-003** | RETURN lateral duplicate — parent `side_forming` / `return_face_bonding` canonical vs module `RETURN_PROFILE_*` |
| **DEC-004** | Painting canonical — parent `painting` vs module `PAINTING` |
| **DEC-005** | Workcenter source policy — enrich parent aggregate at compile vs module alias WC vs manual post-materialize |
| **DEC-006** | `estimated_minutes` source — dossier time assumptions vs capacity registry vs null-with-warn |
| **DEC-007** | Dependencies / DAG — linear MVP vs finish-aware parallel branches |
| **DEC-009** | POST materialize remains **blocked** until DEC-003/004/005/007 resolved |

Also track (non-blocking for materialize by default): **DEC-001** (svg_geometry_analysis), **DEC-002** (premount_bar_preparation).

**Exit:** Owner answers recorded; DEC-009 stays blocked until minimum DEC-003, DEC-004, DEC-005, DEC-007 answered.

---

### Faza 1 — Step 9B UI read-only visibility

**Goal:** Operator sees plan truth with gaps visible — no writes.

**Current state:** Implemented on ExecutionDetail for the validated fixture path; adjacent surfaces still pending.

- Show persisted `planned_tasks[]`, `planned_operations[]`, orphan ops
- Badge: workcenter null, minutes null, duplicate lateral warnings, audit-only
- **No** materialize button, **no** sessions, **no** Employee Mobile
- Safe per DEC-008 recommendation (`SAFE_FOR_UI_READONLY_ONLY`)

**Depends on:** Faza 0 decisions documented (can proceed in parallel with owner filling DEC table).

---

### Faza 2 — Upstream task contract enrichment

**Goal:** Fix snapshot-at-freeze quality so new orders carry correct operational metadata.

- Parent `task_rules` canonical; module codes as aggregate aliases only
- Workcenter populated on parent-priced operations at aggregate compile
- Operation role mapping aligned with dossier + mini-modules
- Dependency model beyond immediate-predecessor linear chain
- Exclude module duplicate rows from ever becoming operational tasks

**Systems touched (future GO):** `product_aggregate_service`, dossier JSON, possibly `product_definition_builder`, snapshot re-freeze on **new** quotes only — never retroactive reprice.

**Exit:** New fixture order shows non-null WC on planned tasks (where policy defines source); no duplicate lateral in materialization audit.

---

### Faza 3 — Materialization GO

**Goal:** `POST .../execution/plan-v2/materialize-tasks/{order_id}` exercised on controlled fixture.

**Preconditions:** DEC-003, DEC-004, DEC-005, DEC-007 answered; Faza 2 upstream enrichment validated on new snapshot chain.

- Idempotent materialize → `operational_tasks[]` inside `tasks_json`
- Sets `execution_tasks_created: true`
- **Still no** sessions, **no** Employee Mobile, **no** pricing recalculation, **no** `/price`

**Verification:** Materialization audit GET matches POST dry-run; operational readiness status → `v2_operational_ready`.

---

### Faza 4 — Workcenters / utilaje connection

**Goal:** Operation → workcenter → machine/utilaj chain trustworthy for scheduling.

- Enrich aggregate operations with authoritative WC codes
- Link workcenter registry to utilaje capacity metadata (doc 14 boundary)
- Capacity hints remain **non-commercial** (no hourly client pricing)

**Depends on:** Faza 3 materialized tasks with WC populated.

---

### Faza 5 — Employees / roles / skills eligibility

**Goal:** Know **who can** work a task before assignment.

- employee → role → skill → workcenter/operation eligibility matrix
- Task eligibility rules on `operational_tasks[]` (read model first)
- Assignment (`assign_plan_task`) only after eligibility defined

**Depends on:** Faza 4 workcenter truth on operational tasks.

**Note:** Assignment is later than eligibility; do not conflate.

---

### Faza 6 — Execution reality / sessions / actuals (Step 11)

**Goal:** Real minutes and material deviations post-order.

- `POST .../execution/reality/start-task` / end-task
- ExecutionActuals populate; no mutation of accepted commercial price
- Guards: only when `v2_operational_ready`

**Depends on:** Faza 3 materialization stable; Faza 4–5 recommended before production GO.

---

### Faza 7 — ProfitabilityAnalysis post-job truth (Step 10 completion)

**Goal:** quoted vs estimated vs **actual** margin.

- `actual_total_cost`, `actual_margin_*` when HR/inventory costing available
- Learning loop recommendations — no write-back to quote

**Depends on:** Faza 6 actuals; owner GO for HR/inventory cost formulas.

---

### Faza 8 — Step 11 UI labels / deprecation

**Goal:** No misleading preview-as-official labels.

**Current state:** Partial. ExecutionDetail and core realignment docs are improved, but orders/quotes/product-related surfaces still need the broader sweep.

- preview vs official vs internal vs legacy vs audit-only vs executable
- Intake live calc vs Snapshot V2 vs draft `grand_total=0`
- Frozen paths labeled (`/price`, V3/V4 task dry-run)

**Depends on:** Can start partial parallel with Faza 1; must complete before declaring canonical path “production official”.

---

### Faza 9 — Step 12 dead pieces cleanup

**Goal:** Remove or archive classified DEAD pieces **one at a time**.

- Only after canonical route proven on real jobs
- Owner GO **per piece** (doc 19)
- Never before Faza 3–6 stable for volumetric pilot

---

### Faza 10 — Employee Mobile final-final

**Goal:** Mobile operator consumes materialized, assigned, session-ready tasks.

**Preconditions (all required):**

1. Task graph stable (Faza 2–3)
2. Workcenter/machine connection (Faza 4)
3. Eligibility model (Faza 5)
4. Sessions/actuals hardened (Faza 6)
5. UI labels clear (Faza 8)

**Forbidden before Faza 10:** Employee Mobile as production driver for V2 orders with empty `operational_tasks[]`.

---

### Parallel track — Commercial / registry (7G–7I) — not blocking Faza 0–3 but required for scale

| Step | Focus | Status | Relation to execution phases |
| ---- | ----- | ------ | ---------------------------- |
| **7G** | CPP as default commercial path | Preview exists | Already in Step 8 snapshot; extend coverage |
| **7H** | EIC non-hourly in CE separation | Preview exists | Side B of snapshot |
| **7I** | Pricing Registry tab separation | NOT STARTED | Reduces legacy `/price` temptation |

Legacy `/price` deprecation aligns with Faza 8–9, not before V2 snapshot is default for all new quotes.

---

## 5. Gate checklist per phase

| Phase | Entry criteria | Allowed changes | Forbidden changes | Exit criteria | Owner GO required |
| ----- | -------------- | --------------- | ----------------- | ------------- | ----------------- |
| **0 — Owner decisions** | Full Flow + Step 9 semantic audits complete | Docs, decision table updates | Any runtime / POST materialize | DEC-003/004/005/007/009 recorded | **Yes** (decisions themselves) |
| **1 — Step 9B UI read-only** | Plan persist validated; DEC-008=A | Read-only UI panels, badges | Materialize, sessions, assignment, pricing | UI shows 12 tasks, gaps labeled | **Yes** for UI scope |
| **2 — Upstream enrichment** | DEC-003/004/005/007 answered | Aggregate/dossier/task_rules, snapshot re-freeze on new quotes | Retroactive quote reprice; `/price`; CE rewrite | New fixture: WC on parent ops; no duplicate materialization candidates | **Yes** |
| **3 — Materialization GO** | Faza 2 exit + DEC-009=B | POST materialize on fixture; pytest | Sessions, Employee Mobile, pricing | `operational_tasks[]` populated; readiness `v2_operational_ready` | **Yes** |
| **4 — WC / utilaje** | Faza 3 exit | WC on ops, utilaje linkage, capacity metadata | Commercial hourly pricing | WC resolvable on all materialized tasks | **Yes** |
| **5 — Employees / eligibility** | Faza 4 exit | Eligibility read models, role/skill maps | Forced assignment without rules | Eligibility query per operational task | **Yes** |
| **6 — Sessions / actuals** | Faza 3 exit (min); Faza 4–5 recommended | start/stop, ExecutionReality | Quote/order price mutation | Sessions on fixture; actual minutes stored | **Yes** |
| **7 — Profitability complete** | Faza 6 exit | Actual cost formulas, margin fields | Write-back to quote | `actual_margin_*` non-null on closed job | **Yes** |
| **8 — UI labels** | Awareness of all phases | Copy/labels/banners only | Layout redesign | Zero unlabeled preview-as-official | **Yes** |
| **9 — Step 12 cleanup** | Faza 3–8 stable on pilot | Archive/delete per piece | Bulk auto-delete | DEAD pieces removed with evidence | **Yes per piece** |
| **10 — Employee Mobile** | Faza 3–6 + 8 stable | Mobile task consume/start | Mobile before materialize | Mobile E2E on materialized order | **Yes** |

---

## 6. Decisions required before materialization

| Decision ID | Topic | Options | Recommended option | Blocks materialization? | Owner answer |
| ----------- | ----- | ------- | ------------------ | ----------------------- | ------------ |
| **DEC-001** | `svg_geometry_analysis` orphan op | A) non-operational analytics; B) merge READINESS; C) new task_rule | **A** — non-operational analytics | No (if labeled) | **PENDING_OWNER** |
| **DEC-002** | `premount_bar_preparation` | A) BOM-only; B) conditional task_rule when premount active | **A** default; **B** when premount selected | Yes if premount jobs need fab without rule | **PENDING_OWNER** |
| **DEC-003** | RETURN lateral duplicate / canonical `side_forming` | A) parent canonical; B) module canonical; C) both (reject) | **A** — parent canonical; module = aggregate alias only | **Yes** | **PENDING_OWNER** |
| **DEC-004** | `PAINTING` module duplicate | A) parent `painting`; B) module `PAINTING`; C) both | **A** — parent canonical | **Yes** | **PENDING_OWNER** |
| **DEC-005** | Workcenter source policy | A) enrich parent at compile; B) map module alias WC; C) manual post-materialize; D) registry-only pass | **A + B** upstream before materialize | **Yes** for scheduling quality | **PENDING_OWNER** |
| **DEC-006** | `estimated_minutes` source | A) null + warn; B) dossier time_assumptions; C) capacity registry; D) planner entry only | **B or C** long-term; **A** short-term | No for audit dry-run; **Yes** for production scheduling GO | **PENDING_OWNER** |
| **DEC-007** | Dependency model | A) linear MVP; B) finish-aware DAG; C) parallel branches (template/premount) | **B** before production GO; **A** ok for draft audit | **Yes** for realistic shop scheduling | **PENDING_OWNER** |
| **DEC-008** | Step 9B UI before gap fix | A) proceed with gap badges; B) wait for upstream | **A** — proceed read-only | No | **PENDING_OWNER** |
| **DEC-009** | POST materialize | A) remain blocked; B) GO after DEC-003/004/005/007 | **A** — remain blocked until upstream | **Yes** — gate for all materialize | **PENDING_OWNER** |

**Minimum before materialize GO:** DEC-003, DEC-004, DEC-005, DEC-007 answered; DEC-009 explicitly set to B by owner; Faza 2 enrichment validated.

---

## 7. What must never happen

| Rule | Rationale |
| ---- | --------- |
| **No commercial hourly pricing** | P-Media does not offer “ore × tarif” to clients |
| **No `/price` for new canonical V2 path** | Mixed cost-plus model; frozen intent |
| **No CostEngine as commercial price generator** | CE = internal cost calculator only (target) |
| **No QuoteOrchestrator as canonical V2 path** | `_apply_commercial` cost-plus deviation |
| **No Employee Mobile before Faza 10** | Requires materialized + labeled task graph |
| **No `operational_tasks[]` write before materialization GO** | DEC-009 + Faza 2 prerequisites |
| **No sessions before Step 11 / Faza 6 GO** | Actuals without plan truth creates false profitability |
| **No Step 12 cleanup before canonical route stable** | Risk removing still-used legacy bridges |
| **No UI labels implying preview is official** | Misleading operator actions |
| **No retroactive quote reprice from actuals** | Accepted commercial promise is frozen |
| **No materialize with duplicate lateral ops unresolved** | Double execution risk (DEC-003/004) |
| **No assignment without materialized operational tasks** | Parser returns empty from `planned_tasks` only readers |

---

## 8. Current top risks

| # | Risk | Severity | Phase that mitigates |
| - | ---- | -------- | -------------------- |
| 1 | Duplicate lateral module ops materialized alongside parent tasks | **CRITICAL** | Faza 0 + 2 (DEC-003/004) |
| 2 | All planned tasks `workcenter` null | **CRITICAL** | Faza 0 + 2 + 4 (DEC-005) |
| 3 | POST materialize exercised before owner decisions | **CRITICAL** | Faza 0 (DEC-009=A) |
| 4 | `estimated_minutes` null — no capacity baseline | **HIGH** | Faza 0 + 2 (DEC-006) |
| 5 | Linear dependency chain wrong for vinyl/paint/template branches | **HIGH** | Faza 0 + 2 (DEC-007) |
| 6 | Employees/skills disconnected from task graph | **HIGH** | Faza 5 |
| 7 | Utilaje/workcenters admin-only, not on frozen ops | **HIGH** | Faza 4 |
| 8 | Legacy `/price` still callable for quotes | **HIGH** | 7I + Faza 8–9 |
| 9 | UI preview vs official snapshot confusion | **MEDIUM** | Faza 1 + 8 |
| 10 | Doc lag (7G NOT STARTED vs preview implemented; V3 catalog note stale) | **MEDIUM** | Docs sync after each phase exit |

---

## 9. Recommended immediate next step

**Owner decisions DEC-003 / DEC-004 / DEC-005 first** (with DEC-007 and DEC-009 explicitly kept blocked until answered).

**Why:**

- Materialization is **BLOCKED_NEEDS_OWNER_GO** (DEC-009=A today).
- Step 9B UI read-only is **safe** but does **not** resolve duplicate lateral ops or null workcenters — it only surfaces them.
- Without DEC-003/004, materialize risks **double execution** (parent + module lateral).
- Without DEC-005, materialized tasks have **no authoritative workcenter** for scheduling or later assignment.
- Faza 2 upstream enrichment depends on these decisions; implementation before owner answers risks rework.

**After owner answers:** Either Faza 1 (Step 9B UI read-only with gap badges) in parallel with Faza 2 scoping, or Faza 2 directly if owner prefers fix-before-UI.

---

## 10. Status summary

| Area | Current status | Next action |
| ---- | -------------- | ----------- |
| Intake V6 product truth | VALIDATED_WITH_GUARDS | Extend only with new template GO |
| Form System | PARTIAL | Pilot bindings sufficient for volumetric |
| ProductSystem template/dossier | PARTIAL | Dossier task_rules + module dedup policy (DEC-003/004) |
| ProductDefinition | VALIDATED | No change until Faza 2 GO |
| ProductAggregate + task_rules | VALIDATED_WITH_GUARDS | Upstream WC + alias policy (Faza 2) |
| CommercialPriceProposal | IMPLEMENTED_PREVIEW_ONLY | 7G extend; docs sync |
| EstimatedInternalCost | IMPLEMENTED_PREVIEW_ONLY | 7H/7I separation |
| Quote / Order Snapshot V2 | VALIDATED_WITH_GUARDS | Default for new volumetric quotes |
| ExecutionPlan V2 draft | VALIDATED_WITH_GUARDS | Step 9B UI or hold for Faza 0 |
| Materialization | BLOCKED_NEEDS_OWNER_GO | Owner DEC-003/004/005/007/009 |
| Workcenters on tasks | PARTIAL | DEC-005 → Faza 2/4 |
| Employees / skills | PARTIAL | Faza 5 after materialize |
| Sessions / actuals | FROZEN | Faza 6 after materialize GO |
| ProfitabilityAnalysis | PARTIAL | Faza 7 after actuals |
| UI labels | NOT_STARTED | Faza 1 + 8 |
| Legacy `/price` | DEAD_LEGACY_RISK | Deprecate in Faza 8–9 |
| Employee Mobile | FROZEN | Faza 10 final-final |

---

## Appendix A — When is it safe to…?

| Question | Safe when | Not safe now because |
| -------- | --------- | -------------------- |
| **Materialize tasks?** | DEC-003/004/005/007 answered; Faza 2 validated; DEC-009=B; controlled fixture | Duplicates + null WC + blocked GO |
| **Link employees to tasks?** | Faza 3 materialized + Faza 5 eligibility defined | `operational_tasks[]` empty; no eligibility |
| **Link utilaje/workcenters?** | Faza 4 after WC on frozen ops (DEC-005 applied) | Parent ops WC null on order 88002 |
| **Start sessions / actuals?** | Faza 6 GO; `v2_operational_ready` on order | Guards block `v2_not_materialized` |
| **Employee Mobile?** | Faza 10 — all of Faza 3–6 + 8 stable | Mobile before materialize forbidden |

---

## Appendix B — Verification commands (reference — run only with owner GO)

| Phase | Suggested verification |
| ----- | ---------------------- |
| Step 8 chain | Targeted pytest quote snapshot accept/convert suites |
| Step 9 preview/persist | `POST .../execution/plan-v2/preview/{order_id}`; persist idempotency |
| Materialization audit | `GET .../materialization-audit` — no POST |
| Materialize (Faza 3+) | `POST .../materialize-tasks/{order_id}` on fixture only |
| Operational readiness | `execution_plan_operational_readiness_service` status codes |
| Profitability MVP | `GET /api/v1/profitability-analysis/order/{order_id}` |

Full pytest suite not required for documentation-only tasks.

---

## Document history

| Version | Date | Change |
| ------- | ---- | ------ |
| 1.0.0 | 2026-06-30 | Initial route from Full Flow Alignment Audit + Step 9 semantic owner review |
| 1.0.1 | 2026-06-30 | Step 9 HTTP fresh persist status: NEEDS_VERIFICATION → PASS / VALIDATED_WITH_GUARDS |
