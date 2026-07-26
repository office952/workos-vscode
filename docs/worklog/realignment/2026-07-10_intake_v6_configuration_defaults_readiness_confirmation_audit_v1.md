# Intake V6 — Configuration Defaults, Readiness & Final Confirmation Logic Audit V1

**Task:** `INTAKE_V6_CONFIGURATION_DEFAULTS_READINESS_CONFIRMATION_AUDIT_V1`  
**Date:** 2026-07-10  
**Type:** Read-only functional logic audit  
**Verdict:** **PARALLEL_TRUTH_CONFIRMED**  
**Accepted HEAD:** `58370b1`  
**Repo HEAD at audit:** `5208f05` (post-audit-baseline; 2-step UI simplification)  
**Application code changed:** NO  
**Database rows changed:** 0  

---

## Owner direction confirmed

- **3 steps remain:** Pas 1 Straturi → Pas 2 Configurare produs → Pas 3 Rezumat final + confirmare finală.
- **Final confirmation once**, at the bottom of Step 3 only.
- **Do not** re-confirm per tab/card/field unless proven necessary.
- **Do not** hide warnings before proving root cause.

At accepted HEAD `58370b1`, operator step order was `["layers", "review", "confirm"]` with footer **Continuă la Confirmare**. At current HEAD `5208f05`, visible progress is **2 steps** (`Straturi` / `Configurare`), internal `confirm` redirects to `review`, and final summary is embedded in Review — **this contradicts restored owner direction** and is documented as **HIGH_RISK_CONTRADICTION** (finding F-ARCH-01).

---

## Runtime workspace

| Field | Value |
|-------|-------|
| Workspace ID | `22ef834d-f2d0-453b-a7a7-118928c98a39` |
| Workspace code | `IV6-189D2F12` |
| Template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Route | `http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator` |
| Workspace status | `ready_for_quote_preview` |
| Handoff status | `QUOTE_HANDOFF_BLOCKED` |
| Fatal blockers | `operator_confirmation_missing` |
| Review warnings | `unclassified_vector_artwork_requires_decision` |
| `finish_setup.confirmed` | **true** |
| `finish_setup.internal_draft_quote_confirmed` | **false** |
| Global `return_depth_mm` | **60** |
| Global `return_finish_type` | `white_aluminum` |
| Letter groups (4) | All `return_depth_mm=60`, all `confirmed=false` |
| Artwork (2) | Both `execution_type=print_laminate`, both `confirmed=false` |
| `selected_layer_refs` | **null** (not persisted on this workspace) |
| Live API | Backend `:8000` returned 503 during audit; persisted JSON capture used |

Capture: `docs/qa/intake-v6-configuration-defaults-readiness-confirmation-audit-v1/captures/workspace_field_summary.json`

---

## Three-step flow audit

| Step | Operator purpose | What is selected | What is persisted | What requires explicit decision | Auto-derived | Confirmed flags | Display-only |
|------|------------------|------------------|-------------------|--------------------------------|--------------|-----------------|----------------|
| **Pas 1 — Straturi** | Layer role assignment | face / printed_artwork roles per SVG layer | `layer_role_setup.layers[].confirmed_role`, `confirmation_state` | Unclassified vector perimeter vs operator-confirmed scope | Auto roles from analyzer | Per-layer `confirmation_state=confirmed` when operator confirms | Analyzer metrics chips |
| **Pas 2 — Configurare** | Product configuration | Face finish, cant finish, 60 mm depth, print+laminate, backing, LED, mounting | `finish_setup.*`, `letter_group_finishes[]`, `artwork_finishes[]` on autosave | Artwork classification when raw vector > confirmed perimeter | Letter groups from analyzer; defaults 60 mm + white_aluminum + print_laminate | **Every edit sets `confirmed=false`** on finish_setup and rows; row `confirmed` stays false unless explicit confirm path | UI shows defaults via `finishFromPayload` fallback when field null |
| **Pas 3 — Rezumat final** (target) | Review + **single** operator confirmation | Full configuration summary | `finish_setup.internal_draft_quote_confirmed` via `saveIntakeV6InternalDraftQuoteConfirmation` | Checkbox + draft boundary ack | Handoff preview recomputed | **Separate from field values** | At `58370b1`: dedicated `IntakeV6ConfirmStep`; at `5208f05`: collapsed into Review |

**Flow truth:** Pas 1 = layer decisions ✓ · Pas 2 = product decisions ✓ · Pas 3 = review + confirm once ✓ **by design at 58370b1**, **broken at 5208f05** (2 visible steps).

---

## Default value audit

| Field | Displayed default | Default source | Persisted? | Canonical? | Used by pricing | Used by PD | Used by readiness | Classification |
|-------|-------------------|----------------|------------|------------|-----------------|------------|-------------------|----------------|
| Return/cant width 60 mm | 60 mm in UI | `DEFAULT_RETURN_DEPTH_MM = 60` (`intakeV4LetterGroups.ts`) | **Yes** on fixture (global + all groups) | Yes (`ALLOWED_RETURN_DEPTH_MM`) | Yes via `return_depth_mm` | Via finish_setup bridge | Return/cant mapper reads depth but blocks on `confirmation_state` | **REAL_PRODUCT_DEFAULT** |
| Return/cant finish Alb | Alb · 60 mm | `INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE` = `white_aluminum` | **Yes** per group | Yes | Yes (stock color) | Bridge builds `finish_variant` | Blocked until component confirmation | **REAL_PRODUCT_DEFAULT** |
| Print + laminare (artwork) | Print + laminare | `deriveArtworkFinishes` default `execution_type: print_laminate` | **Yes** on fixture | Yes | Derived print/lam flags | productTruthDraft | `artwork.confirmed=false` → UI pending count | **REAL_PRODUCT_DEFAULT** (with false `confirmed`) |
| Face finish oracal_651 | Oracal 651 | `finishFromPayload` fallback | Yes + nearest color codes | Yes | Yes | Yes | Row `confirmed=false` | **REAL_PRODUCT_DEFAULT** |
| Global finish_setup.confirmed | N/A (backend) | Set true on explicit save with `confirmed=true` | **true** on fixture | Backend gate | Handoff policy | — | **CORRECT** for workspace-level save |
| Return/cant component confirmation | Diagnostics blocked | `return_cant_product_truth_bridge._build_instance` always `confirmation_state: "blocked"` | Written to `product_truth.components.return_cant` | Intended future component truth | Pricing keys built | Readonly mapper requires `confirmed` | **DISPLAY_PLACEHOLDER / TECHNICAL_STUB** — not operator-selectable |

**Answers to specific questions:**

- **Is 60 mm a real default or UI-only?** Real default; persisted on fixture.
- **Is print + laminare real or presentation fallback?** Real; `execution_type=print_laminate` persisted.
- **Does not changing defaults produce usable values?** Values exist in payload; readiness still fails on **confirmation flags**, not missing values.
- **Does readiness require `confirmed=true` despite valid values?** **Yes** — per-row `letter_group.confirmed`, `artwork.confirmed`, and return/cant `confirmation_state`.

---

## Field persistence matrix (fixture workspace)

| Field | Visible UI | UI default? | Explicit selection? | Workspace path | Persisted value | Confirmed flag | Readiness path | Blocker source | Complete? |
|-------|------------|-------------|---------------------|----------------|-----------------|----------------|----------------|----------------|-----------|
| Face material | Oracal 651 | Yes | Implicit default | `letter_group_finishes[].face_finish_type` | `oracal_651` | `confirmed=false` | `finish_setup.confirmed=true` | Row pending count | **Value yes / flag no** |
| Face thickness | Plexi (template) | Derived | N/A | template dossier | dossier | — | PD | — | CORRECT |
| Face finish | Oracal + code | Yes | Auto nearest color | `face_oracal_code` | set | `confirmed=false` | artwork/letter pending | — | **Value yes / flag no** |
| Return material | Alb / gold | Yes / mixed | Some groups changed | `return_finish_type` | persisted | `confirmed=false` | RETURN_CANT mapper | RETURN_CANT_* | **Value yes / flag no** |
| Return width | 60 mm | **Yes (REAL)** | Default unless changed | `return_depth_mm` | **60** | `confirmed=false` | return_cant bridge + mapper | RETURN_CANT_* | **Value yes / flag no** |
| Return finish | stock aluminum | Yes | Default | `return_finish_type` | persisted | `confirmed=false` | mapper | RETURN_CANT_* | **Value yes / flag no** |
| Stock color | Alb | Yes | Default | `white_aluminum` | persisted | — | bridge | — | Yes |
| Oracal / RAL | Oracal codes | Auto | Nearest match | `face_oracal_code` | set | — | color picker warning if missing | — | Yes on fixture |
| Print | print_laminate | **Yes** | Default derive | `artwork_finishes[].execution_type` | `print_laminate` | `confirmed=false` | handoff artwork + pending count | unclassified_vector + pending | **Value yes / flag no** |
| Laminare | combined mode | **Yes** | Same row | `execution_type` | `print_laminate` | `confirmed=false` | productTruthDraft | — | **Value yes / flag no** |
| Backing | forex default | Yes | Default | `finish_setup.backing_mode` | persisted | global confirmed | finish_setup | — | Yes |
| LED | ON modules | Yes | Default | `finish_setup.illuminated` | true | — | lighting blockers if invalid | — | Yes |
| Mounting | direct_wall | Yes | Default | `finish_setup.mounting_system` | persisted | — | — | — | Yes |
| Template | TPL-VOLUMETRIC-LETTERS_v2 | Bound | Pas 0 | `product_binding.template_code` | persisted | — | template_out_of_scope guard | — | Yes |
| Operator final confirm | Unchecked | N/A | **Required Step 3** | `finish_setup.internal_draft_quote_confirmed` | **false** | **This flag** | `operator_confirmation_missing` | Valid until Step 3 | **Correctly incomplete** |

---

## Confirmation inventory

| Confirmation flag | Path | Set where | Set by | Meaning | Blocks | Duplicate? | Recommendation |
|-------------------|------|-----------|--------|---------|--------|------------|----------------|
| Layer role confirmed | `layer_role_setup.layers[].confirmation_state` | Pas 1 save | Operator | Layer role decision final for that layer | `layer_roles_incomplete` | No — distinct decision | **Keep** (Pas 1 only) |
| Letter group confirmed | `letter_group_finishes[].confirmed` | Review autosave | System default false; rarely true | Per-card "confirmed" | `pendingConfirmationCount`, artwork surfacing | **Duplicates value presence** | **Derive** from populated fields or remove from operator UX |
| Artwork row confirmed | `artwork_finishes[].confirmed` | Review autosave | System default false | Per-artwork confirm | pending count, handoff surfacing | **Duplicates execution_type** | **Derive** when `execution_type != needs_decision` |
| Finish setup confirmed | `finish_setup.confirmed` | Review save | Autosave with `confirmed=true` on successful save | Workspace-level "finishes saved & acknowledged" | `finish_setup_not_confirmed` | Partial overlap with rows | **Keep internal**; tie to autosave not operator re-confirm |
| Internal draft quote confirmed | `finish_setup.internal_draft_quote_confirmed` | Step 3 API | Operator checkbox once | **Final operator confirmation** | `operator_confirmation_missing` | No — canonical final gate | **Keep as single operator boundary** |
| Return/cant confirmation_state | `product_truth.components.return_cant.instances[].confirmation_state` | Backend bridge on save | Always `"blocked"` today | Component-truth staging | RETURN_CANT_* diagnostics | **Duplicates finish values** | **Internal only** until promote workflow exists |
| Face confirmed perimeter | `components.face.confirmed_perimeter` | Not on fixture | — | Geometry truth for cant | RETURN_CANT_DEPENDENCY_* | Separate concern | Keep technical |
| Quote geometry confirmed | `quote_geometry.confirmed` | Geometry save | System | Perimeter evidence | pricing baseline | No | Keep technical |

**Count:** ~7 distinct confirmation concepts; **3 are operator-facing** (layer roles, per-row finish/artwork, final draft confirm) — should be **2** (Pas 1 layers + Pas 3 once).

---

## Return/cant chain matrix

| Concept | UI source | Workspace path | Mapper input | PD input | Readiness input | Fixture value | Contradiction? |
|---------|-----------|----------------|--------------|----------|-----------------|---------------|----------------|
| Material / finish | Cant dropdown Alb | `letter_group_finishes[].return_finish_type` | bridge → `finish_variant` | dossier module | mapper `material_profile` / finish | `white_aluminum` / gold | **No on value** |
| Width 60 mm | Depth selector | `return_depth_mm` global + per group | bridge → `material_profile.width_mm` | — | mapper `depth_mm` | **60** | **No on value** |
| Finish type | UI label | same as material | bridge | — | mapper | stock_color | No |
| Source layer | Layer card | `group_key` / layer_role_setup | `_resolve_layer_group_ids` | — | `layer_group_ids` | keys exist; **refs null** | **Yes — mapping gap** |
| Perimeter | Geometry panel | `quote_geometry.letter_perimeter_m` | `_build_geometry` evidence_only | — | dependency row | present | **Blocked (unconfirmed perimeter)** |
| Confirmation | N/A (not shown) | `product_truth…confirmation_state` | readonly mapper | — | `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED` | always `blocked` | **YES — root false positive** |
| Component owner | — | bridge instances | mapper | PD list | diagnostics | instances built | confirmation blocks despite values |

**Verdict — why "Alb · 60 mm" visible but blocked:** Values **are persisted** (answer **B + D + H**). UI reads `finish_setup` / letter groups. Readiness diagnostics read `product_truth.components.return_cant` where bridge **always** sets `confirmation_state=blocked` and appends `RETURN_CANT_COMPONENT_CONFIRMATION_MISSING` (`return_cant_product_truth_bridge.py:256-239`). Frontend readonly mapper treats non-`confirmed` source_state as **blocked** regardless of visible 60 mm (`returnCantTruthFieldsReadonlyMapper.ts:155-156`). Per-row `letter_group.confirmed=false` adds operator pending noise but is not the primary RETURN_CANT code path.

---

## Print + laminare matrix

| Concept | Visible selection | Persisted path | Confirmation flag | Consumer | Warning source | Correct? |
|---------|-------------------|--------------|-------------------|----------|----------------|----------|
| Combined mode | Print + laminare | `artwork_finishes[].execution_type = print_laminate` | `confirmed=false` | productTruthDraft, pricing preview | `pendingConfirmationCount`, "Artwork/logo neconfirmat" | **Value correct / flag wrong** |
| print_required | derived | null on fixture (derived at read) | — | productTruthDraftBuilder | — | OK |
| lamination_required | derived | null on fixture | — | same | — | OK |
| printed_artwork control | Step 1 role | `layer_role_setup` | layer confirm | artwork row creation | `unclassified_vector_artwork_requires_decision` | **Partially correct** — vector perimeter gap is real |
| Finish confirmation separate | Yes | row `confirmed` | independent of execution_type | Review header | FALSE_POSITIVE for default print_laminate |

---

## Readiness & blocker matrix

| UI / code message | Raw code | Source | Input paths | Fixture values | Actually missing? | Classification |
|-------------------|----------|--------|-------------|----------------|-------------------|----------------|
| Handoff blocat — verifica verdictul | `QUOTE_HANDOFF_BLOCKED` | handoff preview policy | all issue codes | fatal present | No — correct aggregate | VALID_BLOCKER (aggregate) |
| Confirma in pasul Confirmare | header action `confirm-step` | `intakeV6ReviewHeaderStatus.ts` | `operator_confirmation_missing` | internal_draft=false | Final confirm genuinely missing | **VALID** but **misplaced in Pas 2** at 5208f05 |
| Mergi la Artwork | artwork surfacing | handoff + row confirmed | artwork rows | execution set, confirmed false | Decision partially missing (classification) | **WRONG_CONFIRMATION_DEPENDENCY** for finish; **VALID_WARNING** for classification |
| Artwork necesită decizie | `unclassified_vector_artwork_requires_decision` | `has_unclassified_vector_artwork` | raw vs confirmed perimeter | gap detected | **Yes — classification** | VALID_WARNING |
| Operator confirmation lipseste | `operator_confirmation_missing` | `list_v4_handoff_issue_codes` | `internal_draft_quote_confirmed` | false | **Yes until Step 3** | **VALID_BLOCKER** (correct gate, wrong step UX at HEAD) |
| Verifica finisajul fetelor | pending / color | `resolveLayerCardStatus` | missing oracal | codes present | No on fixture | FALSE_POSITIVE (if shown) |
| Verifica latimea cantului | RETURN_CANT_* | readonly mapper | confirmation_state | depth=60 persisted | **No** | **FALSE_POSITIVE** |
| Verifica varianta confectionare spate | backing validators | finish_setup | backing_mode | set | No | FALSE_POSITIVE if shown |
| RETURN_CANT_* diagnostics | multiple | bridge + mapper | product_truth | values present, state blocked | **No** | **FALSE_POSITIVE** / **PARALLEL_TRUTH** |

---

## Parallel truth matrix

| Concept | Source A | Source B | Canonical (target) | Conflict? | Runtime consequence |
|---------|----------|----------|--------------------|-----------|---------------------|
| Cant width 60 mm | UI / `finishFromPayload` fallback | `letter_group_finishes[].return_depth_mm` | **finish_setup payload** | No on fixture | Display matches persist |
| Cant readiness | Persisted depth | `product_truth…confirmation_state=blocked` | **Persisted product values** | **YES** | False RETURN_CANT blockers |
| Print/laminate | UI default derive | `execution_type=print_laminate` | **artwork_finishes row** | No | Value OK |
| Artwork "unconfirmed" | `confirmed=false` | `execution_type` populated | **execution_type + decision** | **YES** | Inflated pending count |
| Operator confirmation | Field values complete | `internal_draft_quote_confirmed=false` | **Step 3 flag only** | No — by design | Correct fatal until confirm |
| Global vs row confirm | `finish_setup.confirmed=true` | all rows `confirmed=false` | Single boundary | **YES** | Contradictory completeness |
| Layer refs | layer_role_setup | `svg.selected_layer_refs` | selected_layer_refs (derived) | **YES (null)** | Return/cant layer_group context warnings |
| Step count UX | 3-step at 58370b1 | 2-step at 5208f05 | **3 steps** | **YES** | Operator confirms in wrong surface |

---

## Operator vs system responsibility

| Responsibility | Operator UI | Backend/system | Violations |
|----------------|-------------|----------------|------------|
| Choose product values | YES | NO | — |
| Persist choices | Trigger | YES | Autosave sets `confirmed=false` on every edit — OK internally |
| Validate required fields | Display | YES | — |
| Compute readiness | NO | YES | Readiness uses confirmation flags not values (**violation**) |
| Confirm technical mappings | NO | YES | RETURN_CANT requires operator-visible blocked state (**violation**) |
| Final confirmation once Step 3 | YES | Persist | 5208f05 embeds in Pas 2 (**violation F-ARCH-01**) |
| Reconfirm each field | **NO** | **NO** | `pendingConfirmationCount` counts 6 rows (**violation F-DUP-01**) |
| Generate diagnostics | NO | YES | RETURN_CANT false positives (**violation F-FP-01**) |

---

## Findings (priority)

| ID | Classification | Summary |
|----|----------------|---------|
| F-FP-01 | **FALSE_POSITIVE_WARNING** | RETURN_CANT diagnostics block despite persisted 60 mm + Alb |
| F-DUP-01 | **DUPLICATE_CONFIRMATION** | `letter_group.confirmed` / `artwork.confirmed` duplicate value presence |
| F-PT-01 | **PARALLEL_TRUTH** | `finish_setup.confirmed=true` vs all rows `confirmed=false` |
| F-PT-02 | **PARALLEL_TRUTH** | UI finish values vs `product_truth.return_cant.confirmation_state=blocked` |
| F-BLD-01 | **BLOCKING_LOGIC_DEFECT** | Operator sees complete cant; system treats as unconfirmed component |
| F-ARCH-01 | **HIGH_RISK_CONTRADICTION** | `5208f05` 2-step flow vs owner 3-step + Step 3 confirm |
| F-ARCH-02 | **HIGH_RISK_CONTRADICTION** | Review header "Confirmă în pasul Confirmare" while confirm merged into review |
| F-COR-01 | **CORRECT** | `operator_confirmation_missing` when `internal_draft_quote_confirmed=false` |
| F-COR-02 | **CORRECT** | `unclassified_vector_artwork_requires_decision` — real classification gap |
| F-DEBT-01 | **DOCUMENTED_DEBT** | `selected_layer_refs` not persisted on fixture (prior FHA audit) |
| F-DEBT-02 | **DOCUMENTED_DEBT** | Bridge always emits `RETURN_CANT_COMPONENT_CONFIRMATION_MISSING` pending owner promote |

---

## Owner decisions required

### DEC-CDRC-01 — Return/cant readiness source

| | |
|--|--|
| **Problem** | Persisted 60 mm + finish treated as blocked in RETURN_CANT diagnostics |
| **Evidence** | `workspace_field_summary.json`; bridge `confirmation_state=blocked`; mapper `readyFromClassification` |
| **Current** | Component confirmation required independent of finish_setup values |
| **Desired** | Readiness uses persisted depth + finish; component confirmation internal until promote |
| **Risk** | HIGH — operator mistrust of diagnostics |
| **Recommended fix** | Derive mapper readiness from `finish_setup` + letter groups when complete; demote RETURN_CANT to technical-only until promote |
| **Files** | `return_cant_product_truth_bridge.py`, `returnCantTruthFieldsReadonlyMapper.ts`, awareness panels |
| **Backend / Frontend** | Both |
| **Migration** | No |
| **Owner GO** | YES |

### DEC-CDRC-02 — Per-row finish confirmation

| | |
|--|--|
| **Problem** | Default product values persist with `confirmed=false`, inflating pending actions |
| **Evidence** | All 4 letter groups + 2 artwork rows false despite populated fields |
| **Current** | Every autosave edit sets `confirmed=false`; pending count treats rows as operator actions |
| **Desired** | Row flags derived when required fields populated; operator confirm only at Step 3 |
| **Risk** | HIGH — repeated confirm fatigue |
| **Recommended fix** | Remove row `confirmed` from operator pending UX; keep as internal dirty tracking OR derive on save |
| **Files** | `IntakeV6ReviewStep.tsx`, `intakeV4LetterGroups.ts`, `intakeV4ArtworkFinish.ts`, `intakeV6ReviewHeaderStatus.ts` |
| **Backend / Frontend** | Primarily frontend; optional backend stop reading row confirmed |
| **Migration** | Optional backfill derive |
| **Owner GO** | YES |

### DEC-CDRC-03 — Restore 3-step navigation

| | |
|--|--|
| **Problem** | `5208f05` collapsed confirm into review (2 visible steps) |
| **Evidence** | `intakeV6OperatorProgressSteps.ts` (2 steps); `IntakeV6OperatorWorkspace.tsx` confirm→review redirect |
| **Current** | 2-step visible progress |
| **Desired** | Restore `layers → review → confirm` with Step 3 footer confirm |
| **Risk** | HIGH — architectural drift from owner model |
| **Recommended fix** | Revert/replace 5208f05 navigation portions; keep compact summary **inside** Step 3 not Step 2 |
| **Files** | `IntakeV6OperatorWorkspace.tsx`, `IntakeV6OperatorProgressSteps.ts`, `IntakeV6ProgressBar.tsx`, footer |
| **Backend / Frontend** | Frontend |
| **Migration** | No |
| **Owner GO** | YES |

### DEC-CDRC-04 — Single final confirmation boundary

| | |
|--|--|
| **Problem** | Multiple operator-facing confirmations (rows + header + checkbox) |
| **Evidence** | Confirmation inventory above |
| **Current** | `internal_draft_quote_confirmed` + row flags + header CTA |
| **Desired** | Pas 1 layer roles + Pas 3 `internal_draft_quote_confirmed` only |
| **Risk** | MEDIUM |
| **Recommended fix** | Keep `internal_draft_quote_confirmed` as sole product confirm; demote others |
| **Files** | Policy already correct in `intake_v4_internal_draft_quote_policy_service.py`; UX consumers |
| **Backend / Frontend** | Both |
| **Migration** | No |
| **Owner GO** | YES |

### DEC-CDRC-05 — Real defaults without re-confirm

| | |
|--|--|
| **Problem** | 60 mm and print_laminate behave as placeholders in confirmation model |
| **Evidence** | Defaults persist but `confirmed=false` |
| **Current** | Defaults require same confirm path as explicit changes |
| **Desired** | Untouched real defaults count as complete product truth |
| **Risk** | MEDIUM |
| **Recommended fix** | On hydrate, set row completeness derived; only reset on explicit override |
| **Files** | derive/merge functions in letter groups + artwork finish |
| **Backend / Frontend** | Frontend + optional policy |
| **Migration** | No |
| **Owner GO** | YES |

---

## Recommended final confirmation model

1. **Pas 1:** Operator confirms layer roles only (`layer_role_setup.confirmation_status=complete`).
2. **Pas 2:** Operator selects product values; **immediate persist** on autosave; **no per-row operator confirm**; `finish_setup.confirmed=true` means "saved configuration snapshot" (internal).
3. **Pas 3:** Operator reviews compact summary; **one** action sets `internal_draft_quote_confirmed=true`.
4. **Technical validations** (geometry, artwork classification gap, pricing baseline) run automatically; warnings remain visible but distinguish **missing values** vs **missing confirm flag**.
5. **Legacy flags:** `letter_group.confirmed`, `artwork.confirmed`, `return_cant.confirmation_state` become **derived/internal** unless owner promote workflow requires explicit component confirm later.
6. **Blockers that remain:** real missing decisions (artwork classification), invalid combinations, missing final Step 3 confirm — **not** populated defaults.

---

## Tests

| Area | Coverage | Gap |
|------|----------|-----|
| 60 mm default | `intakeV6FinishHydration.test.ts`, letter group tests | No test that persisted 60mm ≠ RETURN_CANT blocked |
| print_laminate default | `intakeV4ArtworkFinish` derive tests | No test row confirmed=false vs execution populated |
| finish confirmation policy | `test_intake_v4_internal_draft_quote_confirmation_policy.py` ✓ | — |
| return cant bridge | `test_return_cant_product_truth_bridge.py` ✓ | Tests expect blocked state — encodes current bug |
| final confirmation Step 3 | `IntakeV6ConfirmStep.test.tsx` ✓ | No test for 3-step navigation at 58370b1 parity |
| false positive RETURN_CANT | mapper unit tests ✓ | Fixture with persisted 60mm + blocked state not asserted as false positive |

---

## Honest opinion

| Question | Answer |
|----------|--------|
| Is 60 mm really selected? | **Yes — persisted** on global finish_setup and every letter group. |
| Is print + laminare really selected? | **Yes — `execution_type=print_laminate` persisted** on both artwork rows. |
| Why does the system still warn? | Parallel confirmation model: row `confirmed=false`, return/cant `confirmation_state=blocked`, final `internal_draft_quote_confirmed=false`, plus legitimate artwork classification warning. |
| Are confirmation flags duplicating real values? | **Yes** — at least 3 layers duplicate completeness. |
| Is operator asked to confirm too often? | **Yes** — 6 row pendings + header CTA + final checkbox. |
| Can final confirmation be only once in Step 3? | **Yes** — backend already designed around `internal_draft_quote_confirmed`; UX must stop row-level operator confirm. |
| Most misleading warning? | **RETURN_CANT_* / verify cant** when Alb·60mm is already persisted. |
| Strongest truth source? | **`finish_setup` persisted payload** (values). |
| Weakest/wrong truth source? | **`product_truth.components.return_cant.confirmation_state`** stub always blocked. |
| Fix first? | **DEC-CDRC-01 + DEC-CDRC-02** — stop false RETURN_CANT + row confirm duplication (before re-expanding Step 3 nav). |

---

## Next safe implementation slice

**Slice:** *Return/cant readiness alignment v1* — When `finish_setup.confirmed=true` and letter group has `return_depth_mm` + active `return_finish_type`, treat return/cant readonly mapper as **ready** for operator diagnostics; keep component `confirmation_state` internal; stop surfacing `RETURN_CANT_COMPONENT_CONFIRMATION_MISSING` as operator blocker. No change to pricing. Pair with removing row-level pending count from review header (read-only derive).

Do **not** start with hiding warnings in UI without bridge/mapper logic change.

---

## Forbidden scope confirmed

No frontend/backend/DB/product/pricing/Quote/Order/Execution/SVG/selected_layer_refs implementation in this task.

---

## Delivery footer

| Field | Value |
|-------|-------|
| Task | INTAKE_V6_CONFIGURATION_DEFAULTS_READINESS_CONFIRMATION_AUDIT_V1 |
| Verdict | **PARALLEL_TRUTH_CONFIRMED** |
| Accepted HEAD | 58370b1 |
| Three steps preserved | **NO at repo HEAD (5208f05)** — YES at accepted HEAD |
| Final confirmation only in Step 3 | **TARGET CONFIRMED** (backend); **VIOLATED at HEAD UX** |
| Runtime verified | Capture yes; live API no (503) |
| 60 mm selection verified | **YES (persisted)** |
| Print + laminare verified | **YES (persisted)** |
| False-positive warnings | RETURN_CANT_*, row unconfirmed, misplaced confirm CTA |
| Duplicate confirmation flags | Yes (≥3 layers) |
| Parallel truths | Yes (documented) |
| Blocking logic defects | F-BLD-01 |
| Tests | 27 backend pass; 29/31 frontend pass |
| Application code changed | NO |
| Database rows changed | 0 |
| Worklog | this file |
| Ready for owner implementation decision | **YES** |
| Cat sunt in directia stabilita | **38/100** (codebase vs owner model) |
| Roadmap awareness | **9/10** |

---

## Commit

Suggested: `Audit Intake V6 confirmation logic`
