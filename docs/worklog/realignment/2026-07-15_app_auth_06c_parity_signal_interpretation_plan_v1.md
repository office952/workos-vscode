# APP-AUTH-06C — Parity signal interpretation plan v1

**Task:** `APP-AUTH-06C` — `PARITY_SIGNAL_INTERPRETATION_PLAN_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `b123173`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Worktree:** `C:\w\psiso`  
**Verdict:** `APP_AUTH_06C_SIGNAL_INTERPRETATION_PLAN_READY_FOR_OWNER_DECISIONS`  
**Next:** `OWNER-DECISION-05-PARITY-SIGNAL-AUTHORITY-AND-SANDU-RECONCILIATION`

**Scope:** Plan / interpretation only. No code, parity, DB, employee, competency, mapping, eligibility, assignment, persistence, enforcement, third consumer, or migration changes.

**Session ledger:** [`docs/worklog/session/2026-07-15_session_master_backup_runtime_parity_governance_alignment.md`](../session/2026-07-15_session_master_backup_runtime_parity_governance_alignment.md)

**Evidence:** `docs/qa/product-system-active-path-isolation-v1/app_auth_06c/` (15 JSON artifacts)

---

## Executive summary

All **16** unique parity fingerprints from the APP-AUTH-06 pilot are inventoried, grouped into **4** root-cause groups, and classified under the owner-approved P3 taxonomy. They collapse to **2** actionable unique problem groups — both centered on **Sandu (employee_id=4)**:

1. **Registry vs legacy competence conflict** (1 fingerprint)
2. **Hybrid explicit-mapping eligibility without registry competence** (10 fingerprints across 5 pilot operations)

The remaining **5** fingerprints are **EXPECTED_TRANSITION** baseline controls (employees 1–2 aligned; Sandu print probe partial alignment).

**No DEFECT_PROVEN** or **TECHNICAL_INVESTIGATION** classifications are justified by current evidence. Parity behaved as designed: observe-only, response-invariant, zero mutations.

**Recommended next gate:** Option A — **owner reconciliation** (`OWNER-DECISION-05`). Third consumer readiness: **NOT_READY**.

---

## 1. Evidence source reconciliation

| Evidence source | Relevant facts | Current | Conflicts | Used |
|-----------------|----------------|---------|-----------|------|
| APP-AUTH-02 + owner_decision_package | Sandu dual-source competences; 7 explicit mappings; montaj_led policy open | ACCEPTED | None | YES |
| APP-AUTH-02B / 02C | Available projection closure; external HTTP PASS | COMPLETE | None | YES |
| APP-AUTH-03 | 18 consumers; Sandu 7-step observe flow | PLAN COMPLETE | 14 vs 16 unwired — resolved in 06/OD-04 | YES |
| APP-AUTH-04 | Comparators + contracts isolated in `backend/parity/` | GATE I1 PASS | None | YES |
| APP-AUTH-05 @ 6aedb3d | 2 consumers wired; invariance PASS | COMPLETE | Count ambiguity corrected | YES |
| APP-AUTH-06 @ 738965a | 420 raw; 16 unique; 0 false positives | COMPLETE | None | YES |
| OWNER-DECISION-04 @ deb5d69 | P1–P10 confirmed; preliminary categories | CONFIRMED | P10 UI-TRUTH branch paused per ledger | YES |
| Session ledger @ b123173 | Roadmap → 06C | COMPLETE | None | YES |

Full matrix: `evidence_source_reconciliation.json`

---

## 2. Fingerprint inventory

**Expected:** 16 · **Inventoried:** 16

| Fingerprint | Domain | Consumer | Employee | Operation | Freq | Class | Confidence |
|-------------|--------|----------|----------|-----------|------|-------|------------|
| 1b8d5993 | competence | mobile + eligibility | E4 | — | 40 | CONFIRMATION_REQUIRED | high |
| 830f4323 | eligibility | mobile | E4 | volumetric_letter_assembly | 40 | CONFIRMATION_REQUIRED | high |
| b99d3923 | eligibility | mobile | E4 | vinyl_cutting | 40 | CONFIRMATION_REQUIRED | high |
| 1ec1a240 | eligibility | mobile | E4 | led_assembly | 20 | CONFIRMATION_REQUIRED | high |
| 757a2fc1 | eligibility | mobile | E4 | led_wiring | 20 | CONFIRMATION_REQUIRED | high |
| 3a92d452 | eligibility | mobile | E4 | installation_prep | 20 | CONFIRMATION_REQUIRED | high |
| 03708dc9 | explicit_mapping | mobile | E4 | volumetric_letter_assembly | 40 | POLICY_DECISION | high |
| 4c1eeaf5 | explicit_mapping | mobile | E4 | vinyl_cutting | 40 | POLICY_DECISION | high |
| 1bb7cc71 | explicit_mapping | mobile | E4 | led_assembly | 20 | POLICY_DECISION | high |
| 1be32d24 | explicit_mapping | mobile | E4 | led_wiring | 20 | POLICY_DECISION | high |
| 1786a41e | explicit_mapping | mobile | E4 | installation_prep | 20 | POLICY_DECISION | high |
| 5b5190f1 | competence | eligibility | E1 | print | 20 | EXPECTED_TRANSITION | high |
| a318c09b | competence | eligibility | E2 | print | 20 | EXPECTED_TRANSITION | high |
| 93e81c6f | eligibility | eligibility | E1 | print | 20 | EXPECTED_TRANSITION | high |
| 7542aad2 | eligibility | eligibility | E2 | print | 20 | EXPECTED_TRANSITION | high |
| 83c881d5 | eligibility | eligibility | E4 | print | 20 | EXPECTED_TRANSITION | medium |

Full detail: `fingerprint_inventory.json`

---

## 3. Root-cause grouping

```text
16 unique fingerprints != 16 independent business problems
```

| Root cause group | Fingerprints | Employees | Operations | Confidence |
|------------------|--------------|-----------|------------|------------|
| RCG-01 registry/legacy competence conflict | 1 | E4 | — | high |
| RCG-02 hybrid explicit mapping without registry competence | 10 | E4 | 5 pilot ops | high |
| RCG-03 dual-source baseline aligned | 4 | E1, E2 | print | high |
| RCG-04 partial print alignment despite drift | 1 | E4 | print | medium |

**Unique problem groups:** **2** (RCG-01 + RCG-02)

Detail: `fingerprint_root_cause_groups.json`

---

## 4. Classification contract

Owner P3 refined categories with decision tree:

1. Required inputs present? → else **INSUFFICIENT_DATA**
2. Sources match? → **EXPECTED_TRANSITION**
3. Owner-confirmed authority exists? → if runtime contradicts → **DEFECT_PROVEN** / else **TECHNICAL_INVESTIGATION**
4. Policy-driven mismatch? → **POLICY_DECISION**
5. Else → **CONFIRMATION_REQUIRED**

**Final counts:**

| Class | Count |
|-------|-------|
| CONFIRMATION_REQUIRED | 6 |
| POLICY_DECISION | 5 |
| EXPECTED_TRANSITION | 5 |
| TECHNICAL_INVESTIGATION | 0 |
| DEFECT_PROVEN | 0 |
| INSUFFICIENT_DATA | 0 |

Contract: `classification_contract.json` · Matrix: `fingerprint_interpretation_matrix.json`

---

## 5. Sandu interpretation (operation-by-operation)

**Accepted:** Sandu must not be changed automatically. Legacy is not assumed correct. Registry is not assumed correct.

### Pilot operations (5)

| Operation | Registry op | Registry skill | Legacy skill | Mapping | Auth | Op eligible | Canon eligible | Fingerprints |
|-----------|-------------|----------------|--------------|---------|------|-------------|----------------|--------------|
| volumetric_letter_assembly | assembly | SK_PRINT | SK_ASSEMBLY | explicit | false | yes | no | 830f4323, 03708dc9 |
| vinyl_cutting | colantare | SK_PRINT | SK_VINYL_APPLICATOR | explicit | false | yes | no | b99d3923, 4c1eeaf5 |
| led_assembly | montaj_led | SK_PRINT | SK_ELECTRICIAN | explicit | false | yes | no | 1ec1a240, 1bb7cc71 |
| led_wiring | montaj_led | SK_PRINT | SK_ELECTRICIAN | explicit | false | yes | no | 757a2fc1, 1be32d24 |
| installation_prep | field_installation | SK_PRINT | SK_FIELD_INSTALLER | explicit | true | yes | no | 3a92d452, 1786a41e |

### All seven APP-AUTH-02 mappings

assembly, colantare, field_installation, montaj_led, packaging, quality_control, welding — all lack registry competence match; print/print_roll aligned.

**Operations analyzed:** 7 mappings · **Pilot runtime-proven:** 5

Detail: `sandu_operation_interpretation.json`

---

## 6. Duplication interpretation

| Metric | Value |
|--------|-------|
| Raw observations | 420 |
| Duplicate observations | 404 |
| Unique fingerprints | 16 |
| Unique problem groups | 2 |

Duplicates come from **20 HTTP requests × 2 consumers × stable fixture**, plus **paired eligibility + explicit_mapping events** per operation. Fingerprint grouping is **sufficient**. In-memory suppression is **not needed** now; could hide real state changes if misapplied.

Detail: `duplicate_interpretation.json`

---

## 7. Generalizability

| Finding | Scope | Generalizable | Risk |
|---------|-------|---------------|------|
| Sandu competence conflict | employee-specific | NO | HIGH |
| Hybrid mapping without competence | architecture-wide | YES | HIGH |
| Multi-fingerprint per operation | domain-wide | YES | MEDIUM |
| E1/E2 aligned baselines | fixture control | NO | LOW |
| Unprobed mappings (packaging, QC, welding) | employee-specific | NO | MEDIUM |

Detail: `generalizability_matrix.json`

---

## 8. Signal quality thresholds

Overall: **USEFUL_FOR_OBSERVE_ONLY_OWNER_DECISIONS** (P1 aligned). PASS on deterministic, explainable, invariant, confidential-safe dimensions. **PARTIAL** on owner-actionable until Q1–Q8 answered.

Detail: `signal_quality_thresholds.json`

---

## 9. Authority matrix

| Domain | Source A | Source B | Authority | Owner confirmed |
|--------|----------|----------|-----------|-----------------|
| competence | registry | legacy JSON | UNRESOLVED (Sandu) | NO |
| authorization | registry resources | legacy machines | PARTIAL | partial |
| operation_mapping | explicit list | skill requirements | POLICY_UNRESOLVED | NO |
| eligibility | operational hybrid | canonical comparator | OBSERVE_ONLY | P5 yes |
| employee_identity | registry | legacy HR | STABLE | yes |
| resource_capability | registry | legacy | UNRESOLVED (Sandu) | NO |

Does not override A1–A22. Detail: `authority_matrix.json`

---

## 10. Owner decision questions

Eight questions packaged (Q1–Q8): competence authority, explicit mapping policy, authorization requirement, legacy transitional status, fail-closed eligibility, expected discrepancies, evidence before correction, remain observe-only.

**Plan does not answer on behalf of owner.**

Detail: `owner_decision_questions.json`

---

## 11. Next-gate options

| Option | Recommendation |
|--------|----------------|
| A — Owner reconciliation only | **RECOMMENDED_DEFAULT** |
| B — Technical audit | OPTIONAL if new ambiguity |
| C — Continue same two consumers | DEFER if owner delays |
| D — Third consumer plan | NOT_NOW |
| E — Enforcement/persistence | FORBIDDEN |

Detail: `next_gate_options.json`

---

## 12. Third-consumer readiness

**CONS-REGISTRY-CATALOG-API:** **NOT_READY**

Likely re-reads registry catalog; low incremental truth; increases duplicate risk without closing Sandu questions.

Detail: `third_consumer_readiness.json`

---

## 13. Blocked scope

Persistence, manager projection, enforcement, source switch, migration, APP-AUTH-07, third consumer, automatic remediation — all **blocked**.

Enforcement posture: CONFIRMATION_REQUIRED/POLICY → **FORBIDDEN** or **PREMATURE**.

Detail: `blocked_scope.json`

---

## 14. Task breakdown

| Task | Recommended |
|------|-------------|
| **OWNER-DECISION-05** — parity signal authority + Sandu reconciliation | **YES — NEXT** |
| APP-AUTH-06D — technical audit | Only if new TECHNICAL_INVESTIGATION evidence |
| APP-AUTH-06E — stability followup | Only if owner defers OD-05 |
| APP-AUTH-07 | **NOT proposed** |

Detail: `implementation_task_breakdown.json`

---

## 15. Acceptance criteria

| Criterion | Met |
|-----------|-----|
| All 16 fingerprints inventoried | YES |
| Root-cause grouped | YES (4 groups, 2 problems) |
| All classified | YES |
| Duplicates separated from unique problems | YES |
| Sandu operation-by-operation | YES (7 mappings, 5 pilot) |
| Owner questions explicit | YES (Q1–Q8) |
| No source authority invented | YES |
| No automatic remediation | YES |
| Third consumer unconnected | YES |
| Persistence/enforcement blocked | YES |
| Next gate = owner review | YES |

---

## 16. Honest opinion

The pilot did its job: it surfaced a **known, documentable Sandu reconciliation debt** without pretending parity picks a winner. The scary number **420** is mostly **repeat emissions**, not **420 bugs**. The real decision surface is narrow:

1. Who owns Sandu's competence truth?
2. What is the transitional rule for **hybrid explicit mapping**?

Until those are owner-closed, more parity wiring would add noise, not clarity. **Do not** connect a third consumer or persist observations yet.

---

## 17. Roadmap awareness checkpoint

- UI-TRUTH-01A complete; 01B–01E paused
- Parity frozen at 2 consumers (P5)
- Session ledger realigned; main roadmap restored
- This plan completes the P10 step "signal interpretation plan"
- Implementation of any data/policy fix remains **after OWNER-DECISION-05**

---

## 18. Dead pieces check

No dead code introduced (docs only). Existing parity adapter remains observe-only and disconnected from enforcement paths. Sandu helper remains in-process read-only.

---

## Delivery footer

| Field | Value |
|-------|-------|
| Task | APP-AUTH-06C — PARITY_SIGNAL_INTERPRETATION_PLAN_V1 |
| Starting HEAD | `b123173` |
| Fingerprints expected | 16 |
| Fingerprints inventoried | 16 |
| Root-cause groups | 4 |
| Raw observations | 420 |
| Duplicate observations | 404 |
| Unique problem groups | 2 |
| Sandu operations analyzed | 7 |
| CONFIRMATION_REQUIRED | 6 |
| TECHNICAL_INVESTIGATION | 0 |
| EXPECTED_TRANSITION | 5 |
| POLICY_DECISION | 5 |
| DEFECT_PROVEN | 0 |
| INSUFFICIENT_DATA | 0 |
| Source authority invented | NO |
| Automatic remediation proposed | NO |
| Third consumer | NOT_CONNECTED |
| Third-consumer readiness | NOT_READY |
| Persistence | NOT_AUTHORIZED |
| Manager projection | NOT_AUTHORIZED |
| Enforcement | NOT_AUTHORIZED |
| Source switch | NO |
| Migration | NOT_AUTHORIZED |
| APP-AUTH-07 | BLOCKED |
| Next task | OWNER-DECISION-05-PARITY-SIGNAL-AUTHORITY-AND-SANDU-RECONCILIATION |
| Code changed | NO |
| DB changed | NO |
| Verdict | APP_AUTH_06C_SIGNAL_INTERPRETATION_PLAN_READY_FOR_OWNER_DECISIONS |
