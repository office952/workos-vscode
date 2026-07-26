# Segmented ACM/ACP electrical connection management

- **Date:** 2026-07-19
- **Branch:** `feature/product-system-active-path-isolation-v1`
- **HEAD initial:** `c4ff585`
- **Verdict:** PASS

## Research summary

Electrical truth was split: letters own LED/PSU/`mains_cable_length_m`; shell owns single `power_supply_service_corner`. Segmented assemblies had no per-panel 220V. Nested new contract under `finish_setup.segmented_background.electrical_connection_management` (no DB migration).

## Ownership

| Owner | Truth |
|-------|--------|
| Shell assembly | Per-panel 220V service points, cable exit/routing notes, inter-panel LV feed, workshop/install flags |
| Letters | Unchanged LED/local wiring |
| Interface | Existing binding `cable_passage_context` / primary-secondary |
| Tasks | `future_task_intent` INFORMATIONAL_ONLY only |

## Runtime

- Backend: `:8002` (compat PASS)
- Frontend: `VITE_API_BASE_URL=http://127.0.0.1:8002`
- Live workspace: `b177a4eb-bdc4-4eb2-8304-2e729f005c4b` (`IV6-2F586DC2`)
- Evidence: `docs/qa/segmented-electrical-2026-07-19/`

## Tests

- `pytest tests/test_acm_segmented_electrical_connection_v1.py` (+ segmented suites) → 34 passed
- Vitest electrical helpers/panel → pass
- Live CASE 1 segmented regression → pass

## Next

Optional: bind `power_supply_group_id` to existing PSU list read-only (still no sizing formulas).
