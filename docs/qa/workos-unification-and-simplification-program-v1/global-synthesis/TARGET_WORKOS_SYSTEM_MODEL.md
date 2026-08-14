# Target WorkOS system model

Conceptual only. **Do not implement.**

```text
TARGET_WORKOS_MODEL = DEFINED
BIG_BANG_REWRITE_REQUIRED = NO
```

## Recommended commercial teaching

```text
Cerere → configurare în Intake V6 → Ofertă → Comandă înghețată
```

Product System becomes **admin / configuration language**, not a Lucrări step. ProductDefinition stays **without a dedicated page**. Human confirm remains Intake V6.

## Recommended execution teaching

```text
Atelier = canonical monitor (what is happening)
ONE Owner-chosen action surface later (today: /operator is de-facto action)
Tablet / employee-app-v2 = specialized layouts on the same task API
Ops-Graph / Reality Review = Sistem / Audit
```

Do not merge Atelier + operator + tablet blindly. Respect grain:

```text
commercial line  ≠  technical operation  ≠  execution task  ≠  operator card
```

## Recommended people / resources

| Concept | Target |
|---------|--------|
| Employees | KEEP — only master |
| Attendance | KEEP — ≠ session |
| Payments / Advances | KEEP separate truths; **MOVE nav** under Oameni |
| Employee Records | LABEL_DEMO / HIDE_UNTIL_REAL |
| Suppliers | one entity; **both pages remain justified** until Owner picks a primary UI |
| Documents | REMOVE_FROM_PRIMARY_NAV or KEEP_AS_EXPLICIT_DEMO |
| Reports | MANAGEMENT projection; never sold-money |
| Pricing | REFERENCE / admin; never offer editor |
| Utilaje | catalog; link to MachineRun as “stare”, not occupancy |

## Text diagram

```text
COMMERCIAL     Cerere ──► Intake V6 ──► Quote ──► Order snapshot
                    │                      │
COMPILER       Product System / PD / PA ───┘  (admin language)
                    │
EXECUTION      ExecutionPlan ──► tasks ──► Atelier (watch)
                                         ──► action surface (Owner pick)
                                         ──► tablet / employee-app (specialized)
PEOPLE         Employee master ──► Pontaj │ Plăți │ Avansuri
               Evidență HR = demo until real files
RESOURCES      Inventory │ Pricing registry │ Machines │ Suppliers
MANAGEMENT     Reports (live projection) │ Dashboard (admin)
GOVERNANCE     /modules = map + freeze  │ /governance = ownership + gates
```

No new runtime systems. No new registries. No new portals.
