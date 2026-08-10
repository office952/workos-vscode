# SETTINGS_FIELD_LEDGER — WORKOS_SETTINGS_AUTHORITY_AND_PERSISTENCE_AUDIT_V1

**Route:** `/settings` · **Source UI:** `frontend/src/pages/Settings.tsx`  
**HEAD:** `bd7c61fd` · **Evidence date:** 2026-08-10  
**Screenshots:** `screenshots/01-societate.png` … `04-integrari.png`

Classification legend: `LIVE_BACKEND` | `STATIC_FE` | `COMPUTED_BACKEND` | `DEAD_UNUSED` | `WRITE_ONLY_SECRET`

---

## Tab: Societate

| Field ID | UI label | Editable | Authority class | Persist target | Save action | Notes |
|----------|----------|----------|-----------------|----------------|-------------|-------|
| `default_vat_pct` | TVA implicit pentru oferte (%) | YES | LIVE_BACKEND | `company_commercial_settings.default_vat_pct` via `PUT /api/v1/company-commercial-settings` | Salvează TVA | Money-affecting |
| `eur_to_ron_rate` | Curs EUR/RON (RON pentru 1 EUR) | YES | LIVE_BACKEND | `company_commercial_settings.eur_to_ron_rate` | Salvează curs | Money-affecting; manual |
| `company.name` | Denumire | NO (display) | STATIC_FE | none — `mockData.companySettings` | none | Banner admits static |
| `company.cui` | CUI | NO | STATIC_FE | none | none | |
| `company.regCom` | Reg. Comerțului | NO | STATIC_FE | none | none | |
| `company.address` | Adresă | NO | STATIC_FE | none | none | |
| `company.city` | Oraș | NO | STATIC_FE | none | none | |
| `company.postalCode` | Cod Poștal | NO | STATIC_FE | none | none | |
| `company.vatPayer` | Plătitor TVA | NO | STATIC_FE | none | none | **Not** linked to `default_vat_pct` |
| `company.adminContact` | Administrator | NO | STATIC_FE | none | none | |
| `company.phone` | Telefon | NO | STATIC_FE | none | none | |
| `company.email` | Email | NO | STATIC_FE | none | none | |
| `company.website` | Website | NO | STATIC_FE | none | none | |
| `company.bankName` | Bancă | NO | STATIC_FE | none | none | |
| `company.iban` | IBAN | NO | STATIC_FE | none | none | |

Banner (honesty partial): *„Tabul Societate afișează profil local static…”* — covers identity/bank/contact; does **not** apply to VAT/FX panels above it.

---

## Tab: Plăți Repetitive

| Field ID | UI label | Editable | Authority class | Persist target | Save action |
|----------|----------|----------|-----------------|----------------|-------------|
| list KPIs | Total lunar / active / overhead counts | NO | COMPUTED_BACKEND | derived from entity list | Reîncarcă |
| `recurring_payment.*` | Adaugă/editează plată (name, category, amount, currency, frequency, include_in_overhead, include_in_equipment, status, …) | YES | LIVE_BACKEND | `/api/v1/entities/recurring-payments` CRUD | Creează / Salvează |
| other-currency KPI | Alte valute (lunar) | NO | COMPUTED_BACKEND | display only; **no FX conversion** | — |

Demo probe: `items_count=0` on demo DB.

---

## Tab: Cost Intern

| Field ID | UI label | Editable | Authority class | Persist target | Notes |
|----------|----------|----------|-----------------|----------------|-------|
| honesty strip | INTERNAL ONLY / NOT CLIENT PRICE / FROZEN / NEEDS OWNER GO | NO | UI chrome | — | Declares non-client-price |
| `baseConfig.currency` | Monedă | NO | COMPUTED_BACKEND | `GET …/cost-engine/base-config` | |
| `baseConfig.total_productive_hours_month` | Ore productive / lună | NO | COMPUTED_BACKEND | same | |
| `baseConfig.average_labour_hour_cost` | Cost mediu manoperă / h | NO | COMPUTED_BACKEND | same | Internal avg — ≠ RoleSkill policy |
| `baseConfig.overhead_hour_cost` | Overhead / h | NO | COMPUTED_BACKEND | same | |
| `baseConfig.monthly_overhead_cost` | Overhead lunar | NO | COMPUTED_BACKEND | same | Feeds from recurring payments incl. overhead |
| `config.moneda_implicita` | Monedă implicită | YES | LIVE_BACKEND | `PUT …/cost-engine/config` | |
| `config.ore_productive_luna_firma` | Ore productive/lună (firmă) | YES | LIVE_BACKEND | same | null → employee sum |
| `config.overhead_profile_name` | Profil overhead | YES | LIVE_BACKEND | same | |
| `config.metoda_overhead` | Metodă overhead | YES | LIVE_BACKEND | same | |
| `config.cost_ora_manopera_default` | Cost oră manoperă default | YES | LIVE_BACKEND | same | INTERNAL ONLY fallback |
| `config.allow_manual_override` | Override manual permis | YES | LIVE_BACKEND | same | |

---

## Tab: Integrări (SmartBill only)

| Field ID | UI label | Editable | Authority class | Persist target | Notes |
|----------|----------|----------|-----------------|----------------|-------|
| health cards | Stare Integrări | NO | LIVE_BACKEND read | `GET …/providers/smartbill/health` | READ only in this audit |
| `enabled` | ENABLED | YES | LIVE_BACKEND | `PUT …/providers/smartbill/config` | Not write-probed (side-effect risk) |
| `base_url` | BASE URL | YES | LIVE_BACKEND | same | |
| `username` | USERNAME | YES | LIVE_BACKEND | same | |
| `token` | TOKEN (WRITE-ONLY) | YES | WRITE_ONLY_SECRET | same | Never retained in FE after save; **no token snapshot in evidence** |
| `lookup_path` | LOOKUP PATH | YES | LIVE_BACKEND | same | |
| `timeout_seconds` | TIMEOUT SECONDS | YES | LIVE_BACKEND | same | |
| Test connection | Test connection (local) | action | LIVE_BACKEND | POST test | **NOT_EXERCISED** (external risk) |
| Clear token | Clear token | action | LIVE_BACKEND | POST clear | **NOT_EXERCISED** |

Runtime read (demo): `enabled=false`, credentials absent; source `app_settings`.

---

## Dead / unused relative to `/settings`

| Artifact | Class | Evidence |
|----------|-------|----------|
| `frontend/src/api/settings.ts` (`settingsApi`) | DEAD_UNUSED on this page | Settings.tsx does not import it; probe `GET /api/v1/settings` → 404 on this stack |
| Mock `recurringPayments` in `mockData.ts` | DEAD_UNUSED for tab | Tab uses live API |

---

## Money-affecting fields (page scope)

1. `default_vat_pct`  
2. `eur_to_ron_rate`  
3. Recurring payment amounts flagged `include_in_overhead` (internal cost path)  
4. Cost Intern editable rates/overhead params (internal; Modules marks CostEngine LEGACY vs CPP money authority)
