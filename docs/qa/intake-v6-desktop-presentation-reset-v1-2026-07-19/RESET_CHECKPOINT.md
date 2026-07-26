# RESET CHECKPOINT — Desktop Presentation Reset V1

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD at checkpoint:** `62308fc0bb8f3b764f22a1ebef8745873b89b481`  
**Functional baseline:** `9f0efa0ce810ec0126ec6b3e1abe5d8d1e675602`  
**Audit pack:** `62308fc`  
**Owner decisions:** D1–D7 accepted · GO granted  
**Mode:** Checkpoint before implementation — frontend presentation only

## Pre-flight

| Item | Value |
|------|--------|
| FE / BE | `:3000` / `:8003` · 200 |
| Staged | empty |
| Foreign WIP | present — untouched |
| Viewport target | 1440×1000 · narrow 1100×900 |

### Component ownership (implementation targets)

| Surface | Component |
|---------|-----------|
| Composition | `IntakeV6ProductCompositionPanel` |
| Blocker banner | `IntakeV6ReviewOperatorBlockerBanner` |
| Footer | `IntakeV6OperatorWorkspaceFooter` |
| Pricing | `IntakeV6LiveCalculationSummary` |
| Iluminare contract | `renderSectionByKey("iluminare")` in ReviewStep |
| Lighting specialized | `IntakeV6ReviewLightingSection` |
| Montaj commercial | `intake-v6-montaj-commercial-cluster` |
| Fundal | `intake-v6-fundal-carcasa-cluster` |
| Confirmare | `IntakeV6FinalConfigurationSummary` + Handoff |
| Diagnostics | accordion `intake-v6-review-technical-details` (+ FormSystem / Promotion / Capture panels) |

Diagnostics already gated by accordion collapse, but still mount and dominate scroll when opened; first paint must not expose their content. Confirmare currently wraps purpose in collapsed “Rezumat configuratie”.

---

## 1. What currently occupies L1

Produs nested cards · full-bleed rose/amber banner · “next step in footer” · scope strip · tab chrome · pricing gate paragraph · contract iluminare fields · Montaj floating template · empty inactive cards · Product System badges/hashes · Confirmare collapsed purpose · multiple status channels.

## 2. What should occupy L1

Product identity + status + confirm CTA · compact attention chip · active-tab primary decisions · calculated results (secondary) · commercial summary · footer next action.

## 3. Remove from operator L1

Footer-hint banner copy · pricing composition-gate essay · adapter/engineering helpers · raw TPL/IDs/hashes · Product System L1 badges · Form System / Promotion / Runtime capture (keep behind Diagnostic tehnic only) · empty inactive Montaj cards · duplicate PSU/Tip iluminare when specialized owns lighting · finish ownership tokens on L1 · Page1 “use footer” detached handoff chrome.

## 4. Move to disclosure / contextual

Registry warnings · finish ownership · LED calc details · Avansat · commercial adjustments · diagnostic panels · excluded scope · template codes.

## 5. Local warnings

Cant incomplete → near Cant · composition → Produs CTA · missing rates → pricing chip only · segmented → Fundal local.

## 6. Duplicate warning surfaces that disappear

Banner “Următorul pas este în footer” · pricing paragraph repeating composition gate · page-level Cant amber when letter-local exists · redundant full-bleed slab weight (becomes compact chip).

## 7. Nested frames that disappear

Finisaje outer SectionShell heavy frame when letter cards suffice · Montaj SectionShell+cardCompact double wrap · empty prep/site bordered empties · Confirmare technical accordion around primary checklist.

## 8. Desktop width

Keep decision + rail grid; start tab decisions above fold; short enums share rows where safe; reduce footer dual-bar visual weight without removing guidance spine.

## 9. Confirmare first paint

Status + blockers + checklist + primary action always visible. Technical modular readiness stays collapsed. Render unused `allFatalBlockers` in handoff when present (same truth source).

## 10. Truth / counts unchanged

No backend · no FinishSetup contract change · no blocker count semantics change · no pricing math · no support-role / Contur suport persistence change · footer still owns next action.

## 11. Before screenshots

From audit pack `docs/qa/intake-v6-desktop-ui-reset-2026-07-19/screenshots/` + fresh capture into this pack `before_*`.

## 12. Acceptance screenshots

After implementation: Finisaje / Cant / Iluminare / Montaj ACM / Fundal / Confirmare / pricing / diagnostic collapsed+expanded / footer / 1440 / 1100 / reload — see SCREENSHOTS.md in this pack.
