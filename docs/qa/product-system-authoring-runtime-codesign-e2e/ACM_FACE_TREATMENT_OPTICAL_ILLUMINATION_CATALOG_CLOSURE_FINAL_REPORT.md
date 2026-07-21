# ACM FACE-TREATMENT OPTICAL AND ILLUMINATION CATALOG CLOSURE — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `9bdcfaa89f12c83f151d5d9ceec76b7aa82bbaf0` (`9bdcfaa8`) — **reconfirmed** |
| Axis | **B only** — optical / plexiglas / illumination commercial catalog closure |
| CP0 | `ACM_FACE_TREATMENT_OPTICAL_CATALOG_CP0_FREEZE.md` — **FROZEN** |
| Allowlist | `ACM_FACE_TREATMENT_OPTICAL_CATALOG_ALLOWLIST.md` |
| Shared map | `ACM_FACE_TREATMENT_OPTICAL_CATALOG_SHARED_MAP.md` |
| Engine | native inline |
| Dirty tree | preserved; allowlist-only |
| Publication | **KEEP_DRAFT** |

---

## 1. Owner GO readback

Owner GO to close optical/plexiglas/illumination commercial truth for Axis B **before** volumetric dual-select. Wire existing keys only; add rates only from canonical owner truth; STOP exact mappings when rates absent. No invent rates. No XOR/SKU/publication/push/PR. No remapping volumetric/LIGHT-ROUTED into Axis B.

## 2. Accepted evidence (not recreated)

Prior structural path: `ACM_FACE_TREATMENT_COMMERCIAL_PATH_FINAL_REPORT.md` (PASS_WITH_WARNINGS; CPP/EIC blocked by missing optical catalog). Gap audit confirmed stubs / wrong-product / genuinely missing for treatment optical priced lines.

## 3. Kickoff confirmation

| Item | Result |
|------|--------|
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `9bdcfaa8` — matches accepted tip |
| Dirty tree | large unrelated dirty — untouched outside allowlist |
| Alembic | **not required** |

## 4. Absolute boundaries (honored)

No XOR change; no letters+logo dual-select; no logo/ACM/VL publish; no new SKU; no LIGHT-ROUTED revival; no PI/CI/CT; no SVG parsers; no invented optical prices; no volumetric LED remapping; no Execution materialization; no push/PR; no dirty reset.

## 5. Executive truth (română)

Catalogul optic/electrical RO pentru tratamentele de față rămâne **lipsă**. Am închis onest maparea comercială: fiecare nevoie are status `WIRED` / `KEY_STUB_NO_RATE` / `WRONG_PRODUCT` / `LEGACY_FORBIDDEN` / `GENUINELY_MISSING`. Insert-only **nu** moștenește blocker-ul de iluminare routed. Liniile tratament rămân **BLOCKED**; panoul-only rămâne valid; subtotal tratamente = `BLOCKED` / null. KEEP_DRAFT.

## 6. CP0 freeze

**FROZEN** — identities unchanged; rate remapping freeze locked; illumination scoping locked (insert-only ≠ routed illum BLOCK).

## 7–12. Agents A–G

| Agent | Status |
|-------|--------|
| A Catalog identity | **DONE** — resolution rows + statuses; zero optical WIRED priced |
| B Domain / PT | **DONE** — scoped blockers aligned domain ↔ CPP |
| C PD / Aggregate | **DONE** — catalog + UI summary projected; materials/ops empty |
| D Quantity / ops | **DONE** — intents identity; optical/illum blockers precise |
| E CPP / EIC | **DONE** — scenario guards; panel 6 `acm_*` preserved |
| F UI / Readiness | **DONE** — readiness / blockers / lines_allowed / subtotal exposed |
| G QA / Evidence | **DONE** — tests + screenshots + proof JSON + this report |

## 13. Checkpoints CP0–CP6

| CP | Verdict |
|----|---------|
| CP0 | **PASS / FROZEN** |
| CP1 | **PASS** shared catalog map |
| CP2 | **PASS** resolver projection |
| CP3 | **PASS** scoped blockers |
| CP4 | **PASS** CPP scenario proofs |
| CP5 | **PASS** UI commercial exposure |
| CP6 | **PASS_WITH_WARNINGS** evidence — priced optical close incomplete |

## 14. Root identity

`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` — KEEP_DRAFT, unpublished.

## 15. Routed identity

Unchanged: `FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT` / `ACP-LOCAL-MODULE-ROUTED-BACKLIT`. Routed illuminated → optical + illumination BLOCK.

## 16. Insert / relief identity

Unchanged: `FACE-TREATMENT-ACRYLIC-INSERT` / `RELIEF_PLEXI_10MM` badge. Insert-only → optical BLOCK only.

## 17. Catalog resolution (closed vs BLOCKED)

| Need | Status | Closed? |
|------|--------|---------|
| Panel shell commercial | `WIRED` | Yes (pre-existing) |
| Acrylic ~10 mm material | `KEY_STUB_NO_RATE` | **BLOCKED** |
| Optical backing plexi | `WRONG_PRODUCT` | **BLOCKED** |
| CNC route / cut backing | `GENUINELY_MISSING` | **BLOCKED** |
| Insert CNC / fit / retain | `GENUINELY_MISSING` | **BLOCKED** |
| Insert adhesive / spacers | `GENUINELY_MISSING` | **BLOCKED** |
| Treatment LED/PSU/wiring | `WRONG_PRODUCT` (no remap) | **BLOCKED** |
| LIGHT-ROUTED | `LEGACY_FORBIDDEN` | Not wired |

**Optical priced WIRED count (excl. panel):** **0**

## 18. Coexistence / blocker scoping

| Scenario | Optical BLOCK | Illumination BLOCK |
|----------|---------------|--------------------|
| panel-only | No | No |
| insert_only | Yes | **No** |
| routed_illuminated | Yes | Yes |
| both | Yes | Yes |
| both + frame | Yes | Yes (frame orthogonal) |

## 19. Quantity / double-sheet

Unchanged: treatment qty keys ∩ panel keys = ∅. Aggregate `materials=[]`, `operations=[]`, `owns_panel_sheet=false`.

## 20. CPP / EIC

| Path | Status |
|------|--------|
| Panel CPP | Unchanged — 6 `acm_*` lines with treatments present |
| Treatment lines | **BLOCKED** — `treatment_commercial_lines_allowed=false` |
| Invented plexi/LED/PSU/wiring/hourly | **Absent** (proven) |
| Guards | no_double_sheet / no_volumetric_led_fold_in / no_psu_duplicate / no_hourly_commercial_price |

## 21. Product Truth / PD

Catalog resolution + commercial UI summary projected into PD values via `project_for_product_definition` / `acm_panel_pd_projection`.

## 22. UI

`AcmBoxedFaceTreatmentPanel` exposes readiness overall, scoped blocker codes, `treatment_commercial_lines_allowed`, subtotal `BLOCKED`|null — no redesign.

## 23. Tests run

| Command | Result |
|---------|--------|
| `pytest tests/test_acm_face_treatment_commercial_path_v1.py -q` | **18 passed** |
| Vitest `AcmBoxedFaceTreatmentPanel.test.tsx` | **4/4 PASS** |

## 24. Screenshot pack

| # | File | Result |
|---|------|--------|
| 01 | `screenshots/acm-face-treatment-optical-catalog/01_panel_only_readiness.png` | CAPTURED |
| 02 | `…/02_insert_only_scoped_blockers.png` | CAPTURED |
| 03 | `…/03_routed_illuminated_blockers.png` | CAPTURED |
| 04 | `…/04_both_commercial_blocked.png` | CAPTURED |

## 25. Runtime evidence

`runtime/acm_face_treatment_optical_catalog_closure_proof.json` — 5 scenarios + catalog statuses + guards.

## 26. Live seed honesty

No applied_content volumetric links created. No new SKUs. No publication. No rate invention.

## 27. Product configuration verdict

**PASS_WITH_WARNINGS** (PARTIAL commercial close) — catalog map + scoped blockers + UI honesty closed; priced optical/illumination treatment lines remain BLOCKED pending owner RO rates.

## 28. Publication recommendation

**KEEP_DRAFT**. Do not publish ACM/VL/logo. Do not revive LIGHT-ROUTED. Do not remap volumetric LED.

## 29. Next owner decision (max one)

**Provide dedicated ACM face-treatment optical / plexiglas (~10 mm) / treatment-CNC / ACM-cavity illumination owner rate RO** (EUR + unit + ownership). Until then, treatment commercial lines remain honestly BLOCKED.

## 30. Stop conditions

| Condition | Triggered? |
|-----------|------------|
| Absent owner rates for optical mappings | **Yes — STOP those mappings** (continued others; kept BLOCK) |
| Only legacy pricing for treatments | Yes — LEGACY_FORBIDDEN; not wired |
| Ambiguous unit | No new ambiguous unit invented |
| LED ownership conflict requiring redesign | **Yes — STOP priced illumination close** (WRONG_PRODUCT; no remap) |
| Broad pricing redesign | No — not attempted |
| Alembic required | No |
| Inseparable dirty tree | No — allowlist clean |

## 31–35. Direction scores (0–100)

| Axis | Score |
|------|------:|
| Catalog honesty / no invent | 96 |
| Scoped illumination blockers | 95 |
| Panel CPP isolation | 94 |
| UI commercial exposure | 90 |
| Screenshot evidence | 78 |
| Full priced optical close | 28 |
| Boundary discipline | 97 |

**Overall direction this run: 82/100**

## Forbidden confirmation

No XOR change · no dual-select · no invent rates · no volumetric remap · no LIGHT-ROUTED revival · no new SKU · no publication · no push/PR.

## Commit SHAs

| # | SHA | Message |
|---|-----|---------|
| 0 | `9bdcfaa8` | kickoff HEAD |
| 1 | `682e0494` | docs(qa): freeze ACM face-treatment optical catalog CP0 and shared map |
| 2 | `61911a3e` | feat(product-system): add face-treatment optical catalog resolution map |
| 3 | `fa0e891b` | feat(product-system): scope optical and illumination commercial blockers |
| 4 | `839ed377` | fix(product-system-ui): expose face-treatment commercial readiness and blockers |
| 5 | `bf9da181` | test(product-system): prove optical catalog partial close and CPP scenarios |
| 6 | `742edd2f` | docs(qa): finalize ACM face-treatment optical illumination catalog closure |

## Files changed (allowlist)

- `backend/services/acm_face_treatment_commercial_path_v1.py`
- `backend/services/acm_panel_pd_projection.py`
- `backend/tests/test_acm_face_treatment_commercial_path_v1.py`
- `frontend/src/features/product-system/AcmBoxedFaceTreatmentPanel.tsx`
- `frontend/src/features/product-system/AcmBoxedFaceTreatmentPanel.test.tsx`
- `docs/qa/.../ACM_FACE_TREATMENT_OPTICAL_CATALOG_*`
- `docs/qa/.../ACM_FACE_TREATMENT_OPTICAL_ILLUMINATION_CATALOG_CLOSURE_FINAL_REPORT.md`
- `docs/qa/.../runtime/acm_face_treatment_optical_catalog_closure_proof.json`
- `docs/qa/.../screenshots/acm-face-treatment-optical-catalog/**`
- worklog section **ACM FACE-TREATMENT OPTICAL AND ILLUMINATION CATALOG CLOSURE**
