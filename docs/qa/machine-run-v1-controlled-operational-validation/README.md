# MachineRun V1 — Controlled Operational Scenario Validation

**Owner GO:** `AUTHORIZE_MACHINE_RUN_V1_CONTROLLED_OPERATIONAL_SCENARIO_VALIDATION`  
**Date:** 2026-08-09  
**Evidence class:** `CONTROLLED_SCENARIO_EVIDENCE` (not workshop / not `REAL_OPERATIONAL_EVIDENCE`)

```text
LIVE_WORKSHOP_VALIDATION = NOT_AVAILABLE
CONTROLLED_OPERATIONAL_VALIDATION = COMPLETED
```

## Environments

| Env | Purpose | Writes |
| --- | ------- | ------ |
| Protected QA `:3000` + `:8000` (`backend/dev.db`) | Empty list theme/refresh browser | **0** MachineRun writes |
| Isolated `_isolated_s67_validation.db` | Scenario matrix 1–16, 19–20 + HTTP 13–15 | isolated only |
| Isolated closure DB `:8010` (pre-existing) | Optional stateful UI (CORS limited from alt FE ports) | isolated only |

```text
PROTECTED_QA_RUNTIME_WRITES = 0
PROTECTED_BASELINE_DIFF = NONE
```

## Key artifacts

| File | Role |
| ---- | ---- |
| `scenario_matrix.json` | Full 20-scenario results |
| `browser_capture_report.json` | QA light/dark + reload |
| `screenshots/` | list light/dark from QA FE |
| `_seed_isolated_validation.py` | rebuild isolated DB (gitignored) |
| `_run_controlled_scenarios.py` | scenario runner |
| `_browser_capture.mjs` | Playwright capture |

Isolated DB files are gitignored — do not commit.

## Hardening gap (do not fix in this GO)

**TERMINAL_MEMBERSHIP_REELIGIBILITY (S3)**  
After `RELEASE` / `CANCEL`, participant rows can remain `ACTIVE` while the MachineRun is terminal.  
`by-task` lookup correctly ignores terminal runs, but CREATE guard + candidate discovery still treat those ACTIVE rows as blocking → tasks cannot re-enter a new MachineRun / candidate list.

Bounded fix scope is recorded in `scenario_matrix.json` → `hardening_fix_candidate`.

## Verdict pointer

See worklog:  
`docs/worklog/realignment/2026-08-09_machine_run_v1_controlled_operational_scenario_validation.md`
