# APP-AUTH-06F — Sandu competence and mapping reconciliation plan v1

**Task:** `APP-AUTH-06F` — `SANDU_COMPETENCE_AND_MAPPING_RECONCILIATION_PLAN_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `c8f723a`  
**Verdict:** `APP_AUTH_06F_SANDU_RECONCILIATION_PLAN_READY_FOR_OWNER_REVIEW`  
**Next:** `APP-AUTH-06G-SANDU-EVIDENCE-COLLECTION`

**Scope:** Plan and evidence preparation only. No code, DB, Sandu, competence, mapping, authorization, eligibility, parity enforcement, or migration changes.

**Upstream:** APP-AUTH-06C @ `6f19de1` · OWNER-DECISION-05 @ `c8f723a`

**Evidence:** `docs/qa/product-system-active-path-isolation-v1/app_auth_06f/` (17 JSON artifacts)

---

## Executive summary

Exact **7/7** operations reconciled with proven registry aliases. Competence requirements **7/7 CONFIRMED_RUNTIME** from seed. Sandu registry snapshot shows **SK_PRINT_OPERATOR** only while legacy JSON retains production skills. **Zero** operations automatically confirmed. **Zero** operation-specific production completion history. **5/7** controlled-resource paths show **AUTHORIZATION_MISSING** in registry.

Recommended next gate: **APP-AUTH-06G** (supervisor/practical evidence collection) before **OWNER-DECISION-06**.

---

## Seven operations (exact)

| # | Review code | Registry op | Pilot | Mapping |
|---|-------------|-------------|-------|---------|
| 1 | volumetric_letter_assembly | assembly | YES | YES |
| 2 | vinyl_cutting | colantare | YES | YES |
| 3 | led_assembly | montaj_led | YES | YES |
| 4 | led_wiring | montaj_led | YES | YES |
| 5 | installation_prep | field_installation | YES | YES |
| 6 | packaging | packaging | NO | YES |
| 7 | quality_control | quality_control | NO | YES |

---

## Sandu registry snapshot (read-only)

- **Registry competences:** `SK_PRINT_OPERATOR` (no level/evidence metadata)
- **Legacy JSON skills:** locksmith, assembly, vinyl, electrician, field installer
- **Registry resources:** `MCH-EPSON-60800` only
- **Legacy machines:** weld + assembly workstations
- **Explicit mappings:** 7 conflict mappings + welding (8th, out of gate)

---

## Evidence gaps (critical)

1. No supervisor/practical confirmation for any operation
2. No training records
3. No operation-coded completion history (execution_reality refs are fixture/T05B)
4. Registry resource authorizations missing for assembly/vinyl/LED/QC paths
5. Per-operation competence level undecided

---

## Owner package (all 7)

**proposed_owner_choice:** `MORE_EVIDENCE_REQUIRED` for every operation — **NOT confirmed**.

Grouped owner questions: GQ-01..GQ-06 in `owner_questions.json`.

---

## Risks

Highest: false competence promotion, unsafe machine access, mapping-as-hidden-authorization, premature DB correction. Mitigated by OD-05 policy + this plan boundaries.

---

## Delivery footer

| Field | Value |
|-------|-------|
| Operations identified | 7/7 |
| Owner decisions prepared | 7/7 |
| Operations auto-confirmed | 0 |
| Authorizations missing | 5 |
| Authorizations not required | 1 |
| Runtime history ops proven | 0 |
| DB writes | 0 |
| Next | APP-AUTH-06G-SANDU-EVIDENCE-COLLECTION |
| Verdict | APP_AUTH_06F_SANDU_RECONCILIATION_PLAN_READY_FOR_OWNER_REVIEW |
