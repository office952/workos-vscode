# AUDIT — ACP Internal Frame Existing Contract & Runtime

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Owner GO | `GO_AUDIT_ACP_INTERNAL_FRAME_EXISTING_CONTRACT_AND_RUNTIME_ONLY` |
| Start | `ACP_INTERNAL_FRAME_AUDIT_IN_PROGRESS` |
| **Final verdict** | **`INTERNAL_FRAME_EXISTS_AS_PARTIAL_CONFIGURATION`** |
| HEAD | `525ab979b1ea5e42eea39659d3dc5b97cde1a382` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Scope | Audit only — no app edits, no commit |

---

## Mini decizia mea (owner)

Owner a acordat GO explicit pentru auditul contractului și runtime-ului existente pentru cadrul interior ACP, **înainte** de a crea un Component Template separat.

---

## Executive summary

`internal_frame_enabled` există deja pe calea ACP (SVG Analyzer → `svg_support_selection` → binding/mounting → ProductDefinition canonical), dar este **doar un boolean + clearance numeric hardcodat (`frame_clearance_mm = 5`)**. Nu există material otel/aluminiu, profil, secțiune, traverse, procese, contribuție Aggregate/CPP sau Component Template dedicat. Label-ul Step 2 pentru `frame_clearance_mm` („Luft / clearance cadru”) descrie **spațiu față de cadru**, nu fabricarea cadrului de rigidizare.

---

## Baseline

| Check | Result |
|-------|--------|
| HEAD | `525ab97` — `ci(product-system): prepare template lifecycle validation gate` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Dirty tree | Large unrelated WIP present — **untouched** |
| FE | `http://127.0.0.1:3000` — up |
| BE | `http://127.0.0.1:8001` — up (`/health` 200; `:8000` down) |
| Workspace | `f07058e2-3b40-4935-b55a-6a10b457241b` |
| Template product | `TPL-VOLUMETRIC-LETTERS_v2` + mounting `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |

---

## Search coverage

Terms searched (case-insensitive / near forms): `internal_frame`, `internal_frame_enabled`, `frame_enabled`, `frame_material`, `frame_profile`, `frame_section`, `frame_depth`, `inner_frame`, reinforcement/metal/aluminium/steel frame, `cadru interior`, `cadru metalic`, `rigidizare`, `20x20`, `20x20x1.5`, service corner, casing/support/panel/ACP/ACM frame.

Primary hits for **ACP internal frame**: FE closed-contour + Alucobond panel, BE persistence/PD, mounting `frame_clearance_mm`, SVG binding capability flag `internal_frame: true`.

**Not** the same concept: `TPL-METAL-PREMOUNT-STRUCTURE_v1`, layer role `metal_frame` / „Cadru metalic”, lightbox `frame_profile`, volumetric mounting bars `20x20x1.5`.

---

## Product System table (`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`)

| # | Question | Answer |
|---|----------|--------|
| 1 | `internal_frame_enabled` field? | Yes — on selection/binding/mounting/PD canonical; **not** a dossier child component |
| 2 | Type | **Boolean** (+ derived `frame_clearance_mm` number) |
| 3 | Frame material type? | **No** |
| 4 | Steel/aluminium choice? | **No** |
| 5 | Profile? | **No** |
| 6 | Section? | **No** |
| 7 | Thickness? | **No** (only ACM panel thickness) |
| 8 | Crossbar count? | **No** |
| 9 | Derived frame dims? | **No** (only panel W/H; clearance hardcoded 5 mm) |
| 10 | Rigidization config? | **Partial** — boolean only |
| 11 | Service corner relation? | Parallel field on same selection; **not** coupled to frame |
| 12 | Interface contract for frame? | Capability flag `internal_frame` in SVG binding contract only |
| 13 | Child component? | **No** (`comp_acm_panel_face`, `comp_casetted_returns`, `comp_mounting_fasteners` only) |
| 14 | Optional component? | ACP template is optional addon; frame is optional **flag inside** ACP |
| 15 | Process contribution? | **No** for frame |
| 16 | Material contribution? | **No** for frame |
| 17 | Machine capability? | Process has `ALUCOBOND_PANEL_FABRICATION`; **no** frame-specific capability |
| 18 | Inactive isolation? | Off ⇒ clearance 0 / flag false; no material/process leakage found for frame |
| 19 | Owner-facing UI? | Step 1 checkbox „Cadru interior activ”; Step 2 numeric „Luft / clearance cadru” |
| 20 | Lifecycle readiness? | Capability listed on SVG binding; **no** dedicated lifecycle stage for frame |

### Concept map

| Concept | Exista | Unde | Tip | Authority | Consumator | Gap |
|---------|--------|------|-----|-----------|------------|-----|
| `internal_frame_enabled` | Yes | `svg_support_selection`, binding config, mounting config, PD `canonical_values` | boolean | Operator checkbox (Step 1 Alucobond panel) | PD builder; mounting normalize | No technical model |
| `frame_clearance_mm` | Yes | mounting / ACM quote_input fields | number mm | FE maps enabled→`5`, else `0`; Step 2 editable | ACM quote payload passthrough | Mislabel risk vs metal frame |
| Capability `internal_frame` | Yes | `svg_component_binding_contract.py` | geometry_requirements / capabilities bool | Product System contract registry | Lifecycle inspect surfaces it | Not validated as complete config |
| Frame material (steel/Al) | No | — | — | — | — | Missing |
| Frame profile/section | No | — | — | — | — | Missing |
| Crossbars / length formulas | No | — | — | — | — | Missing |
| Frame process ops | No | ACM seed ops | — | — | Aggregate has 3 ACM comps only | Missing |
| Frame Component Template | No | — | — | — | — | Not created (correct until model chosen) |
| Metal Premount | Yes (other) | `TPL-METAL-PREMOUNT-STRUCTURE_v1` | separate product | Independent concept from ACP internal frame; composition binding declares mounting-support XOR vs Alucobond *panel* (not vs nested frame) | Mounting metal path | Must not be reused as ACP frame authority |

---

## SVG Analyzer findings

| Behavior | Present? | Evidence |
|----------|----------|----------|
| Operator checkbox only | **Yes** | `IntakeV6AlucobondContourPanel.tsx` |
| Auto-deduce need | **No** | Default `false` in `emptySvgSupportSelection` |
| Extract frame dimensions | **No** | Only panel geometry |
| Generate frame geometry | **No** | Blank preview is panel+folds only |
| Save flag | **Yes** | `confirmAlucobondSelection` |
| Save material/profile/crossbars/orientation | **No** | |
| Service opening | Separate `service_corner` | Not frame-owned |
| Warnings for incomplete frame | **No** | Casing validators only |
| Preview for frame | **No** | |

### Semantics: `internal_frame_enabled` means what?

**Demonstrated from code:** operator intent flag that (1) is stored on confirmed Alucobond selection and (2) when true, sets `frame_clearance_mm = 5` in mounting configuration (`buildAcmMountingSolutionFromSelection`).

Closest interpretations that match code:

1. **Partial:** „există / se cere cadru interior” as a marker — **yes**.
2. „doar operatorul cere rigidizare” — **yes** (manual checkbox).
3. „sistemul trebuie să calculeze ulterior cadrul” — **not implemented**.
4. „doar marker pentru Pasul 2” — **partial** (clearance appears in Step 2; no full config).
5. „configurație incompletă” — **yes**.
6. „component instance implicită” — **no** (no separate component instance).

---

## Step 1 findings

| Check | Result |
|-------|--------|
| Where | Alucobond casing block after Contur suport → Panou Alucobond |
| Checkbox | Yes — „Cadru interior activ” |
| Premature full config? | Boolean only — material/profile would be premature; marker itself is early |
| Saved in binding | Intended via `bindingFromSupportSelection`; **runtime workspace binding.configuration was `{}`** (gap / alternate associate path) |
| Composition | Does **not** activate a separate component |
| Persists after refresh | Selection flag persists when saved through Alucobond confirm path |
| Owner visible | Yes |

**Step 1 verdict:** **doar marker** (corect ca intent flag; prea devreme pentru configurație tehnică completă).

---

## Step 2 findings (Montaj / suport ACM)

| # | Question | Answer |
|---|----------|--------|
| 1 | Dedicated section? | No — ACM field grid only |
| 2 | Real fields? | `frame_clearance_mm` numeric |
| 3 | Checkbox only echoed? | Flag not shown as checkbox; clearance shown |
| 4 | Hardcoded values? | Enable path defaults clearance **5** |
| 5 | Default `20x20x1.5`? | **No** for ACP frame (that profile belongs to letter mounting bars / other paths) |
| 6 | Steel/aluminium? | **No** |
| 7 | Formulas? | **No** for frame length |
| 8 | Unit guard? | Panel unit ambiguity only |
| 9 | Validation? | Clearance ≥ 0 coalesce; no frame completeness rules |
| 10 | Inactive isolation? | Clearance 0 when off |

---

## FinishSetup / ProductDefinition / ProductAggregate

### FinishSetup

Persists in:

- `finish_setup.svg_support_selection.internal_frame_enabled`
- `finish_setup.mounting_solution.configuration.frame_clearance_mm` (+ optional `internal_frame_enabled` when mapped)
- binding `configuration.internal_frame_enabled` when built from selection sync

### ProductDefinition

When selection `confirmed` + `ALUCOBOND_CASED_PANEL`:

- `canonical_values.internal_frame_enabled` (boolean)
- **Does not** project material/profile/crossbars/component_template_code for frame

Classification: **partial** (`internal_frame_enabled: true` alone ≠ complete).

### ProductAggregate

Runtime aggregate for `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`:

- Components: face / returns / fasteners only
- Materials: ACM panel + fasteners
- **No** frame material line, length, weld, paint, or task projection

Inactive rule (observed): flag off ⇒ no frame materials/processes (there are none either way).

### CPP boundary

| Area | Status |
|------|--------|
| Material cost mapping for frame | **MISSING** |
| Process cost mapping for frame | **MISSING** |
| Profile resource option | **MISSING** |
| Steel/aluminium pricing | **MISSING** / **NOT_APPLICABLE** until Resource Options exist |
| Owner gate | **GUARDED** (commercial not ready) |
| Commercial readiness | **NOT_APPLICABLE** for frame as complete cost object |

---

## Lifecycle findings

- Lifecycle inspector surfaces SVG binding capability `internal_frame` under ACP geometry requirements.
- Does **not** treat frame as separate component, require Step 2 completeness, PD nested config, Aggregate projection, or runtime proof for frame.
- Does **not** confuse nested internal frame with Metal Premount in readiness stages.
- Binding contract strings `xor_with_metal_support` / `xor_with_alucobond_cased` apply to **mounting support choice** (Alucobond cased panel vs Metal Premount template), **not** to `internal_frame` vs premount.
- **Owner Product Truth (2026-07-18):** internal frame and premount are different concepts and may coexist; do **not** treat them as mutually exclusive unless a specific product Interface Contract proves it. Default: independent, optionally activatable, no mixed authority.
- **Correct future rule (not implemented):** if `internal_frame_enabled` then require nested frame config (material + profile) before commercial/task readiness; if false, zero frame contribution.

---

## Internal frame vs Metal Premount

| | Cadru interior ACP | Structură metalică premontaj |
|--|--------------------|------------------------------|
| Template | Nested config on `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | `TPL-METAL-PREMOUNT-STRUCTURE_v1` |
| Function | Rigidize cased panel (intent) | Support letters/assembly |
| SVG | Closed contour ACP | `svg_binding_enabled=false` |
| Relationship | **Independent** of premount (owner default) | May coexist with ACP + internal frame when product allows |
| Confusion risks | Shared words „cadru metalic” in legacy SVG layer roles / mock ops | Do not reuse premount materials/profiles as ACP frame authority |

No shared Component Template for ACP internal frame. Legacy labels „Cadru metalic” / `metal_frame` are **letter SVG layer roles**, not ACP reinforcement.

**XOR status (corrected):** There is **no** Product-Truth XOR between *cadru interior* and *premontaj*. Declared composition guards XOR Alucobond **panel mounting support** vs Metal Premount **as mounting_solution** — a separate concern from nested frame configuration. Runtime today also picks a single `mounting_solution.template_code`; that is not proof that nested frame and premount are mutually exclusive concepts.

---

## Material / dimensional / process logic

| Area | Status |
|------|--------|
| Steel vs aluminium Resource Option | **Lipsa** |
| Canonical profiles for ACP frame | **Lipsa** |
| Free-text material | **Lipsa** |
| Hardcoded profile `20x20x1.5` for ACP frame | **Lipsa** (exists elsewhere for mounting bars) |
| Frame width/height/setback formulas | **Lipsa** (only clearance hardcode 5) |
| Crossbar spacing | **Lipsa** |
| Documented only | `ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md` maps enabled→clearance |
| Process cut/weld/assemble/paint | **Lipsa** for frame |

---

## Runtime proof

| Item | Value |
|------|-------|
| URL FE | `http://127.0.0.1:3000` (Intake V6 workspace) |
| API | `http://127.0.0.1:8001/api/v1/intake-v6/workspaces/{id}` |
| Workspace | `f07058e2-3b40-4935-b55a-6a10b457241b` |
| Product template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Mounting template | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Binding | `bind_acm_runtime` / `SUPPORT_CONTOUR` / `CONFIRMED` |
| Baseline | `internal_frame_enabled=false`, `frame_clearance_mm=0`, panel **2000×700** |
| Toggle proof | PUT finish-setup (early association) → `internal_frame_enabled=true`, `frame_clearance_mm=5.0` (**200**) |
| Restore | PUT → `false` / `0` (**200**) — workspace returned to baseline |
| PD/Aggregate preview endpoints on workspace | Not exposed; template-level PD/Aggregate show **no** frame material/ops |
| Prior fixture proof | `docs/audits/_runtime_fixture_proof.json` with `internal_frame_enabled: true` |

---

## Dead pieces

| Piece | Note |
|-------|------|
| Capability `internal_frame: true` without consumer completeness | Contract claims capability; no validation of full config |
| Step 1 checkbox without Aggregate consumer | Flag/PD only |
| Step 2 clearance label ≠ metal reinforcement | Semantic drift |
| Binding `configuration: {}` on live WS | Early associate path may omit nested config including frame |
| Docs tooling table „Cadru interior / Decupaje — —” | Stale relative to checkbox |
| `20x20x1.5` elsewhere | Must not be assumed as ACP frame default |
| Lifecycle stage for frame | Absent (not a false PASS stage; simply not modeled) |

---

## Model comparison & single recommendation

| Criteriu | Config locală ACP | Componentă separată |
|----------|-------------------|---------------------|
| Reutilizare | Low today (ACP-only) | Speculative |
| Material propriu | Needed, can be Resource Option nested | Would duplicate if split early |
| Procese proprii | Needed later; inseparable from casing assembly initially | Premature |
| Configurație | Boolean+clearance exists — extend nested | Overkill until local complete |
| Interfețe | Panel geometry already owns envelope | Needs interface contract not present |
| Lifecycle | Through ACP | Separate would amplify Metal Premount confusion |
| Intake | Marker in Step 1; config in Step 2 | Extra composition instance |
| PD | Nested under ACP instance | New instance |
| Aggregate | Local projection when ready | Component projection |
| CPP | Guarded until options exist | Same gap |
| Complexitate | Lower | Higher |

**Single recommendation:** keep **local nested configuration on ACP**; complete it (material Resource Option otel/aluminiu + profile + dimensional rules) before considering a Component Template.

**Next safe step:** `Option 2 — GO ACP LOCAL FRAME CONFIGURATION COMPLETION`

---

## Owner gates (report only)

| Gate | Optiuni | Recomandare |
|------|---------|-------------|
| Model | config locală / componentă separată | **config locală** |
| Material | Resource Option / template separat | **Resource Option** (otel \| aluminiu) |
| Activare | checkbox / component instance | **checkbox** (Step 1 marker) + Step 2 full config |
| Step 1 | marker / fără config | **marker** |
| Step 2 | configuratie completa | **da (target)** |
| PD | nested config / component instance | **nested config** |
| Aggregate | local projection / component projection | **local projection** |
| Lifecycle | prin ACP / separat | **prin ACP** |
| CPP | guarded / ready | **guarded** |

---

## Acceptance

| Criterion | Status |
|-----------|--------|
| Appearances found | PASS |
| SVG / PS / Step1 / Step2 / FS / PD / PA / CPP / lifecycle | PASS |
| Frame vs premount | PASS |
| Steel/Al evaluated | PASS (missing) |
| Formulas inventoried | PASS (absent/hardcoded clearance) |
| Single recommendation | PASS — Option 2 |
| No app edits / no commit | PASS |
| Runtime proof | PASS (toggle+restore) |
| Dead pieces | PASS |
| Roadmap checkpoint | See worklog |

---

## STOP

Audit complete. No implementation.
