# Worklog — Intake V6 component-aware SVG assignment + FinishSetup durability

| Field | Value |
|-------|-------|
| Task | `INTAKE_V6_COMPONENT_AWARE_SVG_ASSIGNMENT_AND_FINISHSETUP_DURABILITY` |
| Owner GO | explicit |
| Date | 2026-07-17 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `62dc7a7` |
| Start | `INTAKE_V6_COMPONENT_AWARE_SVG_ASSIGNMENT_IN_PROGRESS` |
| Final | `INTAKE_V6_COMPONENT_AWARE_SVG_ASSIGNMENT_COMPLETE_WITH_GUARDS` |

## Stages

1. FinishSetup schema: `svg_support_selection` + `svg_component_bindings`.
2. Persistence service: validate, sync support selection, PD instances.
3. FE: Product System availability → assignment panel; ACP nested under Contur suport.
4. Legacy layer options marked non-authority; no Vector ACP / BOND.
5. Tests: BE persistence/PD + FE bindings + Step 1 regression.

## Key files

- `backend/schemas/intake_v4.py`
- `backend/services/svg_component_binding_persistence.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/services/product_definition_builder_service.py`
- `frontend/.../IntakeV6SvgComponentAssignmentPanel.tsx`
- `frontend/src/lib/intakeV6/svgComponentBindings.ts`

## Next safe step

**Option 1 — OWNER REVIEW OF INTAKE V6 COMPONENT-AWARE SVG ASSIGNMENT**

---

## OWNER VISUAL INTEGRATION REVIEW

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| GO | `OWNER_REVIEW_INTAKE_V6_STEP1_SVG_MODULAR_UI_INTEGRATION` |
| HEAD reviewed | `26eb0c7` |
| Verdict | **`DUAL_UI_FLOW_STILL_VISIBLE`** |
| Dual-flow class | `SINGLE_SOT_BUT_DUPLICATED_UI` |
| Report | `docs/audits/2026-07-17_intake_v6_step1_svg_modular_ui_integration_review.md` |
| App edits | None |
| Commit | None |

### Findings (short)

- Modularitatea Product System există (availability payload live, bindings/PD durable).
- UI Step 1 încă arată flow legacy pe carduri + panou „Asocieri produs” + ACP nested = al doilea sistem vizual.
- Legacy adapter (Vector Litere/Logo) maschează asocierea pe Component Template.
- Contour overlay pe preview e reutilizabil — nu lipsește modularitatea, lipsește unificarea vizuală.

### Recommended next

**Option 2 — GO SMALL INTAKE V6 SVG UI UNIFICATION FIX**  
(carduri existente + Contur suport + progressive ACP; păstrează SoT actual)

---

## SVG UI UNIFICATION

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| GO | `SMALL_INTAKE_V6_SVG_UI_UNIFICATION_FIX` |
| Verdict | **`INTAKE_V6_SVG_UI_UNIFICATION_COMPLETE_WITH_GUARDS`** |
| Audit | `docs/audits/2026-07-17_intake_v6_step1_svg_modular_ui_integration_review.md` § SMALL UI UNIFICATION |
| Screenshots | `docs/audits/screenshots/2026-07-17_intake_v6_svg_ui_unification/` |

### Implementation (UI only)

- Unified layer cards: geometry role + Product System component + status/optional/guard.
- Contur suport card in same grid; ACP progressive disclosure.
- Assignment panel demoted to read-only summary.
- Auto-sync letter/logo `svg_component_bindings` from layer confirmation.
- No Product System / FinishSetup / ProductDefinition / availability API changes.

### Runtime

- FE `:3000` / BE `:8001` live.
- Workspace `IV6-4DD49A26`; ACP fixture upload for support-contour proof.
- No second primary assignment flow; no sync CTA; no Product Template target on cards.

### Next safe step

**Option 1 — OWNER REVIEW OF UNIFIED INTAKE SVG UI**

---

## SVG CARD UX RESTORE

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| GO | `RESTORE_EXISTING_SVG_CARD_UX_WITH_ACP` |
| Verdict | **`EXISTING_SVG_CARD_UX_RESTORED_WITH_ACP`** |
| Screenshots | `docs/audits/screenshots/2026-07-17_intake_v6_svg_card_ux_restore/` |
| Runtime proof | `docs/audits/screenshots/2026-07-17_intake_v6_svg_card_ux_restore/runtime-proof.json` |

### What changed

- `IntakeV6SupportContourGeometryCard` is the canonical layer-like ACP card (`Panou ACP — contur exterior`) in the same grid as Layer verde/portocaliu/logo.
- Removed `IntakeV6SvgComponentAssignmentPanel` from Step 1 (no **Rezumat asocieri** primary UI).
- No permanent Alucobond candidate list; no **Confirmă selecția**; no embedded casing UI; no standalone Contur suport panel.
- Geometry picker stays under **Detalii tehnice → Schimbă geometria** only.
- Composition recommendation reads `svg_component_bindings` / `svg_support_selection` so ACP activates without a `support_panel` layer role.
- Product composition labels use **Panou Alucobond casetat**.

### Runtime (FE `:3000` / BE `:8001`)

| Check | Result |
|-------|--------|
| Workspace | `IV6-4DD49A26` / `9c05851e-3230-4a97-821b-e52293ada844` |
| Fixture | `LITERE-VOLUMETRICE-ACP.svg` |
| No Rezumat asocieri | PASS |
| No permanent candidate list | PASS |
| No standalone Contur suport panel | PASS |
| ACP card in layer grid | PASS |
| Composition includes ACP after association | PASS (`letters_plus_logo_plus_support` / UI label) |

### Tests

| Gate | Result |
|------|--------|
| BE composition + binding | 17 PASS |
| FE SupportContour card + SvgAnalyzerStep + bindings | 17 PASS |

### Next safe step

**Option 1 — OWNER VISUAL ACCEPT OF RESTORED SVG CARD UX**
