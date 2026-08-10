# WORKOS_SETTINGS_AUTHORITY_AND_PERSISTENCE_AUDIT_V1_REPORT

**Status:** COMPLETE (audit-only)  
**HEAD:** `bd7c61fd`  
**Date:** 2026-08-10  
**PRODUCT_CODE_CHANGES:** 0  
**DB_SCHEMA_CHANGES:** 0  
**PRICING_CHANGES:** 0  
**PRODUCT_TRUTH_MUTATIONS:** 0  
**OWNER_DB_MUTATIONS:** 0  
**DEMO_DB_ONLY:** YES  
**PUSH:** NO  

---

## Verdict (plain answers)

```
SETTINGS_PAGE_OVERALL_STATUS = PARTIAL
SETTINGS_HAS_SINGLE_AUTHORITY_MODEL = NO

MONEY_AFFECTING_SETTINGS_WITH_PROVEN_AUTHORITY =
  - company_commercial_settings.default_vat_pct (GET/PUT proven; demo round-trip PASS)
  - company_commercial_settings.eur_to_ron_rate (GET/PUT proven; demo round-trip PASS)
  - recurring_payments → cost-engine overhead inputs (API live; empty on demo)
  - cost_engine config / base-config (API live; INTERNAL / LEGACY vs CPP money authority)

MONEY_AFFECTING_SETTINGS_WITH_AUTHORITY_GAP =
  - default_vat_pct consumers disagree on freeze: document uses quote snapshot; authoritative offer/pricing-review re-applies LIVE Settings VAT to frozen CPP (DEF-01)
  - eur_to_ron_rate consumers disagree on missing-rate: get_eur_to_ron_rate fail-open/default 5.0 (+ possible persist-on-read) vs Logo/CPP fail-closed (DEF-02)
  - manualAdjustmentRon (Intake) is money-affecting but is NOT a Settings FX consumer (linked gap)

STATIC_DATA_PRESENTED_AS_OFFICIAL =
  - Societate identity/bank/contact from mockData.companySettings (SignTech…), with yellow static banner (partial honesty)
  - company.vatPayer mock boolean shown beside live TVA % (unrelated authorities)

PERSISTENCE_FAILURES =
  - none proven for VAT/FX save path on demo DB (round-trip PASS)
  - company identity/bank/contact: NOT_PERSISTED by design (static)

AUTHORITY_CONFLICTS =
  - DEF-01 live VAT on frozen commercial review/offer vs snapshot document VAT
  - DEF-02 FX fail-open helper vs fail-closed Logo/CPP
  - DEF-03 mixed Societate live+static
  - DEF-04 Cost Intern live UI vs Modules CostEngine LEGACY / non-money authority
  - Cost Intern vs RoleSkillLaborCostPolicy: NOT duplicate authority (separate domains)

UNREGISTERED_ACTIVE_SYSTEMS =
  - company_commercial_settings as active money authority (VAT ownership row exists; no PRESENT spine system for company commercial/FX)
  - recurring_payments→overhead as active Cost Intern input authority
  - SmartBill: wired, disabled on demo — do not over-claim as active external authority

FIRST ROOT CAUSE TO REPAIR =
  Live Settings VAT re-applied to frozen CPP totals on authoritative offer/pricing-review (DEF-01), while Settings UI copy implies historical commercial VAT does not move.

NEXT_RECOMMENDED_BUILD =
  WORKOS_VAT_SNAPSHOT_BOUNDARY_INTEGRITY_V1

NEXT_TASK =
  NOT_AUTHORIZED
```

`SETTINGS_PAGE_OVERALL_STATUS = PARTIAL` justification: VAT/FX and Cost Intern/SmartBill reads are live and partially honest; identity/bank remain static; money consumers have freeze/fail-closed conflicts — not fully LIVE, not MOSTLY_STATIC, not wholly MISLEADING.

---

## Scope executed (U1–U7)

| Unit | Deliverable |
|------|-------------|
| U1 | Evidence root, demo DB confirmation, screenshots ×4, probe script |
| U2 | `SETTINGS_FIELD_LEDGER.md` |
| U3 | `SETTINGS_AUTHORITY_MAP.md`, `SETTINGS_PERSISTENCE_MATRIX.md`, `SETTINGS_CONSUMER_GRAPH.md` |
| U4 | `SETTINGS_RUNTIME_EVIDENCE.md` + `probes/probe_results.json` |
| U5 | VAT five-surface + FX provenance in consumer graph / this report |
| U6 | `SETTINGS_DEFECTS.md`, `SETTINGS_NOT_EXERCISED.md` |
| U7 | This report + worklog |

---

## VAT surfaces (summary)

| Surface | Behavior |
|---------|----------|
| CURRENT DEFAULT VAT | Live Settings DB |
| QUOTE PERSISTED VAT | Stamped at generation on quote/pricing |
| QUOTE REVIEW/DISPLAY VAT | **Live Settings VAT × frozen CPP** — first broken boundary |
| ORDER SNAPSHOT | Commercial freeze + separate `profitability_fx_v1` for FX |
| DOCUMENT VAT | Quote snapshot / `quote.vat` — not live Settings GET |

No claim of historical **row mutation** for VAT without evidence.

---

## FX provenance (summary)

See `SETTINGS_CONSUMER_GRAPH.md` §B for SOURCE / READ_TIME / FREEZE_TIME / SNAPSHOT_LOCATION / FALLBACK / FAIL_CLOSED per consumer (Settings, convert, profitability_fx_v1, Logo/CPP, manual RON).

---

## Cost Intern vs RoleSkill

Proven separate domains: different tables, different consumers, no shared write/read truth, no operational conflict proven. Conceptual labor-cost overlap only → **not** DUPLICATE_AUTHORITY.

---

## Why next build is VAT boundary (not pre-forced)

Owner forbade pre-deciding `NEXT_RECOMMENDED_BUILD`. Ranking from this audit: DEF-01 is the sharpest money-affecting integrity + UI honesty break tied to a Settings control the page itself documents incorrectly for review/offer. DEF-02 FX remains P0 and may follow immediately after VAT boundary closure (or combine only if Owner expands GO). Broader `WORKOS_SETTINGS_AUTHORITY_CLOSURE_V1` remains valid for DEF-03/05 but is not the single first root cause.

---

## Artifact index

```
docs/qa/workos-settings-authority-and-persistence-audit-v1/
  SETTINGS_FIELD_LEDGER.md
  SETTINGS_AUTHORITY_MAP.md
  SETTINGS_PERSISTENCE_MATRIX.md
  SETTINGS_CONSUMER_GRAPH.md
  SETTINGS_DEFECTS.md
  SETTINGS_RUNTIME_EVIDENCE.md
  SETTINGS_NOT_EXERCISED.md
  WORKOS_SETTINGS_AUTHORITY_AND_PERSISTENCE_AUDIT_V1_REPORT.md
  probes/run_settings_authority_probes_v1.py
  probes/probe_results.json
  screenshots/01-societate.png
  screenshots/02-plati-repetitive.png
  screenshots/03-cost-intern.png
  screenshots/04-integrari.png
```

Worklog: `docs/worklog/realignment/2026-08-10_workos_settings_authority_and_persistence_audit_v1.md`
