# ACM_PANEL_OPERATOR_INPUT_COMMIT_SEMANTICS_V1

**Status:** Implementation complete — STOP owner review  
**Date:** 2026-07-20  
**Evidence:** [`docs/audits/_evidence/2026-07-20_acm-panel-input-commit-semantics/`](./_evidence/2026-07-20_acm-panel-input-commit-semantics/)  
**Worklog:** [`docs/worklog/realignment/2026-07-20_acm_panel_operator_input_commit_semantics_v1.md`](../worklog/realignment/2026-07-20_acm_panel_operator_input_commit_semantics_v1.md)

---

## 1. Rezumat

Fix izolat: draft local + debounce 500ms + flush/confirm combinat, astfel încât un intent de editare produce maximum un `operatorPatch` / `PUT finish-setup`. Confirmarea cu drafturi pending este **un singur PUT** (updates + authority). Unmount doar anulează debounce; beforeunload doar avertizează.

## 2. Verdict

**PASS** pe acceptance + network proof (`network-proof.json` pass=true).  
SvgAnalyzer neatins. Fundal RO neschimbat. operatorPatch rămâne singura autoritate.

## 3. Root cause

`onChange` → `onUpdateField` → persist imediat pe fiecare keystroke (soak: 3 PUT pentru typing).

## 4. Control inventory

Numeric drafts: width, height, thickness, l1, l2, fold_count.  
Immediate combined: confirm geometry/construction/technical/relation.  
Segmented: flush field drafts apoi patch segmented.  
Select/checkbox AcmPanel: N/A (inexistente).

## 5. Draft model

String local per câmp; status `clean | editing | pending_commit | invalid`. Canonical păstrat până la commit valid. Empty/incomplete temporar nu șterge payload.

## 6. Debounce

`ACM_PANEL_FIELD_COMMIT_DEBOUNCE_MS = 500` — constantă unică. Epoch anulează callback stale după blur/flush/confirm/unmount cancel.

## 7. Flush semantics

`flushAll(): AcmPanelFlushResult` cu `nothing_to_commit | committed | blocked_invalid`.  
Navigare/acțiune doar pe primele două. Confirm: `takePendingUpdates` + `buildAcmPanelConfirmActionWithUpdatesPatch` (fără flush-then-confirm).

## 8. Numeric parsing

Parse la commit; fold_count ∈ {1,2}; mm > 0; NaN/invalid → zero PUT + mesaj local.

## 9. Dirty state

Expus în hook (`data-draft-status` pe input). Fără redesign vizual.

## 10. Concurrency

Epoch per field; ReviewStep request id existent; fără write-path secundar.

## 11. Tests

Drafts 12, operatorPatch +batch/confirm 7, inspector commitSemantics 5, regression acmPanel/composition/coalesce — green.

## 12. Runtime

Fixture `IV6-DB2F86B7`, route operator, 1440×900, BE `:8003`.

## 13. Network proof

Vezi `network-proof.json`. Typing/paste/blur/Enter/section/confirm+pending/two-fields: **1 PUT** fiecare.

## 14. Request counts before/after

| Scenario | Before (soak) | After |
|----------|---------------|-------|
| Typing multi-char | 3 PUT | 1 PUT |
| Confirm + pending L1 | n/a (gate) | 1 PUT combined |

## 15. Refresh

`afterRefreshL1` = valoarea finală (83 în ultima rulare proof).

## 16. Regression

Vitest acmPanel + composition; pytest coalesce — passed. SvgAnalyzer diff: none.

## 17. Screenshots

`shots/01-before.png`, `02-after.png`, `03-refresh.png` în evidence folder.

## 18. Boundaries

Fără remediation, blueprint, MULTI, ReviewStep ownership move, SvgAnalyzer, schema, pricing.

## 19. Risks

Blur între câmpuri = PUT per câmp (acceptat). Invalid blochează nav/confirm.

## 20. Commit

Vezi git după commit — hash complet/scurt în mesajul final agent.

## 21. Opinie sinceră

Fixul e mic ca suprafață și rezolvă exact blocker-ul de soak. `onMouseDown preventDefault` pe confirm e esențial pentru 1 PUT. Direcția e corectă pentru PASS complet S0–S2.

## 22. Direcție stabilită: **93/100**

(era 84; single-PUT gate ridică scorul; rămân legacy Fundal pre-instance și readiness blocked pe fixture.)
