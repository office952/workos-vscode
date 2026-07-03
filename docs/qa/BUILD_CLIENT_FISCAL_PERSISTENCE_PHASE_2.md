# BUILD: Client Fiscal Persistence — Phase 2

**Date:** 2026-06-09  
**Status:** **PASS**  
**Scope:** Operator-confirmed save/update of fiscal client data after lookup (`IntakeDetail` identity section)

---

## 1. Purpose

After a successful fiscal lookup (Phase 1), allow the operator to **explicitly** persist company data into the `clients` entity.

**No auto-upsert** on lookup. DB writes happen only when the operator clicks:

- **Salvează client** — when no client exists for normalized CUI
- **Actualizează client** — when exactly one existing client matches

---

## 2. Schema audit (`clients`)

Existing model fields used:

| Persisted from lookup | DB field |
|-----------------------|----------|
| CUI / tax id | `cui` |
| Company name | `name` |
| Address | `address` |
| City | `city` |
| Fiscal identity | `identity_type = "fiscal"` |

**Not persisted in Phase 2** (no schema field — UI preview only):

- registration number / reg. com.
- VAT payer flag
- county / județ
- provider source
- ANAF warnings

**No DB migration** required for Phase 2.

---

## 3. Backend files touched

| File | Role |
|------|------|
| `backend/services/client_fiscal_persistence.py` | CUI normalization, create/update payload builders, match classification |
| `backend/services/clients.py` | `find_by_normalized_tax_id`, duplicate guard on create, fiscal payload helpers |
| `backend/routers/clients.py` | `GET /api/v1/entities/clients/by-tax-id` |
| `backend/tests/test_client_fiscal_persistence.py` | Persistence + endpoint tests |

Frontend:

| File | Role |
|------|------|
| `frontend/src/lib/api.ts` | `lookupClientsByTaxId`, create/update payload builders |
| `frontend/src/pages/IntakeDetail.tsx` | Client match status UI, save/update buttons, success/error states |

---

## 4. New endpoint

```
GET /api/v1/entities/clients/by-tax-id?tax_id=RO12345678
```

| Property | Value |
|----------|-------|
| Method | GET — **read-only** |
| Auth | Requires authenticated user (same router as clients CRUD) |
| Normalization | RO CUI with/without `RO` prefix |
| Response `status` | `invalid_input` \| `none` \| `single` \| `conflict` |
| `matches` | 0, 1, or N client records |

### Conflict handling

If multiple legacy rows normalize to the same CUI → `status: "conflict"`. UI disables save/update and shows manual resolution message.

Create path also rejects duplicate CUI via service guard (`ValueError` → HTTP 400).

---

## 5. UI behavior (`IdentitySection`)

After lookup `found`:

1. Show proposed data badge: **Date propuse din ANAF** / **SmartBill**
2. Show company preview + warnings
3. Resolve client match via `by-tax-id`
4. Display status:
   - **Client inexistent în sistem** → `Salvează client`
   - **Client existent găsit** → `Actualizează client`
   - **Conflict: mai mulți clienți cu același CUI** → buttons disabled
5. Separate action remains: **Confirmă și aplică datele fiscale** (local intake draft only — not DB)

**No auto-save** on lookup success.

---

## 6. Persistence rules

| Rule | Implementation |
|------|----------------|
| Create only on operator click | `createClientEntity` from Save button |
| Update only on operator click | `updateClient` from Update button |
| No save on `not_found` / `invalid_input` / provider errors | No preview persist path |
| Update non-destructive | Empty/`—` lookup values omitted from update payload |
| Duplicate guard | `ClientsService.create` checks normalized CUI |
| Lookup does not mutate clients | Verified by test |

Existing non-empty client fields are preserved when lookup returns blank address/city.

---

## 7. Tests run

```powershell
$env:APP_ENV="development"
$env:ENVIRONMENT="development"
$env:JWT_SECRET_KEY="local-dev-secret-not-for-production"
C:\Users\offic\workos\backend\.venv\Scripts\python.exe -m pytest `
  backend/tests/test_anaf_client.py `
  backend/tests/test_anaf_fiscal_lookup_contract.py `
  backend/tests/test_smartbill_fiscal_lookup_contract.py `
  backend/tests/test_client_fiscal_persistence.py -q
```

Phase 2 coverage includes:

- create after confirmation payload
- update without empty overwrite
- duplicate reject on create
- conflict classification
- `by-tax-id` endpoint none/invalid
- fiscal lookup does not auto-create client

Frontend:

```powershell
npm run typecheck
npm run validate:frontend
```

---

## 8. Boundary — out of scope (Phase 2)

| Item | Status |
|------|--------|
| DB migration | **No** |
| Seed changes | **No** |
| Auto-upsert on lookup | **No** |
| Persist TVA / reg. com. / county | **No** |
| ProductSystem / Pricing / Quote flow changes | **No** |
| Work Intake V2 major refactor | **No** |
| SmartBill invoicing | **No** |
| Phase 3 (extra fiscal fields / migration) | **Not started** |

---

## 9. Manual smoke (optional)

1. Generic intake → fiscal lookup with valid CUI.
2. Verify **Client inexistent** → **Salvează client** → success message.
3. Repeat lookup for same CUI → **Client existent** → **Actualizează client**.
4. Confirm intake local confirm button still separate from DB save.
