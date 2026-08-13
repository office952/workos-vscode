# Wave 2+ orchestration charter

| Field | Value |
|-------|--------|
| Program | `WORKOS_UNIFICATION_AND_SIMPLIFICATION_PROGRAM_V1` |
| Date | 2026-08-13 |
| Task | Design multi-agent orchestration only |
| Wave 2 execution | **NO** |
| Implementation | NO |
| Cleanup | NO |
| Unfreeze | NO |
| Freeze | `CURRENT_WORKOS_FROZEN_AS_REFERENCE` |
| Owner DB mutations | 0 |

## 1. Goal

Audit the rest of WorkOS at scale **without** losing one coherent system truth.

Not: parallel speed for its own sake.  
Yes: multiple specialized evidence streams → one synthesis → contradiction detection → no local optimization that breaks global logic.

## 2. Model (binding)

```text
MULTI-AGENT RESEARCH
+ SINGLE SYNTHESIS OWNER
+ SINGLE INTEGRATION TRUTH
+ SINGLE RUNTIME OWNER
+ INDEPENDENT CONSISTENCY REVIEWER
```

| Role | Writes | Does not |
|------|--------|----------|
| **System Orchestrator / Synthesis Owner** | `orchestration/canonical/` only | Page-card primary audit; product code |
| **Read-only audit lanes** | `orchestration/lanes/<LANE_ID>/` only | Canonical registries; product code |
| **Runtime / browser coordinator** | `orchestration/runtime/` + screenshot trees | Synthesis verdicts; product code |
| **Consistency reviewer** | `orchestration/review/` only | Synthesis construction; product code |

**Invariant:** `SUBAGENT LOCAL FINDING ≠ GLOBAL SYSTEM VERDICT`. Only the orchestrator may issue global KEEP / SIMPLIFY / MERGE / MOVE / HIDE / REMOVE_CANDIDATE conclusions. Lanes may propose; they may not promote.

## 3. Wave 1 protocol stays permanent

A page is not complete until the invariant in [`../TRAVERSAL_PROTOCOL.md`](../TRAVERSAL_PROTOCOL.md) plus:

`ROUTE` · `PURPOSE` · `OWNER` · all tabs/subtabs/expandables/drawers/modals/popovers · internal links followed once · `FULL_VERTICAL_SCROLL = PASS` on the **actual** container · nested scrollers audited separately · light + dark · loading/empty/error/disabled/read-only reviewed or `STATE_NOT_REACHED` · `PAGE_INTERACTION_INVENTORY` reconciled · `SCREENSHOT_COVERAGE_MANIFEST` complete.

No fake percentages. Scroll bottom alone does **not** complete a route.

## 4. Commercial ≠ execution (carry forward)

```text
COMMERCIAL SERVICE GRANULARITY  ≠  EXECUTION TASK GRANULARITY
```

Classify every 1:1 leak: operation=card · component=tab · registry entity=operator concept · internal status=user status · backend relation=nav relation · task grain=commercial grain. Do not redesign. Classify only.

## 5. Spine the orchestrator must keep in view

AppShell → Intake → Product System → Product Definition → Product Aggregate → Pricing/CPP → Quote → Order → Execution → Actuals/Profitability  

Transversal: HR/Pontaj · Machines/Capacity · Inventory · Pricing Registry · Modules · Governance · Settings · Admin · role homes · diagnostic/reference · legacy/compat.

Canonical boundary docs: `docs/architecture/realignment/` 00–19 and `docs/architecture/product-system/WORKOS_SYSTEMS_ALIGNMENT_MAP.md`.

## 6. What this charter does not authorize

Wave 2 runtime traversal · product code · cleanup · deletion · redesign · unfreeze · page `FINAL` · competing dev servers · parallel Playwright against one mutable role/theme session · Owner `dev.db` writes.
