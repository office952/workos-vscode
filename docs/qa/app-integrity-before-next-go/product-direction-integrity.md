# Product Direction Integrity

**Repo:** `C:\w\psiso`  
**Date:** 2026-07-31  
**Rule:** WorkOS must not become a gaps / not-ready / badge-driven application. Readiness/gap artifacts = internal QA/control only.

---

## Direction checklist

| Question | Answer | Evidence |
|----------|--------|----------|
| Is WorkOS becoming a gap/badge product app? | **NO** (for capacity/execution path) | Ops-graph remains operational RO surface; 20E made zero UI edits |
| Readiness/gap artifacts internal QA only? | **Mostly yes** | Capacity-batch docs under `docs/qa` + handoff; not productized as operator queue |
| Operator UI focused on order/product, plan, task graph, materials, capacity, decisions? | **YES** on Execution/ops-graph path | `/execution/ops-graph`, plan GET with graph + read_clarity |
| Hardcoded **92401** / **13** / **MAT-02** UI? | **NO** | Grep on `MaterializedOpsGraph.tsx`: no 92401/MAT-02 |
| Fixture-specific UI hardcoding? | **WARN carry** | Default fixture shortcut still **973010 / MAT-01** in `MaterializedOpsGraph.tsx` (`FIX_DEC009_MAT_01_ORDER_ID = 973010`) — historical admin fixture helper, not new 92401 productization |

---

## Historical lab surfaces (context, not new drift from 20E)

These pre-exist under Product System / Intake laboratory chrome and are **not** evidence that Batch 20E productized gaps:

- Product System “NOT READY FOR PRICING” badges / E2E readiness panels
- Intake V6 readiness badges / quote handoff readiness copy
- ExecutionDetail operational readiness badge classes (plan readiness status display)

AGENTS.md still marks Product System laboratory as frozen reference. Do **not** expand gap/badge UI in the next GO.

---

## Batch 20E product-direction prior stamp

From handoff/workflow-adv `product-direction-no-gap-app-check.md`:

- Stamp: **PASS_WITH_WARN**
- No new gap/badge UI
- No hardcoded 92401 / MAT-02
- MAT-01 default 973010 = hygiene WARN carry only

Live re-check agrees.

---

## Verdict

**PASS WITH WARNINGS** — Direction remains operational/workflow-focused for the capacity path. Carry WARN: MAT-01 `973010` fixture default hardcode; do not “fix” it by adding a 92401 hardcode button. Keep readiness/gap packs as QA-only.
