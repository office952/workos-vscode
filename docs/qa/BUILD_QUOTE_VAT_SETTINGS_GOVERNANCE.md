# BUILD — Quote VAT Settings Governance

## Purpose

Enforce company-level VAT (`default_vat_pct`) as the single editable source for quote generation. Quotes snapshot VAT at pricing time; documents/PDF use the snapshot, not live Settings.

## Decision

- TVA is a **company setting**, editable only in `/settings` (Societate → TVA ofertare).
- Canonical runtime source: `company_commercial_settings.default_vat_pct`.
- Central default: `DEFAULT_VAT_PCT = 21`.
- `0%` VAT is valid and must not be coerced to 19/21.

## Migration / table / API

| Item | Detail |
|------|--------|
| Migration | `s46_company_commercial_settings` |
| Table | `company_commercial_settings` (`id`, `default_vat_pct`, `created_at`, `updated_at`) |
| Service | `backend/services/company_commercial_settings_service.py` |
| GET | `/api/v1/company-commercial-settings` |
| PUT | `/api/v1/company-commercial-settings` — body `{ "default_vat_pct": number }` |
| Auth | `settings.view` / `settings.update` |

Singleton row: service `get_or_create()` creates default row when missing.

## VAT input removed (frontend)

| Location | Change |
|----------|--------|
| `Settings.tsx` | **Added** editable TVA % panel (only edit surface) |
| `QuoteWizard.tsx` | Read-only “TVA aplicat din Settings: X%” |
| `VolumetricLettersQuoteFlow.tsx` | `CommercialPricingPanel` — VAT read-only from Settings |
| `ProductSystemPricingPreview.tsx` | Read-only Settings VAT display |
| `quoteRevision.ts` | 0-safe fallback via `DEFAULT_VAT_PCT` |

## Quote generation (backend)

- `quotes.py`: `_apply_settings_vat_to_pricing()` overrides `pricing.vat_pct` from Settings before orchestrator.
- `product_system_cost_simulation_service.py`: preview uses Settings VAT; ignores request `vat_pct`.
- `productsystem_pricing_preview_service.py`: same.
- Persisted: `quotes.vat` = snapshot `pricing.vat_pct`; `line_items` JSON includes `pricing.vat_pct`.

## Document / PDF

- `quote_document_service.py`: `_resolve_quote_vat_percent()` from snapshot `pricing.vat_pct` or `quote.vat`; fallback `DEFAULT_VAT_PCT` only when both missing.
- `quote_legacy_revision.py`: `_legacy_quote_vat_pct()` — 0-safe (no `or 19`).
- `quote_pdf_service.py` / `quote_documents.py`: use document snapshot; no hardcoded 19.

## 0% handling

- Validation allows `0 <= value <= 100`.
- `None` falls back to default only when row/field missing, not when value is `0`.
- Document totals: `tva = total_before_vat * (tva_percent / 100)` preserves zero.

## Tests

### Backend

- `tests/test_company_commercial_settings.py` — service + API
- `tests/test_quote_vat_settings_governance.py` — snapshot, document, legacy, override
- Updated `tests/test_quote_commercial_document.py` — vat_pct semantics

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_company_commercial_settings.py tests/test_quote_vat_settings_governance.py tests/test_quote_commercial_document.py -q
```

### Frontend

- `frontend/src/pages/Settings.vatGovernance.test.tsx`
- `frontend/src/components/workos/QuoteWizard.vatGovernance.test.tsx`

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/Settings.vatGovernance.test.tsx src/components/workos/QuoteWizard.vatGovernance.test.tsx
```

## Runtime smoke (manual)

1. `/settings` → Societate → set TVA 21 → save.
2. Generate test quote → flow shows read-only 21%; document/PDF 21%.
3. Set TVA 0 → new quote shows 0%; document/PDF 0% (not 21).
4. Change Settings back to 21 → old quote with snapshot 0% still shows 0%.

## Boundaries (not touched)

- CostEngine pricing formulas / orchestrator VAT math
- SmartBill, payroll, inventory
- Quote history rows (no retroactive VAT rewrite)

## Risks

- Legacy quotes where `quotes.vat` stored VAT **amount** (not %) may mis-resolve if snapshot lacks `pricing.vat_pct`; prefer snapshot when present.
- Societate tab still shows static mock company identity alongside live VAT panel.
- Local dev without Alembic upgrade relies on `create_all` — table created on first settings access via ORM.

## Commands run

```powershell
cd backend
Copy-Item .\dev.db .\dev.db.bak-<stamp>-pre-vat-settings-migration
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:APP_ENV='development'
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest tests/test_company_commercial_settings.py tests/test_quote_vat_settings_governance.py tests/test_quote_commercial_document.py -q
# 47 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/Settings.vatGovernance.test.tsx src/components/workos/QuoteWizard.vatGovernance.test.tsx
# 5 passed
```
