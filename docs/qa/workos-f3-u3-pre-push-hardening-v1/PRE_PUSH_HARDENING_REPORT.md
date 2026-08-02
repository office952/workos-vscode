# F3/U3 pre-push hardening report

| Field | Value |
|---|---|
| Date | 2026-08-02 |
| Controller branch | `feat/capacity-batch-20d-scoped-b-92401` |
| Initial remote | `8a89693a` |
| Initial local HEAD | `7b1ec703` (ahead 2) |
| Hardening commit message | Harden F3 and U3 before push |

## Gates

| Gate | Result |
|---|---|
| Alembic single deployable head | PASS (`s61`) |
| Fresh DB upgrade/downgrade/re-upgrade | PASS |
| AsyncMock RuntimeWarning | PASS (closed; `-W error::RuntimeWarning`) |
| U3 live screenshots day/dark | PASS (14/14) |
| Targeted profitability/post-job tests | PASS (13) |
| U3 `adminProductTruthUi` vitest | PASS |
| Pricing.badges.test | FAIL — pre-existing, no U3/Pricing.tsx delta in F3/U3 range |
| Protected `973019` snapshot | `2d412e6e1234ae44` unchanged |
| Stash `wip-employee-unrelated` | intact at stash@{0} |
| Contamination (DB/secrets/tmp in commit) | excluded |

## Mini decision honored

```text
F3/U3 pre-push hardening first
then F4 canonical material actuals + closed-job proof
U4A scorecard parallel; U4B after stable F4 contracts
```

No premature Profitability Complete / Production Ready / UI Complete claims.
