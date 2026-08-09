# MachineRun UI V1 closure — CREATE / ADD / context links

**GO:** `AUTHORIZE_MACHINE_RUN_UI_CREATE_ADD_AND_CONTEXT_LINKS_CLOSURE`  
**Date:** 2026-08-09  
**Verdict:** PASS · `MACHINE_RUN_V1_E2E = CLOSED`

## Environments

| Env | Purpose | Writes |
| --- | ------- | ------ |
| Live QA `:3000` + `:8000` (`backend/dev.db`) | Regression nav; CREATE button visibility | **0** MachineRun writes (`machine_runs` count stayed 0) |
| Isolated `:3010` + `:8010` (`_isolated_s67_closure.db`) | CREATE/ADD/chips/network | isolated only |

## Request-volume decision (§23)

| Surface | task count | by-task lookups | Verdict |
| ------- | ---------- | --------------- | ------- |
| ExecutionDetail WorkPanel (fixture order 880755) | 1 | 1 | ACCEPTABLE |
| Ops-Graph (same order) | 1 | 1 | ACCEPTABLE |

Typical WorkOS plan pages are ~10–20 tasks. Pattern = one GET per unique `(plan_id, task_key)` with in-page cache — **no bulk API required** at current scale. Documented as `LOOKUP_REQUEST_PATTERN = VERIFIED_ACCEPTABLE`.

## Screenshots (`screenshots/`)

| File | Proof |
| ---- | ----- |
| `mr_list_create_ready_light.png` | CREATE CTA on list |
| `mr_create_dialog_light.png` / `_dark.png` | CREATE dialog theme |
| `mr_create_candidates_light.png` | Multi-plan candidate groups |
| `mr_create_selected_light.png` | Min-2 selection |
| `mr_create_detail_after_light.png` | POST → canonical detail |
| `mr_add_picker_light.png` / `_dark.png` | ADD on HELD |
| `mr_add_after_light.png` | ADD + refetch |
| `ops_graph_chip_light.png` / `_dark.png` | Ops-Graph context chip |
| `execution_detail_chip_panel_light.png` / `_dark.png` | WorkPanel context chip |

## Network / console

- `network_proof.json` — browser API sequence (GET candidates → POST create → GET detail; GET candidate-participants → POST add → GET detail; GET by-task) + live lookup membership.
- `browser_capture_report.json` — full capture log.
- `console_proof.json` — no unhandled promise / React key errors on MachineRun routes. Sparse isolated DB may 404 unrelated ExecutionPlan preview endpoints (not MachineRun loops).

## Seeds (gitignored DB)

- `_seed_isolated_closure.py`
- `_capture_closure.mjs`
- `_network_proof_closure.py`
