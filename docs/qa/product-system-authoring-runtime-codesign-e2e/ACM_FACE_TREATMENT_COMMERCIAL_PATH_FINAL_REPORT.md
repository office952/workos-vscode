# ACM / BOND FACE-TREATMENT COMMERCIAL PATH — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `290a4540481b68826d684dd79798c1e751335383` (`290a4540`) — **reconfirmed tip** |
| Axis | **B only** — shell-local face treatments |
| CP0 | `ACM_FACE_TREATMENT_COMMERCIAL_PATH_CP0_FREEZE.md` — **FROZEN** |
| Allowlist | `ACM_FACE_TREATMENT_COMMERCIAL_PATH_ALLOWLIST.md` |
| Shared map | `ACM_FACE_TREATMENT_COMMERCIAL_PATH_SHARED_MAP.md` |
| Engine | native inline |
| Dirty tree | preserved; allowlist-only |
| Publication | **KEEP_DRAFT** — ACM unpublished; no applied_content links created |

---

## 1. Owner GO readback

Owner GO for **Axis B only**: routed/backlit cut-out + acrylic insert/relief commercial path on `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`. Axis A volumetric XOR unchanged. FACE-TREATMENT LOCAL COMMERCIAL PATH FIRST.

## 2. Accepted evidence (not recreated)

In-chat multi-content audit accepted; `ACM_BOND_MULTI_CONTENT_EXISTING_TRUTH_AUDIT.md` not recreated. Read: multi-child truth audit, ACM boxed composition final report, MIXED ownership, ACP face-treatments composability audit.

## 3. Kickoff confirmation

| Item | Result |
|------|--------|
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `290a4540` — matches accepted tip |
| Backend | `http://127.0.0.1:8000` UP |
| Frontend | `http://127.0.0.1:3000` UP |
| Dirty tree | large unrelated dirty — untouched outside allowlist |
| Alembic | **not required** |

## 4. Absolute boundaries (honored)

No XOR change; no letters+logo dual-select; no logo/ACM/VL publish; no new panel SKU; no LIGHT-ROUTED revival; no PI/CI/CT; no SVG parsers; no invented optical prices; no Execution materialization; no push/PR; no dirty reset.

## 5. Executive truth (română)

Pe rădăcina ACM casetat există acum un traseu comercial local pentru **tratamente de față**: decupaj iluminat și insert plexiglas (~10 mm variantă owner), ortogonal față de conținutul volumetric XOR. Insert și „relief” sunt **același produs**; `RELIEF_PLEXI_10MM` e doar badge UI. Catalogul optic lipsește — liniile comerciale de tratament rămân **BLOCKED onest**. Panoul-only nu e blocat.

## 6. CP0 freeze

**FROZEN** — identities, coexistence, ownership, commercial honesty locked. Insert≠relief STOP **not** triggered.

## 7–12. Agents A–G

| Agent | Status |
|-------|--------|
| A Identities | **DONE** — routed + insert codes; relief badge; legacy dead |
| B Domain / PT | **DONE** — `acm_face_treatments_v1` + pin bag |
| C PD / Aggregate | **DONE** — projection; no panel sheet materials |
| D Quantity / ops | **DONE** — treatment keys ≠ panel keys; guarded intents |
| E CPP / EIC | **DONE** — optical BLOCK; panel CPP 6 `acm_*` lines preserved |
| F UI / Readiness | **DONE** — distinct section + scoped readiness check |
| G QA / Evidence | **DONE** — tests + screenshots + proof JSON + this report |

## 13. Checkpoints CP0–CP7

| CP | Verdict |
|----|---------|
| CP0 | **PASS / FROZEN** |
| CP1 | **PASS** domain + identities |
| CP2 | **PASS** PT pin + confirm path |
| CP3 | **PASS** PD / Aggregate projection |
| CP4 | **PASS** quantity / ops / no double sheet |
| CP5 | **PASS_WITH_WARNINGS** CPP/EIC optical BLOCK honest |
| CP6 | **PASS** UI + readiness |
| CP7 | **PASS** tests + screenshots + report |

## 14. Root identity

`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` — KEEP_DRAFT, unpublished.

## 15. Routed identity (CP0)

| Field | Value |
|-------|--------|
| Treatment | `FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT` |
| Geometry | `CUTOUT_TEXT` / `CUTOUT_LOGO` |
| Module | `ACP-LOCAL-MODULE-ROUTED-BACKLIT` |
| Legacy | `TPL-ACP-LIGHT-ROUTED` = PARALLEL_LEGACY_COST_PATH — not authority |

## 16. Insert / relief identity (CP0)

| Field | Value |
|-------|--------|
| Treatment | `FACE-TREATMENT-ACRYLIC-INSERT` |
| Geometry | `ACRYLIC_INSERT` |
| Module | `ACP-LOCAL-MODULE-ACRYLIC-INSERT` |
| Thickness | 10 mm `OWNER_CONFIRMED_VARIANT`; not sole admitted |
| Relief | `RELIEF_PLEXI_10MM` = **UI badge only** (same product) |

## 17. Coexistence proof

| Scenario | Result |
|----------|--------|
| panel-only (`none`) | PASS — readiness not blocked |
| routed_only | PASS |
| insert_only | PASS |
| both | PASS |
| + frame optional | Orthogonal (unchanged) |
| + applied_content XOR | Orthogonal — XOR validators unchanged |

## 18. Quantity / double-sheet

`TREATMENT_QUANTITY_KEYS ∩ PANEL_QUANTITY_KEYS = ∅`. Aggregate projection `owns_panel_sheet=false`, `materials=[]`. Panel sheet remains shell-owned once.

## 19. Ops intents

Guarded process intents projected (route/cut/backing/insert/retain/illum intent). Rate status **BLOCKED** — no invented CNC/optical rates.

## 20. CPP / EIC / optical blockers

| Path | Status |
|------|--------|
| Panel CPP | Unchanged — 6 `acm_*` lines with face treatments present |
| Treatment commercial lines | **BLOCKED** — `FACE_TREATMENT_OPTICAL_CATALOG_MISSING` / illumination rates |
| Invented plexi/LED lines | **Absent** (proven) |

## 21. Product Truth / PD

Typed bag `acm_face_treatments` pinned via ConfirmJobProductTruth. PD standalone projects domain + quantity matrix + ops + CPP gate + local module instances.

## 22. UI

`AcmBoxedFaceTreatmentPanel` — section **„Tratarea feței Bond/ACM”** on composition tab, separate from `AcmBoxedAppliedContentPanel` XOR. Frame checkbox preserved on XOR panel. Vitest **3/3 PASS**.

## 23. Tests run

| Command | Result |
|---------|--------|
| `pytest tests/test_acm_face_treatment_commercial_path_v1.py -q` | **16 passed** |
| `pytest tests/test_acm_boxed_support_composition_v1.py` + face authority/modules | **30 passed** (regression) |
| Vitest `AcmBoxedFaceTreatmentPanel.test.tsx` | **3/3 PASS** |

## 24. Screenshot pack

| # | File | Result |
|---|------|--------|
| 01 | `screenshots/acm-face-treatment-commercial/01_acm_product_detail.png` | CAPTURED |
| 02 | `…/02_composition_tab_xor_preserved.png` | CAPTURED — both panels present |
| 03 | `…/03_face_treatments_both_enabled.png` | CAPTURED — coexistence=both |

## 25. Runtime evidence

`runtime/acm_face_treatment_commercial_path_proof.json` — 4 coexistence scenarios + identities + readiness panel-only.

## 26. Live seed honesty

Outbound ACM `applied_content` volumetric links remain **0** — not created this build. Face treatments are shell-local typed bag, not composition module links to VL packs.

## 27. Product configuration verdict

**PASS_WITH_WARNINGS** — commercial path wired; optical catalogs incomplete (honest BLOCK); ACM unpublished.

## 28. Publication recommendation

**KEEP_DRAFT**. Do not publish ACM/VL/logo. Do not revive LIGHT-ROUTED.

## 29. Next owner decision (max one)

**Provide optical / plexiglas / illumination rate catalog GO** (or accept commercial treatment lines remain BLOCKED until then).

## 30. Stop conditions

| Condition | Triggered? |
|-----------|------------|
| Ambiguous routed identity | No |
| Insert ≠ relief requiring owner choice | **No** — same product; badge only |
| Only commercial path = archived LIGHT-ROUTED | No |
| Alembic required | No |
| Invent prices | No (blocked) |
| Optical ownership unisolatable | No — shell-local modules + SHELL_COMMON_WITH_ZONE_INTENTS |
| Aggregate double ACM material | No |
| Inseparable dirty tree | No — allowlist clean |
| Destructive reseed required | No |

## 31–36. Direction scores (0–100)

| Axis | Score |
|------|------:|
| CP0 identity freeze | 96 |
| Coexistence honesty | 95 |
| Orthogonal to XOR | 97 |
| No double sheet | 94 |
| Optical commercial honesty | 93 |
| UI separation | 92 |
| Screenshot evidence | 85 |
| Full optical commercial close | 35 |
| Boundary discipline | 96 |

**Overall direction this run: 88/100**

## 37. Forbidden confirmation

| Forbidden | Absent? |
|-----------|---------|
| XOR demote / dual letters+logo | YES |
| New applied_content VL links | YES |
| New panel SKU / LIGHT-ROUTED revival | YES |
| Invented optical prices | YES |
| Alembic / PI / CI | YES |
| git add -A / push / PR | YES |

## 38. Files changed (allowlist)

- `backend/services/acm_face_treatment_commercial_path_v1.py` (new)
- `backend/services/acm_quote_input_helpers.py`
- `backend/services/acm_panel_pd_projection.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/product_truth_job_confirm_service.py`
- `backend/services/product_e2e_readiness_service.py`
- `backend/tests/test_acm_face_treatment_commercial_path_v1.py` (new)
- `frontend/src/features/product-system/AcmBoxedFaceTreatmentPanel.tsx` (+ test)
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `docs/qa/.../ACM_FACE_TREATMENT_COMMERCIAL_PATH_*`
- runtime proof + screenshots
- worklog section

## 39. Commits

| # | SHA | Message |
|---|-----|---------|
| 1 | `7d288bb8` | `docs(qa): freeze ACM face-treatment commercial path CP0` |
| 2 | `31a86738` | `feat(product-system): add ACM face-treatment commercial path domain` |
| 3 | `9034b9ce` | `feat(product-system): wire face treatments through PT PD Aggregate readiness` |
| 4 | `d646be77` | `fix(product-system-ui): expose Bond ACM face-treatment section` |
| 5 | `c020e3be` | `test(product-system): prove face-treatment commercial path coexistence` |
| 6 | tip | `docs(qa): finalize ACM face-treatment commercial path evidence` |

## 40. Return-to-parent envelope

| Field | Value |
|-------|--------|
| verdict | **PASS_WITH_WARNINGS** |
| CP0 identities | routed + insert frozen; relief=badge; legacy dead |
| coexistence | none / routed / insert / both proven |
| pricing/optical blockers | `FACE_TREATMENT_OPTICAL_CATALOG_MISSING` (+ illumination) |
| kickoff HEAD | `290a4540` |
| tip HEAD | see post-commit |
| report_path | this file |
| next_owner_decision | optical/illumination catalog GO (or accept BLOCK) |
| stop_conditions | none triggered |

## 41. Worklog

Section **ACM / BOND FACE-TREATMENT COMMERCIAL PATH** in codesign e2e worklog.

## 42. Assertion discipline

No assertions weakened. Face-treatment suite green; XOR composition regression green.

## PAREREA MEA SINCERA

Axis B was the right sequencing: shell-local face treatments must not wait on XOR demote or logo GO. Insert/relief as one product avoids a false SKU fork. The honest commercial gap is optical catalogs — do not invent rates; panel-only and coexistence contracts are already sound. Keep draft until owner supplies optical RO.
