# Audit — ACP mixed-face foundation owner runtime review

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_ACP_MIXED_FACE_FOUNDATION_RUNTIME_REVIEW_AND_LOCAL_MODULE_PREP` |
| HEAD | `cb822da` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Mode | Review + pre-build design — **no app edits, no commit** |

---

## Verdict

**ACP_MIXED_FACE_FOUNDATION_RUNTIME_REVIEW_PASS**  
**AUTHORITY_AND_PERSISTENCE_COMPLETE · OPERATOR_SURFACE_NOT_IMPLEMENTED**

---

## 1. Commit inventory (`e7082c2..cb822da`)

| Commit | Mesaj | Fisiere (scope) | Inclus in HEAD |
|--------|-------|-----------------|----------------|
| `3b93a42` | docs(product-system): record ACP composable-face system audit | 6 audit/architecture/plan/worklog docs | Yes |
| `6fc9ff3` | feat(product-system): add ACP face-treatment authority contracts | registry, binding contract, availability schema, tests, authority+legacy docs | Yes |
| `44992ce` | feat(svg-analyzer): persist component-owned face treatments | persistence, workspace save hook, FE types/upsert, tests, persistence/binding docs | Yes |
| `934cbc8` | feat(product-definition): compile ACP face-treatment instances | PD builder | Yes |
| `9739136` | docs(workos): record ACP authority persistence validation | worklog | Yes |
| `bd3fae5` | test(product-system): prove ACP mixed-face FinishSetup HTTP round-trip | HTTP tests | Yes |
| `cb822da` | docs(workos): note ACP foundation backend restart and HTTP proof | worklog update | Yes (HEAD) |

Dirty tree: large unrelated WIP (~302 paths). Review docs untracked. App FE/BE for this GO: clean.

---

## 2. Runtime health (no restart)

| Item | Value |
|------|-------|
| FE :3000 | 200 |
| BE :8001 | `{"status":"healthy"}` |
| PID | 9200 |
| Command | `python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload` |
| OpenAPI | `IntakeV4FinishSetup` includes `svg_component_bindings`, `svg_support_selection`, `mounting_fixing_system` |
| Face treatment named OpenAPI props | N/A — free-form binding dicts |
| Checked at | 2026-07-18T16:52:35+03:00 |

---

## 3. Registry inspection

| code | label | allowed_geometry_roles | capabilities | requires_local_module | multi | status | ver |
|------|-------|------------------------|--------------|----------------------|-------|--------|-----|
| `FACE-TREATMENT-APPLIED-VOLUMETRIC-COMPONENT` | Componentă volumetrică aplicată | LETTER/LOGO | letter/logo_vector | false | true | active | 1 |
| `FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT` | Decupaj iluminat (plexiglas pe spate) | CUTOUT_TEXT, CUTOUT_LOGO | boxed_acp_shell, local_face_treatments | **true** | true | active | 1 |
| `FACE-TREATMENT-ACRYLIC-INSERT` | Insert plexiglas | ACRYLIC_INSERT | boxed_acp_shell, local_face_treatments | **true** | true | active | 1 |
| `FACE-TREATMENT-PLAIN-DECORATIVE` | Zonă plină / decorativă | DECORATIVE_VECTOR | boxed_acp_shell, local_face_treatments | false | true | active | 1 |

Separation confirmed: geometry_role ≠ face_treatment ≠ finish ≠ material.

Geometry roles present: `CUTOUT_TEXT`, `CUTOUT_LOGO`, `ACRYLIC_INSERT` (no `ROUTED_FACE`).

---

## 4. Binding contract (real sample)

See `docs/qa/.../binding_contract_sample.json` — fields observed after normalize:

`binding_id`, `selected_geometry{layer_ids,group_ids,element_ids,geometry_hashes,source_svg_hash}`, `geometry_role`, `component_template_code`, `local_zone_id`, `face_treatment_code`, `confirmation_status`, `status`, `local_configuration_status`, `provenance{source,svg_hash,geometry_hash,face_treatment_registry_version}`, `face_treatment_contract_version`, `schema`.

---

## 5. Mixed-face + PD + Lifecycle proof

Artifact: `docs/qa/acp-mixed-face-foundation-runtime-review/mixed_face_foundation_proof.json`

| Check | Result |
|-------|--------|
| Zones stable across array reorder | PASS |
| Shell + letters + cutout + insert coexist | PASS |
| Letters separate PD instance | PASS |
| Shell nests routed + insert treatments | PASS |
| Routed/insert readiness | `LOCAL_CONFIGURATION_REQUIRED` |
| Inactive warnings | 0 |
| Legacy missing treatment | `NOT_APPLICABLE` |
| Unknown treatment | rejected |
| HTTP PUT/GET | PASS (`test_http_mixed_face_finish_setup_save_and_refresh`) |
| Invented BOM/materials | none |

---

## 6. Current UI truth

| Question | Answer |
|----------|--------|
| New geometry roles in Step 1? | **No** — combobox only Vector Litere / Vector Logo / Contur suport |
| Treatment selector? | **No** |
| Component ownership visible? | Partial (composition cards: letters vs ACM) — not treatment ownership |
| local_zone_id visible? | **No** |
| Distinguish applied/routed/insert? | **No** |
| Path for foundation data? | **API / fixture / tests only** |
| False COMPLETE for face modules? | N/A — treatments not in UI; Step 2 shows letter finishes only |

**AUTHORITY_AND_PERSISTENCE_COMPLETE · OPERATOR_SURFACE_NOT_IMPLEMENTED**

Screenshots: `docs/qa/acp-mixed-face-foundation-runtime-review/screenshots/` + `screenshots_index.md`.

Honest opinion: Operator can configure letters + ACP shell casing/finishes/montaj. Mixed-face foundation is invisible in UI — correct for contract-first build, but owner cannot exercise cutout/insert without API.

---

## 7. Regression (targeted — not full repo)

| Suite | Result |
|-------|--------|
| Backend face/FinishSetup/PD/mounting/frame/decouple | **52 passed** |
| Backend template lifecycle (alone) | **8 passed, 1 skipped** |
| Frontend svgComponentBindings + mountingSolution + fixing + acpInternalFrame | **23 passed** |
| Frontend production build | **PASS** |

Statement: targeted relevant regression only — not full repository suite.

---

## 8. Dead pieces (no cleanup)

| Piece | Status | Consumer | Risk | Future action |
|-------|--------|----------|------|---------------|
| `TPL-ACP-LIGHT-ROUTED` | PARALLEL_LEGACY_COST_PATH | QuoteWizard/CostEngine/seeds/tests | Wrong authority if reused for V6 | Keep; do not import |
| Step 1 layer role adapter (3 options) | LEGACY_INTAKE adapter | Intake UI | Hides new geometry roles | Option 2 UI GO |
| Unbound DECORATIVE_VECTOR | Contract listed | none in UI | Low | Later |
| `TPL-BOND-CASETAT` | dead for selection | guards | Low | Keep blocked |
| Dossier task_rules | admin hint | Dossier Studio | Fake task SoT if misread | Banner only |
| LIGHT-ROUTED plexi 3mm/10mm formulas | discoverable | CostEngine | Tempting wrong copy | Owner gates |

---

## 9. Single next safe step

**Option 1 — GO ACP BASE + LOCAL FACE MODULES TECHNICAL CONFIGURATION**

After owner answers gates in `ACP_LOCAL_FACE_MODULE_OWNER_GATES.md`.

---

## Cat sunt in directia stabilita

**92/100%** — foundation verified; operator surface deliberately absent; owner gates still open before modules.
