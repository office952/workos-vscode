# 2026-07-01 V6 Zero Quote Fast Guard

Status: implemented backend guard with focused tests.

## Root Cause

Intake V6 computes non-zero preview values, but `create_guarded_draft_quote_from_intake_v6_workspace` calls the shared legacy `build_v4_quote_draft_payload`. That builder creates draft quote payloads with placeholder commercial values:

- `subtotal = 0.0`
- `total_before_vat = 0.0`
- `vat = 0.0`
- `grand_total = 0.0`
- line item `unit_price = 0`
- line item `total = 0`

Because V6 used that payload directly, a V6 draft could be persisted with normal quote fields showing `0`, even though the V6 priced quote bridge is not implemented.

## Files Changed

- `backend/services/intake_v6_commercial_quote_service.py`
- `backend/tests/test_intake_v6_zero_quote_fast_guard.py`
- `docs/architecture/product-system/V6_PRICED_QUOTE_BRIDGE_DESIGN.md`
- `docs/worklog/realignment/2026-07-01_v6_zero_quote_fast_guard.md`

## Chosen Behavior

Chosen behavior: A, block creation.

If the V6 draft quote payload has zero quote totals and zero line item commercial values, creation is blocked before persistence with:

- error: `V6_QUOTE_PRICING_NOT_CONNECTED`
- message: `Intake V6 has preview values, but official V6 priced quote bridge is not implemented yet.`
- blockers: `V6_DRAFT_UNPRICED`, `QUOTE_NOT_PRICED`, `V6_QUOTE_PRICING_NOT_CONNECTED`

This is safer than allowing a persisted unpriced draft because the current Oferte and output surfaces can still display `0,00 RON` prominently.

## Tests Run

Command:

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_zero_quote_fast_guard.py -q
```

Result: `4 passed, 3 warnings in 0.68s`.

Covered:

- V6 zero quote payload is blocked before persistence.
- V6 zero placeholder returns `V6_QUOTE_PRICING_NOT_CONNECTED` and marks `V6_DRAFT_UNPRICED` / `QUOTE_NOT_PRICED`.
- Legacy V4 draft builder still returns its existing zero placeholder payload.
- Frontend preview gross/net values in trace data are not copied into official quote totals.
- A non-zero backend-priced payload shape is allowed by the guard.

## What Remains Unresolved

- Official V6 priced quote bridge is still not implemented.
- V6 cannot create a draft quote through this path while the only available payload is the legacy zero placeholder.
- No UI badge/label sweep was done.
- No Quote Snapshot V2 runtime bridge was added.
- No Product Truth persistence or pricing engine rewrite was added.

## Next Practical Step

Add a backend priced quote dry-run for V6 that recomputes commercial totals server-side from stable V6 pricing input/Product Truth data and returns a proposed official price without persisting it. Only after that contract is clear should a guarded priced quote write be added.

## Owner GO Required

Owner GO required before any mutation that creates, prices, snapshots, accepts, converts, or creates orders/tasks from V6 quote data.