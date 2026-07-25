# Build — Letters↔ACM Intake composition calc wire v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Track** | C — Intake confirm → CPP connection lines per contract |
| **Boundary** | Persist XOR + outbox qty; no CostEngine / Form System ACM-root rewrite |

## Problem

Remus `test-bond-litere` (litere + Alucobond) recommended `letters_plus_support`, but confirm did not persist `applied_content=letters`. CPP gate `is_letters_acm_composition_active` stayed false → no `letters_acm_conn_*` lines.

Secondary bug: even panel-alone `applied_content=none` writes were stripped by `IntakeV4FinishSetup` parse/dump (field missing on schema).

## Delivered

1. Confirm `letters_plus_support` → `finish_setup.applied_content=letters` (+ mirror on `product_composition_confirmed`).
2. Seed `letters_layer_outbox_m2` from mounting template / letter face fallbacks (integral layer, not per-glyph).
3. Schema: `applied_content`, `letters_layer_outbox_m2`, `letters_layer_outbox_source` on `IntakeV4FinishSetup`.
4. Dry-run quote_input enrich copies composition markers from workspace finish.
5. Outbox resolver also reads `quote_input` / `quote_geometry.letter_face_area_m2`.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_letters_acm_composition_persist.py tests/test_letters_acm_composition_commercial_v1.py tests/test_acm_boxed_support_composition_v1.py -q
```

Result: **19 passed**.

## Operator path (Remus)

1. Upload `test-bond-litere.svg`, map Litere + Alucobond.
2. Confirm composition `letters_plus_support`.
3. Live / dry-run CPP should include `acm_*` + VL lines + `letters_acm_conn_*` (șablon 20 EUR/mp, etc.).

## Out of scope

Frame sellable root · adhesive invent rates · EIC mirror · logo XOR branch
