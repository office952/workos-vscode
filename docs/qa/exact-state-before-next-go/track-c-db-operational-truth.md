# Track C — DB / Operational Truth

**Mode:** READ-ONLY · GET + SQLite read · **no POST**  
**Date:** 2026-07-31 (~23:27 local)  
**DB:** `C:\w\psiso\backend\dev.db`  
**API:** `GET /api/v1/execution/plan/{order_id}` · `GET /api/v1/system/local-compatibility`

---

## Authorize / DEC-009 (live)

| Field | Value |
|-------|-------|
| Source `BATCH_EXECUTE_MATERIALIZE_AUTHORIZED` | **False** (`dec009_materialize_gate.py:77`) |
| Live `batch_execute_materialize_authorized` | **false** |
| `live_dec009` | **A / BLOCKED** |
| Scoped-B stamp | `SCOPED_B_STAMPED` |
| Live scoped identity | **92401 / 13 / FIX-DEC009-MAT-02** |
| MAT-01 | 973010 / 12 · `allow_materialize=false` (historical) |
| Runtime `git_commit` | `a1c28854` |

---

## Operational tasks

| Order | Fixture | Plan | API ops | Tasks array | Materialized | Readiness |
|-------|---------|------|---------|-------------|--------------|-----------|
| **92401** | MAT-02 | **13** | **18** | 18 | True | `v2_operational_ready` |
| **973010** | MAT-01 | **12** | **12** | 12 | True | `v2_operational_ready` |

### Envelope integrity (DB)

| Check | 92401 | 973010 |
|-------|-------|--------|
| Activation hash | `e6edbb802ba3ab25629914a976f6679e` | `15bde334c5c6eb4ad1c5cd6adceac1bb` |
| Ops order_ids | `{92401}` only | `{973010}` only |
| Ops plan_ids | `{13}` only | `{12}` only |
| Unique task_ids | 18/18 | 12/12 |
| Duplicate materialize output | **No** | **No** |
| Null `estimated_time_minutes` | 18/18 (honesty) | retained |
| Null assignments | 18/18 | retained |

**92401/13/MAT-02 represented correctly:** **YES**

---

## Sessions / actuals / out-of-scope

| Surface | Count / state |
|---------|---------------|
| Session tables | **None** |
| Sessions | **0** |
| `execution_reality` 92401 | **0** |
| `execution_reality` 973010 | **0** |
| Attendance events | **0** |
| Help/participants on 92401/973010 | **0** / **0** |

Out-of-scope historical rows (order **23099** help/participants) exist elsewhere — **not** attributed to 20E scoped-B.

---

## Verdict

**PASS** — Live DB/API match Batch 20E leftovers: second fixture materialized once, prior fixture stable, authorize restored, no sessions/actuals on scoped orders, no duplicate envelopes.
