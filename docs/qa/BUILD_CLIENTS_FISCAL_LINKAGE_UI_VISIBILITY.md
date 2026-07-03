# BUILD — Clients Fiscal Linkage & UI Visibility

## Scope

Legare fiscal lookup / persistence (Phase 1 + Phase 2) cu zona reală **Clienți**:

- vizibilitate CUI în listă și detaliu;
- căutare după CUI (și câmpuri fiscale existente);
- status fiscal în listă și în `ClientWorkspace`;
- panel manual **Verifică fiscal** în detaliu client, cu preview și update explicit.

Fără migrare DB, fără Phase 3, fără modificări backend.

## Fișiere

| Fișier | Rol |
|---|---|
| `frontend/src/lib/api.ts` | Helpers `getClientFiscalDisplayStatus`, `getClientFiscalDisplayLabel` |
| `frontend/src/pages/Clients.tsx` | Listă clienți: merge entități DB + KPI comercial |
| `frontend/src/pages/ClientWorkspace.tsx` | Detaliu client: entitate DB, card fiscal, panel verificare |
| `frontend/src/components/clients/ClientFiscalVerifyPanel.tsx` | Lookup fiscal + preview + **Actualizează client** (confirmare explicită) |

## Backend

**Neschimbat.** Reutilizează endpointurile existente:

| Endpoint | Utilizare |
|---|---|
| `GET /api/v1/entities/clients` | `listClients()` — registru entități |
| `GET /api/v1/entities/clients/by-tax-id` | `lookupClientsByTaxId()` — conflict guard în panel |
| `PUT /api/v1/entities/clients/:id` | `updateClient()` — doar la confirmare operator |
| `POST /api/v1/intake-assist/fiscal-lookup` | `lookupFiscalProvider()` — preview fiscal |

## Comportament UI

### `/clients`

- Încarcă clienții din registrul entități (`listClients`) și îi combină cu KPI din intakes / quotes / orders (match după nume).
- Clienții salvați din fiscal lookup apar și **fără** activitate comercială (intake / quote / order).
- Căutare după: nume, contact, CUI, adresă, oraș.
- Badge-uri status fiscal:
  - **Date fiscale salvate**
  - **CUI lipsă**
  - **Client fără identificare fiscală**
- Afișare CUI, adresă/oraș când există în entitate.
- Badge **Registru entități** pentru clienți doar din DB.

### `/clients/:clientName`

- Prioritizează entitatea DB față de fallback din intake.
- Header: CUI, adresă, oraș, badge status fiscal, indicator registru entități.
- Card **Identificare fiscală** (status, CUI, tip identitate, adresă/oraș).
- Panel **Verifică fiscal** (doar dacă clientul există în registrul entități):
  1. interogare fiscală backend;
  2. preview date;
  3. **Actualizează client** — doar la click explicit; fără auto-update.

## Boundary

- Fără migrare DB.
- Fără Phase 3 (reg. com., TVA, județ nepersistate).
- Fără auto-upsert.
- Fără seed changes.
- Fără backend changes.
- Fără modificări Work Intake V2 / ProductSystem / Pricing / Quote flow.
- Fără apeluri ANAF reale în teste (mock-only).

## Teste

### Backend (fiscal + client persistence)

```powershell
$env:APP_ENV="development"
$env:ENVIRONMENT="development"
$env:JWT_SECRET_KEY="local-dev-secret-not-for-production"
C:\Users\offic\workos\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_anaf_client.py backend/tests/test_anaf_fiscal_lookup_contract.py backend/tests/test_smartbill_fiscal_lookup_contract.py backend/tests/test_client_fiscal_persistence.py -q
```

Rezultat așteptat: **34 passed**.

### Frontend

```powershell
npm run typecheck
npm run validate:frontend
```

(`validate:frontend` rulează din **root** repo.)

Rezultat așteptat: **PASS** (lint + typecheck + build).

## Observații

1. Panelul **Verifică fiscal** apare doar dacă clientul există în registrul entități; clienții doar din activitate comercială (fără salvare Phase 2) văd status fiscal derivat, dar nu pot actualiza din pagina clientului.
2. Ruta rămâne `/clients/:clientName`; dacă update-ul fiscal schimbă numele firmei, URL-ul poate rămâne temporar pe numele vechi până la navigare manuală.
3. Viitor: rută pe `client.id` ar fi mai robustă decât match pe nume.

## Verdict

**PASS cu observații**
