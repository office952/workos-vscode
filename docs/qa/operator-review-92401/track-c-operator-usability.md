# Track C — Operator Usability Review (92401)

**Mode:** READ-ONLY · API read-model + ops-graph source (browser MCP unavailable this session)  
**Surface:** `/execution/ops-graph?orderId=92401`  
**Date:** 2026-07-31

---

## Questions

| Question | Answer |
|----------|--------|
| Can the operator understand what needs to be done? | **Mostly yes** — 18 pending materialized tasks with process labels, sequence, depends_on, and requirement-class `machine_type`. Lifecycle = `materialized_pending_execution` (not started). |
| Are tasks grouped clearly? | **Partially** — natural clusters by component/module (face → back → return → finish → LED → QC/pack → ACM structure → volum aluminum). Table is sequence-sorted; **no dedicated group headers** in UI. Sequence numbers jump (1…10, 13–14, 24–29) — explainable as provenance seq, may look “missing” until Owner knows count=18. |
| Materials / components / workcenters understandable? | **Components/modules yes** (codes present). **Workcenter field null** — operator sees `machine_type` as planning requirement class (read_clarity). **`material_inputs` empty ×18** — materials not yet useful on this envelope (honesty gap, not invent). |
| Warnings internal vs gap-badge product? | **Internal/control** on ops-graph: trailing honesty / accepted-risk tags; OwnerGoNotice; DEC-009 strip; OR-09 note that EUR/ml in raw labels is provenance softened for display. **Not** a gap-queue product. Do not expand badges. |
| What should Owner inspect visually next? | See checklist below |

---

## Calm / operational character

| Signal | Observed |
|--------|----------|
| RO badge | Present |
| No start/stop/assign/complete controls | Confirmed in page copy + prior batches |
| Metrics: Ops / Sessions / Actuals / DEC-009 | Operational strip, not readiness cockpit |
| Fixture shortcut | Only **973010** — load 92401 via orderId |
| Commercial EUR/ml in some raw labels | Softened by OR-09 ops-graph policy; hover shows raw |

---

## Owner visual inspection checklist

1. Open `http://127.0.0.1:3000/execution/ops-graph?orderId=92401` (do **not** rely on default).  
2. Identity strip: `order_id=92401`, `plan_id=13`, `fixture=—` (MAT-02 is not a UI hardcode label — expected).  
3. Metrics: Ops tasks **18** · Sessions **0**/— · Actuals empty · DEC-009 **A**.  
4. Scan task table: process names + dependency chain readable; confirm no invented minutes.  
5. Note ACM cluster (seq 24–27) and volum-aluminum cluster (28–29) as structure branches.  
6. Optional regression: load Fixture 973010 → still **12** ops.  
7. Do **not** click anything that would authorize/materialize/execute (none should be offered for POST on this screen).

---

## Usability verdict

**PASS WITH WARNINGS** — Operator can review the live plan calmly for workflow understanding. Named friction: sequence gaps, empty materials, null WC/minutes (accepted honesty), must pass `orderId=92401` explicitly.
