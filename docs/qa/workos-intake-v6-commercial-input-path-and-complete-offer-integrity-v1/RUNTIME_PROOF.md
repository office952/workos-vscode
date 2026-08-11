# RUNTIME_PROOF

| Gate | Result |
|------|--------|
| DEMO_DB_ONLY / isolated pytest for mutating proof | YES |
| OWNER_DEV_DB_MUTATIONS | 0 |
| Baseline / markup / discount / manual RON+FX / missing FX | PASS (pytest matrix) |
| FE display = backend totals | PASS (Vitest LiveCalculationSummary) |
| VAT regression | PASS |
| FX regression | PASS |

## Live UI (read-only)

- Stack: `http://127.0.0.1:3000` + `:8000`
- Canonical Intake V6 route base: `/intake-v6-app/:workspaceId/operator`
- Screenshot: `screenshots/settings-fx-configured-commercial-input-v1.png` (configured FX 5.1 for Manual RON conversion dependency — no Owner DB mutation)
- Mutating commercial scenarios proven on isolated test DB only
