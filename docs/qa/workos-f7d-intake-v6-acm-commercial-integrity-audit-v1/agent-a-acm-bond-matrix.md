# Agent A — ACM / Bond (Alucobond casetat) Input Matrix

Scope: every input specific to the ACM boxed-mounting support panel (`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`), exercised live against `test-bond-litere.svg` in workspace `5a5ce742-f50f-47b0-985b-32cc6f2fb6a4`. Cross-reference: full generic field inventory lives in [`agent-a-field-ledger.md`](./agent-a-field-ledger.md).

## 0. The single biggest finding: does the ACM panel actually enter the quote?

This has to be answered before any per-field row makes sense, because it changes what "commercial effect" means for every field below.

| Evidence | Says |
|---|---|
| Step 1 footer warning (both before and after confirming layer roles) | `Strat „Alucobond_x0020_Casetat” (ACM/casetat) — standby, nu intră în quote litere volumetrice.` |
| Step 1 "Compoziție produs" card | Chip text **"Inclus în propunere"** on the Alucobond casetat card |
| API payload `product_composition_confirmed` (captured after full confirmation) | `"applied_content": "letters"` and the ACM item carries `"status": "available_optional"` (the letters item carries no such status) |
| Step 2, right-rail "Ofertă client" | Shows `Panou Alucobond 86,77 EUR` **as a live line item inside the 2.288,75 RON total**, with 6 sub-lines fully broken out (see §3) |
| Step 3 final recap ("Recapitulare") | Only ever mentions the letters product; the ACM panel is **not listed anywhere** in the last screen before pricing the offer |

**Conclusion (P0, commercial-honesty risk):** the system is internally consistent about the ACM panel being **optional and currently in "available/standby" status** — but three different UI surfaces describe that same state three different ways ("standby, not in quote" / "included in proposal" / silently priced into the visible total with no recap mention). An operator who only reads the composition card and the final total would reasonably conclude the ACM panel **is** committed and priced; an operator who reads the step-1 footer warning would reasonably conclude the opposite. Both readings currently coexist in the same workspace state. This is squarely a commercial-integrity finding and is flagged for Lead / Agent B cross-check since it touches priced-total honesty, not just wording.

---

## 1. Layer/role decision (upstream of all ACM fields)

| Input | Necessity | Timing | Duplication | Default safety | Product effect | Material effect | Labor effect | Commercial effect | Total effect | Persist | Reverse | Terminology |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `Rol geometrie = "Contur suport"` on the black-contour layer | Required to create the ACM component at all | Step 1 | Single entry point (per-layer dropdown) | AI-proposed correctly for this fixture (SVG layer named `Alucobond_x0020_Casetat`) | Creates `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` component instance | n/a at this stage | n/a | n/a until composition confirmed | n/a | `layer_role_setup.layer_bindings[]` | Re-selecting a different role after confirm was not tested this session (out of time; flagged as untested, not confirmed-safe) | "Contur suport" (support contour) is clear operator language; the underlying enum value `support_panel` is never shown, which is correct information hiding |
| Layer-role confirm ("Confirmă") | Required (blocker) | Step 1 | One button per layer + one "confirm all" | n/a | Flips `role_status → confirmed` | n/a | n/a | n/a | n/a | payload | Not tested | Plain Romanian, good |
| Product-composition confirm | Required (blocker) | Step 1 | One "Confirmă" button for the whole composition card (both components at once — not per-component) | Composition auto-includes ACM as `available_optional`, does **not** default it into `applied_content` | See §0 | n/a | n/a | n/a | n/a | `product_composition_confirmed` | Not tested | "Confirmă" is undifferentiated — a single click confirms both the mandatory letters item and the optional ACM item together, so an operator cannot confirm one without the other from this control |

---

## 2. Geometry (auto-derived from SVG, operator-confirmable)

| Input | Necessity | Timing | Duplication | Default safety | Product effect | Material effect | Labor effect | Commercial effect | Total effect | Persist | Reverse | Terminology |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lățime (mm) | Required | Step 2, Panou/carcasă | Also implicitly re-derivable from an optional DXF upload (not tested) | Safe — taken directly from the SVG contour bbox (`2000.001`) | Panel size = cut area | Drives ACM sheet material qty | Drives cutting labor (ml) | Feeds "Debitare panou ACM" + "Material ACM față panou" lines | Yes | `acm_panel_instance.geometry.width_mm` | Editable free-text; not tested for out-of-range values (e.g. negative/zero) | "Lățime (mm)" is plain, but the `.001` mm precision surfaced from the SVG (`2000.001` instead of `2000`) is float-noise leaking into an operator-facing number field — cosmetic but slightly untrustworthy-looking |
| Înălțime (mm) | Required | same | same | Safe — from SVG (`500`) | same | same | same | same | Yes | `acm_panel_instance.geometry.height_mm` | same | none |
| Segmente (panel split) | Optional | Step 2 | n/a | Default: 1 segment = whole panel | Would create multiple panel line items if split | Would multiply material lines | Would multiply cutting/assembly lines | Would multiply the whole §3 cost block | n/a | `geometry.panels[]` | **Not exercised** — this fixture's panel is a single rectangle, so the multi-segment path (relevant for large ACM backgrounds that must ship in pieces) was not tested | n/a |
| DXF measured upload | Optional | Step 2 | Same decision-space as the SVG-derived geometry above ("Cantitățile CUT/V vin din deducere comercială; DXF măsurat e opțional" — explicit UI text) | Absent by default; geometry falls back to SVG-derived (commercial deduction) quantities | Would override the SVG-derived contour with atelier-measured DXF | Would override quantities in §3 | same | same | same | Separate endpoint `POST .../acm-panel/production-geometry/dxf` | **Not exercised** — same native file-picker limitation as the primary SVG upload; not testable through this MCP browser session | The UI is explicit and honest that CUT/V quantities are a *commercial deduction*, not a measured production fact, until DXF is attached — good honesty pattern |

---

## 3. Construction (Pliuri / L1 / L2 / Grosime) — the "5 blockers" set

These five fields are the ones the app itself calls out as **blockers** immediately after layer-role confirmation ("Propunere din catalog — selectează / confirmă în Construcție") — i.e. the system knows these are catalog guesses, not operator truth, until "Confirmă panoul Alucobond" is clicked.

| Input | Necessity | Timing | Duplication | Default safety | Product effect | Material effect | Labor effect | Commercial effect | Total effect | Persist | Reverse | Terminology |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Pliuri (fold count) | Required (blocker) | Step 2 | Single control | Catalog default = 2 pliuri (reasonable given `Alucobond casetat` = boxed/returned edges) | Determines box vs flat-return construction | Determines cant/return ACM material qty (`Material ACM canturi/întoarceri`) | Determines return-forming labor | Yes | Yes | `configuration.fold_count` | Editable (1 or 2); not tested for the 1-pliu path in this session | "Pliuri" (folds) is workshop-native language, good |
| Grosime ACM (mm) | Required (blocker) | Step 2 | Single control | Catalog default = 3mm | ACM sheet spec | Directly proportional to `Material ACM față panou` (15,00 EUR line) | n/a directly | Yes | Yes | `configuration.acm_thickness_mm` | Editable free-text; no client-side min/max observed | none |
| Prima întoarcere (L1, mm) | Required (blocker) | Step 2 | Single control | Catalog default = 60mm | Return depth (front fold) | Feeds cant material | Feeds return-bending labor | Yes | Yes | `configuration.l1_mm` | Editable; not range-tested | none |
| A doua întoarcere (L2, mm) | Required only when "2 pliuri" | Step 2 | Single control, conditionally shown | Catalog default = 25mm | Second return depth | same | same | Yes | Yes | `configuration.l2_mm` | Editable; not range-tested | none |
| Adâncime casetă (computed: `finished_depth_mm`) | Derived, not directly editable as its own input in this UI pass — surfaced as one of the 5 catalog-proposal blockers but the live UI showed it resolved through L1/L2 rather than a separate control | Step 2 | n/a | 60mm (= L1) once confirmed | Overall box depth | n/a directly | n/a directly | n/a directly | n/a | `configuration.finished_depth_mm` | n/a | The blocker list names it as if it were a 6th independent input ("Adâncime casetă: Propunere din catalog…") but no separate "Adâncime casetă" form field was found in the live inspector — it appears to be *computed from* L1/L2 rather than *set alongside* them. **Possible ledger/UI mismatch (P3, needs a second pass with a taller-box fixture to confirm whether an independent control exists for asymmetric setups).** |

**Duplication across the 5 blockers:** all five are listed twice on screen simultaneously before confirmation — once in the top-of-tab "Blocante" list (`Validare panou`) and again as the actual live form fields further down the same tab. This is not wrong (the blocker list is a navigable table of contents), but it does mean the same 5 facts are read twice before the operator can act on them once.

**Confirm action:** "Confirmă panoul Alucobond" commits geometry + construction + finish **together, in one action** (explicit UI copy: "Geometrie, construcție și finisaj — o singură acțiune"). This is a genuinely good pattern — it prevents a half-confirmed panel state — but it also means an operator cannot confirm "just the thickness" while leaving folds pending; all-or-nothing.

---

## 4. Material & finish (foil / screw painting)

| Input | Necessity | Timing | Duplication | Default safety | Product effect | Material effect | Labor effect | Commercial effect | Total effect | Persist | Reverse | Terminology |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cum aplici folia (foil strategy) | Required | Step 2 | Single control | Default = "Fără colant" (no vinyl wrap) | Determines whether a vinyl-wrap labor/material line would appear (none appeared in this fixture — consistent with "Fără colant") | Would add vinyl roll consumption if "După cadru" chosen | Would add wrap-application labor | Would add a line to §3's list | Not tested — this fixture stayed on the "none" branch | `shell_finish.foil_strategy`, `shell_finish.apply_after_frame` | Editable | "Fără colant" (no adhesive vinyl) is plain language |
| Vopsire șuruburi (screw painting, tied to the same control) | Implicit — auto text "Fără colant · vopsire șuruburi" | Step 2 | Coupled to the foil-strategy control rather than its own toggle | Default: screws painted to match plate when no foil | Cosmetic/labor | Minor material (paint) | Minor labor | Included in "Șuruburi / prinderi standard ACM" line (5,00 EUR) | Yes, bundled | `shell_finish.paint_screws_if_no_foil` | Not independently editable in this UI (derived from foil choice) | Also flagged by the raw warning: `canonical_unresolved_warning:PROCESS_MAP_DEFAULT_SCREW_FINISH_NATURAL: default_screw_finish_NATURAL` — the system itself is unsure this default is confirmed, but the UI presents it as settled fact ("Fără colant · vopsire șuruburi") with no visible "unresolved" affordance next to it |

---

## 5. Structure & mounting

| Input | Necessity | Timing | Duplication | Default safety | Product effect | Material effect | Labor effect | Commercial effect | Total effect | Persist | Reverse | Terminology |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cadru interior (internal frame) | Shown as always-on for this template shape | Step 2 | Single checkbox, **readonly** | On by default, cannot be unchecked in this UI state | Structural | Adds internal frame material (not separately broken out as its own €-line in the 6 visible lines — likely folded into "Asamblare suport ACM casetat" 20,00 EUR) | Adds assembly labor | Bundled | Bundled | `configuration.internal_frame_enabled` | Not editable here | Paired with contradictory-feeling caption "Nicio relație de montaj confirmată." right under a checkbox that shows as already checked — reads as "this is set" and "nothing is confirmed" at the same time. **UX finding (P2).** |
| Tip sistem (wall-fixing bracket) | Optional, technical (not commercial scope) | Step 2, "Avansat" (collapsed by default) | Distinct from "Montaj comercial" scope (explicitly documented in-UI as separate) | `— neconfigurat —` (unset) | Would add a physical wall-mount bracket spec | Would add bracket material | Would add fixing labor | Not currently priced (unset) | n/a | `mounting_fixing_system` | Editable, only 2 real options total (unset / vertical steel bracket) | This is exactly the field named in the raw warning `TRIGGER_FIELD_MISMATCH: structura_suport link=metal_support_required intake=finish_setup.mounting_system` — the app is telling QA/devs (via an operator-visible warning) that this technical field and the commercial "montaj" module may be wired to mismatched trigger names. This is a real integration-honesty finding, just expressed in code-identifier language instead of operator language |
| Colț service transformator | Optional | Step 2, appears **twice**: once in "Avansat" (`Colt service transformator` combobox) and once in the "Alimentare și service" ACM sub-block on the same tab | **Duplicated control for the same decision, both live on the Panou/carcasă tab** | `— selectează —` (unset) | Determines transformer/PSU corner placement for a single-panel job | n/a | Minor labor (routing) | Not priced as its own line in the visible 6 | n/a | `power_supply_service_corner` | Editable | 5 real options + "Confirmat manual" escape hatch — reasonable option set, but two entry points for one decision is a real duplication finding (P2) |
| Module produs (Volum aluminiu modular) | Not really a decision — single-option select | Step 2, "Avansat" | n/a | Pre-selected, only option available | Links to a parent aluminum-volume module template | n/a | n/a | n/a | n/a | `volum_aluminum_module_template_code` | n/a | A combobox with exactly one option is UI theatre — should be static text, not an interactive field, per general "don't make operators click through non-decisions" principle |

---

## 6. Commercial priced lines (right-rail "Detalii panou (6)")

Captured live, sum verified: **8,52 + 31,44 + 15,00 + 6,81 + 20,00 + 5,00 = 86,77 EUR**, matching the "Panou Alucobond 86,77 EUR" rollup exactly.

| Line | EUR | Necessity | Duplication | Default safety | Commercial effect | Reverse |
|---|---|---|---|---|---|---|
| Debitare panou ACM | 8,52 | Automatic (from geometry) | n/a | Computed, not operator-set | Cutting labor charge | n/a — recomputes live as geometry/construction changes |
| Frezare V-groove ACM | 31,44 | Automatic (from fold count × perimeter) | n/a | Computed | V-groove milling labor — **the single largest ACM line item**, ~36% of the ACM subtotal | same |
| Material ACM față panou | 15,00 | Automatic (from area × thickness) | n/a | Computed | Face sheet material | same |
| Material ACM canturi / întoarceri | 6,81 | Automatic (from L1/L2 × perimeter) | n/a | Computed | Return/edge material | same |
| Asamblare suport ACM casetat | 20,00 | Automatic (flat-ish assembly charge) | n/a | Computed | Assembly labor (internal frame + boxing) | same |
| Șuruburi / prinderi standard ACM | 5,00 | Automatic | n/a | Computed | Fasteners | same |

**Observation:** every one of these 6 lines is currently a **derived/system value with no operator override control found in this tab** — the only operator inputs that feed them are the geometry + construction + finish fields in §2–§4 above. This is architecturally clean (no shadow price overrides hidden in the ACM panel itself; all commercial overrides are centralized in the "Ajustări comerciale" block described in the field ledger), but it also means an operator cannot correct a single mispriced ACM line without either fixing an upstream technical field or using the blunt global "Ajustare manuală (RON)" control.

---

## 7. Terminology inventory (ACM/Bond specific)

| Term seen in UI | Where | Consistency |
|---|---|---|
| "Alucobond casetat" | Composition card, panel header, recap (absent from recap, see §0) | Consistent |
| "Panou Alucobond" | Right-rail price line, tab config header | Consistent with "Alucobond casetat" — same entity, different noun form, acceptable |
| "ACM" | Warning strings, price-line names ("Debitare panou ACM") | Only used in machine-facing strings, never as the primary operator-facing noun (operator always sees "Alucobond") — consistent, good separation of internal SKU-style naming vs operator language |
| "Contur suport" (layer role) | Step 1 role dropdown | Consistent, operator-friendly |
| "TPL-BOND-CASETAT ... legacy/deprecated" vs "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 ... authority live" | Step 1 "Detalii tehnice compoziție" | **Both template codes are shown to the operator in the same sentence**, one flagged legacy. This is honest but exposes template-migration internals that an operator has no way to act on — arguably belongs in a diagnostics/QA surface, not the main confirm flow |
| "Bond" | Not found anywhere as a standalone operator-facing word — always "Alucobond" or "ACM" | The mission brief's own shorthand ("ACM/Bond") does not correspond to any single UI term; operators would search for "Alucobond", not "Bond" |

---

## 8. Summary verdict for Agent B / Lead handoff

- **Functionally**, the ACM panel flow works end-to-end for this fixture: upload → detect → confirm role → confirm composition → configure geometry/construction/finish → confirm panel → priced lines appear and stay internally arithmetically consistent (86,77 EUR = sum of 6 lines, verified by hand).
- **Commercially**, the single most important open question is §0: whether "available_optional" + "Inclus în propunere" + "already priced into the visible total" + "absent from the final recap" is an acceptable combination for an Owner-facing draft, or whether it represents a real risk of an operator shipping a priced offer with a panel they believe is *not yet* committed (per the step-1 warning) or, conversely, forgetting the panel exists at all by the time they reach the recap. This should be treated as commercial-integrity-adjacent and cross-checked with Agent B's pricing-authority findings.
- **UX-wise**, the ACM tab is the densest and most information-rich screen in the whole Intake V6 flow (7 nested collapsible sections plus the persistent right rail) and is also where every "leaked internal string" finding in this audit concentrates (raw JSON dump, `canonical_unresolved_warning:*` codes, an "Ownership: MOUNTING → …" developer note). See `agent-a-ux-audit.md` for progressive-disclosure proposals.
