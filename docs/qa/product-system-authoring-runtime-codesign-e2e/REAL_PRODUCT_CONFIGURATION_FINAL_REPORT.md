# PRODUCT SYSTEM REAL PRODUCT CONFIGURATION — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `5382525d08f28be90755453caeb36b8830d4ef45` (**reconfirmed**) |
| Owner GO | **YES** — real product configuration (no activation / no publish) |
| Dirty tree | ~360 preserved; allowlist-only |
| Fixture | `TPL-VOLUMETRIC-LETTERS_v2` |
| Aluminiu | **`TPL-VOLUM-ALUMINIU_v1` inactive — not activated** |
| Report | this file |
| Worklog | `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` § PRODUCT SYSTEM REAL PRODUCT CONFIGURATION |
| Evidence | `runtime/vl_real_product_config_system_link_check.json` |

---

## 1. Scope

Fully and coherently configure `TPL-VOLUMETRIC-LETTERS_v2` via existing Product System authoring so an admin can open identity, family, version/lifecycle, usage mode, components (req/opt/cond), each component contract, materials, finishes, operations, quantity contract, Dossier, Runtime Preview, E2E Readiness, real publication blocker, and System Link Check end-to-end — **without force-publish**.

## 2. Kickoff reconfirmation

| Item | Result |
|------|--------|
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` (unchanged) |
| HEAD | `5382525` |
| Prior UI/Usability/a11y | PASS_WITH_WARNINGS preserved |
| Runtime routes | PASS preserved |
| Figma | NEEDS_POLISH preserved |
| External Artwork Boundary | PASS preserved |
| Template publication | BLOCKED preserved (Aluminiu inactive) |

## 3. Inventory (before)

| Item | Live DB state |
|------|---------------|
| Root VL | active; 5 inline components owning BOM |
| Links | Premount optional, Aluminiu required, ACM optional |
| FACE/BACK/LED/FINISH PT rows | **MISSING** |
| usage_mode / instance_schema_id | **null** on all edges |
| Aluminiu | inactive (correct blocker) |
| publication_status | NULL (legacy unspecified — left alone) |

## 4. Workstream A — Root Product Template

| Field | Configured value |
|-------|------------------|
| Identity | `TPL-VOLUMETRIC-LETTERS_v2` |
| Family | `litere_volumetrice` / Litere volumetrice |
| Role | root offerable (usage_mode policy) |
| Lifecycle | `active=true`; `publication_status=NULL` (not forced to DRAFT — would block offerability) |
| Composition | 5 required + 2 optional linked children |
| Root BOM | identity stubs only; materials/ops handed to children |
| Geometry | dossier `geometry_input_contract` consume-only |
| Publish | **not attempted** while blockers remain |

## 5. Workstream B — Component contracts

| Child | Relation | usage_mode | instance_schema_id | Owns |
|-------|----------|------------|--------------------|------|
| `TPL-VOLUMETRIC-FACE_v1` | required | linked_child | letter_group_instances.face | face mats/ops + geometry gate |
| `TPL-VOLUMETRIC-BACK_v1` | required | linked_child | letter_group_instances.back | back mats/ops |
| `TPL-VOLUM-ALUMINIU_v1` | required | linked_child | letter_group_instances.sidewall | return/cant mats/ops |
| `TPL-VOLUMETRIC-LED_v1` | required | linked_child | letter_group_instances.lighting | LED mats/ops |
| `TPL-VOLUMETRIC-FINISH_v1` | required | linked_child | letter_group_instances.finish | finish/pack/QC mats/ops |
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | optional | linked_child | component_placements.mounting | premount |
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | optional | linked_child | acm_panel_component_instance_v1 | ACM boxed |

No ComponentTemplate table. No invented parallel codes — canonical FACE/BACK/LED/FINISH identities used.

## 6. Per-component central answers (summary)

| Component | Required inputs (units) | Validators | CPP/EIC | Aggregate | Execution | Standalone | Publishable |
|-----------|-------------------------|------------|---------|-----------|-----------|------------|-------------|
| Face | area m², W/H mm, finish | geometry consume-only gate | via parent qty | linked_module | preview | component_only | with parent |
| Back | area m², backing mode | form contract | via parent | linked_module | preview | component_only | with parent |
| Aluminiu | perimeter m, depth mm, finish | required inactive → BLOCKED | via parent | linked_module | preview | component_only | **blocked while inactive** |
| LED | count, PSU W, lighting type | lighting fields | via parent | linked_module | preview | component_only | with parent |
| Finish | template area m², count | mounting gates | via parent | linked_module | preview | component_only | with parent |
| Premount | bar length ml | optional trigger | separate line | optional | preview | dual-role offerable | independent |
| ACM boxed | mounting_solution | optional trigger | separate line | optional | preview | dual-role offerable | independent |

## 7. SVG / DWG / DXF

Defined as **geometry inputs only** on FACE + root dossier:

- width/height/depth mm, area m², perimeter m, count, placement, provenance, `external_artwork_analysis_ref`
- Forbidden: parse / analyze / group / extract
- Op `geometry_inputs_readiness_gate` is consume-only (`no_file_parse: true`); replaces misleading root `svg_geometry_analysis` ownership

## 8. Workstream C — Dossier

- Parent dossier patched with `geometry_input_contract`, `component_ownership`, `publication_policy`
- Child dossiers documentary (identity, material/operation keys, ownership labels)
- Dossier is **not** BOM/ops/qty SoT (Aggregate warning `DOSSIER_METADATA_ONLY` remains)

## 9. Workstream D — E2E Readiness

Live static run (see evidence JSON):

| Axis | Status |
|------|--------|
| Verdict | **BLOCKED** |
| BUILD closure | **PASS_WITH_WARNINGS** |
| Template publication | **BLOCKED** |
| Blocking finding | `components.required_inactive.TPL-VOLUM-ALUMINIU_v1` |
| Writes | none (`write_performed=false`) |
| Auto-activate | **none** |

## 10. Workstream E — System Link Check

Mounted on Product Template → E2E Readiness as status table (read-only; no repair/activate/publish).

### System Link Check table (live static)

| Hop | Status | Notes |
|-----|--------|-------|
| Catalog | PASS | VL present + active |
| Components | **BLOCKED** | required inactive Aluminiu |
| Intake | PASS | V6 form contract present |
| Product Truth | NOT_TESTED | static mode |
| ProductDefinition | PASS | read-only preview |
| Aggregate | PASS | read-only build |
| Quantity | PASS | letters measurement rules |
| CPP | NOT_TESTED | no formula duplication |
| EIC | NOT_TESTED | no formula duplication |
| Quote Snapshot | NOT_TESTED | static |
| Order Snapshot | NOT_TESTED | no writes |
| Execution Preview | NOT_TESTED | no materialization |

## 11. Workstream F — Runtime Preview

Prior human-summary Runtime Preview retained (no raw JSON default; no file analysis). Vitest `TemplateRuntimePreviewPanel` PASS.

## 12–18. Component ownership detail

See §5–6. Root no longer duplicates FACE/BACK/LED/FINISH/lateral materials/ops after handoff (`kept_root_operations=0`, `kept_root_materials=0`, 5 stub components).

## 19. Aluminiu analysis (no activation)

| Question | Answer |
|----------|--------|
| Why required? | Canonical return/cant ownership (`modelare_cant`); VL always needs side wall/return |
| Role | required linked child Product Template (component_only policy) |
| Contract | mats: profil 30/60/80/100, Oracal, RAL, adeziv; ops: forming, face bonding, painting |
| Missing for publication | **`active=false`** — readiness hard-blocks TEMPLATE PUBLICATION |
| Required link correct? | **Yes** — `relation_type=required_module`, trigger `volum_aluminum_module_template_code` |
| Should it be active component? | **Owner decision** — evidence does **not** prove safe activation in this pass (pricing/CostEngine/E2E runtime not reopened) |
| Parallel replacement? | Not recommended without owner GO; FACE/BACK/LED/FINISH are not substitutes for cant |

### Owner decision ask

**Only if** owner wants TEMPLATE PUBLICATION unblocked: choose one of  
(A) activate `TPL-VOLUM-ALUMINIU_v1` after dedicated readiness GO,  
(B) demote link to optional/conditional with alternate cant strategy,  
(C) keep BLOCKED (recommended default until commercial/ops GO).  

**This build does not request activation GO** — evidence supports keeping inactive + honest BLOCKED.

## 20. UI changes

Only System Link Check table on readiness panel (config visibility). No general polish. Vitest updated.

## 21. Tests run

```text
pytest:
  test_vl_real_product_configuration_v1.py
  test_product_e2e_readiness_v1.py
  test_product_template_publication_v1.py
  test_product_template_component_contracts_v1.py
  test_product_template_module_links_composition_v1.py
  test_product_aggregate_volumetric_v2.py
→ 31 passed

vitest:
  ProductE2EReadinessPanel.test.tsx
  TemplateRuntimePreviewPanel.test.tsx
→ 2 passed
```

Failure classification during work: aggregate fixture/assertions previously assumed empty parent + 5 dossier components (contradiction under current Aggregate authority). Realigned to identity stubs + linked-module BOM — **BUILD_ALIGNMENT**, assertions not weakened.

## 22. Forbidden confirmation

| Forbidden | Absent? |
|-----------|---------|
| ComponentTemplate table | YES |
| Aluminiu activation | YES |
| Force publish | YES |
| Pricing / CostEngine reopen | YES |
| Build 2 / PI / CI | YES |
| Desktop transport / SVG analysis | YES |
| Execution materialization | YES |
| git add -A / dirty wipe | YES |

## 23. Stop conditions hit?

**None.** Aluminiu activation was **not** required to continue — readiness correctly reports BLOCKED.

## 24–28. Separate verdicts

| Axis | Verdict |
|------|---------|
| Root config | **PASS** |
| Component contracts | **PASS** |
| Dossier documentary | **PASS** |
| Readiness honesty | **PASS** (publication BLOCKED) |
| System Link Check | **PASS** |
| Runtime Preview | **PASS_WITH_WARNINGS** (prior) |
| Template publication | **BLOCKED** (correct) |
| UI polish | unchanged NEEDS_POLISH / PASS_WITH_WARNINGS |

## 29–33. Direction scores

| Axis | Score |
|------|-------|
| Composition completeness | 92 |
| Ownership clarity | 90 |
| Contract typing | 88 |
| Readiness / publication honesty | 95 |
| System Link Check | 90 |
| Geometry boundary discipline | 94 |
| Test / evidence | 88 |
| Boundary discipline | 96 |

**Overall direction: 91/100**

## 34. PAREREA MEA SINCERA

VL is now a real composed product in Product System: FACE/BACK/LED/FINISH exist as child PTs, edges carry usage_mode + schemas, root no longer pretends to own their BOM, Readiness + System Link Check tell the truth. Publication remains correctly BLOCKED on inactive Aluminiu — that is the honest product state, not a failure of this configuration pass. Do not activate Aluminiu casually; do not greenwash publication.

---

## Commits

| SHA | Group |
|-----|-------|
| `80367c0` | feat(product-system): complete VL component module composition contracts |
| `f42172c` | feat(product-system-ui): show System Link Check status table on readiness |
| `c05d57e` | test(product-system): prove VL real product configuration contracts |
| `7de64bb` | docs(qa): record VL real product configuration evidence and report |
| tip HEAD | docs tip SHA table (this patch) |
