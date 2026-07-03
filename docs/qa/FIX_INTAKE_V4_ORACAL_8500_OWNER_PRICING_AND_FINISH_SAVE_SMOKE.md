# FIX_INTAKE_V4_ORACAL_8500_OWNER_PRICING_AND_FINISH_SAVE_SMOKE

## Purpose

Add owner-default Intake V4 pricing for Oracal 8500 translucent at **20.0 EUR/m² before VAT** in the centralized Oracal face pricing source, and stabilize Confirm/Review runtime when API previews fail so browser smoke reflects saved finish state and material pricing.

Combined with `DEBUG_INTAKE_V4_FINISH_SAVE_AND_HANDOFF_RUNTIME_CONNECTIVITY`.

## Root cause

### Save / Failed to fetch

- Browser smoke ran while **backend :8000 and frontend :3000 were not listening** (`netstat` showed no `LISTENING` on those ports).
- `Failed to fetch` on Review save and Confirm previews is a **connectivity failure**, not schema rejection for `oracal_641` / `oracal_651` / `oracal_8500`.
- With stack up, `PUT /api/v1/intake-v4/workspaces/{id}/finish-setup` returns **200** and persists to SQLite.

### Handoff LOADING_HANDOFF

- `IntakeV4ConfirmStep` loaded previews via `Promise.all`; on failure it set `handoffPreview = null` with **no error state**.
- `resolveQuoteHandoffUiStatus(null)` treated null as **LOADING_HANDOFF** forever.
- Fix: track `confirmPreviewLoading` / `confirmPreviewError` and surface **HANDOFF_PREVIEW_UNAVAILABLE** with the fetch message when the request fails.

### Oracal 8500 pricing

- `intake_v4_oracal_face_pricing_service.py` had owner prices only for 641/651.
- Material breakdown skipped owner rows when any group used 8500 (`use_owner_oracal_split = not letter_groups_use_oracal_8500_vinyl`), falling back to registry `face_vinyl` (MAT-ORACAL-651).
- Fix: extend centralized owner map with **8500 → 20.0 EUR/m²**, include 8500 in `face_oracal_vinyl_areas_by_series`, always emit `face_vinyl_8500` with `intake_v4_owner_oracal_8500`.

## Before

| Series | Material row | Unit price | Source |
|--------|--------------|------------|--------|
| 641 | face_vinyl_641 | 6.5 EUR/m² | intake_v4_owner_oracal_641 |
| 651 | face_vinyl_651 | 9.0 EUR/m² | intake_v4_owner_oracal_651 |
| 8500 | face_vinyl (registry) | registry | pricing_registry / MAT-ORACAL-651 bleed |

Confirm handoff badge stuck on **LOADING_HANDOFF** when preview fetch failed.

## After

| Series | Material row | Unit price (before VAT) | Source |
|--------|--------------|-------------------------|--------|
| 641 | face_vinyl_641 | 6.5 EUR/m² | intake_v4_owner_oracal_641 |
| 651 | face_vinyl_651 | 9.0 EUR/m² | intake_v4_owner_oracal_651 |
| 8500 | face_vinyl_8500 | 20.0 EUR/m² | intake_v4_owner_oracal_8500 |

Confirm shows **HANDOFF_PREVIEW_UNAVAILABLE** + error text when previews cannot load; when API responds, handoff shows **ACTION_NEEDED** / **REVIEW_REQUIRED** with explicit blockers.

## Endpoints affected

- `PUT /api/v1/intake-v4/workspaces/{id}/finish-setup` — unchanged contract; persistence verified for 641/651/8500
- `GET .../material-breakdown` — emits owner row `face_vinyl_8500` @ 20.0
- `GET .../quote-handoff-preview` — unchanged; UI error handling only

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_oracal_641_651_pricing.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4QuoteHandoffReadiness.test.ts
```

## Runtime smoke (workspace `0f300dcf-0b77-4fc1-affd-6e2a20329804`, stack up)

Direct API (no quote/order/tasks):

- Save `oracal_641` → material breakdown `face_vinyl_641` @ 6.5
- Save `oracal_651` → `face_vinyl_651` @ 9.0
- Save `oracal_8500` → `face_vinyl_8500` @ 20.0
- Handoff preview → `ACTION_NEEDED` with `finish_setup_not_confirmed` (draft save), not infinite loading

## Boundaries

- No quote policy change
- No quote/order/task creation
- No ExecutionPlan / tasks_json
- No stock consumption
- No CostEngine or global Pricing Registry changes
- TVA not included in material breakdown `unit_price`
- Cant Colantat remains Oracal 651 only (unchanged)
- No push

## Files changed

- `backend/services/intake_v4_oracal_face_pricing_service.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/tests/test_intake_v4_oracal_641_651_pricing.py`
- `frontend/src/lib/intakeV4/intakeV4QuoteHandoffReadiness.ts`
- `frontend/src/lib/intakeV4/intakeV4QuoteHandoffReadiness.test.ts`
- `frontend/src/components/workos/intake-v4/steps/IntakeV4ConfirmStep.tsx`
