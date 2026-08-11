# RUNTIME_PROOF

| Gate | Result |
|------|--------|
| DEMO_DB_ONLY / isolated test DB for mutating proof | YES — pytest IsolatedDBFixture (not Owner `backend/dev.db`) |
| OWNER_DEV_DB_MUTATIONS | 0 |
| Settings GET write-on-read FX | NONE (matrix B/C) |
| Settings GET ALTER schema | NONE |
| Persist 4.97 | PASS (`test_matrix_a_settings_persistence_4_97`) |
| Missing FX blocks money resolve | PASS (matrix B) |
| Quote→Order uses 4.97 / blocks when missing | PASS (matrix D) |
| Profitability freeze stable | PASS (matrix E + convert suite) |

## Live UI (read-only)

- URL: `http://127.0.0.1:3000/settings`
- Observed configured FX field (example live value `5.1`) with honest copy: conversion blocked without configured rate; does not auto-use 5
- Screenshot: `screenshots/settings-fx-configured.png`
- No Settings PUT against Owner DB during this proof
