# Operator Usability Review — 92401 Ops Graph

**Mode:** READ-ONLY  
**Date:** 2026-07-31  
**URL:** `http://127.0.0.1:3000/execution/ops-graph?orderId=92401`

---

## Access evidence

| Check | Result |
|-------|--------|
| Frontend HTTP for Owner URL | **200** |
| Query param `orderId=92401` | Present in URL (required — no 92401 hardcode) |
| Agent browser React mount | **Failed** (empty `#root` after wait; shell only) — **Owner must confirm visually in local browser** |
| Read-model via API | Full 18-task graph available for review |

Agent automated UI capture is **insufficient** for final visual ACCEPT; API/read-model + source structure support recommending Owner visual acceptance.

---

## Calm / operational character (source + API)

| Question | Answer |
|----------|--------|
| Understandable task graph? | **Yes** — process labels, sequence, depends_on, machine_type as requirement class |
| Materials / components / workcenters? | Components/modules present · WC field null · materials empty ×18 (honesty) |
| Gap/badge productization? | **No** — RO badge, metrics strip, accepted-risk honesty tags, OwnerGoNotice; not a gap queue |
| Hardcoded 92401 UI? | **No** — only MAT-01 `973010` fixture shortcut/default |
| Capacity focus? | DEC-009/capacity strip is read-only status, not execute controls |

---

## What Owner should inspect visually

1. Open **exactly** `http://127.0.0.1:3000/execution/ops-graph?orderId=92401` (do not use bare `/execution/ops-graph`).  
2. Identity: `order_id=92401`, `plan_id=13`, `fixture=—` (MAT-02 not hardcoded — expected).  
3. Metrics: Ops **18** · Sessions **0**/— · Actuals empty · DEC-009 **A**.  
4. Table: 18 rows; dependency chain readable; minutes show as — / honesty (not invented).  
5. Confirm RO — no start/stop/assign/complete/POST.  
6. Optional: Fixture 973010 still loads **12** ops.  
7. Mentally note sequence gaps (1…10, 13–14, 24–29) = provenance, not missing count.

---

## Verdict

**PASS WITH WARNINGS — safe for Owner visual acceptance**  
Agent browser did not render React UI; Owner eyes on local browser remain the acceptance step. Named friction: sequence gaps, empty materials, null WC/minutes, 973010 default if query omitted.
