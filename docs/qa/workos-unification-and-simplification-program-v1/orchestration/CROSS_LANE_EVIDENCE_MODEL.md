# Cross-lane evidence model

**One source of truth per registry.** Lanes write fragments. Orchestrator links or appends into canonical files. Do not clone Wave 1 into twelve new encyclopedias.

## Write isolation

```text
orchestration/
  lanes/A|B|C|D|E|F|G|H/     # lane-only
  runtime/                    # RT only
  canonical/                  # ORCH only
  review/                     # REV only
```

No two agents edit the same canonical file in the same turn. Orchestrator reads, then writes. Reviewer never writes canonical.

## Registries (canonical SoT)

| # | Registry | Canonical path | Seed (do not duplicate) | Lane inputs |
|---|----------|----------------|-------------------------|-------------|
| 1 | MASTER_ROUTE_REGISTRY | `canonical/MASTER_ROUTE_REGISTRY.md` | [`../route-inventory.md`](../route-inventory.md) | A–E page cards add `audited` / `owner` |
| 2 | MASTER_PAGE_INTERACTION_REGISTRY | `canonical/MASTER_PAGE_INTERACTION_REGISTRY.md` | [`../PAGE_INTERACTION_INVENTORY.md`](../PAGE_INTERACTION_INVENTORY.md) | Primary lane inventories |
| 3 | MASTER_SCREENSHOT_COVERAGE | `canonical/MASTER_SCREENSHOT_COVERAGE.md` | [`../SCREENSHOT_COVERAGE_MANIFEST.md`](../SCREENSHOT_COVERAGE_MANIFEST.md) | RT segment rows |
| 4 | MASTER_NAVIGATION_GRAPH | `canonical/MASTER_NAVIGATION_GRAPH.md` | [`../NAVIGATION_AND_LINK_GRAPH.md`](../NAVIGATION_AND_LINK_GRAPH.md) | H edges; A–E follows |
| 5 | MASTER_USER_JOURNEY_GRAPH | `canonical/MASTER_USER_JOURNEY_GRAPH.md` | *new* (Wave 1 had nav edges, not journeys) | H primary fragment |
| 6 | MASTER_PAGE_PURPOSE_AND_OWNER_MAP | `canonical/MASTER_PAGE_PURPOSE_AND_OWNER_MAP.md` | Page Completion Foundation roles | Primary lanes |
| 7 | MASTER_UI_PATTERN_LEDGER | `canonical/MASTER_UI_PATTERN_LEDGER.md` | [`../primitive-catalog.md`](../primitive-catalog.md) | F |
| 8 | MASTER_HARDCODED_UI_LEDGER | `canonical/MASTER_HARDCODED_UI_LEDGER.md` | Wave 1 hardcoded notes | F |
| 9 | MASTER_DUPLICATE_TRUTH_LEDGER | `canonical/MASTER_DUPLICATE_TRUTH_LEDGER.md` | *new* | All propose; ORCH owns |
| 10 | MASTER_LEGACY_DEAD_CANDIDATE_LEDGER | `canonical/MASTER_LEGACY_DEAD_CANDIDATE_LEDGER.md` | Policy 19 + DEAD_AND_LEGACY_PATHS | G |
| 11 | MASTER_LIGHT_DARK_ISSUE_MATRIX | `canonical/MASTER_LIGHT_DARK_ISSUE_MATRIX.md` | [`../LIGHT_DARK_VISUAL_RUBRIC.md`](../LIGHT_DARK_VISUAL_RUBRIC.md) | F |
| 12 | MASTER_SYSTEM_CONTRADICTION_LOG | `canonical/CONTRADICTION_LOG.md` | *new* | ORCH only |
| 13 | MASTER_SIMPLIFICATION_CANDIDATE_BACKLOG | `canonical/MASTER_SIMPLIFICATION_CANDIDATE_BACKLOG.md` | *new* | ORCH only (deduped) |

Until Wave 2 runs, canonical files may be **indexes** that point at Wave 1 SoT. Do not copy 174 screenshot rows.

## Flow

```text
Lane fragment  →  RT screenshots (if needed)  →  ORCH merge into one registry
                                              →  REV reads both
```

A lane must cite `file` + `route` + `role` + `theme`. Orchestrator refuses unsourced rows.

## Page card (primary lane only)

Minimum fields: `page_id`, `route`, `role`, `purpose`, `owner`, `reads`, `writes`, `systems`, `interaction inventory status`, `scroll fields`, `disposition proposal` (local), `1:1 leak flags`. Disposition proposal is **not** a global verdict.
