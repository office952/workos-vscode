# ACM BOXED SUPPORT COMPOSITION EXTENSION — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `5dfe807a` (**reconfirmed**) |
| Owner decision | **A** (locked — do not re-ask A/B/C) |
| Previous STOP | `BOND_SECOND_PRODUCT_CONFIGURATION_FINAL_REPORT.md` — **closed by A** |
| CP0 | `ACM_BOXED_SUPPORT_COMPOSITION_CP0_FREEZE.md` — **FROZEN** |
| Allowlist | `ACM_BOXED_SUPPORT_COMPOSITION_ALLOWLIST.md` |
| Shared map | `ACM_BOXED_SUPPORT_COMPOSITION_SHARED_MAP.md` |
| Engine | native inline |
| Dirty tree | preserved; allowlist-only |
| Publication | **KEEP_DRAFT** — no publish executed |

---

## 1. Owner decision readback (A)

Extend existing `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`. No new panel SKU. No new composite root SKU. `applied_content` = volumetric letters **XOR** volumetric logo. Metal frame = **optional**, operator-explicit (`acp_internal_frame`). Logo branch honestly blocked if candidate. Letters branch completed via component reuse (not VL root under ACM — cycle guard).

## 2. Previous STOP closure

Bond second-product STOP on near-identities is **closed** by owner Decision A. Panel identity remains ACM boxed. Composite shape = composition extension, not greenfield PT.

## 3. Kickoff confirmation

| Item | Result |
|------|--------|
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `5dfe807aac7918843342c2532c066034d07614a0` |
| Engine | native inline (no config.local.yaml) |

## 4. Absolute boundaries (honored)

No VL publication; no ACM publication; no PI/CI/CT; no SVG/CAD/Build 2/EP materialization; no pricing redesign; dirty tree untouched outside allowlist; no push/PR; no schema migration.

## 5. Executive truth (română)

Al doilea produs real este **extensie de compoziție** pe rădăcina ACM casetat deja live: conținut aplicat litere XOR logo, cadru metalic opțional. Litere = reutilizare componente VL. Logo root există dar rămâne **blocat onest** (candidate). Fără SKU panou nou.

## 6. CP0 freeze

**FROZEN** — see `ACM_BOXED_SUPPORT_COMPOSITION_CP0_FREEZE.md`.

## 7–12. Agents A–G

| Agent | Status |
|-------|--------|
| A ACM Root | **DONE** — seed + dossier `composition_extension_v1` |
| B Applied Content XOR | **DONE** — `acm_boxed_support_composition_v1` + composition contract |
| C Metal Frame | **DONE** — optional `acp_internal_frame` operator-explicit |
| D PT/PD/Aggregate | **DONE** — standalone graph + BOM exclude applied_content children |
| E Qty/CPP/EIC | **DONE** — panel-only CPP/EIC preserved; separate_quote_line; no double-count rollup |
| F UI/Readiness | **DONE** — radio/checkbox panel + readiness XOR/logo honesty |
| G QA/Evidence | **DONE** — tests + this report |

## 13. Checkpoints CP0–CP6

| CP | Verdict |
|----|---------|
| CP0 | **PASS / FROZEN** |
| CP1 | **PASS** root composition seed |
| CP2 | **PASS** XOR letters\|logo |
| CP3 | **PASS** optional frame |
| CP4 | **PASS** aggregate / PD composition |
| CP5 | **PASS** UI + readiness |
| CP6 | **PASS_WITH_WARNINGS** — screenshots NOT_CAPTURED (no live stack) |

## 14. Root identity

`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` — unchanged panel identity.

## 15. Letters identity

Reuse FACE / BACK / ALUMINIU / LED / FINISH. VL root **not** linked under ACM (avoids cycle with existing VL→ACM optional link). Reference: `TPL-VOLUMETRIC-LETTERS_v2`.

## 16. Logo identity / branch status

Canonical logo **root** exists: `TPL-VOLUMETRIC-LOGO_v1`. Composition edge seeded (`applied_content=logo`). Offerability **honestly blocked** (`LOGO_BRANCH_CANDIDATE_BLOCKED`). RETURN/cant not used as logo product.

## 17. Frame identity / status

Domain `acp_internal_frame` — optional, operator checkbox, no automatic thresholds. Not a PT. Not metal premount.

## 18. XOR proof

| Case | Result |
|------|--------|
| letters only | pack edges emitted; logo absent |
| logo only | logo edge + candidate blocker |
| both forced | `APPLIED_CONTENT_XOR_VIOLATION` |
| none (panel-only) | allowed |

## 19. Quantity / double-count

Applied-content children listed as optional modules; **materials/ops not rolled into ACM panel BOM**. CPP panel-only still 6 `acm_*` lines. `pricing_mode=separate_quote_line`. Anti-hourly: no new hourly contamination.

## 20. Commercial basis

Existing ACM boxed rates + VL/logo reuse. **No invented formulas.**

## 21. Generalization vs VL

| Axis | VL | ACM composition (A) |
|------|----|---------------------|
| Root | Letters | ACM panel |
| Content/support | ACM optional child | Letters/logo XOR child |
| Cycle risk | VL→ACM | ACM↛VL root (guard) |
| Frame | N/A / premount alternate | Optional ACP internal frame |

## 22. UI

`AcmBoxedAppliedContentPanel` — radio (none/letters/logo) + frame checkbox; mounted on ACM composition tab. Vitest **4/4 PASS**.

## 23. Tests run

| Command | Result |
|---------|--------|
| `pytest tests/test_acm_boxed_support_composition_v1.py -q` | **PASS** |
| `pytest … + test_acm_boxed_mounting_standalone_offer_v1.py` | composition PASS; pre-existing `panel_perimeter_m` assertion fails under current `apply_acm_commercial_geometry` (pops legacy perimeter) — **not introduced by XOR**; dirty unrelated test addition not committed |
| Vitest `AcmBoxedAppliedContentPanel.test.tsx` | **4/4 PASS** |

## 24. Screenshot pack 1–20

**NOT_CAPTURED** — Product System stack not live for capture this run. Intended pack (when stack available): ACM overview, composition tab, XOR radios, letters note, logo blocked note, frame checkbox on/off, module link list letters×5 + logo, readiness XOR/logo findings, dossier composition_extension, aggregate optional modules, panel-only CPP, … (20).

## 25. Product configuration verdict

**PASS_WITH_WARNINGS** — composition contracts configured draft; logo branch blocked; unpublished; screenshots missing.

## 26. Publication recommendation

**KEEP_DRAFT**. Do not publish ACM or VL. Logo GO separate. Optional later: publication proof after logo root offerability + live screenshot pack.

## 27. Next owner decision (pick one)

1. **keep draft** — accept composition extension unpublished (**recommended**)
2. **resolve missing logo root offerability** — owner GO on `TPL-VOLUMETRIC-LOGO_v1` before logo branch can be production-ready
3. **future conditional frame** — only if shop needs auto thresholds (explicitly out of v1)
4. **prepare later publication proof** — after (2) + screenshot pack + e2e_ready

## 28–30. Direction scores (0–100)

| Axis | Score |
|------|------:|
| Decision A fidelity | 95 |
| XOR honesty | 94 |
| Logo honesty | 96 |
| Frame optional discipline | 93 |
| No double-count | 92 |
| Letters reuse without VL deep-dive | 90 |
| UI exposure | 88 |
| Screenshot evidence | 20 |
| Publication readiness | 35 |
| Boundary discipline | 96 |

**Overall direction this run: 84/100**

## 31. Forbidden confirmation

| Forbidden | Absent? |
|-----------|---------|
| New panel / composite SKU | YES |
| Publish / auto-activate inactive | YES |
| VL formula / deep-dive | YES |
| Schema migration for XOR | YES |
| Logo RETURN as full product | YES |
| Auto frame thresholds | YES |
| Pricing invent | YES |
| git add -A / push / PR | YES |

## 32. Files changed (allowlist)

See commit SHAs. Primary:

- `backend/services/acm_boxed_support_composition_v1.py`
- `backend/seeds/seed_tpl_acm_boxed_mounting_support_v1.py`
- `backend/services/product_definition_composition_contract.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/acm_quote_input_helpers.py`
- `backend/services/product_e2e_readiness_service.py`
- `backend/tests/test_acm_boxed_support_composition_v1.py`
- `frontend/src/features/product-system/AcmBoxedAppliedContentPanel.tsx` (+ test)
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `docs/qa/.../ACM_BOXED_SUPPORT_COMPOSITION_*`
- worklog section

## 33. Commits

| # | SHA | Message |
|---|-----|---------|
| 1 | `4b367cd5` | `feat(product-system): extend ACM boxed support composition` |
| 2 | `ce4f57b1` | `feat(product-system): add letters-logo XOR and optional frame contracts` |
| 3 | `b65f493b` | `feat(product-system): compile ACM composite truth quantities and readiness` |
| 4 | `b2139b32` | `fix(product-system-ui): expose applied content and optional frame configuration` |
| 5 | `2314550e` | `test(product-system): prove ACM composition and reuse invariants` |
| 6 | tip | `docs(qa): finalize ACM second-product evidence` |

Tip HEAD after docs: see `git rev-parse HEAD` on this branch (docs commit is tip).

## 34. Architecture reopen

None required. Inverse composition pattern documented; job-level exclusivity remains operator intent.

## 35. Runtime stages

Static composition/readiness proven. Live Intake ACM-root journey **not** fully wired (out of minimal extension).

## 36. Dossier / readiness / preview

Dossier section `composition_extension_v1` seeded. Readiness emits XOR contract PASS + logo honesty BLOCKED. PD standalone still builds panel-only selected modules.

## 37. Seed / API path

`seed_tpl_acm_boxed_mounting_support_v1` upserts ACM→letters pack + ACM→logo links (`trigger_field=applied_content`). Preserves existing VL→ACM optional link.

## 38. Remaining blockers

1. Logo root candidate / not offerable  
2. Screenshots 1–20 not captured  
3. Unpublished letters children may warn on live readiness when letters selected  
4. Pre-existing standalone `panel_perimeter_m` vs commercial geometry (unrelated dirty tree)

## 39. Rollback note

Revert allowlisted commits; re-seed ACM template to drop outbound applied_content links. No migration.

## 40. Return-to-parent envelope

| Field | Value |
|-------|--------|
| configuration_verdict | **PASS_WITH_WARNINGS** |
| xor_proof | PASS |
| logo_branch_status | **honestly_blocked** (root exists, candidate) |
| letters_branch_status | **active_reuse** (components; VL root not child) |
| frame_status | **optional operator-explicit** |
| publication_recommendation | **KEEP_DRAFT** |
| HEAD | see tip after commits |
| report_path | this file |
| next_owner_decision | keep draft / resolve logo GO / future conditional frame / later publication proof |

## 41. Worklog

Section **ACM BOXED SUPPORT COMPOSITION EXTENSION** in codesign e2e worklog.

## 42. Screenshot honesty

NOT_CAPTURED.

## 43. Assertion discipline

No assertions weakened. Composition suite green. Unrelated pre-existing perimeter assertion not greenwashed.

## PAREREA MEA SINCERA

Decision A was the right call. Linking VL **root** under ACM would have created a cycle with the live VL→ACM child link — component-pack reuse is the honest smallest extension. Logo root exists, so the branch is not “missing invent”; it is correctly blocked until logo offerability GO. Frame as domain (not PT) stays clean. Do **not** publish yet — draft composition is enough to prove the inverse pattern without pretending the shop SKU is commercially closed.
