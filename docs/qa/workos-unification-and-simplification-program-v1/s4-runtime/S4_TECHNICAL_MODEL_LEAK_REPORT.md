# S4 — Technical-model leak reduction (Option B)

| Field | Value |
|-------|--------|
| Task | `S4_TECHNICAL_MODEL_LEAK_REDUCTION_V1` |
| Option | B |
| Date | 2026-08-14 |
| HEAD before | `9ab027787d1c078fc771c9065c2eab6b25160614` |
| Implementation | YES (display only) |
| Unfreeze | NO |
| Push | NO |

## Verdict

S4 = **PASS**. Factory facts stayed. System implementation language was demoted on Atelier, Operator, Tablet, and Planning first-fold chrome.

## What changed

| Area | Old | New |
|------|-----|-----|
| Atelier breadcrumb | Shop Floor | Atelier |
| Atelier WC titles | CNC_ROUTING / METAL_FAB / LETTER_FORMING | CNC / Lăcătușerie / Sudură / Modelare litere |
| Operator title fallback | raw `task_id` (`node:…`) | component label or `Task producție` |
| Component role badge | `root product` | Produs principal / Componentă |
| Release strip | `Politica: ORDER AND PLAN…` | actionable status; raw policy in details |
| Tablet routing | `Operație {code} → stație {id}` | `Operație {name} → {station}` |
| Planning first fold | Capacity Stage 1 · IMPLEMENTED_INACTIVE, DEC-009, NEEDS ASSIGNMENT TRUTH, EXECUTION PLAN | Detalii tehnice planificare (collapsed) |
| Execution detail | V2 truth panel above the fold | Detalii tehnice plan (collapsed) |
| Machine-run participant | always-visible `task_key` | Detalii tehnice |

Unchanged: backend, routes, RBAC, execution/task generation, Intake V6, Ops-Graph, Reality Review, Product Truth.

## Screenshots

- [s4-atelier-dark.png](s4-atelier-dark.png)
- [s4-atelier-light.png](s4-atelier-light.png)
- [s4-operator-light.png](s4-operator-light.png)
- [s4-tablet-print-light.png](s4-tablet-print-light.png)
- [s4-tablet-print-dark.png](s4-tablet-print-dark.png)
- [s4-execution-dark.png](s4-execution-dark.png)
- [s4-execution-details-open-dark.png](s4-execution-details-open-dark.png)
- [s4-execution-detail-92401-dark.png](s4-execution-detail-92401-dark.png)

## Owner visual verification

1. Atelier — `http://127.0.0.1:3000/shop-floor` — role admin — H1 + breadcrumb **Atelier** — WC titles human — no Shop Floor / CNC_ROUTING as titles.
2. Operator — `http://127.0.0.1:3000/operator` — example **T06 Claim Probe** — no `node:root_product…` headline — raw policy under Detalii politică.
3. Tablet — `http://127.0.0.1:3000/tablet/print` — routing `Operație … → Print` / `Rutare neconfirmată pentru …`.
4. Planning — `http://127.0.0.1:3000/execution` — first fold = next step + Owner GO + order table — open **Detalii tehnice planificare** for IMPLEMENTED_INACTIVE / DEC-009.
5. MachineRun — `http://127.0.0.1:3000/execution/machine-runs` — **STATE_NOT_REACHED** (no active run). Unit proof: `task_key` only inside details.

## Stop

No push. No S5.
