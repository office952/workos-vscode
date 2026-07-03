# 13 — Order Lifecycle Flow

**Current status:** VALIDATED_WITH_GUARDS

---

## 1. Purpose

Document the **complete real order path** from client request / Intake through configured product, offer, owner approval, order, execution plan draft, and **readiness for execution** — what becomes official when, what is blocked, and where it fails.

**Reference fixture:** order `88002`, `quote_snapshot_v2_id=3`, `execution_plan.id=2`, snapshot `QSN2-2026-0003`.

---

## 2. Lifecycle stages

| Stage | UI page | Backend route/service | Data created/read | Source of truth | Status | Risk |
| ----- | ------- | --------------------- | ----------------- | --------------- | ------ | ---- |
| 1. Client request / Intake entry | `/intake` | `intake_requests`, ensure V6 workspace | intake request row | intake_requests | PARTIAL | Legacy list |
| 2. Intake V6 workspace | `/intake-v6/:id/operator` | `POST/GET .../intake-v6/workspaces` | `payload_json` | intake_v6_workspaces | VALIDATED_WITH_GUARDS | Preview ≠ offer |
| 3. Form contract | Intake V6 (implicit) | `GET .../form-contract/{template}` | bindings | mini-module registry | PARTIAL | Pilot only |
| 4. ProductSystem template | Intake binding + admin | template seed / registry | template_code | product_templates + dossier | PARTIAL | Parent thin |
| 5. ProductDefinition build | Intake previews / snapshot compose | `GET .../product-definition/{template}` | PD JSON | derived from workspace | VALIDATED | Read-only compile |
| 6. ProductAggregate build | same | `GET .../aggregate/{template}` | aggregate + task_rules | dossier merge | VALIDATED_WITH_GUARDS | Duplicate ops |
| 7. CPP preview | Intake panels | `POST .../commercial-price-preview/{template}` | commercial lines | hardcoded rules | IMPLEMENTED_PREVIEW_ONLY | Not official alone |
| 8. EIC preview | Intake panels | `POST .../estimated-internal-cost-preview/{template}` | internal lines | internal rules + BOM | IMPLEMENTED_PREVIEW_ONLY | — |
| 9. Quote draft / offer preview | Intake handoff | `create-draft-quote` | quote row, linkage in notes | quotes (unpriced) | VALIDATED_WITH_GUARDS | grand_total=0 |
| 10. Quote Snapshot V2 preview | demo / IV6 | `POST .../quote-snapshot-v2/preview/{template}` | composed snapshot | ephemeral | VALIDATED | — |
| 11. Quote Snapshot V2 freeze | IV6 spine | `POST .../quote-snapshot-v2/freeze/{template}` | quote_snapshot_v2 row | DB snapshot | VALIDATED_WITH_GUARDS | Official candidate |
| 12. Owner approval | Intake V6 | `POST .../owner-approval` | owner record in notes | quote notes JSON | VALIDATED | Gate |
| 13. Quote accept | Intake V6 | `POST .../accept` + accept gate | `accepted_snapshot_v2_id` | quote + snapshot | VALIDATED_WITH_GUARDS | partial readiness ack |
| 14. Order convert | Intake V6 | `POST .../convert-to-order` | order row | order_snapshot_v2_convert | VALIDATED | No plan at convert |
| 15. Order Snapshot V2 | `/orders/:id` | order GET | `snapshot_v2_json` | orders.snapshot_v2_json | VALIDATED | Frozen |
| 16. ExecutionPlan V2 preview | API / future 9B UI | `POST .../plan-v2/preview/{order_id}` | preview envelope | read snapshot | VALIDATED | no_write |
| 17. ExecutionPlan V2 persist draft | API | `POST .../plan-v2/from-order/{order_id}` | execution_plan.tasks_json | execution_plan row | VALIDATED_WITH_GUARDS | HTTP fresh PASS |
| 18. Materialization audit GET | API | `GET .../materialization-audit` | audit report | dry-run | IMPLEMENTED_PREVIEW_ONLY | — |
| 19. Materialization POST | — | `POST .../materialize-tasks/{order_id}` | operational_tasks | **BLOCKED** | BLOCKED_NEEDS_OWNER_GO | DEC-009 |
| 20. Execution sessions | `/execution/:id`, Mobile | `POST .../reality/start-task` | sessions | **FROZEN** | FROZEN | Step 11+ |
| 21. Profitability | ExecutionDetail | `GET .../profitability-analysis/order/{id}` | analysis DTO | read snapshot | PARTIAL | actuals null |
| 22. Employee Mobile | `/employee-app/*` | mobile APIs | — | **FROZEN** | FROZEN | final-final |

---

## 3. State transitions

| From state | To state | Trigger | Who/what | Writes DB? | Guard | Evidence |
| ---------- | -------- | ------- | -------- | ---------- | ----- | -------- |
| (none) | intake_v6 workspace | Create workspace / ensure from request | Operator / API | Yes | template pilot | IV6 routes |
| workspace draft | workspace configured | PUT finish-setup, SVG, geometry | Operator | Yes | validation in PD | payload_json |
| configured | draft quote | create-draft-quote | Operator | Yes | IV6 linkage | quotes.notes |
| draft quote | snapshot preview | preview API | Operator/dev | No | compose CPP+EIC | snapshot preview |
| draft quote | snapshot frozen | freeze API | Operator | Yes | readiness gates | QSN2-2026-0003 |
| frozen snapshot | pricing review done | complete-pricing-review | Operator | Yes | snapshot commercial total | Step 8 QA |
| pricing review | owner approved | owner-approval | Owner | Yes | approval record | Step 8 QA |
| owner approved | quote accepted | accept | Owner/operator | Yes | accept gate, owner_decisions ack | quote accepted_snapshot_v2_id=3 |
| accepted | order created | convert-to-order | Operator | Yes | accept + convert guards | order 88002 |
| order | plan preview | POST preview | Operator/API | No | snapshot_v2 present | 12 tasks |
| (no plan) | plan draft | POST from-order | Operator/API | Yes | idempotent | plan id=2, already_exists |
| plan draft | operational tasks | POST materialize | — | **Blocked** | DEC-009, DEC-003+ | not exercised |
| operational ready | session started | start-task | Operator | Yes | v2_operational_ready | FROZEN |

**Manual vs automatic:** All spine steps through convert are **operator-triggered** HTTP POSTs. **No** auto execution_plan at convert. **No** auto materialize.

---

## 4. Data handoff map

| From | To | Payload/key fields | Frozen? | Recomputed? | Risk |
| ---- | -- | ------------------ | ------- | ----------- | ---- |
| Operator | Intake V6 | `payload_json`, `template_code` | No (mutable until quote lock) | Yes until accept path | Editing after accept |
| Intake V6 | ProductDefinition | workspace paths | No at intake | Yes on each GET | — |
| Intake V6 | ProductAggregate | workspace + template | No at intake | Yes on each GET | — |
| PD + Agg + CPP + EIC | Quote Snapshot V2 | `product_*_snapshot`, commercial/internal snapshots | **Yes at freeze** | No after freeze | — |
| Quote Snapshot V2 | Quote row | `accepted_snapshot_v2_id` | Yes | No | — |
| Quote Snapshot V2 | Order Snapshot V2 | full JSON copy | **Yes at convert** | **No reprice** | — |
| Order Snapshot V2 | ExecutionPlan | `product_aggregate_snapshot.task_contract.task_rules` | Yes (read frozen) | Preview rebuilds from snapshot only | WC null |
| ExecutionPlan persist | tasks_json | `planned_tasks[]`, metadata | Yes after persist | Idempotent persist | Not operational yet |
| Planned tasks | operational_tasks | copy on materialize | Future | Blocked | DEC-009 |

---

## 5. What becomes official when

| Artifact | Official for what | When |
| -------- | ----------------- | ---- |
| Intake `payload_json` | **Product request** workspace truth | From first save — **not** client offer |
| CPP/EIC preview panels | **Preview only** | Any time — label required |
| Quote draft | **Linkage + notes**; intentionally unpriced | create-draft-quote |
| Quote Snapshot V2 **freeze** | **Official frozen offer candidate** (dual commercial + internal) | freeze POST |
| Owner approval | **Owner decision gate** | owner-approval POST |
| Quote **accept** | **Commercial acceptance** binding snapshot | accept POST |
| Order Snapshot V2 | **Frozen order truth** — client promise + internal estimate at accept | convert POST |
| ExecutionPlan draft | **Execution planning draft** — not shop runtime | persist POST |
| Materialization audit GET | **Audit read-only** — not execution | GET only |
| `operational_tasks[]` | **Shop task instances** (envelope) | After materialize GO only |
| Sessions / actuals | **Real minutes** | Step 11+ after materialize |
| Employee Mobile | **Operator mobile UX** | Doc 21 Faza 10 final-final |

---

## 6. Failure points

| Failure | Cause | Severity |
| ------- | ----- | -------- |
| Wrong template binding | workspace template_code ≠ dossier | HIGH |
| Missing PD fields | incomplete geometry/finish | HIGH — blocks freeze |
| Aggregate duplicate operations | module lateral + parent | HIGH — DEC-003/004 |
| Pricing preview confused with official | UI labels | MEDIUM |
| Legacy `/price` used | wrong commercial model | HIGH |
| Order missing aggregate in snapshot | convert without full compose | HIGH — guarded |
| ExecutionPlan workcenter null | parent ops no WC | CRITICAL — DEC-005 |
| estimated_minutes null | no planning source | HIGH — DEC-006 |
| POST materialize before decisions | process error | CRITICAL |
| Employee Mobile before materialize | wrong phase | HIGH |
| Wrong dependency order (paint/vinyl/template) | linear DAG | HIGH — DEC-007 |

---

## 7. Verification on real fixture (order 88002)

| Check | Expected | Status |
| ----- | -------- | ------ |
| `quote_snapshot_v2_id` | 3 | CONFIRMED (worklogs) |
| `execution_plan.id` | 2 | CONFIRMED |
| `planned_tasks` count | 12 | CONFIRMED |
| `planned_operations` count | 17 | CONFIRMED |
| `operational_tasks` | empty | CONFIRMED |
| `execution_tasks_created` | false | CONFIRMED |
| Sessions / execution_reality | none | CONFIRMED |
| HTTP persist POST | 200 `already_exists` | PASS (e9f8033) |
| Materialization audit GET | exists | CONFIRMED (d712802) |
| POST materialize | not exercised | BLOCKED |

---

## 8. Current blockers

| Blocker | Decision/Gate | Blocks | Owner needed? |
| ------- | ------------- | ------ | ------------- |
| Duplicate lateral RETURN/PAINT ops | DEC-003, DEC-004 | Safe materialize | **Yes** |
| workcenter null on all planned tasks | DEC-005 | Scheduling, assignment | **Yes** |
| planning minutes null | DEC-006 | Production scheduling GO | **Yes** |
| Linear dependency chain | DEC-007 | Realistic shop DAG | **Yes** |
| POST materialize disabled | DEC-009 | operational_tasks, sessions, Mobile | **Yes** |
| Upstream WC enrichment not done | Faza 2 | New freezes for materialization | **Yes** |
| UI labels incomplete | Step 11 / Faza 8 | Operator clarity | **Yes** |

---

## 9. Safe next step

**Owner decisions DEC-003 / DEC-004 / DEC-005 first.**

Then: Step 9B UI read-only (parallel OK per DEC-008) or scoping Faza 2 upstream task_contract enrichment — **not** POST materialize, **not** sessions, **not** Employee Mobile.

---

## Related flow documents

- [01_INTAKE_V6_FLOW.md](./01_INTAKE_V6_FLOW.md) · [07_OFFER_QUOTE_ORDER_FLOW.md](./07_OFFER_QUOTE_ORDER_FLOW.md) · [08_EXECUTION_PLAN_FLOW.md](./08_EXECUTION_PLAN_FLOW.md)
- [21_WORKOS_IMPLEMENTATION_ROUTE.md](../realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md)
