# Wave 2 scope recommendation

**WAVE_2_EXECUTION_AUTHORIZED = NO.** This file proposes a boundary only.

## WAVE_2_SCOPE

**Lucrări commercial remainder — Cereri + Comenzi + Clienți list — with Wave 1 `/quotes` as pinned neighbor. Product System excluded.**

| Field | Value |
|-------|--------|
| WHY | Proves multitasking (A primary + F/H observers + ORCH + REV + RT) on the operator-critical Intake→Quote→Order spine without the Product System 16-route lab tree or Producție graph/tablet sprawl. `/quotes` is already reconciled — Wave 2 tests *handoff*, not a redo. |
| EXPECTED_LANES | `A` (primary), `F` (observer), `H` (observer), `G` (static V4-in-V6 classify only), `ORCH`, `REV`, `RT` |
| EXPECTED_SURFACES | `/intake` (list); `/intake-v6/operator` and one existing workspace if reachable without create; `/orders` (list); `/orders/:orderId` if a fixture exists without mutation; `/clients` (list). Observe `/quotes` (Wave 1). Optional: `/clients/:clientName` only if read-only. |
| EXPECTED_DURATION_CLASS | **MEDIUM** |
| Route count | ~5–7 actionable (not ~26 Lucrări, not ~85 app) |
| Interaction | High on Intake V6 workspace; medium on orders/clients lists |
| Centrality | Highest remaining spine; sales home already done |
| Evidence volume | Manageable if V6 is **one** workspace, not every historic file |

## Explicitly out of Wave 2

- All `/product-system/**` (lane D, later)
- `/execution/**`, tablet, operator, employee-app (lane B)
- HR / payments (lane C)
- Inventory / pricing / utilaje / settings (lane E)
- Creating intake workspaces, sending quotes, converting orders
- Redesign, cleanup, unfreeze

## Success for the *model* (not the product)

1. A writes page cards only under `lanes/A/`.
2. F and H write observations only.
3. RT is the only browser driver; scroll exhaustion on `main` (+ nested if any).
4. ORCH writes one synthesis; no lane writes canonical.
5. REV returns PASS / PASS_WITH_GAPS / CONTRADICTION_FOUND / INSUFFICIENT_EVIDENCE.
6. Zero product-code diffs. Zero Owner DB writes.

If the model holds, Wave 3 can take **B (production remainder)** or **D (Product System)** as a separate Owner GO — not both.
