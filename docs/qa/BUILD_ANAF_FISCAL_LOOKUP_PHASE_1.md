# BUILD: ANAF Fiscal Lookup — Phase 1

**Date:** 2026-06-09  
**Status:** **PASS**  
**Scope:** Fiscal company lookup for Work Intake identity (`IntakeDetail` generic path)

---

## 1. Purpose

Add official **ANAF** fiscal lookup alongside existing **SmartBill** integration, without changing the fiscal lookup contract consumed by the frontend.

Operators can resolve RO company data (name, CUI, address, TVA status signals, e-Factura warnings) via:

- `provider: "anaf"` — ANAF only
- `provider: "smartbill"` — legacy SmartBill only
- `provider: "auto"` — ANAF first, SmartBill fallback only on technical failure

---

## 2. Files touched

| Area | File |
|------|------|
| Backend ANAF client | `backend/services/anaf_client.py` |
| Provider orchestration | `backend/services/fiscal_lookup_service.py` |
| API boundary | `backend/routers/intake_assist.py` |
| Frontend API/types | `frontend/src/api/intakeAssist.ts` |
| UI lookup | `frontend/src/pages/IntakeDetail.tsx` (lookup + preview only in Phase 1 scope) |
| Tests | `backend/tests/test_anaf_client.py` |
| Tests | `backend/tests/test_anaf_fiscal_lookup_contract.py` |
| Tests | `backend/tests/test_smartbill_fiscal_lookup_contract.py` |

---

## 3. Contract preserved

`POST /api/v1/intake-assist/fiscal-lookup` response shape unchanged for frontend consumers:

- `available`, `provider`, `status`, `message`
- `normalized`: `tax_id`, `company_name`, `registration_number`, `address`, `city`, `county`, `country`, `vat_payer`, `source`
- `warnings[]`
- `requires_operator_confirmation`

Extended literals only:

- request `provider`: `"anaf" | "smartbill" | "auto"` (default `"auto"`)
- response `provider`: resolved `"anaf" | "smartbill"`
- `normalized.source`: `"anaf" | "smartbill"`

---

## 4. Providers

| Provider | Behavior |
|----------|----------|
| `anaf` | Calls ANAF v9 `PlatitorTvaRest` only |
| `smartbill` | Existing SmartBill client only |
| `auto` | ANAF first; SmartBill only if ANAF returns technical failure |

### Fallback rules (`auto`)

Fallback to SmartBill **only** when ANAF status is:

- `provider_timeout`
- `provider_error`
- `rate_limited`
- `not_configured`

**No fallback** when ANAF returns:

- `found`
- `not_found`
- `invalid_input`

Business-negative ANAF data (inactive, non-VAT payer, e-Factura warnings) stays on ANAF result — **not** a fallback trigger.

---

## 5. ANAF warnings

When ANAF returns `found`, backend may attach warnings such as:

- contribuabil inactiv
- neînregistrat RO e-Factura
- stare înregistrare atipică

Frontend displays warnings via optional `payload.warnings?.length` — empty/missing warnings do not break UI.

---

## 6. ANAF client details

- Production URL: `https://webservicesp.anaf.ro/api/PlatitorTvaRest/v9/tva`
- No authentication required
- In-memory cache + ~1 req/s rate limiter
- Config via env: `ANAF_ENABLED`, `ANAF_TVA_URL`, `ANAF_TIMEOUT_SECONDS`, `ANAF_CACHE_TTL_SECONDS`, `ANAF_RATE_LIMIT_SECONDS`

---

## 7. Tests run

```powershell
$env:APP_ENV="development"
$env:ENVIRONMENT="development"
$env:JWT_SECRET_KEY="local-dev-secret-not-for-production"
C:\Users\offic\workos\backend\.venv\Scripts\python.exe -m pytest `
  backend/tests/test_anaf_client.py `
  backend/tests/test_anaf_fiscal_lookup_contract.py `
  backend/tests/test_smartbill_fiscal_lookup_contract.py -q
```

Expected: all Phase 1 fiscal lookup tests pass with mocked providers (no live ANAF HTTP in tests).

Frontend:

```powershell
npm run typecheck
npm run validate:frontend
```

---

## 8. Boundary — out of scope (Phase 1)

| Item | Status |
|------|--------|
| Client DB persistence | **Not in Phase 1** → Phase 2 |
| DB migration | **No** |
| Seed changes | **No** |
| Live ANAF calls in automated tests | **No** — mock only |
| Work Intake V2 rewrite | **No** |
| ProductSystem / Pricing / Quote flow | **No** |
| SmartBill invoicing | **No** |

---

## 9. Manual smoke (optional)

1. Open generic `IntakeDetail` (non-volumetric shell).
2. Enter valid RO CUI → **Interogare fiscală backend**.
3. Confirm preview shows company data + provider badge (ANAF/SmartBill).
4. Confirm warnings render when present; no crash when absent.
