# OWNER-DECISION-05 — Parity signal authority and Sandu reconciliation

**Task:** `OWNER-DECISION-05` — `PARITY_SIGNAL_AUTHORITY_AND_SANDU_RECONCILIATION_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `6f19de1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `OWNER_AUTHORITY_DECISIONS_CONFIRMED_READY_FOR_SANDU_PLAN`  
**Next:** `APP-AUTH-06F-SANDU-COMPETENCE-AND-MAPPING-RECONCILIATION-PLAN`

**Scope:** Owner decision gate only. No code, DB, Sandu, competence, authorization, mapping, eligibility, parity enforcement, persistence, third consumer, or migration changes.

**Upstream:** APP-AUTH-06C @ `6f19de1` (accepted)

**Evidence:** `docs/qa/product-system-active-path-isolation-v1/owner_decision_05/`

---

## Executive summary

Owner confirmed **14 of 15** policy decisions (S1–S6, S8–S15). **S7** operation-level classifications are **reviewed 7/7** but **deferred** to human review in APP-AUTH-06F — no operation marked `CONFIRMED_COMPETENT` without explicit input.

**Canonical policy direction:**

- Registry = competence authority (S1:A)
- Legacy = transitional evidence only (S2:A)
- Mapping = routing preference, not competence (S3:B; C for audited exceptions)
- Authorization mandatory for controlled resources (S4:A)
- Eligibility = observe-only now; future fail-closed + exceptions (S5:D → A+C)
- Sandu behavior unchanged until review (S6:A)
- Parity stays observe-only, two consumers (S10:A)

---

## Owner response package

| ID | Choice | Confirmed | Summary |
|----|--------|-----------|---------|
| S1 | A | YES | Registry is canonical competence authority |
| S2 | A | YES | Legacy skills are transitional evidence |
| S3 | B (+C for exceptions) | YES | Mapping is routing preference, not competence |
| S4 | A | YES | Authorization mandatory for controlled resources |
| S5 | D (future A+C) | YES | Observe-only now; future fail-closed + audited exceptions |
| S6 | A | YES | Sandu behavior unchanged until human review |
| S7 | REVIEWED_DEFERRED | PARTIAL | 7/7 inspected; per-operation decisions → APP-AUTH-06F |
| S8 | CONFIRM | YES | Competence levels required on confirmed competences |
| S9 | CONFIRM | YES | Temporary exception contract confirmed; not implemented |
| S10 | A | YES | Parity observe-only, two consumers |
| S11 | A | YES | Separate correction plan after review; no immediate DB |
| S12 | CONFIRM | YES | Target eligibility policy confirmed |
| S13 | A | YES | Observe-only transition until exit criteria |
| S14 | CONFIRM | YES | Broader employee audit required separately |
| S15 | A | YES | Next = APP-AUTH-06F reconciliation plan |

**Amendments:** S1:A does not authorize cleanup; S6:A forbids auto promote/remove/disable; S7 entries are inspection-only; no migration/enforcement/third consumer.

---

## Sandu operation matrix (S7)

All seven operations: `MORE_EVIDENCE_REQUIRED` / `PENDING_HUMAN_REVIEW` / `DEFERRED_TO_APP_AUTH_06F`.

| Operation | Registry op | Pilot proven | Owner decision |
|-----------|-------------|--------------|----------------|
| volumetric_letter_assembly | assembly | YES | DEFERRED |
| vinyl_cutting | colantare | YES | DEFERRED |
| led_assembly | montaj_led | YES | DEFERRED |
| led_wiring | montaj_led | YES | DEFERRED |
| installation_prep | field_installation | YES | DEFERRED |
| packaging | packaging | NO | DEFERRED |
| quality_control | quality_control | NO | DEFERRED |

`welding` documented separately (eighth APP-AUTH-02 override). `print` / `print_roll` aligned — not in conflict matrix.

Detail: `sandu_operation_decision_matrix.json`

---

## Target policy (S12)

```text
Competenta structurata
+ autorizare unde este necesara
+ mapping ca preferinta/routing
+ exceptie temporara explicita
= eligibilitate canonica viitoare
```

Legacy skills: `evidence transitional` · `not silent authority`

---

## Implementation boundary

Even after OWNER-DECISION-05, **not authorized:**

- DB/registry updates · legacy deletion · mapping changes · eligibility changes · mobile/assignment changes · parity enforcement

**Next task is plan only:** APP-AUTH-06F.

---

## Delivery footer

| Field | Value |
|-------|-------|
| Task | OWNER-DECISION-05 |
| Starting HEAD | `6f19de1` |
| Decisions total | 15 |
| Decisions confirmed | 14 |
| Decisions deferred | 1 (S7 per-operation) |
| Competence authority | Registry canonical (S1:A) |
| Legacy skills | Transitional evidence (S2:A) |
| Mapping policy | Routing preference (S3:B) |
| Authorization policy | Mandatory controlled resources (S4:A) |
| Eligibility policy | Observe-only now; future A+C (S5:D) |
| Sandu operations reviewed | 7/7 |
| Sandu behavior changed | NO |
| Competence levels | CONFIRMED_CONTRACT |
| Temporary exception contract | CONFIRMED_NOT_IMPLEMENTED |
| Parity mode | OBSERVE_ONLY_TWO_CONSUMERS |
| Third consumer | BLOCKED |
| Persistence | NOT_AUTHORIZED |
| Enforcement | NOT_AUTHORIZED |
| Data correction | NOT_AUTHORIZED |
| Next task | APP-AUTH-06F-SANDU-COMPETENCE-AND-MAPPING-RECONCILIATION-PLAN |
| Verdict | OWNER_AUTHORITY_DECISIONS_CONFIRMED_READY_FOR_SANDU_PLAN |
