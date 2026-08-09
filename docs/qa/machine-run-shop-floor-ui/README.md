# MachineRun shop-floor UI — evidence pack

**GO:** `AUTHORIZE_MACHINE_RUN_SHOP_FLOOR_UI_IMPLEMENTATION`  
**Date:** 2026-08-09  
**Primary route:** `/execution/machine-runs`

## Environments

| Env | Purpose | Writes |
| --- | ------- | ------ |
| Live QA `:3000` + `:8000` (`backend/dev.db`) | Empty list + navigation | **0** MachineRun writes |
| Isolated `:3010` + `:8010` (`_isolated_s67_ui.db`) | State matrix + network commands | isolated only |

## Screenshots (`screenshots/`)

| File | Proof |
| ---- | ----- |
| `mr_list_empty_light.png` / `_dark.png` | QA empty list theme matrix |
| `mr_list_active_light.png` / `_dark.png` | Isolated open list |
| `mr_detail_held_light.png` / `_dark.png` | HELD detail |
| `mr_detail_reserved_dark.png` | RESERVED detail |
| `mr_detail_running_dark.png` | RUNNING detail |
| `mr_detail_completed_dark.png` | COMPLETED + release hint |
| `mr_detail_released_light.png` / `_dark.png` | RELEASED read-only |

## Network

`network_proof.json` — CREATE→CONFIRM→START→COMPLETE→RELEASE on isolated `:8010` with `expected_version` + GET refetch after each command.

## Console

No uncaught exceptions / failed route loads observed on `/execution/machine-runs` during browser QA (light + dark).

## Seeds (not committed)

- `_seed_isolated_states.py` — rebuilds isolated DB  
- `_network_proof.py` — command audit  
- `_isolated_s67_ui.db` — gitignored  
