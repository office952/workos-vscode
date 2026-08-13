# Wave 3 — Order → Execution

| Field | Value |
|-------|--------|
| ORDER_ROUTE | `/orders/ORD-IV6-V2-1786318810-31` |
| ORDER_ID | `ORD-IV6-V2-1786318810-31` (code) / `973024` (DB) |
| EXECUTION_ENTRY_CONTROL | **Vezi execuția** (generate not shown — plan already exists) |
| CONTROL_LABEL | Vezi execuția |
| DESTINATION | `/execution/973024` |
| CONTEXT_PRESERVED | PARTIAL |
| ORDER_ID_VISIBLE | YES (code on orders; 973024 on execution) |
| EXECUTION_PLAN_ID_VISIBLE | YES/PARTIAL |
| USER_RELEVANCE | Operator must map code ↔ numeric id |
| TECHNICAL_LEAK | URL is DB `order_id` |
| HONESTY_STATUS | GOOD_EDGE (control) + TECHNICAL_DESTINATION (identity) |

Convert does **not** create a plan (backend). Plan is a later step (`POST /plan/from-order` or V2). Wave 2 correctly left generate as SNR. This order already has a plan, so View works without mutation.

Atelier does **not** show ORD-IV6 as the live job. Live card: `print - ORD-92400`.

Gap closure: **DIFFERENT_ACTIVE_WORK**. `ORD-92400` is another order (`order_id=92400`) with the only matching `in_progress` print (`T-M06-CLAIM-POLICY`, Putaru Sandu). 973024 has 18 tasks, **0 in_progress**, so it cannot occupy the machine card. Not a contradiction. See `WAVE_3_ORDER_EXECUTION_ATELIER_IDENTITY.md`.
