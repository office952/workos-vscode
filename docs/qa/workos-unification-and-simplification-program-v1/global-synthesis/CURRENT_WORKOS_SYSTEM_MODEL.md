# Current WorkOS system model

| Field | Value |
|-------|--------|
| Date | 2026-08-14 |
| Baseline | `4018cf271cee156b8014f19c7928f7fd781cefa3` |
| Evidence | Waves 1–5 remotely closed |
| Freeze | `CURRENT_WORKOS_FROZEN_AS_REFERENCE` ON |

```text
CURRENT_WORKOS_MODEL = PARTIAL
```

The working three-spine + lateral-belt model **holds**. It is not one operator story.

## Validated spines

```text
COMMERCIAL   Cerere → Intake V6 → Quote → frozen Order snapshot
COMPILER     Product System → ProductDefinition (no page) → ProductAggregate
EXECUTION    Frozen graph + ExecutionPlan → operational tasks → actuals / MachineRun
```

**Projections (not spines):** Atelier (canonical monitor), `/operator` + `/tablet` (compat action), employee-app-v2 (specialized), Dashboard (admin audit home).

**Lateral belt:** Employees, Attendance, Payments, Advances, Inventory, Pricing registry, Machines, Settings, Documents (mock), Collaborators (supplier projection), Reports (live operational money).

## What WorkOS is now

A **production-cost laboratory / reference** that already contains a real sold-work compiler and a real execution materializer, wrapped in an AppShell that still teaches **implementation history**: FLUX Produse in the commercial strip, three action UIs, audit pages in everyday nav, and mock/demo surfaces that look official.

## What it is not

- One coherent commercial journey (Wave 2 PARTIAL)
- One coherent production action home (Wave 3: monitor ≠ action)
- A live document / HR-dossier / DMS product (Wave 5)
- A second commercial price engine (`/reports`, pricing registry)

## Level-1 systems (final — do not revive 12+9)

1. Sold-work commercial (Intake + Quote + Order snapshot)
2. Compiler (PS / PD / PA)
3. Execution (plan + tasks + MachineRun)
4. People operations (employee master + attendance + payment + advance)
5. Resource registries (inventory + pricing registry + machines + suppliers)
6. Company / CostEngine settings
7. System map / governance (admin)

Everything else is a **projection, compat surface, audit page, demo, or placeholder**.
