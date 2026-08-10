# SETTINGS_DEFECTS — root-cause groups

Avoid one-ticket-per-field. Groups below.

---

## DEF-01 — Live VAT reapplied to frozen commercial review/offer

| Key | Value |
|-----|-------|
| **ROOT_CAUSE** | Authoritative offer + pricing-review paths call `get_default_vat_pct(db)` when deriving totals from frozen CPP, so CURRENT DEFAULT VAT overlays frozen commercial net at read time. |
| **AFFECTED_FIELDS** | Settings `default_vat_pct`; review/offer `vat_percent` / `vat_amount` / gross |
| **AFFECTED_CONSUMERS** | `intake_v6_snapshot_authoritative_pricing_review_service`, `intake_v6_snapshot_authoritative_offer_service` (`commercial_totals_from_frozen_cpp`) |
| **BUSINESS_RISK** | Changing Settings VAT after freeze can change **displayed** VAT/gross on review/offer without mutating quote row — operator may treat display as frozen fiscal truth. |
| **UI_HONESTY_RISK** | Settings copy claims historical documents do not update; document path is snapshot-based, but review/offer re-reads live VAT — partial truth / misleading. |
| **SEVERITY** | **P0** |
| **RECOMMENDED_BOUNDARY** | Bounded VAT/snapshot integrity closure: freeze VAT with commercial snapshot **or** label review VAT as live policy overlay; align UI copy. |
| **NOT** | Historical mutation of persisted `quote.vat` (not proven) |

---

## DEF-02 — FX fail-open vs fail-closed + bootstrap write-on-read

| Key | Value |
|-----|-------|
| **ROOT_CAUSE** | Same Settings FX field consumed with incompatible discipline: `get_eur_to_ron_rate` / `get_settings` defaults to 5.0 and may persist default on NULL; Logo/CPP canonical path fails closed. |
| **AFFECTED_FIELDS** | `eur_to_ron_rate` |
| **AFFECTED_CONSUMERS** | dry-run, order convert / profitability stamp (uses helper), Logo/CPP (fail-closed), Settings UI |
| **BUSINESS_RISK** | Silent diagnostic FX (5.0) can enter paths that do not fail closed; profitability stamp freezes whatever helper returns. |
| **UI_HONESTY_RISK** | Settings presents a single “official” rate; consumers disagree on missing-rate behavior. |
| **SEVERITY** | **P0** |
| **RECOMMENDED_BOUNDARY** | Bounded FX/commercial-authority closure: one missing-rate policy; no silent persist-on-read; stamp provenance everywhere. |

Related (consumer, not Settings writer): manual RON adjustment does not use Settings FX (see Intake V6 price-input audit) — keep as linked risk, not separate Settings field ticket.

---

## DEF-03 — Societate mixed authority (live money + static legal identity)

| Key | Value |
|-----|-------|
| **ROOT_CAUSE** | One tab mixes LIVE VAT/FX with STATIC mock company/bank/contact; banner covers static profile but page still reads as “Setări societate” official card. |
| **AFFECTED_FIELDS** | name, CUI, regCom, address, bank, IBAN, vatPayer, contact… |
| **AFFECTED_CONSUMERS** | Operator perception; **no** proven backend legal SoT from these fields |
| **BUSINESS_RISK** | Medium — wrong identity if used as legal reference; money fields themselves persist correctly. |
| **UI_HONESTY_RISK** | **High** — static presented as company data next to live fiscal controls; `vatPayer` mock ≠ Settings VAT %. |
| **SEVERITY** | **P1** |
| **RECOMMENDED_BOUNDARY** | Settings authority closure: backend company profile SoT **or** demote identity to clearly non-official sandbox chrome; keep VAT/FX as separate live cluster. |

---

## DEF-04 — Cost Intern live edit vs Modules LEGACY / non-money authority

| Key | Value |
|-----|-------|
| **ROOT_CAUSE** | Settings exposes live CostEngine config while Modules marks CostEngine LEGACY / not commercial money authority; conceptual labor overlap with RoleSkillActuals confuses operators. |
| **AFFECTED_FIELDS** | Cost Intern config + base-config metrics |
| **AFFECTED_CONSUMERS** | Internal cost aggregates / overhead; **not** CPP client price; **not** RoleSkill actuals |
| **BUSINESS_RISK** | Low for client price if boundaries hold; medium if operator treats Cost Intern as offer rates. |
| **UI_HONESTY_RISK** | Medium — badges help (INTERNAL ONLY); Modules INACTIV vs live edit still conflicting story. |
| **SEVERITY** | **P2** |
| **RECOMMENDED_BOUNDARY** | Clarify registration: keep separate from RoleSkill; either retire write UI or register honest INTERNAL system — **not** DUPLICATE_AUTHORITY with RoleSkill. |

**Cost Intern vs RoleSkillLaborCostPolicy:** proven **LEGITIMATELY_SEPARATE_DOMAINS** (different stores/consumers; no shared write/read truth).

---

## DEF-05 — Active commercial settings under-registered in Modules

| Key | Value |
|-----|-------|
| **ROOT_CAUSE** | `company_commercial_settings` (esp. FX) and recurring-payment overhead inputs are runtime authorities without first-class PRESENT system registration comparable to their money/ops impact. VAT has SETTINGS_OWNERSHIP row; FX/recurring/integrations do not as PRESENT systems. |
| **AFFECTED_FIELDS** | FX, recurring overhead flags, SmartBill capability |
| **AFFECTED_CONSUMERS** | Governance operators reading Modules/Ownership |
| **BUSINESS_RISK** | Medium governance blind spot |
| **UI_HONESTY_RISK** | Medium |
| **SEVERITY** | **P2** |
| **RECOMMENDED_BOUNDARY** | Register only **genuine** active authorities (company commercial, SmartBill when enabled) — not every static cluster. |

**UNREGISTERED_ACTIVE_SYSTEMS (strict):**  
1. `company_commercial_settings` FX (+ VAT already ownership-rowed but not PRESENT spine system) as active money authority  
2. Recurring-payments→overhead pipeline as active Cost Intern input authority  

SmartBill: wired capability, **disabled** on demo — gap = registration/visibility; do not over-claim UNREGISTERED for disabled external I/O.

---

## Ranking for next build

1. DEF-01 (VAT review/offer live overlay)  
2. DEF-02 (FX fail-open discipline)  
3. DEF-03 (Societate mixed honesty)  
4. DEF-04 / DEF-05 (Cost Intern / Modules registration)
