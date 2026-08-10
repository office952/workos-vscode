# SETTINGS_AUTHORITY_MAP

**GO:** WORKOS_SETTINGS_AUTHORITY_AND_PERSISTENCE_AUDIT_V1  
**Question:** Who owns truth for each Settings cluster?

---

## 1. Company commercial (VAT / FX)

| Aspect | Proven |
|--------|--------|
| Canonical store | `company_commercial_settings` (`backend/models/company_commercial_settings.py`) |
| Service | `CompanyCommercialSettingsService` |
| API | `GET/PUT /api/v1/company-commercial-settings` |
| UI writer | Settings Societate panels only (VAT + FX) |
| Modules / Governance | VAT listed in `SETTINGS_OWNERSHIP_ROWS` as CODE_ENFORCED; **no** first-class PRESENT spine system id for company commercial settings / FX |
| Defaults | `DEFAULT_VAT_PCT=21.0`, `DEFAULT_EUR_TO_RON_RATE=5.0` |

**Authority verdict:** LIVE backend singleton row — **proven money authority**.  
**Governance gap:** active runtime authority without a Modules PRESENT system card for FX/company commercial as a whole (VAT ownership row exists; FX/recurring/integrations do not as PRESENT systems).

---

## 2. Company identity / bank / contact

| Aspect | Proven |
|--------|--------|
| Source | `frontend/src/lib/mockData.ts` → `companySettings` |
| Backend SoT | **NONE** for these fields |
| UI honesty | Yellow banner: static local profile |

**Authority verdict:** STATIC_FE display.  
**Defect class:** mixed authority on one tab (live VAT/FX + static identity) — **not** total page failure.

---

## 3. Recurring payments

| Aspect | Proven |
|--------|--------|
| Store | entity CRUD `/api/v1/entities/recurring-payments` |
| Consumer | CostEngine base-config monthly overhead aggregation |
| FX | Explicit UI: other currencies **without** EUR/RON conversion via Settings FX |

**Authority verdict:** LIVE for overhead inputs. Not commercial client-price authority.

---

## 4. Cost Intern vs RoleSkillLaborCostPolicy

| Dimension | Cost Intern (Settings) | RoleSkillLaborCostPolicy |
|-----------|------------------------|--------------------------|
| Store | `cost_engine` config / base-config | `role_skill_labor_cost_policies` |
| Writer UI | `/settings` Cost Intern | Actual-cost / policy APIs (not this page) |
| Consumer | CostEngine LEGACY internal aggregates | Profitability **actual** labor lines |
| Feeds CPP client price? | **NO** (UI + Modules: LEGACY / not money authority) | **NO** (actuals, not offer price) |
| Same write/read truth? | **NO** | **NO** |
| Operational conflict proven? | **NO** — conceptual overlap (labor €/h) only | |

**Classification:** `LEGITIMATELY_SEPARATE_DOMAINS` — **not** `DUPLICATE_AUTHORITY`.

Modules truth: CostEngine card `cost_engine_legacy` status **INACTIV** / not money authority, while Settings still exposes live edit — **honesty / registration tension**, not duplicate labor truth.

---

## 5. Integrations (SmartBill)

| Aspect | Proven |
|--------|--------|
| Config source label | `app_settings` |
| API | `/api/v1/integrations/providers/smartbill/*` |
| Secrets | Backend-protected; FE write-only token field |
| Runtime (demo) | `enabled=false`, not configured |

**Authority verdict:** LIVE config authority when enabled; disabled on demo.  
**UNREGISTERED_SYSTEM?** Only if treated as active runtime authority — capability exists and is wired; currently disabled → mark as **ACTIVE_CAPABILITY_PRESENT / disabled**, register gap if Modules has no integration system (do not invent UNREGISTERED for every helper field).

---

## 6. Dead admin settings API

`frontend/src/api/settings.ts` is unused by Settings.tsx. Not an authority for this page.

---

## Single authority model?

**SETTINGS_HAS_SINGLE_AUTHORITY_MODEL = NO**

Page aggregates: company commercial DB + static mock identity + recurring entities + CostEngine config + SmartBill app_settings — without one ownership model.
