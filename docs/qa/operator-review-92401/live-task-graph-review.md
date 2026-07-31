# Live Task Graph Review — 92401 / Plan 13 / MAT-02

**Mode:** READ-ONLY · GET + SQLite SELECT  
**Date:** 2026-07-31  
**SHA:** `a1c28854`  
**Owner URL:** `http://127.0.0.1:3000/execution/ops-graph?orderId=92401`

---

## Checklist (review targets 1–4, 9–10)

| # | Target | Observed | Class |
|---|--------|----------|-------|
| 1 | Exactly 18 operational tasks | API + DB **18** · unique task_ids **18/18** | **PASS** |
| 2 | Plan 13 / MAT-02 correct | plan_id **13** · scoped-B live `92401/13/FIX-DEC009-MAT-02` · readiness `v2_operational_ready` | **PASS** |
| 3 | No duplicate materialize output | unique keys OK · envelope sha stable · single activation hash | **PASS** |
| 4 | No out-of-scope tasks | foreign order_ids **0** · foreign plan_ids **0** | **PASS** |
| 9 | Pricing not affected by time/pontaj | No price/EUR/commercial fields on plan or tasks · minutes **null ×18** · attendance **0** | **PASS** |
| 10 | Ops-graph via `?orderId=92401` · no 92401 hardcode | URL uses query param · `MaterializedOpsGraph.tsx` has **no** 92401/MAT-02 constants (only MAT-01 973010 default) | **PASS** |

---

## Envelope identity

| Field | Value |
|-------|-------|
| Order | 92401 |
| Plan | 13 |
| Fixture (gate) | FIX-DEC009-MAT-02 |
| Activation hash | `e6edbb802ba3ab25629914a976f6679e` |
| Envelope sha16 (tasks_json) | `02c70f7dbf963bc8` |
| Prior 973010 | ops **12** · hash `15bde334…` unchanged |

---

## Task set (18)

Sequence indices (provenance, not contiguous 1–18):  
`1–10, 13–14, 24–29` — count still **18**. Clusters: face/back/return/finish/LED/QC/pack · ACM structure · volum aluminum.

Honesty retained: null minutes · null WC field · null assignee · empty `material_inputs[]`.

---

## Verdict

**PASS WITH WARNINGS** — Graph is safe for Owner visual acceptance. Warnings: sequence gaps, empty materials, null planning fields, UI default still 973010 if query omitted.
