# Wave 4 — active / sold / execution scope

```text
Product System (can exist)
  → Intake V6 workspace (configured / selected)
  → ProductDefinition preview (compiled active modules)
  → ProductAggregate (graph + measurements + task_contract)
  → CPP / V6 preview money
  → Quote snapshot (when handoff exists)
  → Order snapshot FROZEN
  → Execution plan from frozen graph
```

Representative (Wave 2/3 fixture):

| Question | Answer |
|----------|--------|
| SELECTED | V6 payload (geometry, finishes, modules) — confirm still had blockers |
| ACTIVE | Letters Slice 1 offer_scope / compile_active_scope |
| SOLD | Order `ORD-IV6-V2-1786318810-31` frozen snapshot |
| FROZEN | `order_snapshot_service` copies PD + cost + quote; no recompile |
| REACHES EXECUTION | 973024 / 18 tasks named from template graph |
| AUTHORING ONLY | PS workshops, composer mock, planned sections, candidate COMP-* |

Drift: V6 confirm blocked vs order already frozen (**DEFINITION_DRIFT**). Live Atelier ≠ this order (execution UI, not PS). Premount root_offerable BE vs FE scope omit.

**ACTIVE_SOLD_EXECUTION_SCOPE = PARTIAL**
