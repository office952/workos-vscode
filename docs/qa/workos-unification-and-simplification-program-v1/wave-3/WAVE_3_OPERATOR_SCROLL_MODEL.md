# Wave 3 — `/operator` scroll model

| Field | Value |
|-------|--------|
| Route | `/operator` |
| Role × theme for proof | admin × light (gap-closure RT) |
| Original Wave 3 RT | 20-segment cap; MAIN ≈ 74 425 px; `FULL_VERTICAL_SCROLL=FAIL` ×4 |
| Gap-closure log | `runtime/rt-gap-closure-log.json` |

## Classification (exactly one)

**OPERATOR_SCROLL_MODEL = FINITE_STATIC**

| Candidate | Proven? |
|-----------|---------|
| FINITE_STATIC | **YES** |
| FINITE_PAGINATED | NO — API has no `page` / `cursor` / `limit` |
| FINITE_VIRTUALIZED | NO — `nextTasks.map` + assignment `assignableTasks.map` render every row |
| LAZY_APPEND | NO |
| INFINITE_SCROLL | NO |
| POLLING_APPEND | NO — `useOperatorData` fetches once on mount; refresh only after action |
| UNBOUNDED_LIVE_FEED | NO — Atelier polls (`useShopFloorData` 10 s); `/operator` does not |
| UNKNOWN | NO |

**NON_FINITE_BEHAVIOR_PROVEN = NO**

## Evidence

| Probe | Result |
|-------|--------|
| Frontend | `useOperatorData` → single `GET /api/v1/operator/tasks` |
| Backend | `list_all_tasks` selects **all** `execution_plan` rows; no pagination |
| API snapshot | HTTP 200; **234** tasks; 220 `assigned` / 12 `done` / 2 `in_progress`; 19 orders |
| DOM start | Next-task rows **220**; assignment rows **222** |
| DOM end (after jump + 3 s) | 220 / 222 — unchanged |
| INITIAL_SCROLL_HEIGHT | **75277** |
| MAX_SCROLL_HEIGHT_OBSERVED | **75277** |
| HEIGHT_AFTER_JUMP | 75277 |
| HEIGHT_AFTER_SETTLE | 75277 |
| GREW_AFTER_SETTLE | false |
| BOTTOM_REACHED | **YES** |
| ITEM_COUNT_START / END | 234 / 234 |
| LOAD_TRIGGER | mount GET only |
| APPEND_BEHAVIOR | none — full snapshot rendered |
| TERMINATION_CONDITION | `scrollTop >= max` after jump-to-end + 3 s settle |
| WHY_BOTTOM_IS_NOT_STABLE (initial RT) | **20-segment exhaust cap** (~17 k px travel) on an already-tall finite list. The `+4000` probe then looked like “new content”. Not append/poll. |

## Coverage

Finite surface → true bottom required.

| Region | File |
|--------|------|
| top | `runtime/screenshots-gap-closure/admin/light/operator-top/` |
| representative middle | `…/operator-mid/` (`scrollTop` 33491) |
| deep | `…/operator-deep/` (`scrollTop` 63261) |
| bottom | `…/operator-bottom/` |

**REPRESENTATIVE_SCROLL_COVERAGE = PASS**  
**FULL_SCROLL_FAILURES_FINITE_SURFACES = 0** (gap-closure proof supersedes the four original `/operator` FAIL rows)

Original 20-segment packs remain historical. They are **incomplete exhaustion**, not a second truth.
