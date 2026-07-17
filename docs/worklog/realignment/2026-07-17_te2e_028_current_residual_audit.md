# 2026-07-17 — TE2E-028 current residual audit

## Objective

Reconcile TE2E-028 accepted Wave 7 limitations against current runtime/code. Present truth only. Planning and owner gates. No implementation.

## Repository gate

| Check | Result |
|-------|--------|
| Repo | `C:/w/psiso` |
| Remote | `https://github.com/office952/workos-vscode.git` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `c6a4c14` (matches expected) |
| Staged | none for this audit |
| Dirty tree | protected (unrelated local dirt untouched) |
| Ports | FE `:3000` · BE `:8001` — both up |
| Closed baselines | Wave 7 · UI-TRUTH-01B/01C · Control Center V1 · UTF-8/G13 intact |

## Method

1. Extracted canonical TE2E-028 from issue registry, D-020, W7-T03 checklist, STATUS/TASK_GRAPH.
2. Reverified each of the five residuals against live APIs and `/execution/92402|92403` UI (GET only).
3. Separated W7-T02 **resolved mechanics** from TE2E-028 **open debt**.
4. Did not mutate reference orders/plans/snapshots.
5. Did not modify application code.

## Canonical result

- **Title:** Same-scenario / W7-T02 remaining limitations  
- **Status:** OPEN (accepted debt)  
- **Conflict:** none (`TE2E_028_SCOPE_CONFLICT` not raised)  
- **Verdict:** `TE2E_028_OWNER_GATES_READY`

## Live RO proof (summary)

| Order | Plan | Post-Job summary | Commercial | write_back |
|-------|------|------------------|------------|------------|
| 92402 | 8 | matched=1 · missing_actual=17 · variance=0 | 3549.1286 locked | false |
| 92403 | 9 | matched=0 · missing_actual=17 · variance=1 (0→75) | 3549.1286 locked | false |

Planning minutes: **18/18 = 0.0** on plan 8 (R1 still open).  
Labor money: `excluded` (R3 intentional).  
Materials: `not_captured` / no inventory mutation (R2 deferred).

## Classification snapshot

| Residual | Class |
|----------|--------|
| Missing-actual honesty / variance / Plan vs execuție | RESOLVED_CURRENT (W7-T02) |
| Planning-minute source zeros | OPEN_CURRENT |
| Stock G3 deferred | OPEN_CURRENT |
| Labor $ excluded | OPEN_CURRENT (keep) |
| Deterministic fixture | OPEN_CURRENT |
| Letters-only breadth | OPEN_CURRENT |

## Recommendation

**Option A — Planning-minute source integrity** (narrow reconciliation meaning), reference data READ ONLY, implementation STOP until owner GO.

## Documents

- Audit: `docs/audits/2026-07-17_te2e_028_current_residual_audit.md`

## Owner decision (unpause)

```text
TE2E-028 = UNPAUSE
BUILD = RECONCILIATION
MISSING ACTUAL = KEEP EXPLICIT
TASK LIFECYCLE = DEFER
VARIANCE = CURRENT MODEL
REFERENCE DATA = NEW TEST DATA
AUDIT COMMIT = DA
IMPLEMENTATION = GO
```

Narrow build: **TE2E-028A planning-minute source integrity**. Plans 8/9 and orders 92402/92403 remain read-only. Preview `planning_minutes_source` nulling is a clue, not assumed sole root cause.

## Commit status

- `3420b57` — `docs(execution): approve te2e-028 planning-minute audit`
- (implementation) — `fix(execution): preserve planned-minute source integrity`

---

## Implementation — TE2E-028A (planning-minute source)

### Owner decision

Applied exactly as unpause pack above. Narrow reconciliation only.

### Root-cause research

Proven loss chain (preview null was a **clue**, confirmed as primary cut, not sole):

1. `product_aggregate_service._operations_from_rows` dropped template `estimated_minutes` / `calculation_type`
2. `execution_plan_v2_preview_service` hardcoded `estimated_minutes=None` / `planning_minutes_source=None`
3. `execution_plan_task_parser` materialize coerced null → `0.0`
4. Post-Job read persisted plan (correct consumer) and therefore saw zeros as present

Authoritative source for this slice: **template static operation `estimated_minutes`** carried on `ProductAggregateOperation`, provenance `product_aggregate_snapshot.operations.estimated_minutes`. Formula_based `0` placeholders remain absent (not invented).

### Source precedence

1. Aggregate op `estimated_minutes` with `calculation_type=static` (or non-formula) → use value + provenance  
2. `formula_based` with `0` → treat as missing  
3. No value → missing + `PLANNING_MINUTES_SOURCE_REQUIRED`  
4. CostEngine / EIC / commercial — ignored (existing V2 rule)

### Implementation

- Additive fields on `ProductAggregateOperation`
- Preview `resolve_planning_minutes_from_aggregate_op`
- Materialize keeps `null` when missing; copies `planning_minutes_source`
- Post-Job surfaces planned source when present

### Test data

- Pytest fixture orders (ephemeral)  
- Live local fixture: order `972901` / plan `10` / label `TE2E-028A LIVE PROOF — TEST FIXTURE` — **not** Wave 7 reference; may delete  
- Plans `8`/`9` and orders `92402`/`92403` untouched

### Tests

`pytest tests/test_te2e_028a_planning_minute_source.py` + materialize null regression + existing planning-minutes missing test — pass.

### Runtime proof

- Aggregate live: `qc_letters=(15.0, static)`  
- Preview/plan/Post-Job: planned 15 present, actual `not_captured`, `missing_actual`, `write_back=false`  
- Refs after: plan 8/9 still `total_min=0.0`

### Modules / Governance

- Modules: **EVIDENCE/LIMITATION UPDATE** (ExecutionPlan + Post-Job limitation text; `ev.te2e_028a`)  
- Governance: **NO BOUNDARY CHANGE**

### Remaining TE2E-028 residuals

Stock G3 · labor $ · fixture qualification · Letters breadth · formula ops without planning-duration authority · task lifecycle (deferred)

### Status

`TE2E-028A PLANNING-MINUTE SOURCE = COMPLETE — PROVEN_CURRENT`  
`TE2E-028` parent issue remains **open**
