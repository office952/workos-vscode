# Audit — Intake V6 Step 1 SVG role ↔ Product System templates

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| GO | `GO_INTAKE_V6_STEP_1_SVG_ROLE_AND_PRODUCT_SYSTEM_TEMPLATE_AUDIT_ONLY` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `bc68c1b` |
| Start | `INTAKE_V6_SVG_TEMPLATE_MAPPING_AUDIT_IN_PROGRESS` |
| Verdict | **`PRODUCT_SYSTEM_FIRST_REQUIRED`** |
| App edits | **None** |
| Commit | **None** |

## Mini decizia mea (confirmed by code)

```text
1. Audit Product System templates for vector roles
2. Audit Intake V6 Step 1 assignment
3. Stabilize missing contract: Vector litere / Vector logo / Vector fundal·ACP
4. Only then: complete Product System exposure → connect SVG Analyzer selection
```

Do **not** start from “detect rectangle → save Alucobond” as the sole path. Mature system first.

---

## Executive verdict

Step 1 (“Straturi”) works visually for **letters vs logo**, but semantics are **not** “operator picks a Product Template for a vector.” Reality:

```text
SVG layer
→ production role (hardcoded FE: face | printed_artwork)
→ selected_layer_refs (vector_litere | vector_logo)
→ composition recommendation (TPL-VOLUMETRIC-LETTERS_v2 | TPL-VOLUMETRIC-LOGO_v1)
```

ACP / Alucobond is a **second, parallel system**:

```text
closed contour candidate
→ ContourRoleOption (hardcoded FE)
→ intended svg_support_selection + mounting_solution
→ BE FinishSetup DROPS svg_support_selection
→ mounting_solution (TPL-ACM-BOXED-MOUNTING-SUPPORT_v1) may persist
```

Product System **already has** Alucobond support (`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` + process `ALUCOBOND_CASED_PANEL`), but Intake Step 1 does **not** expose PS components as the option list. Latent layer role `support_panel` still recommends stale **`TPL-BOND-CASETAT`** (`pending_template`).

**Therefore: Product System–first alignment of the vector→component contract is required before more Intake ACP UI work.**

---

## 1. Baseline

| Item | Value |
|------|-------|
| Repo | `C:/w/psiso` |
| HEAD | `bc68c1b` (after closed-contour Alucobond commits `223aba4` + worklog) |
| FE / BE | `http://127.0.0.1:3000` / `:8001` — both HTTP 200 |
| Fixture | `C:\Users\offic\Desktop\fisiere-teste-svg\LITERE-VOLUMETRICE-ACP.svg` |
| SHA-256 | `afce1e6f07ffb9db1ec328aa53898dc76e2b6c461429a5a5605de0b3430d85ba` |
| Dirty tree | Unrelated WIP left untouched; **no** app edits for this audit |

---

## 2. Product System inventory (audited first)

### Product Template — letters

| Cod | Status | Authority |
|-----|--------|-----------|
| `TPL-VOLUMETRIC-LETTERS_v2` | Active Work Intake root | `template_usage_mode_policy`, `seed_active_template_scope` |
| `TPL-VOLUMETRIC-LETTERS` | Legacy alias only | `template_architecture_scope` |

### Component / process composition (letters)

| Cod | Tip | Optional | Notes |
|-----|-----|----------|-------|
| `FACE` / `CANT` / `BACK` / `LIGHTING` | Process components | Core / lighting when illuminated | `volumetric_letters_v1.py` |
| `METAL_SUPPORT` | Process + `TPL-METAL-PREMOUNT-STRUCTURE_v1` | XOR support | Bars path |
| `ALUCOBOND_CASED_PANEL` | Process component | XOR support when `support_type=alucobond_cased` | Not a PS “vector” template |
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | PS linked child template | Optional addon via `mounting_solution` | Canonical ACM support |
| `TPL-VOLUMETRIC-FACE_v1` … `LED` / finish | PS component templates | Component-only | Naming ≠ process codes |
| `TPL-VOLUMETRIC-LOGO_v1` | Candidate product | Not root-offerable | Linked segment only |
| `TPL-ACM-CASSETTED-PANEL` | Archived / candidate | Not mounting allow-list | Easy to confuse |
| `TPL-BOND-CASETAT` | Composition **pending** placeholder | Dead/stale vs ACM boxed | Used if `support_panel` layer role present |
| `TPL-COMP-LETTER-*` | Inert component-first | `active: False` | Parallel taxonomy |

### Alucobond field readiness (PS / mounting)

| Field | In ACM configuration / process? | Via closed-contour build? |
|-------|----------------------------------|---------------------------|
| Panel W/H | Yes (`panel_width_mm` / `height`) | Yes (mapped) |
| `return_depth_mm` / L1 | Yes | Yes (`l1_mm` → return depth) |
| `rear_lip_mm` / L2 | Yes | Yes |
| `fold_count` | Extended in mounting normalize | Yes |
| Service corner | Process requires `power_supply_service_corner` | Partial (finish field; not always in ACM config) |
| `svg_support_element_id` | Passthrough in mounting config | Yes (FE); **typed selection dropped by BE schema** |
| Internal frame | `frame_clearance_mm` / boolean | Yes |

**No Product System “vector” component exists.** “Vector Litere / Vector Logo” are Intake owner labels for SVG production roles.

### Master PS table

| Concept | Cod | Tip | Status | Authority | Folosit runtime | Probleme |
|---------|-----|-----|--------|-----------|-----------------|----------|
| Letters product | `TPL-VOLUMETRIC-LETTERS_v2` | Product Template | Active | scope + form | Yes | Legacy alias/dossier |
| Logo product | `TPL-VOLUMETRIC-LOGO_v1` | Product Template | Candidate | usage policy | Suggestion only | Not offerable root |
| Alucobond process | `ALUCOBOND_CASED_PANEL` | Process component | Active when typed support | `volumetric_letters_v1` | Resolver | Dual naming vs ACM tpl |
| Alucobond PS | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | Product Template (child) | Seeded linked | mounting allow-list | Via `mounting_solution` | Not Step 1 option source |
| Stale support rec | `TPL-BOND-CASETAT` | Pending placeholder | Composition only | recommendation service | If `support_panel` role | **Duplicate SoT vs ACM** |
| SVG contour role | `ALUCOBOND_CASED_PANEL` | Contour role | FE V1 | closed-contour | Partial persist | Schema drop |
| Vector (PS) | — | — | Absent | — | N/A | Labels only in Intake |

---

## 3. What “Vector litere / Vector logo” really are

| Label UI | Cod intern | Ce reprezintă real | Sursa | Salvat unde | Consumator |
|----------|------------|--------------------|-------|-------------|------------|
| Vector Litere | `face` | SVG **production role** (letters face geometry), **not** a Product Template | Hardcoded FE `INTAKE_V6_OWNER_LAYER_ROLE_OPTIONS` | `layer_role_setup` + `selected_layer_refs.role=vector_litere` | Composition → `TPL-VOLUMETRIC-LETTERS_v2` |
| Vector Logo | `printed_artwork` (`logo` normalized) | SVG **production role** for artwork/logo | Same FE list | `vector_logo` | Composition → `TPL-VOLUMETRIC-LOGO_v1` (candidate) |
| Fundal / suport / bond / caseta | `support_panel` | Latent full catalog role | `intakeV4LayerRoleOptions` | Would → pending `TPL-BOND-CASETAT` | **Not in Step 1 owner dropdown** |
| Panou Alucobond casetat | `ALUCOBOND_CASED_PANEL` | Contour **role** → ACM mounting | Alucobond panel FE | Intended `svg_support_selection` + `mounting_solution` | PD / mounting; selection schema gap |

**Answer:** `Vector Litere` is an **SVG role label** mapped (hardcoded) to Product Template recommendation. It is **not** a Component Template and **not** a Product Template identity.

---

## 4. Intake V6 Step 1 — runtime controls

| Control UI | Input | Optiuni | Sursa optiuni | Output | Persistenta | Verdict |
|------------|-------|---------|---------------|--------|-------------|---------|
| Layer role `<select>` | Layer (`layer.id` \| name) | Vector Litere, Vector Logo | **Hardcoded FE** | `face` / `printed_artwork` | `PUT …/analysis-bundle` → `layer_role_setup` | Active owner path |
| Confirmă toate sugestiile | Pending layers | Analyzer autoRole | FE `guessLayerAutoRole` | Same | analysis-bundle | Active |
| Target badge | Layer + role | Display only | FE `resolveIntakeV6LayerTargetTemplate` | Template code string | None (display) | Not authority |
| Closed-contour list | Contour candidates | Geometry-ranked | FE analyzer | `contour_id` | Local until confirm | Active propose |
| Contour role | Selected contour | 5 RO options | Hardcoded FE | ContourRoleOption | finish-setup (partial) | Dual flow |
| Casing fields | After Alucobond role | fold/L1/L2/corner/frame | Hardcoded FE | mounting config | `mounting_solution` persists | Typed selection lost on BE |
| Product composition | From layer roles | Template items | BE recommendation | Composition confirm | Separate endpoint | Letters/logo only for owner UI |

**Options are not Product-System-backed.** `getIntakeV6RoleOptionsForLayer` exists but Step 1 table does **not** use it for the select (owner two-option list only).

Route: `/intake-v6/:workspaceId/operator` · step `layers` · Component: `IntakeV6SvgAnalyzerStep`.

---

## 5. Layer vs element vs component

| Concept | Runtime meaning |
|---------|-----------------|
| SVG layer | Analyzer aggregate (often Corel `<g>`); Step 1 role unit |
| SVG element | Parsed drawable (`el-N` or SVG `id`); not assigned layer roles |
| Closed contour | Geometry candidate (`cc_<hash>`); Alucobond unit |
| Component instance | Created later via composition / mounting / process — **not** at role click |
| Component Template | PS `TPL-*` / process codes — **not** the Step 1 dropdown |

### Answers (fixture-aware)

1. Operator assigns roles to **layers** (not individual letter paths) in the main table.
2. If one layer contains letters + chenar, roles **cannot** be split — whole layer gets one role.
3. Letters are grouped by analyzer layers / parts; not one-role-per-glyph in Step 1.
4. Logo: name/kind heuristics → `printed_artwork`; owner may override.
5. Background: latent `support_panel` **or** new closed-contour path — **two systems**.
6. Outer contour → should become support **component input**, not Product Template; today closed-contour → mounting child.
7. Component instance: composition confirm / mounting_solution / process resolve — after Step 1.
8. Mixed layer → wrong product recommendation risk.
9. Flat SVG (no clean layers): synthetic layers / colors; still layer-scoped roles.
10. Element-only identity: closed-contour path only; not unified with layer roles.

---

## 6. Real fixture proof (no file mutation)

| Item | Result |
|------|--------|
| Exists | Yes |
| SHA | `afce1e6f…` unchanged |
| Structure | 1 group, 2 paths (letter subpaths), 1 stroke polygon (panel) |
| Closed contours | 21 |
| Top panel candidate | polygon `cc_60db6024`, contains 15, outer |
| Layer roles ACP option | **Not** in owner dropdown |
| Closed-contour Alucobond | Present as separate panel |
| Dual systems | **Yes** |

Machine metrics: `docs/audits/_runtime_fixture_proof.json`.  
Click-path screenshots on seeded workspace: **GUARDED** (no write/seed in audit-only GO). FE/BE up; analyzer proof via vitest.

---

## 7. Dual-flow assessment (critical)

| Aspect | Flow A — layer roles | Flow B — closed-contour |
|--------|----------------------|-------------------------|
| Unit | Layer | Contour / element |
| Persist | `layer_role_setup` | Intended `svg_support_selection` (**dropped**) + `mounting_solution` |
| Support code | Pending `TPL-BOND-CASETAT` if `support_panel` | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Owner Step 1 | Letters/Logo only | Separate Alucobond panel |
| Integrated? | **No** — parallel |
| Duplicate SoT risk | **Yes** — stale bond vs ACM boxed |

---

## 8. ProductDefinition path

```text
Layer role confirm
→ layer_role_setup + selected_layer_refs
→ composition recommendation (letters/logo templates)
→ (later) ProductDefinition composition / canonical bindings

Closed-contour Alucobond confirm
→ finish_setup.mounting_solution (persists)
→ finish_setup.svg_support_selection (FE sends; BE schema strips)
→ PD builder projects casing only if selection present in raw finish dict
→ support_type=alucobond_cased when projected
```

**Gap:** typed selection authority does not survive FinishSetup validation → reload/PD can lose contour identity even if mounting remains.

---

## 9. Variant evaluation (ACP label) — recommend one

| Variant | Clarity | Authority | Scale | Material-independent | PS fit | Verdict |
|---------|---------|-----------|-------|----------------------|--------|---------|
| A Vector fundal | Medium | Role only | High | Yes | Needs second pick | Partial |
| B Vector ACP | Low (material in role) | Blurs | Low | No | Bad | Reject |
| C Panou Alucobond casetat | High for this product | Component-tied | Medium | No | Matches current contour UI | OK for confirm step |
| D Contur suport | High geometric | Role | High | Yes | Needs component pick | Strong |
| **E PS active components** | Highest | PS authority | Highest | Yes | Best | **Recommended** |

**Recommended architecture (Variant E + D):**

```text
Product Template (letters) active
→ Product System exposes assignable components (incl. optional Alucobond support)
→ Operator selects SVG unit (layer and/or closed contour)
→ Associates to that component instance
→ Confirms component-specific config (casing only if Alucobond active)
→ ProductDefinition stores instances + geometry refs
```

Owner-facing label for the geometry step: **Contur suport** (or keep layer “Fundal / suport” as geometric role).  
Owner-facing label for the component: **Panou Alucobond casetat** (`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` / process `ALUCOBOND_CASED_PANEL`).  
Do **not** invent Product Template `Vector ACP`.

---

## 10. Option source authority

| Model | Current? | Recommended? |
|-------|----------|--------------|
| A Hardcoded Intake | **Yes (Step 1)** | No as final |
| B Separate SVG role registry | Partial (layerRoleTypes + V4 options) | Roles geometric only |
| C PS active components | **No** | **Yes for assignable targets** |
| D Controlled combo | Partial latent helpers | **Yes** — geometric role + PS component |

---

## 11. Inactive isolation

| Case | Today |
|------|-------|
| No Alucobond confirm | PD builder: no casing leakage from non-confirmed roles |
| Owner Step 1 without support role | No ACP required in layer dropdown |
| PS without mounting_solution | Process support none / metal / alucobond from typed fields |
| Optional support activation **before** geometry assign | **Not** implemented as PS-driven Step 1 gating |

Direction needed: component inactive ⇒ zero ACP options/fields/blockers. Partially true for PD casing; **not** true as PS-driven UI.

---

## 12. Tests run (audit only)

| Suite | Result |
|-------|--------|
| `intakeV6LayerRoleOptions.test.ts` | 6 PASS |
| `closedContourCandidates.test.ts` | 6 PASS |
| `IntakeV6SvgAnalyzerStep.test.tsx` | 11 PASS |
| FinishSetup schema probe (Python) | Confirms `svg_support_selection` dropped |
| Broader svgAnalyzer / full BE | Not used as gate; known pre-existing noise |

Coverage gaps: no E2E that asserts layer role + contour role unified; no test that FinishSetup must keep `svg_support_selection`.

---

## 13. Dead pieces (report only — no cleanup)

- Hardcoded `INTAKE_V6_OWNER_LAYER_ROLE_OPTIONS` (2 items)
- Latent full catalogs unused by Step 1 select
- `getIntakeV6RoleOptionsForLayer` unused by role table
- `support_panel` → `TPL-BOND-CASETAT` pending vs live ACM boxed
- Dual Alucobond UI vs layer fundal role
- FE `svg_support_selection` without BE schema field
- `TPL-ACM-CASSETTED-PANEL` naming confusion
- Inert `TPL-COMP-LETTER-*`
- Raw template codes in owner “Țintă automată” badges

---

## 14. Recommended implementation order (no impl now)

```text
1. Product System: publish assignable SVG-bindable components for letters root
   (retire TPL-BOND-CASETAT pending; ACM boxed is authority)
2. Unify dual flows: one assignment model (geometry unit → component)
3. Persist typed selection (FinishSetup schema) — separate small GO
4. Intake Step 1: component-aware options from PS (not hardcoded ACP list)
5. Owner runtime validation on real ACP SVG
6. Later: process/material/CPP (not this track)
```

**First build (proposed):** Option 1 — Product System vector-component template alignment.

---

## 15. Owner gates (summary)

See `docs/plans/2026-07-17_intake_svg_template_mapping_owner_gates.md`.

Recommended config: select **layer and/or closed contour** as geometry unit; choice means **component association** (after geometric role); options from **Product System**; label **Contur suport → Panou Alucobond casetat**; activate component **before** or **with** association; V1 single support; **unify** closed-contour into same flow; PD via component instance + mounting_solution; **Product System first = yes**.
