# Capacity Batch 17 — Track B: Read-Model Clarity

**Mode:** Display-only API / read-model honesty · **no materialize** · **no invent** · **no new ops/sessions/actuals**  
**Date:** 2026-07-31  
**Fixture:** `FIX-DEC009-MAT-01` · order `973010` · plan `12` · ops **12** · sessions **0** · actuals **0**  
**Branch:** `fix/capacity-batch-17-read-model-clarity`  
**UI route (consumer):** `/execution/ops-graph` (Track C owns copy/layout)

---

## Kickoff / scope

| Item | Value |
|------|-------|
| Purpose | Close Batch 16 OR-01 / OR-02 / V-13 / chip-noise **from the GET plan read model** |
| Allowlist | `backend/services/execution_ops_graph_read_clarity.py` · wire in `routers/execution.py` `_plan_row_to_dict` · FE types in `frontend/src/api/execution.ts` · tests · this handoff |
| Shared with Track C | Prefer B owns API/read-model; C owns `MaterializedOpsGraph` UI copy — merge carefully |
| Forbidden | Materialize POST · invent minutes/WC/`machine_code`/unit · remap sequence to dense 1..N · sessions/actuals · Employee Mobile · CostEngine/Pricing/PD |

```text
DISPLAY-ONLY ENRICHMENT — NO PERSIST MUTATION
```

---

## What changed

| Change | Detail |
|--------|--------|
| New service | `backend/services/execution_ops_graph_read_clarity.py` |
| GET plan enrich | `_plan_row_to_dict` attaches per-task `read_clarity` + plan `ops_graph_read_clarity` |
| Persist | **Unchanged** — `tasks_json` not rewritten |
| FE types | `OpsGraphTaskReadClarity` / `OpsGraphPlanReadClarity` on `PlannedTaskRow` / `ExecutionPlanResponse` |
| Tests | `backend/tests/test_execution_ops_graph_read_clarity.py` (9 passed) |

### Counts guard (fixture snapshot + enricher)

| Metric | Before | After enrich |
|--------|--------|--------------|
| Operational tasks | **12** | **12** |
| Sessions | **0** | **0** (untouched) |
| ExecutionActuals | **0** | **0** (untouched) |

Enrichment `counts_guard.input_count == output_count`. No new task rows.

---

## Honesty field contract (for Track C)

Each `tasks[]` item keeps raw envelope fields and adds `read_clarity`:

### Identity (unambiguous)

| Path | Meaning |
|------|---------|
| `read_clarity.identity.task_id` | Full deterministic id |
| `read_clarity.identity.short_code` | `technical_name` (canonical short) |
| `read_clarity.identity.label` | `display_name` / `name` |
| `read_clarity.identity.sequence_index` | Template source index (may skip) |
| `read_clarity.identity.source_operation_code` | Op code (may differ from short_code — OR-05) |
| `ops_graph_read_clarity.sequence.gaps` | e.g. `[11,12]` for fixture — **not densified** |

### Lifecycle / status (OR-01)

| Path | Fixture value |
|------|---------------|
| Raw | `operational_status = "pending"` (was present but not displayed) |
| `read_clarity.lifecycle.value` | `pending` |
| `read_clarity.lifecycle.display_label` | `materialized_pending_execution` |
| Classification | `present` |
| Note | Plan lifecycle only — **not** ExecutionActuals / sessions |

### Machine / WC (OR-02)

| Field | Classification | Rule |
|-------|----------------|------|
| `machine_code` | `owner_accepted_risk` (CAP-012) when null | **Never** coalesce from `machine_type` |
| `machine_type` | `present` · role `planning_requirement_class` | Capability / WC-class hint — **not** assigned utilaj |
| `workcenter` | `owner_accepted_risk` (F7_OD1) when null | Do **not** invent by copying `machine_type` |

`display_hints.do_not_coalesce_machine_code_from_machine_type = true`  
UI must stop `machine_code ?? machine_type` in the Machine column.

### Qty / unit (V-13)

| Field | Classification |
|-------|----------------|
| `quantity` | `present` (typically `1.0`) — plan-task count |
| `unit` | `unknown` when absent — **do not invent** piece/ml/m2 |

### Minutes

| Field | Classification |
|-------|----------------|
| `estimated_time_minutes` null + planning gap | `owner_accepted_risk` (CAP-004) |
| Present (qc=15) | `present` |

### Deps

| Path | Notes |
|------|-------|
| `depends_on.task_ids` | Full ids |
| `depends_on.short_codes` | Mapped via peer `technical_name` (one vocabulary) |
| Empty deps | `not_required` (root) |

### Warning collapse (OR-04)

| Bucket | Contents |
|--------|----------|
| `warnings.raw_warnings` | Envelope warnings unchanged |
| `warnings.accepted_gap_codes` | e.g. `CAP-004`, `CAP-012`, `F7_OD1`, `HR_OUT_OF_STAGE` |
| `warnings.active_warnings` | Non-accepted residual warnings only |

---

## Null classification vocabulary

| Code | Meaning |
|------|---------|
| `present` | Value from persisted operational_task |
| `unknown` | Absent / unclassified — show `—`; do not invent |
| `not_required` | Empty is valid (e.g. root deps) |
| `owner_accepted_risk` | Locked Owner residual — disclose, do not fill |
| `blocked_pending_owner_truth` | Reserved for future hard Owner-truth blocks (not used to invent) |

---

## Track C consumer checklist

1. Status column ← `task.read_clarity.lifecycle.display_label` (fallback raw `operational_status`).
2. Machine instance ← `machine_code` only; if null show `—` + CAP-012 from `accepted_gap_codes`.
3. Requirement / type column ← `machine_type` labeled as requirement class (not “Machine assigned”).
4. WC ← explicit `workcenter` only; null → OD1 risk, not `machine_type`.
5. Chips ← prefer `accepted_gap_codes` (one summary) + `active_warnings`; avoid 5–6 raw chips/row.
6. Seq gap note ← `ops_graph_read_clarity.sequence` (gaps `[11,12]`).
7. Depends: prefer `read_clarity.depends_on.short_codes`.
8. Do not invent unit / minutes / assignments.

---

## Tests

```text
pytest backend/tests/test_execution_ops_graph_read_clarity.py -q
# 9 passed (includes FIX-DEC009 snapshot when Batch 16 evidence path present)
```

Related plan GET smoke: `test_execution_plan_operational_readiness` / plan-filtered `test_execution_flow` — passed.

---

## SMART CODE COMPLIANCE

| Gate | Evidence |
|------|----------|
| No materialize | GET enrich only; no POST materialize path touched |
| No invent | Nulls classified; `machine_type` not written into `machine_code`/`workcenter`/`unit` |
| Counts unchanged | 12/0/0; `counts_guard` equality |
| No frontend business truth calc | Types only on FE; honesty computed server-side from persisted fields |
| No CostEngine / Pricing / PD / Aggregate | Untouched |
| Analyzer / WorkOS import | Untouched |
| Track C coordination | UI copy left to Track C; API contract documented here |

---

## Return summary

| Item | Value |
|------|-------|
| **API** | `GET /execution/plan/{id}` → `tasks[].read_clarity` + `ops_graph_read_clarity` |
| **Fields honesty** | Status surfaced; machine_code ≠ machine_type; WC/minutes/unit/employee classified |
| **Counts** | **12 / 0 / 0** unchanged |
| **PR** | https://github.com/office952/workos-vscode/pull/33 |
| **SHA** | `cf6a0e1a394b1f75915553b0554ca15eb6391827` |
