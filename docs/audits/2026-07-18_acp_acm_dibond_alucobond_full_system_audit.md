# Full system audit — ACP / ACM / Dibond / Alucobond

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_FINALIZE_BLUEPRINT_AUDIT_AND_AUDIT_ACP_COMPOSABLE_FACE_SYSTEM` |
| HEAD at audit | `e7082c2` (after Blueprint docs commit) / baseline accepted `f741006` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Mode | Audit + Blueprint docs finalize — **no app edits** |
| Related | Terminology map · Face composition source map · Composability audit · Recommendation |

---

## Executive verdict

**ACP_SHELL_LIVE_MIXED_FACE_MISSING_AUTHORITY_FORK_BLOCKS_COMPOSITION**

1. Live Intake V6 path: Litere + **one** Panou Alucobond casetat (`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`).
2. Illuminated routed ACP exists as **parallel** CostEngine product (`TPL-ACP-LIGHT-ROUTED`).
3. Owner mixed-face (applied + routed + insert + plain) is **not representable**.
4. First failing boundary: SVG binding contract + FinishSetup (no face-treatment roles/persistence).
5. Blueprint/Dossier patterns can organize **admin UI** later; must not become SoT.
6. Accepted UI direction remains: reuse Dossier visual patterns inside current Product System UI.

---

## 1. Product System inventory

| Cod | Tip | Status | Scop real | Variante | Consumers | Gap |
|-----|-----|--------|-----------|----------|-----------|-----|
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | Product / linked child | **Live** | Boxed ACM cut/V-groove/fold/assemble/mount | Thickness, fold_sides (dossier variants) | Intake V6, PD, Aggregate rates, lifecycle | No face zones / LED / insert |
| `TPL-VOLUMETRIC-LETTERS_v2` | Parent product | Live | Letters + optional support | — | Intake primary | Support ≠ face treatment |
| `TPL-ACP-LIGHT-ROUTED` | Hierarchical CostEngine product | Seeded / QuoteWizard | Routed face + plexi diffuser + LED + 10 mm relief + finish | quote_input driven | Pricing/CPP tests | Not V6 SVG-bindable composition |
| `TPL-ACM-CASSETTED-PANEL` | Candidate | Future / owner_go | Intended cassette product | Pack seed | SVG layer maps, some tests | Not Intake root |
| `TPL-CUT-ACM-LETTERS` | Pack seed | Pack | Flat cut ACM letters | — | Layer maps | Not volumetric |
| `TPL-BOND-CASETAT` | Legacy string | Blocked | Stale composition | — | Guarded | Dead for selection |
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | Support XOR | Live | Metal bars | — | Mounting | Not ACP face |

**Classification:** ACM boxed = **product-capable casing** (not complete luminous multi-zone face). LIGHT-ROUTED = **complete luminous product** on a **parallel** path. CASSETTED = **partial/candidate**.

Components under boxed seed (face panel, returns, fasteners) — casing slice, not illuminated face modules.

### Interface contracts (related)

| Contract | Status for mixed-face |
|----------|----------------------|
| SVG bindable components (`accepted_geometry_roles`) | Live for LETTER/LOGO/SUPPORT only |
| FinishSetup `svg_component_bindings` | Live; no face-treatment array |
| Mounting solution / fixing / internal frame | Live shell config — orthogonal to face treatments |
| CostEngine LIGHT-ROUTED component tree | Parallel illuminated authority — not V6 bindables |
| Dossier variants / task_rules / readiness | Admin/docs — not runtime SoT |

### Git history inspected (non-exhaustive)

Recent ACP/ACM commits on branch lineage include mounting decoupling + fixing (`c0a3404`…`f741006`), SVG role alignment (`514896e`, `611fc20`, `98f9471`), internal frame (`80f0bc0`…). No historical commit introduces `face_mode` / `visual_zones[]` / `CUTOUT_*` / `ACRYLIC_INSERT` as V6 geometry roles. Illuminated routed knowledge remains under CostEngine / `TPL-ACP-LIGHT-ROUTED` seeds and QuoteWizard path — not a deleted React Flow canvas or lost zone model.

### Product vs support conflict

Historically ACP was misread as commercial mounting prep. Post-`c0a3404`, ACM boxed is a **product configuration** independent of `mounting_scope=none`. That fix does **not** grant face-treatment composability — it only clarifies shell identity vs commercial prep.

---

## 2. SVG Analyzer findings

- Can confirm **one** Alucobond cased contour + letter/logo layers.
- Cannot attach cutout/insert/routed **treatments** to that contour as first-class roles.
- `plexiInserts10mm` is a **layer confirmation flag** for nesting heuristics — not ACP insert SoT.
- `inner_hole` / „decupat” ≠ push-through product truth.
- Confusion: contour role ≠ `SUPPORT_CONTOUR` ≠ layer `support_panel`.

---

## 3. Intake Step 1 / 2 / FinishSetup

| Stage | Finding |
|-------|---------|
| Step 1 | Per-layer roles for letters/logo; global support contour; composition confirm letters+ACP; fragmented model |
| Step 2 | Shell config (dims, thickness, fold, frame, fixing, service corner); commercial mounting decoupled; **no** routed/insert zone editors |
| FinishSetup | `svg_component_bindings` + `mounting_solution` + optional `mounting_fixing_system`; **no** `face_treatments[]` |

---

## 4. Finish model

ACP boxed path lacks stock color / Oracal / RAL on panel face. Letters own surface finishes. LIGHT-ROUTED owns finish as CostEngine component. Finish ≠ treatment ≠ material — currently collapsed incorrectly for multi-zone ACP.

---

## 5. ProductDefinition / Aggregate / Lifecycle

| Layer | Mixed-face? |
|-------|-------------|
| PD | `svg_component_instances` from bindings — product instances, not zones |
| Aggregate | Letters + ACM linked compile — no zone BOM identity |
| Lifecycle | Support/letter wiring, frame profile gate, fixing evidence — no per-zone readiness |

Searched `face_mode`, `visual_zones`, `face_treatment(s)`: **absent** in runtime SoT.

---

## 6. CPP / Tasking boundary

| Capability | CPP | Tasking |
|------------|-----|---------|
| Simple ACP boxed | PARTIAL/READY (owner rates) | PARTIAL (ops codes) |
| Routed ACP | LEGACY LIGHT-ROUTED | MISSING on V6 |
| Plexiglas backing | LEGACY | MISSING V6 |
| Insert 10 mm | LEGACY / layer flag | MISSING V6 |
| LED / electrical on ACP face | LEGACY / letters path | MISSING V6 face |
| Applied letters | PARTIAL letters path | PARTIAL letters |

Binding guards: `no_cpp_from_binding`, `no_tasking_from_binding` on ACM support.

Dossier `task_rules`: **visual/admin hint** — not runtime.

---

## 7. Dossier UI pattern assessment

| Pattern Dossier | Util ACP | Reutilizare | Risc | Recomandare |
|-----------------|----------|-------------|------|-------------|
| Fixed groups + authority banners | High | VISUAL_PATTERN | Treating groups as SoT | Port to PS UI |
| Variants | Medium (thickness/fold) | REUSE_WITH_ADAPTER | Variant as exclusive face_mode | Keep construction variants only |
| Layers list | Docs only | CONCEPT | Fake geometry SoT | Docs only |
| Inspector / readiness summary | High | REUSE_AS_IS pattern | Duplicate readiness UIs | One readiness authority |
| Active/archive + versioning | Medium | REUSE_AS_IS | — | Keep |
| task_rules editor | Low for SoT | DO_NOT_REUSE as runtime | Parallel tasking | Banner only |
| Component tree | High future | CONCEPT → Option 2 later | Premature modules | After authority fix |

**Direction:** Current contracts = authority · Dossier-inspired UI = administration · PD = confirmed config · Aggregate = compile · existing tasking = ops.

---

## 8. Duplicate authority

| Item | Class |
|------|-------|
| `TPL-ACM-BOXED…` live | **canonical** (V6 composition) |
| `TPL-ACP-LIGHT-ROUTED` | **legacy / parallel** illuminated |
| `TPL-ACM-CASSETTED-PANEL` | **owner gate / candidate** |
| `TPL-BOND-CASETAT` | **dead** for selection |
| Contour vs geometry vs layer roles | **conflict** |
| bindings vs svg_support_selection vs mounting_solution | **adapter** (synced) |
| Dossier task_rules vs Aggregate | **conflict if misused** |
| `plexiInserts10mm` vs insert treatment | **legacy / wrong authority** |
| MAT-ACP plexi vs MAT-ACM panel | **conflict naming** |

---

## 9. Runtime proof status

| Scenario | Status |
|----------|--------|
| A Simple ACP | Conceptually/runtime viable on V6 |
| B Routed + plexi | Not V6 composition |
| C Insert 10 mm | Not ACP zone |
| D Mixed letters + routed | **Blocked** at binding/FinishSetup |
| BE stale | Persistence guarded for recent fields — does not change mixed-face verdict |

No E2E PASS claimed for mixed-face.

---

## 10. Single recommendation

**Option 4 — FIX AUTHORITY/PERSISTENCE CONFLICT FIRST**

See `docs/plans/ACP_FACE_TREATMENTS_MODEL_RECOMMENDATION.md`.

Follow-on (after Option 4): Option 2 (ACP base + local face modules) preferred over exclusive variants.

---

## 11. Acceptance

| Criterion | Met |
|-----------|-----|
| Blueprint docs committed isolated | Yes `e7082c2` |
| Terms + git/history inspected | Yes |
| Templates / SVG / Step1–2 / Finish / PD / Agg / Lifecycle / CPP / tasking | Yes |
| Dossier patterns evaluated | Yes |
| First failing boundary identified | Yes |
| No app edits for ACP audit | Yes |
| ACP docs not committed | Yes (owner review) |
| Single recommendation | Option 4 |

**Cat sunt in directia stabilita: 90/100%.**
