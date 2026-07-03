# Step 9B UI Truth Layer + Doc Sync

## 1. Status

**PASS_WITH_GUARDS**

Implemented a read-only Step 9B truth layer in ExecutionDetail and synchronized the most visible realignment docs to reflect current runtime status more accurately.

---

## 2. Scope

In scope:

1. frontend read-only V2 truth visibility
2. fetch `plan-v2/preview/{order_id}`
3. fetch `plan-v2/from-order/{order_id}/materialization-audit`
4. render planned tasks / planned operations / audit-only materialization state
5. sync 7G / 7H / Step 9 status wording in core realignment docs

Out of scope:

1. materialization POST
2. sessions / actuals expansion
3. Employee Mobile
4. backend schema changes
5. pricing path rewrite

---

## 3. What changed

Runtime/UI:

1. Added Step 9B V2 truth layer to ExecutionDetail.
2. Shows `planned_tasks`, `planned_operations`, warning badges, and materialization audit summary.
3. Surfaces null workcenters and null minutes explicitly.
4. Keeps everything read-only.
5. Added read-only V2 snapshot-to-plan summary on Orders detail.
6. Added read-only frozen Snapshot V2 truth card on Quotes detail.
7. Relabeled Orders execution dispatch language from misleading production-task wording to draft-plan wording.
8. Added broader truth-boundary banners on ProductSystem and Pricing to mark them as upstream/internal inputs, not frozen V2 or execution truth.
9. Added downstream navigation cues from ProductSystem and Pricing toward Quotes and Orders truth surfaces.
10. Added broader truth-boundary banner on Quotes to separate frozen commercial truth from upstream pricing/product previews.
11. Added broader truth-boundary banner on ExecutionDetail to separate Step 9B audit surfaces from captured execution reality.
12. Clarified Quotes wording around displayed commercial totals, output composition preview, and saved output snapshot candidates so they are not confused with frozen V2 truth.

Documentation:

1. 7G now marked as preview implemented, not `NOT STARTED`.
2. 7H now marked as preview implemented, not docs-only.
3. Step 9 wording updated to reflect current validated state and Step 9B visibility.

---

## 4. Files changed

| Path | Action |
| ---- | ------ |
| `frontend/src/api/execution.ts` | Updated |
| `frontend/src/components/execution/ExecutionPlanV2TruthPanel.tsx` | Created |
| `frontend/src/hooks/useExecutionPlanV2Truth.ts` | Created |
| `frontend/src/pages/ExecutionDetail.tsx` | Updated |
| `frontend/src/pages/Orders.tsx` | Updated |
| `frontend/src/pages/Quotes.tsx` | Updated |
| `frontend/src/lib/api.ts` | Updated |
| `frontend/src/lib/dataStore.ts` | Updated |
| `frontend/src/lib/mockData.ts` | Updated |
| `frontend/src/pages/Orders.createdFromQuote.test.tsx` | Updated |
| `frontend/src/pages/Quotes.route.test.tsx` | Updated |
| `frontend/src/pages/ProductSystem.tsx` | Updated |
| `frontend/src/components/pricing/PricingRegistrySpaciousView.tsx` | Updated |
| `frontend/src/pages/ProductSystem.badges.test.tsx` | Updated |
| `frontend/src/pages/Pricing.badges.test.tsx` | Updated |
| `frontend/src/pages/Quotes.tsx` | Updated |
| `frontend/src/pages/Quotes.route.test.tsx` | Updated |
| `frontend/src/pages/ExecutionDetail.tsx` | Updated |
| `frontend/src/components/workos/QuoteOutputCompositionPreview.tsx` | Updated |
| `frontend/src/components/workos/QuoteOutputSnapshotsSection.tsx` | Updated |
| `docs/architecture/realignment/05_COMMERCIAL_PRICE_PROPOSAL.md` | Updated |
| `docs/architecture/realignment/06_ESTIMATED_INTERNAL_COST.md` | Updated |
| `docs/architecture/realignment/20_ROADMAP_STEPS_7G_TO_12.md` | Updated |
| `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` | Updated |
| `docs/architecture/realignment/23_WORKOS_CONTROLLED_IMPLEMENTATION_TODO_BACKLOG.md` | Created |
| `docs/architecture/realignment/README.md` | Updated |
| `docs/worklog/realignment/2026-06-30_step9b_ui_truth_layer_and_doc_sync.md` | Created |
| `docs/worklog/realignment/2026-06-30_dec003_return_operation_owner_packet.md` | Created |
| `docs/worklog/realignment/2026-06-30_dec004_painting_owner_packet.md` | Created |
| `docs/worklog/realignment/2026-06-30_dec005_dec006_workcenter_minutes_policy_packet.md` | Created |
| `docs/worklog/realignment/2026-06-30_dec007_dec009_dependency_materialization_gate_packet.md` | Created |

---

## 5. Validation

1. frontend typecheck passed (`pnpm exec tsc --noEmit`)
2. runtime UI verified on `/execution/88002`
3. Step 9B panel shows 12 planned tasks, 17 planned operations, audit-only state, and non-operational readiness item
4. read-only DB audit verified persistence chain in `backend/dev.db`
5. focused Orders test passed after V2 order-detail truth panel and labeling changes
6. focused Quotes route test passed after frozen Snapshot V2 truth card changes
7. focused ProductSystem and Pricing badge tests passed after broader truth-boundary banner changes
8. focused Quotes route test passed after broader quote truth-boundary banner changes
9. runtime browser verification confirmed new truth-boundary messaging on ProductSystem and ExecutionDetail
10. focused Quotes route test passed after broader commercial totals / output preview candidate wording changes

DB audit highlights:

1. `orders.id=88002` exists with `code=ORD-IV6-V2-1782815703-1`, `status=locked`, `quote_snapshot_v2_id=3`.
2. `execution_plan.id=2` exists for `order_id=88002` with `plan_source=order_snapshot_v2`, `source_quote_snapshot_v2_id=3`, `source_snapshot_code=QSN2-2026-0003`.
3. `execution_plan.tasks_json` contains `12` planned tasks and `17` planned operations.
4. `quote_snapshots_v2.id=3` exists with `status=frozen` and `readiness=partial_with_owner_decisions`.
5. SQLite schema currently contains `execution_plan` and `execution_reality`, but does **not** contain `execution_tasks` or `task_sessions` tables.
6. `execution_reality` exists, but order `88002` has `0` rows.

---

## 6. Remaining blockers

1. owner decisions DEC-003 / DEC-004 / DEC-005 / DEC-007 / DEC-009
2. materialization still blocked
3. sessions still blocked

---

## 7. Next recommended step

Proceed to upstream enrichment for task contract quality only after owner decisions are explicit.

Current controlled backlog state:

1. Track A advanced — docs/backlog references in place; major status drift reduced.
2. Track B advanced — ExecutionDetail, Orders, and Quotes now expose read-only V2 truth.
3. Track C advanced — owner packets for DEC-003 / DEC-004 / DEC-005 / DEC-006 / DEC-007 / DEC-009 are prepared.
4. Track D remains correctly blocked until owner answers are explicit.