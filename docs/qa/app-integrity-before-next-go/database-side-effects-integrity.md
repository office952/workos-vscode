# Database / Side-Effects Integrity

**Repo:** `C:\w\psiso`  
**DB:** `C:\w\psiso\backend\dev.db` (read-only SQLite queries)  
**Also:** live `GET /api/v1/execution/plan/{order_id}`  
**Date:** 2026-07-31  
**Mode:** No POST materialize · no entity creation

---

## Authorize / DEC-009 live state

From `GET /api/v1/system/local-compatibility` (live):

| Field | Value |
|-------|-------|
| `live_dec009` | **A** / BLOCKED |
| `batch_execute_materialize_authorized` | **false** |
| `scoped_b_stamp` | `SCOPED_B_STAMPED` |
| `scoped_b_order_id` | **92401** |
| `scoped_b_plan_id` | **13** |
| `scoped_b_fixture_id` | `FIX-DEC009-MAT-02` |
| Historical MAT-01 | 973010 / 12 / `allow_materialize=false` |
| Source constant | `BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = False` in `dec009_materialize_gate.py` |

**Authorize restored:** **YES** (matches Batch 20E final evidence).

---

## Operational tasks (scoped envelopes)

| Order | Plan | API `operational_tasks_count` | DB envelope ops | Planned | Activation hash | Unique task_ids |
|-------|------|-------------------------------|-----------------|---------|-----------------|-----------------|
| **92401** | **13** | **18** | **18** | 18 | `e6edbb802ba3ab25629914a976f6679e` | 18/18 |
| **973010** | **12** | **12** | **12** | 12 | `15bde334c5c6eb4ad1c5cd6adceac1bb` | 12/12 |

Scope checks (DB):

| Check | 92401 | 973010 |
|-------|-------|--------|
| `ops_order_ids` | `{92401}` only | `{973010}` only |
| `ops_plan_ids` | `{13}` only | `{12}` only |
| Duplicate task_ids | None | None |
| Cross-contamination | None | None |

Matches Batch 20E post-materialize evidence (`evidence/capacity-batch-20e/counts_post.json`, `summary_batch_20e.json`).

**20E materialize result exists only inside approved scoped-B (92401/13):** **PASS**  
**No duplicate scoped-B materialize output:** **PASS** (unique 18 task_ids; 973010 unchanged at 12)

---

## Sessions

| Check | Result |
|-------|--------|
| Tables matching `%session%` | **None** in `dev.db` |
| Session-like counts | **0** (no session tables) |
| 20E response `no_sessions_created` | **true** (prior evidence) |

**Verdict sessions:** **PASS** — no sessions created for this path.

---

## Actuals / ExecutionActuals / execution_reality

| Surface | Count |
|---------|-------|
| `execution_reality` total rows | 7 (historical, other orders) |
| `execution_reality` order **92401** | **0** |
| `execution_reality` order **973010** | **0** |
| `employee_attendance_events` | **0** |

**Verdict actuals for scoped fixtures:** **PASS**

---

## Other execution-adjacent rows (out of scoped-B)

| Table | Total | 92401 | 973010 | Note |
|-------|-------|-------|--------|------|
| `execution_task_participants` | 3 | 0 | 0 | All on order **23099** (pre-20E historical) |
| `execution_task_help_requests` | 23 | 0 | 0 | Sample order_ids **23099** |

Not attributed to Batch 20E scoped-B materialize.

---

## Unauthorized entity creation

| Forbidden class | Observed for 92401/973010 |
|-----------------|---------------------------|
| Extra materialize beyond one approved POST | No (envelope stable at 18 / 12) |
| Sessions | No |
| ExecutionActuals / reality rows | No |
| Employee Mobile joins on scoped orders | No (participants/help = 0) |

---

## Verdict

**PASS** — Side effects match approved Batch 20E scoped-B outcome; authorize remains false; no unauthorized sessions/actuals on 92401/973010.
