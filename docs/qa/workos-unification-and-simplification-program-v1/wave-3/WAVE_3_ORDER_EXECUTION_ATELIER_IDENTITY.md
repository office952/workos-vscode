# Wave 3 — Order → Execution → Atelier identity

Observed in the initial audit: `ORD-IV6-V2-1786318810-31` → `/execution/973024`, while Atelier showed `print - ORD-92400`.

**This is not an identity contradiction.**

## Classification (exactly one)

**ORDER_EXECUTION_ATELIER_RELATION = DIFFERENT_ACTIVE_WORK**

| Candidate | Why not |
|-----------|---------|
| SAME_WORK_COHERENT | Live Atelier job is a different `order_id` |
| SAME_WORK_IDENTITY_SPLIT | 973024 ↔ IV6 is code vs DB id of **one** order; 92400 is **another** order |
| DIFFERENT_ACTIVE_WORK | **YES** — `ORD-92400` has the live `in_progress` print |
| STALE_PROJECTION | Live API + tick; 92400 task is `in_progress` now |
| FILTERED_OUT | Secondary fact: 973024 has **no** `in_progress` task, so it cannot occupy the machine card |
| CONTRADICTION | Same-work facts do not conflict |
| UNKNOWN | Resolved |

## Required answers

| Question | Answer |
|----------|--------|
| Is 973024 expected on Atelier? | As a **job row** only if the shop-floor job table projects all operator-task orders. As the **live machine card**, **no** — occupancy requires `status === in_progress` and a `machine_type` match (`useShopFloorData.mapDBMachineToMachine`). 973024 has 0 `in_progress` tasks. |
| What filter controls Atelier visibility? | Live card: `in_progress` ∩ machine_type substring. Queue count: `assigned` ∩ machine_type. Job list: one job per `order_id` from the same unbounded operator-task payload. |
| Is ORD-92400 another active job? | **YES.** `order_id=92400`, `order_code=ORD-92400`, task `T-M06-CLAIM-POLICY` / print / `in_progress` / employee 4 Putaru Sandu. |
| What id does ExecutionPlan expose? | URL and page: numeric **`order_id` 973024**. Body also shows commercial **`ORD-IV6-V2-1786318810-31`**. |
| What id does Atelier expose on the live card? | `currentJobId = ORD-${order_id}` → **`ORD-92400`**. Here the commercial code happens to equal `ORD-{db id}`. |
| Is the commercial Order id preserved downstream? | On Execution detail: **YES** (`order_code`). On Atelier live card: **only if** `order_code` equals `ORD-{id}`; the card prints the **DB id**, not `order_code`. Operator rows use `JOB-{order_id}`. |
| Can a human trace the same job without DB ids? | Order → Execution: **partial** (Vezi execuția keeps the work, URL becomes 973024). Execution → Atelier live card: **no** for this IV6 order — it is not the live job. Operator list **does** contain 973024’s 18 tasks, buried in 234 rows. |

## Snapshot facts (gap-closure GET)

**973024 / `ORD-IV6-V2-1786318810-31`:** 18 tasks; 1 `done` (`CUT_FACE`, Florin CNC); 17 `assigned`; **0 `in_progress`**.

**92400 / `ORD-92400`:** 1 task; **`in_progress`**; print; Putaru Sandu.

**Atelier DOM:** `ORD-92400` present; `973024` absent; IV6 code absent.

**Execution `/execution/973024`:** 973024 + IV6 present; 92400 absent.

## Identifier map

| Layer | Identifier shown |
|-------|------------------|
| Orders | `ORD-IV6-V2-1786318810-31` |
| Execution URL | `/execution/973024` |
| Operator job chip | `JOB-973024` / `JOB-92400` / `JOB-23099` |
| Atelier live card | `ORD-92400` (from `order_id`) |
| Tablet print active | `ORD-92400` + `T06 Claim Probe` |

W3-C1 / W3-C4 in the initial contradiction log are **retracted** as contradictions. See `WAVE_3_SYSTEM_CONTRADICTIONS.md`.
