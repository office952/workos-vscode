# Intake V6 — Support Role Truth Repair Checkpoint

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD at checkpoint:** `4dede53d8fd220d0773da318f6e7384bdd532048`  
**Audit baseline (exact hash):** `4dede53d8fd220d0773da318f6e7384bdd532048` — `docs(intake-v6): audit layer role and template wiring`  
**Visual pilot accepted:** `f39c260`  
**Acceptance stack:** FE `http://127.0.0.1:3000` · BE `http://127.0.0.1:8003`  
**Mode:** Checkpoint before implementation (no code yet at write time)

---

## 1. Root cause

Client SVG analyzer expands solid fills into `pseudo:fill-*` layers, then `guessLayerAutoRole` short-circuits **every** pseudo layer to `face` / high confidence. On ACM segmented fixtures the grey support panel and red letter fills are therefore both proposed as **Vector Litere**. Correct ACM binding (`SUPPORT_CONTOUR` → `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`) exists only after operator correction + FinishSetup association.

Secondary causes in the same boundary:

- Fresh Contur suport association can fail FinishSetup persistence (operator sees honest error copy, but path is unreliable).
- Server `POST …/svg` populates `path_geometry_summary` + weak `layer_role_setup` but leaves `svg_analysis_json` / `svg_source_text` null → Page 1 client analyzer stays empty.
- Progress `canAccessIntakeV6Step` treats Review and Confirmare identically once analysis is ready.

---

## 2. Why `pseudo:* → face` is unsafe

Pseudo layers are **fill clusters**, not proven letter faces. A large outer panel fill is the common ACM support envelope. Forcing `face` pushes the operator toward confirming the wrong physical role; if left uncorrected, letter template binding attaches to support geometry.

Color is not product truth — the short-circuit is structural (id prefix), which is why grey ACM and red letters share the same false certainty.

---

## 3. Geometry signals available

**Per layer (already computed):** `widthMm`, `heightMm`, `boundingAreaSqm`, `filledAreaSqm`, `subPathCount`, `closedSubPathCount`, `pathElementCount`, `elementCount`, paint evidence.

**Closed contours (already computed after layers):** `area_mm2`, `contains_count`, `contained_area_ratio`, `rectangularity_score`, `is_outer_candidate`, bbox/centroid.

**Missing today for role guess:** sibling relative area / envelope relationship; contour↔layer association at proposal time.

---

## 4. Support candidate evidence (strong)

Propose `support_panel` (still **unconfirmed**) when **all** of:

1. Layer is pseudo (solid-fill cluster) or unnamed solid fill without letter/logo name semantics.
2. Relative envelope: largest (or near-largest) filled/bounding area among production pseudo fills.
3. Composition share high (≈≥35% of total filled/bounding area of sibling production fills) **or** bbox matches an `is_outer_candidate` closed contour.
4. Complexity low vs letter siblings: fewer closed subpaths / elements than at least one sibling face candidate **or** single/few large closed shapes vs multi-glyph sibling.
5. At least one other sibling remains a plausible letter/face geometry (so we are not inventing support on simple single-layer letters).

Display label: Contur suport. Confirmation still required.

---

## 5. Ambiguity cases

| Case | Proposal |
|------|----------|
| Single pseudo fill, multi-glyph letters | `face` (preserve simple letters) |
| Multiple similar-area pseudos, no outer envelope | `unknown` |
| Pseudo with weak area/containment evidence | `unknown` |
| Named ACM/dibond synonyms | existing name path → `support_panel` |
| Clear multi-shape letter fill with sibling outer panel | `face` |

Never force ambiguous geometry to `face`.

---

## 6. Proposal vs confirmation boundary

Detection → **proposal** → operator review → **explicit confirmed role** → binding → ProductDefinition → ProductAggregate.

Repair may change `autoRole` / candidates only. It must not set `confirmationState=confirmed`, must not auto-confirm segmented background or product composition, must not write SUPPORT_CONTOUR without operator Contur suport selection.

---

## 7. Persistence failure trace

Observed UI: `Salvarea Contur suport / ACP a eșuat (FinishSetup)`.

Trace:

1. `handleUpdateLayerRole(role=support_panel)` → `buildAssociatePrimarySupportContourPatch`
2. `persistFinishPatch` → `saveFinishSetup` → `PUT …/finish-setup`
3. Backend `save_finish_setup_for_intake_v6_workspace`: early association allowed when SUPPORT_CONTOUR / support selection present and `confirmed=false`; otherwise `layer_roles_incomplete` 422
4. Preconditions: `layer_role_setup` + svg analysis/source must exist (`early_svg_association_blocked`)
5. Binding validation / segmented coalesce can still 422

Likely fresh-path failure modes to prove/fix:

- FinishSetup fired before analysis-bundle/`layer_role_setup` persisted (race with debounced role persist)
- Auto letter-binding sync race wiping or racing support write
- Stale/`state.error` messaging hiding real 422 detail
- Missing closed-contour candidates on report (separate honest blocker — already coded)

---

## 8. Server / client ingest difference

| Path | What is stored | Page 1 UI |
|------|----------------|-----------|
| Client file chooser | `svg_analysis_json` + `svg_source_text` + roles via analysis-bundle | Pseudo layers + proposals |
| Server `POST …/svg` | `path_geometry_summary` + `layer_role_setup` (often `unknown`); **no** `svg_analysis_json` / `svg_source_text` | Empty upload / no analyzer hydration |

Hydration (`hydrateAnalyzerStateFromPayload`) requires `svg_analysis_json.layerRoleConfirmation` + svg meta — server-only upload never satisfies this.

---

## 9. Smallest selected repair

**Track A:** Replace pseudo short-circuit with evidence-driven classification; add a post-pass using sibling geometry + closed-contour outer evidence (no color rules).

**Track B:** Ensure Contur suport association waits for / ensures analysis + layer_role_setup persistence; surface backend error detail; keep single-write merge for support+letter bindings; prevent duplicate SUPPORT_CONTOUR.

**Track C:** Persist `svg_source_text` on server upload; hydrate bridge: if source text exists without client analysis report, run **existing** client `analyzeSvgString` once and persist analysis-bundle (no second analyzer).

**Track D:** After A–C, gate Confirmare on role confirmation + composition readiness while keeping Review accessible for fixing; do not change final `canSubmit` domain logic.

---

## 10. Rejected alternatives

| Alternative | Why rejected |
|-------------|--------------|
| Color-only “grey = ACM” | Explicitly forbidden; not product truth |
| Fixture filename / Desktop color hardcodes | Non-general, brittle |
| Auto-confirm support / segmented / composition | Violates detection≠confirmation |
| ProductDefinition / Aggregate / registry redesign | Out of GO |
| Broad SVG analyzer rewrite | Overscope |
| Second server analyzer as Page 1 truth | Dual parsers; prefer one FE analyzer bridge |
| Montaj / pricing / DS expansion | Explicitly blocked |

---

## 11. Test matrix

1. Pseudo fill + strong support envelope → propose `support_panel`, not confirmed  
2. Pseudo fill clear letter geometry → `face`  
3. Ambiguous pseudo → `unknown`  
4. Multiple pseudos (ACM+letters)  
5. Support+letters fixture (ACM segmented)  
6. Crossing fixture  
7. Simple letters fixture — no false support  
8. Proposal ≠ confirmation  
9. Support association persistence  
10. Reload persistence  
11. Duplicate association protection  
12. FinishSetup failure copy surfaces real error  
13. Server-upload hydration (source text → client analysis)  
14. Client-upload path unchanged success  
15. No empty Page 1 after valid hydrated upload  
16. Confirmare access if changed  
17. Review remains accessible  
18. Template mapping invariants  
19. No visual pilot regression (scope: no DS files touched)  
20. No Montaj regression (no Montaj files touched)

---

## 12. Rollback boundary

Revert only this repair commit. Does not touch PD/Aggregate, Montaj IA, pricing, DS pilot, migrations, seeds, or foreign WIP. Binding contract constants remain unchanged.

---

## Pre-flight snapshot (checkpoint time)

| Item | Value |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `4dede53d8fd220d0773da318f6e7384bdd532048` |
| Audit commit files | QA pack under `docs/qa/intake-v6-layer-role-template-wiring-audit-2026-07-19/` + worklog + letter-pilot runtime note updates |
| Foreign WIP | Present (availability service, screenshots, segmented runtime JSON, etc.) — untouched |
| FE `:3000` | 200 |
| BE `:8003` | healthy |
| `:3001` | down — not acceptance |

### Exact implementation touchpoints (planned)

| Concern | Primary files |
|---------|----------------|
| Pseudo creation | `semanticAndPseudoLayerExpansion.ts` |
| Role proposal | `guessLayerAutoRole.ts` + post-pass near `analyzeSvg.ts` / `analyzeLayers.ts` |
| Closed contour | `closedContourCandidates.ts` (consume, not redesign) |
| Support associate | `associatePrimarySupportContour.ts`, `IntakeV6SvgAnalyzerStep.tsx` |
| Role persist | `useIntakeV6Workspace.ts`, `intakeV6LayerRoleBridge.ts` |
| FinishSetup BE | `intake_v6_workspace_service.py` (early association only if needed) |
| Server upload | `upload_svg_to_intake_v6_workspace` + hydrate bridge in FE |
| Progress | `intakeV6Readiness.ts` |

**Implementation may begin after this checkpoint is committed to the working tree (uncommitted doc is fine; code follows).**
