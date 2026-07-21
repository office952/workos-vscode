# VOLUM ALUMINIU — Component Contract Audit

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `6608cdc5` (reconfirmed) |
| Mode | READ-ONLY — no activation / no publish / no schema / no pricing edit / no commit |
| Subject | `TPL-VOLUM-ALUMINIU_v1` |
| Report path | `docs/qa/product-system-authoring-runtime-codesign-e2e/VOLUM_ALUMINIU_COMPONENT_CONTRACT_AUDIT.md` |
| Evidence dir | `docs/qa/product-system-authoring-runtime-codesign-e2e/volum-aluminiu-audit/` |

---

## 1. Kickoff confirmation

| Item | Result |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `6608cdc5dbeeadaee6c021b520c6435726576814` |
| Dirty tree | Preserved untouched (large prior WIP; inspection-only) |
| Accepted priors | P0/P1 PASS; VL config PASS; publication BLOCKED by inactive Aluminiu; Publish fail-closed; external analysis boundary preserved |
| Backend | Started temporarily for read-only API/DB evidence; no PT/Quote/Order writes |
| Frontend UI Product System | Session gate blocked live PS screenshots; evidence boards + API/DB used instead |

## 2. Absolute boundaries (honored)

Not done:

- activate / publish / delete / rename / demote `TPL-VOLUM-ALUMINIU_v1`
- change links, schema, fields, formulas, materials prices, pricing, ops, Product Truth, UI, lifecycle
- commit / push / PR
- SVG/DWG/DXF, desktop transport, PI/CI, ComponentTemplate table, Build 2, Execution materialization, mobile
- Pricing Registry / CPP/EIC architecture reopen

Done: inspect code/DB/API, existing tests, static readiness, Aggregate read, screenshots of evidence boards, this report.

## 3. Executive truth (română)

**Volum Aluminiu este component tehnic real de cant/return/volum din aluminiu**, nu „doar material aluminiu”. Este child Product Template (`component_only`), required pe Litere volumetrice, cu BOM/ops/formule proprii și linie comercială pe ml. **Nu e gata de activare**: lipsesc confirmation/material_profile/perimeter_source la granița de componentă, există dualitate de ID-uri, depth form ≠ gate material, iar publicarea VL e blocată onest de `active=false`. **Recomandare owner: keep blocked** — nu activa doar ca să treacă Publică.

## 4. What it represents

Technical component for illuminated volumetric letters:

- role: return / sidewall / cant / volume edge
- implementation: aluminium profile (depth-gated 30/60/80/100 mm)
- finishes: stock aluminum colors, RAL paint, Oracal wrap
- ops: machine forming, face bonding, conditional painting

Operator label candidate (recommended, no rename): **„Cant / volum din aluminiu”**.

## 5. Identity map

| Axis | Value |
|------|--------|
| Template code | `TPL-VOLUM-ALUMINIU_v1` |
| Family | `volum_aluminiu_modular` / „Volum aluminiu modular” |
| Child component_id (BOM owner) | `comp_volum_aluminiu_module` |
| Parent stub component_id | `comp_lateral_litere` |
| Mini-module | `modelare_cant` |
| Shared contract key | `volumetric_return_side` |
| Admin display | „Aluminiu (volumetric)” (`productSystemAdminDisplay.ts`) |
| Availability label | „Cant / laterale” |
| PS ownership card | „VOLUM ALUMINIU / CANT” |

## 6. PT / child / dual-role / legacy classification

| Classification | Verdict |
|----------------|---------|
| Product Template row | YES (not ComponentTemplate table) |
| Child / linked_child | YES |
| component_only policy | YES (`root_offerable=false`) |
| Dual-role offerable (like Premount/ACM) | NO |
| Legacy standalone material SKU | NO — full module with ops + finish gates |
| Legacy replacement target | UI copy mentions future `RETURN-CANT` replacing this code — aspirational, not live active duplicate |

## 7. Parents / used-by

Live DB + contract API:

- **Only parent:** `TPL-VOLUMETRIC-LETTERS_v2`
- relation: `required_module`
- usage_mode: `linked_child`
- instance_schema_id: `letter_group_instances.sidewall`
- pricing_mode: `separate_quote_line`
- execution_mode: `linked_child_work`
- link active: true
- trigger_field: `volum_aluminum_module_template_code`

No children under Aluminiu.

## 8. Why required by VL

VL always needs a return/sidewall for volumetric letters. Mini-module registry marks `modelare_cant` as `required_module_link` always required for VL. Seed + composition stamp keep Aluminiu as required child. Publication/readiness hard-block when that required child is inactive — intentional honesty, not an accident.

## 9. Logo reuse

| Letters | Logo |
|---------|------|
| `TPL-VOLUM-ALUMINIU_v1` | `TPL-VOLUMETRIC-LOGO-RETURN_v1` (separate, active in DB) |
| Shared contract key `volumetric_return_side` | Logo role label „Return / cant logo” |
| Commercial class `modelare_cant` reused conceptually | Logo line `logo_return_cant` with logo perimeter paths |

**Reusable as concept/role, not as the same activated template today.** Letters Aluminiu is not the live Logo return module.

## 10. usage_mode / relation / policy

| Field | Value |
|-------|--------|
| usage_mode (edge) | `linked_child` |
| relation_type | `required_module` |
| usage_mode_policy | component_only; linked_child_allowed; not root_offerable; owner_go_required=false (policy metadata) |
| contract role | `child_component` |

`owner_go_required=false` in policy does **not** authorize activation — seed/readiness still keep it inactive until explicit owner GO.

## 11. Instance schema

- Hint + live edge: `letter_group_instances.sidewall`
- Geometry input hints (contract service): `letter_perimeter_m`, `return_depth_mm`, `depth_mm`
- Form bindings: `return_depth_mm`, `return_finish_type`, `return_oracal_code`, module trigger `volum_aluminum_module_template_code`

## 12. Inputs (owned vs dependency)

| Input | Unit | Ownership |
|-------|------|-----------|
| `return_depth_mm` | mm | Component/module config (form) |
| `return_finish_type` | enum | Component/module config |
| `return_oracal_code` | code | Component finish detail |
| `letter_perimeter_m` | m / ml | Parent/geometry consume-only dependency |
| `depth_mm` | mm | Geometry hint / overlap with return depth |
| Profile material | gated by depth | Child material list |
| Confirmation state | — | **Missing** at component boundary |

## 13. Validators / gates

- Depth gate materials: 30 / 60 / 80 / 100 mm
- Finish gate: RAL paint vs Oracal wrap vs stock aluminum finishes
- Readiness hard validator: required child inactive → BLOCKED
- Geometry readiness is consume-only (no SVG parse in WorkOS)
- **Mismatch:** Intake form option depths include **40 / 120** while material gates are **30 / 60 / 80 / 100**

## 14. Materials

Owned on child PT (`required_materials_json`), Aggregate provenance `linked_module` / `TPL-VOLUM-ALUMINIU_v1`:

- `MAT-PROFIL-LATERAL-LITERE-30MM|60MM|80MM|100MM` — `return_profile_linear_meter`
- `MAT-ORACAL-651` — `return_wrap_area`
- `MAT-VOPSEA-RAL` — `return_paint_consumption`
- `MAT-ADEZIV-CANT-LITERE` — `return_profile_adhesive`

Root VL currently has **0** materials (handoff done).

## 15. Finishes

- Stock aluminum finishes via `return_finish_type` (white/black/gold/mirror etc.)
- RAL paint path (material + `PAINTING` op gated)
- Oracal wrap path
- `return_cant_product_truth_bridge` maps depth→profile and finish→vinyl/paint keys
- Component-owned `color_target` / confirmation still marked pending in PS ownership UI

## 16. Quantities

- Primary commercial/internal quantity path: **perimeter ml** (`letter_perimeter_m`)
- Profile selection gated by depth
- Wrap/paint consumption formulas depth-sensitive
- Gradi/runtime note: cant labor currently depth-independent in some traces (known warning, not repaired here)
- Separate calculation blocked while perimeter_source + confirmation_state are not component-first-class

## 17. Operations

Child-owned:

| Code | Formula | Workcenter (seed) |
|------|---------|-------------------|
| `RETURN_PROFILE_MACHINE_FORMING` | `return_profile_machine_forming` | WC_FORMING |
| `RETURN_PROFILE_FACE_BONDING` | `return_profile_face_bonding` | WC_ASSEMBLY |
| `PAINTING` | `return_painting_linear_meter` | WC_PAINT |

Aggregate maps bonding under `modelare_cant` (not assembly module). Root VL ops count = 0 after handoff.

## 18. Pricing refs (commercial)

- Rule: `modelare_cant_aluminiu` / `VOL_V2_RETURN_PROFILE_ML`
- Module: `modelare_cant`; component_code: `comp_lateral_litere`
- Basis: **ml** (not minutes/hourly)
- Explicit warning: „Technical inputs: letter_perimeter_m, return_depth_mm — not minutes.”
- Link pricing_mode: `separate_quote_line` (composition intent)
- Live CPP exercise: **NOT_TESTED** in static readiness (boundary respected)

## 19. Cost refs (internal / EIC)

- Internal op rule `modelare_cant` / `INT_VOL_V2_RETURN_ML`
- Basis: **ml**; anti-hourly contamination scanner present in EIC service
- Seed metadata `estimated_hours=3.0`, `base_labor_rate=80.0` exist on template row but commercial/EIC paths for this module are ml-based — treat hours fields as **non-authority leftovers**, not commercial SoT
- Live EIC: **NOT_TESTED** in static readiness

## 20. Commercial-hourly compliance check

| Check | Result |
|-------|--------|
| Separate-calc commercial basis hourly? | **NO** — ml |
| EIC basis hourly for modelare_cant? | **NO** — ml |
| Explicit anti-hourly guards in CPP/EIC? | **YES** |
| Stop condition „hourly commercial in separate calc”? | **Not triggered** |

**PASS** for commercial-hourly philosophy on this component’s documented rules.

## 21. Parent duplication analysis

| Area | Status |
|------|--------|
| Root materials/ops for cant | Cleared (0/0) — good |
| Root stub `comp_lateral_litere` | Still present (identity only, empty BOM) |
| Child BOM id `comp_volum_aluminiu_module` | Owns mats/ops |
| Dual ID risk | **Yes — naming dualitate**, not two active BOM owners |

Not a second active return component; it is identity-stub vs BOM-owner split.

## 22. Wrong-place formulas

- Formulas live on child materials/ops — correct place for ownership direction
- Commercial/EIC rules still key `comp_lateral_litere` while child mats use `comp_volum_aluminiu_module` — **cross-id coupling**
- Legacy Intake V3/V4 still carry return painting task codes (historical paths) — outside activation scope; not proof that VL Aggregate wrongly hosts child formulas
- Dossier `quote_readiness_json` text claims modular template „activ” while DB `active=false` — **documentary overclaim**

## 23. Compiler / PT / Agg / Qty / CPP-EIC readers

| Reader | Sees Aluminiu as |
|--------|------------------|
| ProductAggregate | required module `modelare_cant` → child template; mats/ops provenance linked_module |
| ProductDefinition | linked module path / return fields |
| Intake V6 form | `modelare_cant` module bindings |
| return_cant PT bridge | runtime sidewall/return truth hydration |
| Mini-module registry | ACTIVE_OPERATIONAL metadata (catalog/registry status ≠ DB active flag) |
| CPP/EIC | module `modelare_cant` ml rules |
| E2E readiness | known required inactive child blocker |

## 24. Dossier

- Child dossier exists (seed `_volum_aluminum_dossier_payload`)
- Documentary: identity, material_keys, operation_keys, task_rules, costengine_mapping
- Aggregate warning `DOSSIER_METADATA_ONLY` still applies — dossier is **not** BOM/qty SoT
- `quote_readiness_json.ready_for_quote_selector: true` conflicts with inactive DB flag — do not trust dossier for activation

## 25. UI labels (operator meaning)

| Surface | Label |
|---------|-------|
| Admin human name | Aluminiu (volumetric) |
| Availability | Cant / laterale — „Volum/cant lateral din aluminiu.” |
| Ownership card | VOLUM ALUMINIU / CANT |
| Composition authoring | module code shown as `TPL-VOLUM-ALUMINIU_v1` |
| Legacy replacement panel | says RETURN-CANT replaces Aluminiu (future/aspirational — confusing) |
| Recommended admin label | Cant / volum din aluminiu |
| Recommended role label | Return / cant (sidewall) |
| Implementation qualifier | aluminiu |

Internal codes stay; **no rename executed**.

## 26. Legacy / RETURN-CANT

- Offer-scope map: `RETURN-CANT` → frozenset `{modelare_cant}`
- LegacyReplacement UI treats RETURN-CANT as successor naming for Aluminiu module
- Runtime Aggregate still reads `TPL-VOLUM-ALUMINIU_v1`
- **Not** two active duplicate return components today

## 27. Dead code / noise

- Parent stub empty BOM is intentional identity residue, not dead
- Mini-module `operational_status=ACTIVE_OPERATIONAL` while DB inactive is **status vocabulary mismatch**, not dead code
- Historical V3/V4 return painting seeds remain outside VL Aggregate authority
- No evidence of orphan formula exclusive to Aluminiu with zero readers

## 28. Runtime path Catalog → EP

```text
Catalog PT (inactive child)
  → Module link required on VL
  → Intake V6 form (modelare_cant fields)
  → Product Truth / return_cant bridge (sidewall bag)
  → ProductDefinition preview
  → ProductAggregate (linked_module mats/ops)
  → Quantity / commercial measurement (perimeter)
  → CPP / EIC (ml rules; static NOT_TESTED)
  → Quote/Order snapshots / EP (NOT_TESTED; no materialization)
```

Readiness blocks publication while child inactive. Aggregate still **builds** with inactive required child (warning/blocker at readiness, not hard Aggregate crash).

## 29. Source-of-truth matrix

| Concern | SoT | Notes |
|---------|-----|-------|
| Template identity | `Product_templates.template_code` | `TPL-VOLUM-ALUMINIU_v1` |
| Active flag | DB `active` | false by seed policy |
| Composition requiredness | module_links.relation_type | required_module |
| BOM materials/ops | child PT JSON | Aggregate linked_module |
| Form fields | Intake V6 modular contract | modelare_cant |
| Geometry perimeter | external consume-only / parent context | not WorkOS file parse |
| Commercial line | commercial_rules_volumetric_v2 | ml |
| Internal cost | internal_cost_rules_volumetric_v2 | ml |
| Dossier | metadata only | not BOM authority |
| Publication gate | E2E readiness | required_inactive_child |

See screenshot `02_sot_matrix_catalog_to_ep.png`.

## 30. Separate calculation test

**Verdict: PARTIAL**

| Criterion | Result |
|-----------|--------|
| Child/dual-role PT exists | PASS |
| Schema / instance path | PASS (sidewall) |
| Validators / gates | PASS_WITH_WARNINGS (depth option mismatch) |
| Qty ownership | PARTIAL (perimeter dependency) |
| Ops + resources | PASS_WITH_WARNINGS (workcenters present; machine registry not fully component-surfaced) |
| Pricing refs | PASS_WITH_WARNINGS (ml refs exist; live CPP NOT_TESTED; id dualitate) |
| Component confirmation truth | FAIL / missing |
| Component-root quote | NOT_IMPLEMENTED (blocked by design) |
| Dry-run separate calc endpoint | NOT_IMPLEMENTED as dedicated component-root calc |

UI already states: `partial_ready · calculation blocked`.

## 31. Readiness / publication blockers

- Known conflict constant: `KNOWN_REQUIRED_INACTIVE_CHILD = TPL-VOLUM-ALUMINIU_v1`
- Finding: `components.required_inactive.TPL-VOLUM-ALUMINIU_v1`
- Prior System Link Check: Components BLOCKED; template_publication BLOCKED; write_performed=false
- Tests: `test_product_e2e_readiness_v1.py` expects this inactive finding
- Publication GET may show legacy_unspecified offerability metadata; **publish transition / FE fail-closed still gated by readiness** — do not treat GET `publish_allowed` as activation GO

## 32. Blocked by incompleteness vs mere inactive flag

| Layer | Reality |
|-------|---------|
| Publication hard block | **Mere inactive flag** (required child) |
| Separate calculation honesty | **Incompleteness** beyond flag: confirmation_state, material_profile, perimeter_source, depth option alignment, dual component ids, dossier overclaim |
| Conclusion | Flipping `active=true` alone would clear publication blocker but **would not** make separate calculation honest |

## 33. Missing activation evidence

Missing before any activation GO:

1. Owner commercial/ops GO for Aluminiu as required live child
2. Component confirmation_state path
3. Explicit material_profile component truth
4. Confirmed perimeter_source dependency contract
5. Align form depth options with material gates
6. Resolve/document dual ids (`comp_lateral_litere` vs `comp_volum_aluminiu_module`) for CPP/EIC/Aggregate
7. Live CPP/EIC dry-run on modelare_cant (without opening Pricing architecture)
8. Logo reuse decision (share Aluminiu vs keep LOGO-RETURN)
9. Clarify RETURN-CANT naming vs Aluminiu (docs/UI only — no rename now)
10. Dossier quote_readiness text corrected to match inactive truth (docs later)

## 34. Activation recommendation (recommendation only)

### **NO-GO**

Also acceptable phrasing: **GO_WITH_CONDITIONS** only if owner opens a dedicated activation build covering §33 — **not** recommended in this audit.

Do **not** activate only because VL publication is blocked.

## 35. Naming recommendation (no rename)

| Layer | Keep / recommend |
|-------|------------------|
| Internal code | Keep `TPL-VOLUM-ALUMINIU_v1` |
| Mini-module | Keep `modelare_cant` |
| Admin label | Prefer **Cant / volum din aluminiu** over bare „Aluminiu” |
| Role label | Return / cant / sidewall |
| Implementation | aluminiu |
| Avoid | Treating it as generic aluminium inventory SKU |

## 36. Stop conditions evaluation

| Stop condition | Triggered? |
|----------------|------------|
| Two active duplicate return components | **NO** |
| Identity vs material inseparable | **NO** (combined naming, separable contract) |
| Hourly commercial in separate calc | **NO** |
| Split incompatible pricing owners | **NO** |
| Qty needs geometry intelligence (WorkOS parse) | **NO** (consume-only) |
| Destructive migration for activation | **NO** evidence |
| Required link objectively wrong | **NO** |
| Runtime uses different component than PS shows | **WARNING only** (dual ids / RETURN-CANT aspirational copy) — not hard stop |
| Dirty-tree blocks inspection | **NO** |

**No hard stop-condition abort.** Audit completed.

## 37. Screenshots

Folder: `docs/qa/product-system-authoring-runtime-codesign-e2e/volum-aluminiu-audit/`

| # | File | Content |
|---|------|---------|
| 1 | `01_evidence_board_overview.png` | Identity / blocker / used-by / separate calc / NO-GO |
| 2 | `02_sot_matrix_catalog_to_ep.png` | Catalog→EP SoT matrix |
| 3 | `03_readiness_aluminiu_blocker.png` | required_inactive finding |

**Screenshot count: 3**

Note: Live Product System UI session was blocked by auth probe; evidence boards built from live API/DB facts.

## 38. Tests / commands / evidence consulted

Commands (read-only / evidence):

```text
git rev-parse HEAD  → 6608cdc5...
DB inspect Product_templates + module_links (async_session_maker)
GET /api/v1/product-system/templates/TPL-VOLUM-ALUMINIU_v1/component-contract
GET /api/v1/product-system/aggregate/TPL-VOLUMETRIC-LETTERS_v2
GET /api/v1/product-system/e2e-readiness/.../static
pytest tests/test_product_e2e_readiness_v1.py tests/test_product_aggregate_volumetric_v2.py tests/test_product_template_component_contracts_v1.py -q
→ 19 passed
```

Key sources: seeds `seed_tpl_volumetric_letters_v2.py`, `seed_tpl_volumetric_letters_component_modules_v1.py`, mini-module registry, commercial/internal rules, readiness service, shared volumetric contracts, PS ownership UI, prior `REAL_PRODUCT_CONFIGURATION_FINAL_REPORT.md`.

## 39. Owner decision recommendation (do not execute)

### **keep blocked**

Alternatives explicitly **not** chosen by this audit:

- prepare activation — only after §33 evidence pack
- correct relationship — link is already correct as required return child
- consolidate duplicate — no second active return BOM owner; dual ids need cleanup build later
- insufficient evidence — enough evidence for NO-GO; insufficient for GO

Exact next owner decision:

> Keep `TPL-VOLUM-ALUMINIU_v1` inactive and VL publication BLOCKED until a dedicated Aluminiu activation readiness GO closes confirmation/material_profile/perimeter/depth-alignment/id-duality — **or** consciously demote the required link (separate build). Do not activate to greenwash Publică.

## 40. Roadmap / direction awareness

Aligned with:

- Component-owned calculation boundary (docs)
- External artwork consume-only
- No ComponentTemplate table
- Product-root quote still `product_total`
- Publication honesty via inactive required child

Not claiming Build 2 / component-root Intake / Pricing Registry reopen.

## 41. Direction scores (0–100) + final pack

| Dimension | Score | Note |
|-----------|------:|------|
| Identity clarity (technical) | 78 | Real cant/return component, not bare material |
| Operator label clarity | 55 | Mixed Aluminiu / Cant / RETURN-CANT vocabulary |
| Composition correctness | 88 | Required linked_child sidewall is right |
| BOM/ops ownership | 82 | Child owns; root cleared; dual ids warn |
| Separate calculability | 48 | PARTIAL — blocked honestly |
| Quantity truth | 52 | Perimeter dependency + depth option mismatch |
| Commercial-hourly compliance | 90 | ml + anti-hourly |
| Activation readiness | 25 | NO-GO |
| Logo reuse readiness | 40 | Concept shared; template not shared |
| Publication honesty | 92 | Inactive required child blocks correctly |

### Final verdicts (return-to-parent)

| Item | Verdict |
|------|---------|
| Separate calculability | **PARTIAL** |
| Activation recommendation | **NO-GO** |
| Owner decision | **keep blocked** |
| Commercial-hourly | **PASS** (compliant) |
| Stop conditions | **None hard-triggered** |
| HEAD | `6608cdc5` |
| Report | this file |
| Screenshots | **3** |
| Commit | **none** (prefer no commit) |
