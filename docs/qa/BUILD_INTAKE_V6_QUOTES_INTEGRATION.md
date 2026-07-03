# BUILD — Integrare Intake V6 ↔ Oferte (Quotes)

**Date:** 2026-07-02  
**Status:** **PASS** (integrare funcțională + verificare runtime quote #6)  
**Branch:** `fix/intake-v6-quotes-integration`  
**Base:** `feature/step-7g-commercial-price-proposal`  
**Commits principale:** `7ad7642`, `5b0840d`

**Documente companion:**

- [V6_PRICED_QUOTE_BRIDGE_DESIGN.md](../architecture/product-system/V6_PRICED_QUOTE_BRIDGE_DESIGN.md) — design inițial (problema zero-path)
- [V6_PRICED_QUOTE_WRITE_PATH_DESIGN.md](../architecture/product-system/V6_PRICED_QUOTE_WRITE_PATH_DESIGN.md) — write + guards
- [QUOTE_SNAPSHOT_V2_FOR_V6_PRICED_QUOTES.md](../architecture/product-system/QUOTE_SNAPSHOT_V2_FOR_V6_PRICED_QUOTES.md) — snapshot comercial
- [2026-07-01_v6_dry_run_runtime_fix_and_quote6_trace.md](../worklog/realignment/2026-07-01_v6_dry_run_runtime_fix_and_quote6_trace.md) — trace runtime + crash fix

---

## 1. Problema

Ofertele create din Intake V6 apăreau în **Oferte** (`/quotes`) cu **0,00 RON**, deși operatorul vedea estimări non-zero în Intake (calcul live, material breakdown, pricing input preview).

### Simptome observate

| Unde | Ce vedea operatorul | Ce era adevărul |
|------|---------------------|-----------------|
| Intake V6 — Review / Calcul live | ~6000+ RON (preview) | **Non-oficial** — aid UI |
| Intake V6 — Confirm → Creare draft | Quote creat, handoff OK | Draft **intenționat nepretuit** (`grand_total = 0`) |
| Oferte — card / detail | `0,00 RON` ca total comercial | Coloane DB quote nepopulate |
| Oferte — acțiuni comerciale | Fără buton de prețuire oficială | Backend avea API-uri, **frontend nu le apela** |

### Cauze (stratificate)

1. **Draft boundary by design** — `create-draft-quote` scrie placeholder 0 RON; preview-ul Intake nu devine automat preț oficial.
2. **Lipsă UI bridge** — endpoint-urile `priced-quote-dry-run`, `priced-quote/write`, `snapshot-v2` existau pe backend dar **nu erau legate în Quotes.tsx**.
3. **Crash runtime dry-run** — `CommercialPriceProposalService._classify_modules()` apelat cu semnătură veche → `TypeError` la primul dry-run real.
4. **Reguli comerciale incomplete** — unele module/reguli owner (dev-bridge Step 8) blocau dry-run până la completarea rate-urilor interim.

---

## 2. Soluția (rezumat)

Am implementat un **pod comercial V6** în pagina Oferte: operatorul pornește de la draft nepretuit, rulează **dry-run backend**, scrie **total oficial** pe quote, apoi poate continua fluxul (Snapshot V2 → review → accept → comandă) prin **commercial spine**.

```
Intake V6 Confirm
    │ create-draft-quote (grand_total = 0, draft intern)
    ▼
Oferte / Quotes detail
    │ detectează quote V6 + workspace_id
    │ IntakeV6QuoteCommercialSpinePanel
    ▼
GET  .../priced-quote-dry-run     ← recomputare server-side din Product Truth
    │ V6_PRICED_DRY_RUN_READY + total > 0
    ▼
POST .../priced-quote/write       ← persistă subtotal/VAT/grand_total pe quote
    ▼
POST .../quotes/{id}/snapshot-v2  ← îngheață total comercial (când guards permit)
    ▼
Flux comercial existent (pricing review, owner approval, accept, convert)
```

**Regula de aur:** UI Intake **nu** copiază preview-ul în DB. Doar backend-ul, după dry-run + write confirmat, devine sursa prețului oficial.

---

## 3. Detectarea ofertelor V6 în UI

### Identificare quote V6

`frontend/src/lib/intakeV6/intakeV6QuoteDisplay.ts`:

- `isIntakeV6Quote()` — `intakeId` începe cu `IV6-` **sau** `id` match `Q-V6-IV6-...`
- `isUnpricedIntakeV6Quote()` — status `draft` **și** `grandTotal <= 0`
- `formatV6QuoteTotalLabel()` — afișează **„Nepretuit (draft V6)”** în loc de `0,00 RON` misleading

### Legătura quote ↔ workspace

`frontend/src/pages/Quotes.tsx` — `deriveIntakeV6WorkspaceId()`:

| Sursă | Pattern | Workspace UUID |
|-------|---------|----------------|
| `quote.intakeId` | `IV6-{uuid}` | suffix după `IV6-` |
| `quote.id` | `Q-V6-IV6-{uuid}-...` | UUID din cod quote |

Spine panel primește `workspaceId`, `quoteId`, `clientAnalysisHash`, `intakeCode`.

---

## 4. Backend — API-uri folosite de integrare

Router: `backend/routers/intake_v6_workspaces.py`

| Method | Endpoint | Rol |
|--------|----------|-----|
| POST | `/workspaces/{id}/create-draft-quote` | Draft intern 0 RON (din Confirm) |
| GET | `/workspaces/{id}/priced-quote-dry-run` | Preview oficial fără scriere DB quote |
| POST | `/workspaces/{id}/priced-quote/write` | Scrie totaluri + line items pe quote existent |
| POST | `/workspaces/{id}/quotes/{quote_id}/snapshot-v2` | Snapshot comercial V2 |
| GET | `/workspaces/{id}/commercial-spine-state` | Stare flux quote-to-order pentru spine |

### Servicii

| Serviciu | Fișier | Responsabilitate |
|----------|--------|------------------|
| Dry-run | `intake_v6_priced_quote_dry_run_service.py` | pricing input → CommercialPriceProposal → total + blockers |
| Write | `intake_v6_priced_quote_write_service.py` | Verifică dry-run hash/total, persistă quote |
| Snapshot V2 | `intake_v6_quote_snapshot_v2_service.py` | Quote trebuie priced înainte de snapshot |
| Pricing input | `intake_v6_pricing_input_service.py` | Adapter registry → preview payload (template_code) |
| Dev-bridge rates | `commercial_rules_volumetric_v2.py` | Rate interim QA (Step 8), nu Pricing Registry producție |

### Fix runtime critic (dry-run crash)

**Problema:** `_classify_modules()` necesită `payload` + `bindings_by_key`; `commercial_price_proposal_service.py` și `estimated_internal_cost_service.py` apelau semnătura veche.

**Fix:** Ambele servicii construiesc `bindings_by_key` din `IntakeV6ModularFormContractService` (același pattern ca ProductDefinition builder).

**Dovadă:** `backend/tests/test_intake_v6_priced_quote_dry_run_runtime.py` + trace quote #6 în worklog.

---

## 5. Frontend — componente integrare

### Client API

`frontend/src/lib/intakeV6/intakeV6Api.ts`:

- `getIntakeV6PricedQuoteDryRun(workspaceId)`
- `writeIntakeV6PricedQuote(workspaceId, body)`
- `createIntakeV6QuoteSnapshotV2(workspaceId, quoteId, body)`
- `getIntakeV6CommercialSpineState(workspaceId)`
- Acțiuni downstream: `completeIntakeV6PricingReview`, `persistIntakeV6OwnerApproval`, `acceptIntakeV6Quote`, `convertIntakeV6QuoteToOrder`

Tipuri: `frontend/src/lib/intakeV6/intakeV6PricedQuoteTypes.ts`

### Commercial spine (UI principal)

`frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx`:

- Hero total + **workflow stepper** (Prețuire → Snapshot → Review → Aprobare → Accept → Comandă)
- **Primary CTA** dinamic (`write` → `pricing` → `approval` → …)
- Dry-run la mount / refresh; write cu `expected_total_gross` + `expected_pricing_hash` (anti-race)
- Blockers traduse via `intakeV6QuoteHandoffReadiness.ts`

### Pagina Oferte

`frontend/src/pages/Quotes.tsx`:

- Afișează spine **deasupra** line items când `showIntakeV6CommercialSpine`
- Ascunde banner global readiness + truth boundary duplicate pentru V6
- Total nepretuit: label amber **„Nepretuit (draft V6)”**, nu zero silențios
- Note JSON brute ascunse; summary uman via `intakeV6QuoteNotes.ts`
- Panouri secundare în `IntakeV6QuoteDetailExtras.tsx` (collapsed)

---

## 6. Flux operator (pas cu pas)

1. **Intake V6** — Straturi → Review → Confirm; confirmare operator + **Creare draft intern**.
2. **Redirect / link** — Oferte; quote `Q-V6-IV6-{workspace}-...`, status `draft`, total 0.
3. **Deschide detail quote** — spine V6 vizibil; mesaj nepretuit clar.
4. **Dry-run automat** — spine încarcă total propus + blockers dacă există.
5. **„Scrie prețul pe ofertă”** (primary CTA) — POST write; quote refresh → total oficial (ex. **2587,94 RON**).
6. **Snapshot V2** — când quote e priced și guards permit.
7. **Review / aprobare / accept / comandă** — același spine, acțiuni secundare collapsed.

---

## 7. Verificare runtime (quote #6)

| Câmp | Valoare |
|------|---------|
| Workspace DB id | `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3` |
| Workspace code | `IV6-BB8EE3F8` |
| Quote id | `6` |
| Quote code | `Q-V6-IV6-BB8EE3F8-1782910533` |

**Trace reușit (post-fix):**

1. Dry-run: `V6_PRICED_DRY_RUN_READY`, total gross > 0  
2. Write: quote actualizat cu total oficial  
3. UI Oferte: afișează total priced, nu 0 RON placeholder  

*(Valoarea exactă depinde de payload workspace + dev-bridge rates la momentul trace-ului; exemplu documentat: **2587,94 RON**.)*

---

## 8. Fișiere modificate (integrare)

### Backend

| Fișier | Schimbare |
|--------|-----------|
| `routers/intake_v6_workspaces.py` | Routes dry-run, write, snapshot-v2 |
| `services/intake_v6_priced_quote_dry_run_service.py` | Dry-run pipeline |
| `services/intake_v6_priced_quote_write_service.py` | Write guards + persist |
| `services/intake_v6_quote_snapshot_v2_service.py` | Snapshot V2 |
| `services/commercial_price_proposal_service.py` | Fix `_classify_modules` call |
| `services/estimated_internal_cost_service.py` | Fix `_classify_modules` call |
| `data/commercial_rules_volumetric_v2.py` | Dev-bridge prices (interim) |
| `schemas/intake_v6.py` | Request/response types |
| `services/intake_v6_product_pricing_adapter_registry.py` | Spike: routing pricing input by template |

### Frontend

| Fișier | Schimbare |
|--------|-----------|
| `lib/intakeV6/intakeV6Api.ts` | Client priced-quote + spine APIs |
| `lib/intakeV6/intakeV6PricedQuoteTypes.ts` | TS types |
| `lib/intakeV6/intakeV6QuoteDisplay.ts` | Detect V6 / unpriced |
| `lib/intakeV6/intakeV6QuoteHandoffReadiness.ts` | Blocker labels RO |
| `lib/intakeV6/intakeV6QuoteNotes.ts` | Human summary din notes JSON |
| `components/.../IntakeV6QuoteCommercialSpinePanel.tsx` | Spine UI + workflow |
| `components/.../IntakeV6QuoteDetailExtras.tsx` | Extras collapsed |
| `pages/Quotes.tsx` | Wiring spine + layout V6 |

### Teste

| Fișier | Acoperire |
|--------|-----------|
| `backend/tests/test_intake_v6_priced_quote_dry_run.py` | Dry-run logic (mocked CPP) |
| `backend/tests/test_intake_v6_priced_quote_write.py` | Write guards |
| `backend/tests/test_intake_v6_priced_quote_dry_run_runtime.py` | Runtime classifier path |
| `frontend/.../IntakeV6QuoteCommercialSpinePanel.test.tsx` | Spine UI |
| `frontend/src/lib/intakeV6/intakeV6QuoteDisplay.test.ts` | V6 / unpriced detect |
| `frontend/src/pages/Quotes.commercialActions.test.tsx` | Quotes + spine placement |

---

## 9. Comenzi validare

### Frontend (targeted)

```powershell
cd frontend
npm test -- --run IntakeV6QuoteCommercialSpinePanel.test.tsx
npm test -- --run intakeV6QuoteDisplay.test.ts
npm test -- --run Quotes.commercialActions.test.tsx
npm test -- --run IntakeV6ConfirmStep.test.tsx
```

### Backend (targeted)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_priced_quote_dry_run.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_priced_quote_write.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_priced_quote_dry_run_runtime.py -q
```

### Smoke manual

1. Stack: backend `:8000`, frontend `:3000`, `VITE_ENABLE_DEV_AUTH=true`
2. Intake V6 workspace ready → Confirm → Creare draft
3. `/quotes` → deschide quote V6 draft
4. Spine: dry-run → write → verifică total > 0

---

## 10. Boundary — ce NU s-a schimbat

- **CostEngine** — nu e apelat din Intake CRUD
- **Pricing Registry producție (Step 7I)** — încă folosim dev-bridge volumetric
- **Preview Intake** (calcul live, material breakdown) — rămâne non-oficial
- **Schema DB** — fără migrări noi pentru acest slice
- **QuoteWizard V2 / WorkIntake V2** — path separat, neatinse
- **Creare quote nou din Quotes** — flux V6 pornește din Intake Confirm, nu din Quotes list

---

## 11. Limitări cunoscute

| Limită | Impact | Următor pas |
|--------|--------|-------------|
| Dev-bridge `commercial_rules_volumetric_v2.py` | Rate interim, nu owner-approved registry | Step 7I Pricing Registry |
| Dry-run poate fi blocked de owner decisions | Write indisponibil până la reguli complete | Matrice decizii comerciale V6 |
| `Quotes.tsx` are ramuri V6-specifice | Datorie la al 2-lea template | Modularizare Phase B–D |
| PR GitHub | Necesită `gh auth login` | Deschidere manuală compare URL |

---

## 12. Diagramă adevăr comercial

```
┌─────────────────────────────────────────────────────────────┐
│ Intake payload_json + pricing input preview                 │
│   PREVIEW / PRODUCT TRUTH — nu total oficial ofertă          │
└───────────────────────────┬─────────────────────────────────┘
                            │ priced-quote-dry-run (server)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Dry-run totals + pricing_hash                                │
│   PROPUNERE OFICIALĂ — încă nescrie în DB                   │
└───────────────────────────┬─────────────────────────────────┘
                            │ priced-quote/write
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ quotes.grand_total, line items                               │
│   PREȚ OFICIAL PERSISTAT                                     │
└───────────────────────────┬─────────────────────────────────┘
                            │ snapshot-v2
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Quote Snapshot V2                                            │
│   ADEVĂR COMERCIAL ÎNGHEȚAT (handoff comandă)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 13. Concluzie

**Problema de conectare** nu era că Intake V6 „nu calcula” — calcula preview. Problema era **lipsea punții operator din Oferte către API-urile backend de prețuire oficială**, plus un **crash runtime** la dry-run.

Integrarea rezolvă:

1. UI clar pentru draft nepretuit (nu zero misleading)  
2. Spine comercial cu dry-run → write → snapshot  
3. Fix classifier pentru dry-run real  
4. Teste targeted frontend + backend  

Pentru modularizarea pe mai multe produse, vezi [INTAKE_V6_MODULARIZATION_AUDIT.md](../architecture/INTAKE_V6_MODULARIZATION_AUDIT.md).
