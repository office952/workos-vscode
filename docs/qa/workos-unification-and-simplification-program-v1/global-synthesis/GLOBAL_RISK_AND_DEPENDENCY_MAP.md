# Global risk and dependency map

## Dependency graph

```text
OD-1 ──► S1 (FLUX + commercial labels)
OD-2, OD-3 ──► S2 (Documents / Evidență)
OD-7, OD-10 ──► S3 (reports + people money IA)
S1 ──► S4, S5
OD-6 ──► S6 (blocked until chosen)
S1–S3 ──► S7
S1–S4 ──► S8
OD-5 ──► forbids inventing PD page in any wave
OD-9 ──► forbids premount activation
OD-11 ──► forbids “fixing” pontaj RBAC in S1–S5
```

## Risks if we ignore the plan

| Risk | If ignored | Mitigation |
|------|------------|------------|
| Commercial lie | Sales configure in Product System | S1 first |
| Snapshot vs live money | Reports treated as sold | GS-04 / OD-7 |
| Merge grains | Atelier starts 234 tasks | S6 gated |
| Merge people money | Payment write into labor | VALID_SEPARATE |
| Unfreeze by accident | Feature work during reference freeze | IMPLEMENTATION = NO until Owner |
| Big-bang | New shell + domain + nav together | 8 bounded waves |
| Silent finding drop | Wave issues vanish | GLOBAL_CONSISTENCY_REVIEW |
| False REMOVE | Kill `/operator` as “dup” | ACTIVE_COMPAT |

## What must not move together

- Navigation + ProductDefinition + Execution action in one GO
- RBAC + IA + pricing
- Display rename + API/DB rename
- Documents “real storage” + nav hide (would invent a product)

## Rollback posture

Every proposed wave is display/nav first. Compat routes stay. No schema. No unfreeze in the plan itself.
