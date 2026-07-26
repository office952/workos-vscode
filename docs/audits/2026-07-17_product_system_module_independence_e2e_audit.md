# Product System Module Independence E2E Audit

**Date:** 2026-07-17  
**Build:** `PRODUCT_SYSTEM_MODULE_INDEPENDENCE_E2E_AUDIT`  
**Mode:** Audit only — no implementation, schema, seed, migration, or data mutation  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `b0306d41983700912e1420c05ece1ada4cadce12` (`b0306d4`)  
**Remote:** `https://github.com/office952/workos-vscode.git`  
**Runtime probed:** FE `:3000` (200) · BE `:8001` (docs 200)  
**Scope:** Letters + Logo + ACM only  

---

## Mini decision

```text
VERDICT = FULL_TEMPLATE_COUPLING_FOUND
MODULE INDEPENDENCE MODEL = REWORK
INTAKE ENTRY MODEL = HYBRID
ACTIVE-SCOPE READINESS = REWORK
STANDALONE MODULE PRICING = CONFLICTED
STANDALONE MODULE EXECUTION = ACTIVE_OPERATIONS_ONLY / CONFLICTED
MODELED RETURN STANDALONE = PARTIAL
LETTERS COMPONENTS = PARTIAL
LOGO COMPONENTS = BLOCKED
ACM COMPONENTS = PARTIAL
AUDIT COMMIT = DA — OWNER APPROVED
RUNTIME IMPLEMENTATION = STOP
```

**Owner-approved (2026-07-17):** this audit is Level-3 evidence. Official current truth is declared only in `/modules` + `/governance`.

Owner law not yet satisfied end-to-end:

> Un modul neales nu este o problemă. Un modul ales trebuie să se susțină singur. Template-ul combină module — nu le ține captive.

---

## 1. Repository state

| Check | Result |
|-------|--------|
| Repo | `C:/w/psiso` |
| Remote | `https://github.com/office952/workos-vscode.git` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `b0306d4` — **matches expected** |
| Staged | none for this audit |
| Dirty tree | large unrelated dirty tree — **not modified by this audit** |
| Application code | **unchanged** |
| FE / BE | up (`:3000` / `:8001`) |

**Gate:** PASS — proceed with audit.

---

## 2. UI audit (Letters / Logo / ACM surfaces)

### 2.1 Product System index — `/product-system`

| Finding | Detail | Severity |
|---------|--------|----------|
| Product-first catalog | Cards/filters/families orient operator toward complete Product Templates, not standalone modules | Medium |
| Letters root | `TPL-VOLUMETRIC-LETTERS_v2` present as active offerable | Info |
| Logo | Candidate / non-offerable root — not a sellable module chip in Product System | Medium |
| ACM | Mounting/support + linked path; casseted panel remains archived/candidate | Medium |
| Ghost / planned | `/product-system/components` and similar completeness stubs exist as planned, not runtime independence | Low |
| Pricing link | Template pages link to `/inventory/pricing?template=…` — correct ownership (PS does not own tariffs) | OK |
| Dossier link | Canonical `/product-system/blueprint-dossier` | OK |

### 2.2 Product Template page

| Area | Observed truth | Independence impact |
|------|----------------|---------------------|
| Identity / version / family | Code-suffix versioning (`_v2`); family grouping only | OK |
| Components / modules | Parent BOM JSON + module links + mini-module registry (Letters) | Modules not first-class sellable entities in UI |
| Settings / defaults | Mixed template + FE + company | Settings do not travel cleanly with a module |
| Dependencies | Link triggers + activation_kind; PD ignores offer_scope | **Full-template coupling** |
| Operations / formulas | On template / child JSON | Composed by parent Aggregate merge |
| Intake contract | Letters modular form contract + generic renderer pilot | Partial |
| Commercial measurements | Not owned on template page — Aggregate | OK conceptually |
| Readiness / warnings | Template-level completeness language still present | Risk of inactive-module “missing” framing |
| Edit / save | Standard PS draft save — out of scope to change | — |

### 2.3 Canonical Dossier — `/product-system/blueprint-dossier`

| Check | Result |
|-------|--------|
| Canonical route | Yes (`CANONICAL_ROUTES.dossier`) |
| Legacy `/product-system/dossier-completion` | **Redirect** → blueprint-dossier (`App.tsx` Navigate replace) — not a second active page |
| Tabs / sections | Blueprint documentation of **full** Letters (and linked) graph — documents complete product, not sold-scope subset |
| Module links / ops / task rules | Present for parent product dossier | Expected for documentation; must not drive inactive-module readiness |
| Terminology | Control Center publishes canonical concepts; dossier UI still product-document oriented | Low–Medium |
| Empty / legacy | Historical completion dashboard retired via redirect | OK |

### 2.4 Intake V6 — `/intake-v6`

| Area | Truth | Severity |
|------|-------|----------|
| Product/template selection | Letters root primary; Logo fail-closed / non-offerable; ACM via mounting/composition | Product-first |
| Module selection | **`offer_scope`**: `full_product` (default) vs `component_subset` with `FACE \| RETURN-CANT \| BACK \| LIGHTING \| ELECTRICAL` | Key hybrid lever |
| UI panel | `IntakeV6OfferScopePanel` — operator can select RETURN-CANT only | Proven in FE tests |
| Field visibility | `intakeV6SoldScopeVisibility` hides unsold FACE/BACK/LIGHTING/ELECTRICAL when subset | OK for operator fields |
| Defaults | FE / finish defaults can still look pre-configured (depth, materials, lighting) | Medium — inactive look “present” |
| Mounting / ACM | Orthogonal to sold-scope chips (FINISH/MOUNTING deferred in Slice1) | Gap for ACM-as-sold-module |
| Validation / readiness | Offer-scope confirmation + dependency validator; **PD activation still full-template** | **Critical** |
| Calculation preview | Live-calc offer-scope pytest **FAILING** at HEAD — full-module commercial lines still appear | **Critical** |
| Quote handoff | Relies on payload `offer_scope` + CPP filter; path-dependent | Conflicted |
| Terminology | Sold modules use FACE / RETURN-CANT …; runtime mini-modules use `modelare_cant` etc. | Alias map exists |

### 2.5 Inventory / Pricing

| Route | Role | Independence check |
|-------|------|-------------------|
| `/inventory` | Materials / stock | PS references material keys — does not own stock |
| `/inventory/pricing` | Pricing Registry UI | Canonical; `/pricing` redirects here |
| Product System | Links to pricing keys; finish workshop cites registry | Correct separation |

### 2.6 Modules / Governance — `/modules`, `/governance`

| Check | Result |
|-------|--------|
| Concept dictionary | Wired via `productSystemCanonicalModel.ts` (Letters/Logo/ACM stabilization) |
| Independent module calculation | **Not expressed** as operator truth |
| Active-scope readiness | **Not expressed** |
| Composed vs standalone | **Not expressed** |
| Sold-scope / offer_scope | **No Control Center matches** for sold-scope language |
| Impact | Corrections prepared in §20 — **not applied in this audit** |

### 2.7 Representative UI findings (structured)

| # | URL | Page / section | Visible truth | Source | Expected (owner law) | Severity |
|---|-----|----------------|---------------|--------|----------------------|----------|
| U1 | `/intake-v6` → Review | Offer Scope | Default full product; chips for subset | FE offer_scope panel | Hybrid entry OK if readiness respects selection | Info |
| U2 | `/intake-v6` → Review | Sold subset RETURN-CANT | Fields for face/back/LED hidden | `intakeV6SoldScopeVisibility` | Inactive modules silent | OK |
| U3 | `/product-system` | Catalog | Product cards, not module services | PS index | Module-first not available | Medium |
| U4 | `/product-system/blueprint-dossier` | Dossier | Full Letters graph documentation | Blueprint dossier | Doc OK; must not = readiness | Low |
| U5 | `/product-system/dossier-completion` | Redirect | Navigates to blueprint-dossier | `App.tsx` | No second dossier | OK |
| U6 | `/modules` / `/governance` | Control Center | Canonical concepts; no sold-scope independence | `currentTruthControlCenter` | Should state active-scope law | Medium |
| U7 | `/inventory/pricing` | Registry | Tariff ownership outside PS | Pricing page | PS must not own prices | OK |

Screenshots: not captured this pass (runtime API/code evidence preferred). Re-capture optional for owner review.

---

## 3. Product / template inventory (locked scope)

| Product | Template code | Usage | Standalone sellable root? | Notes |
|---------|---------------|-------|---------------------------|-------|
| Letters | `TPL-VOLUMETRIC-LETTERS_v2` | ACTIVE | Yes (full product) | Only full mini-module registry |
| Logo | `TPL-VOLUMETRIC-LOGO_v1` | PARTIAL / candidate | No (`root_offerable=false`) | Child LOGO-* TPLs; fail-closed |
| ACM mounting support | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | PARTIAL | Partial (linked / support) | Not Slice1 sold chip |
| ACM casseted panel | `TPL-ACM-CASSETTED-PANEL*` | Archived / future | No | Out of activation |

Child / stand-in templates (not independent Product System sell SKUs today):

- `TPL-VOLUM-ALUMINIU_v1` — return/cant child  
- Metal premount / ACM boxed support — mounting chain  
- Ghost policy codes `TPL-VOLUMETRIC-FACE_v1` etc. — no DB seed  

---

## 4. Component / module inventory

| Product | Module/component | Physical/functional meaning | Settings owner | Inputs | Outputs | Dependencies | Standalone candidate | Current status |
|---------|------------------|-----------------------------|----------------|--------|---------|--------------|----------------------|----------------|
| Letters | `geometry_svg` | Analyzer / geometry facts | PD + workspace SVG | SVG / quote_geometry | Geometry facts | File prep | Calc-only (not sold) | Always when geometry present |
| Letters | `debitare_fata` / FACE | Letter face cut | Mixed FE + finish | Face material, area | Face BOM / commercial face ML | Geometry | Yes (Slice1 FACE) | PD always_on when analysis_ready |
| Letters | `modelare_cant` / RETURN-CANT | Modeled return / cant | Child TPL + finish return | Perimeter, depth, return material/finish | Return profile ML + ops | **Hard:** perimeter geometry | **Yes — primary case** | Representable in UI+BOM filter; PD not scoped |
| Letters | `debitare_spate` / BACK | Backing panel | Mixed | Back material, area | Back m² line | Geometry / face area calc | Yes (Slice1 BACK) | PD always_on |
| Letters | `sistem_led` / LIGHTING+ELECTRICAL | Illumination + PSU bucket | Finish lighting fields | Illuminated, lighting type | LED/PSU lines | Conditional lit | Partial (whole-module bucket) | Conditional in PD; Slice1 maps both to `sistem_led` |
| Letters | `finisaje` | Finish + mounting template bucket | Finish groups + FE | Finish selections | Finish / sablon lines | Conditional / always | Deferred sold code FINISH | PD **always_on** (or conditional if template) |
| Letters | `structura_suport` | Support / bars / ACM mount | Mounting solution + composition | Mounting system | Support ops/materials | Conditional bars/ACM | Mount path; FINISH/MOUNTING deferred | PD inactive unless bars/composition |
| Letters | Assembly (implicit ops) | Bonding / assembly ops on full product | Template ops | Active components | Ops / tasks | **Composition** for complete letters | No as sold Slice1 | Pulled with parent Aggregate |
| Logo | LOGO face/body children | Logo body composition | Logo child TPLs | Logo geometry/bindings | Partial aggregate | Logo composition | Not commercial root | PARTIAL / blocked as root |
| Logo | `electrica_logo` | Future electrical | Reserved | — | — | — | No | FUTURE_RESERVED |
| ACM | Boxed mounting support | Support structure for letters | ACM child template | Mount selection | Mount commercial/ops when active | Composition under Letters | Partial as linked module | PARTIAL |
| ACM | Panel / cassette full product | Full ACM cassette | Archived template | — | — | — | Future | BLOCKED (out of scope activation) |

**Aliases / ghosts:** FACE↔`debitare_fata`, RETURN-CANT↔`modelare_cant`, BACK↔`debitare_spate`, LIGHTING/ELECTRICAL↔`sistem_led`; ghost FACE/BACK/LED/FINISH TPL codes in policy maps.

---

## 5. Settings ownership (per module — condensed)

| Setting | Owner | Storage | Default source | Workspace override | Derived? | Consumer | Classification |
|---------|-------|---------|----------------|--------------------|----------|----------|----------------|
| SVG / analysis identity | Intake workspace | workspace payload | Analyzer | Yes | Partial | PD geometry | workspace |
| Letter depth / return height | Mixed FE + finish | `finish_setup` / defaults | FE defaults (e.g. 60 mm) | Yes | No | Return calc | **hidden FE default risk** |
| Face / back materials | Mixed FE option maps + inventory keys | finish / letter groups | FE maps | Yes | No | Aggregate / CPP | company option + workspace |
| Return material / profile | Return child + finish | finish / module fields | Template/FE | Yes | No | `modelare_cant` | module-owned aspirational / **storage mixed** |
| Illumination flags | Finish | `illuminated`, `lighting_system_type` | FE defaults (`led_modules` risk) | Yes | No | PD `sistem_led` | workspace / conditional |
| Mounting system | Mounting solution | finish + composition | FE / composition | Yes | No | `structura_suport` / ACM | workspace + composition |
| Offer scope sold modules | Intake operator | `payload.offer_scope` | Default `full_product` | Yes | No | CPP/BOM/Exec filters; **not PD** | workspace selection |
| Commercial rates | Pricing Registry | `/inventory/pricing` | Company rates | No (lookup) | No | CPP 7G | commercial |
| Planning minutes | Aggregate ops formulas | Aggregate | Template formulas | Derived | Yes | ExecutionPlan | execution / derived |

**Defects:**

1. Frontend option duplication vs Product System contract.  
2. Hidden defaults make inactive modules appear configured.  
3. Parent-template settings reused by single modules (return depth on letters finish).  
4. Settings cannot fully travel with a module without Letters parent payload shape.

---

## 6. Composed vs standalone matrix

| Module | Composed works | Standalone representable | Standalone Intake inputs | Standalone PD | Standalone Aggregate | Standalone CPP | Standalone Execution | Gap |
|--------|---------------:|-------------------------:|--------------------------|---------------|----------------------|----------------|----------------------|-----|
| FACE | Yes | Partial (offer_scope) | Visibility OK | No (always_on with siblings) | No native filter | BOM FACE-only **broken** (empty); live-calc unfiltered | Preview filter if snapshot scoped | PD + pricing path conflict |
| RETURN-CANT / `modelare_cant` | Yes | **Yes via component_subset** | Perimeter + return fields | No — PD still activates face/back/finisaje | Aggregate merges parent/dossier | BOM RETURN-only **PASS**; live-calc **FAIL** (extra lines) | Exec sold-scope reader exists | PD readiness + live-calc + Aggregate |
| BACK | Yes | Partial | Visibility OK | No | No | Path-dependent | Same | Same class as FACE |
| LIGHTING / ELECTRICAL | Yes when lit | Partial (whole `sistem_led`) | Visibility OK | Conditional PD | Partial | Mapped both→`sistem_led` | Task filter tests exist | Op split deferred |
| FINISH | Yes | Deferred Slice1 | Not sold chip | PD always_on | Pulls with parent | Often present when unscoped | Via finisaje ops | Deferred + always_on |
| structura_suport / ACM | When mounted | Linked, not Slice1 sold | Mounting UI | Composition-gated | Linked child | Mount lines when active | Partial | Not module-first sell |
| Logo body | Composition only | No as commercial root | Candidate | Fail-closed | Partial | Ownership gap | Unverified as root | BLOCKED as root |
| ACM cassette product | N/A archived | No | No | No | No | No | No | Out of activation |

**Smallest contract change (no implementation now):**

1. ProductDefinition `_resolve_module_state` must accept resolved `offer_scope` / sold runtime set → `validate(active_module)` only.  
2. One pricing path (live-calc + BOM + CPP) must share `resolve_pricing_active_modules`.  
3. Aggregate emit (or filter) components/ops/measurements by active runtime modules before commercial/execution consumers.  
4. Keep Intake `component_subset` as the hybrid entry; do not invent new templates for return-only.

---

## 7. Canonical case — modeled return only (E2E trace)

### Intent

```text
Customer requests modeled return/cant only.
Upstream: analyzed perimeter or approved direct perimeter.
Active: modelare_cant (+ geometry/perimeter calc) + selected finishing if applicable.
Inactive: face, backing, illumination, electrical, support, mounting, print, unrelated assembly.
```

### Representation mechanism (existing)

- Intake: `offer_scope.mode = component_subset`, `sold_modules = ["RETURN-CANT"]`  
- Map: `RETURN-CANT` → runtime `{modelare_cant}`; calc `{GEOMETRY, PERIMETER}`  
- Commercial rule: `modelare_cant_aluminiu` / `module_code=modelare_cant`

### Trace (current HEAD)

| Stage | Fields requested | Modules activated | Blockers / warnings | Components / materials / qty | Commercial lines | Execution tasks |
|-------|------------------|-------------------|---------------------|------------------------------|------------------|-----------------|
| Intake V6 UI | Return-relevant finish + geometry; face/back/LED **hidden** when subset confirmed | Operator sold: RETURN-CANT | Offer-scope confirm + dependency rules; global analysis still required | N/A (UI) | N/A | N/A |
| ProductDefinition | Missing fields for **selected modules list that still includes face/back/finisaje** when analysis ready | Live probe (no offer_scope): `modelare_cant,debitare_fata,debitare_spate,sistem_led,finisaje,geometry_svg` | Full-template readiness coupling | PD does not shrink to return-only | — | — |
| ProductAggregate | Parent + dossier + linked modules merge | Not offer_scope-aware in `product_aggregate_service` | May include unrelated parent BOM/ops | Full Letters graph risk | Measurements may include inactive scopes unless filtered later | Task rules from dossier (full) |
| Commercial measurements | Perimeter-driven for return | Should be return-only | Gap if Aggregate emits face area etc. | Return profile ML expected | — | — |
| CPP 7G | Rule filter via `resolve_pricing_active_modules` | BOM path RETURN-only **tests PASS** | Live-calc path **tests FAIL** — face/back/finisaje still priced | Path-dependent | Face/LED/support **must be absent** for return-only — **not guaranteed on live-calc** | — |
| Quote preview | Depends on dry-run path used | Same conflict | Inactive-module money = defect | — | Risk of unrelated lines | — |
| Execution preview | `execution_sold_scope_reader` + `include_task_rule_for_sold_scope` | Filters when snapshot carries sold_scope | If Aggregate/dossier unscoped and snapshot missing scope → leak | — | — | Active-ops-only **when scope frozen** |

### Live PD probe (workspace without offer_scope)

```text
tpl=TPL-VOLUMETRIC-LETTERS_v2
PD selected=modelare_cant,debitare_fata,debitare_spate,sistem_led,finisaje,geometry_svg
PD inactive=structura_suport,electrica_logo
```

### Defect summary for this case

Any warning/blocker/commercial line/op for face, back, LED, PSU, support, mounting, print while only RETURN-CANT is sold = **full-template assumption defect** (grouped in §16).

---

## 8. Active-scope readiness audit

Required invariant:

```text
validate(active_module)
NOT validate(full_parent_template)
```

| Rule / source | Applies when | Owner | Blocking level | Current behavior | Correct? |
|---------------|--------------|-------|----------------|------------------|----------|
| PD `_resolve_module_state` face/back/return | analysis_ready | ProductDefinition | Module selection / missing fields | **always_on** for all three | **No** |
| PD `finisaje` | nearly always | ProductDefinition | Missing finish fields | **always_on** (unless mounting_template_enabled → conditional) | **No** for subset |
| PD `sistem_led` | illuminated | ProductDefinition | pending/inactive | Conditional | Partial OK |
| PD `structura_suport` | bars / composition | ProductDefinition | inactive/active | Conditional | OK direction |
| Intake FE sold visibility | component_subset | Frontend | Hide fields | Hides unsold | Yes (UI only) |
| Offer-scope confirmation | subset selected | Intake readiness | Blocks confirm | Requires valid sold set | Yes |
| Sold-scope dependency validator | confirmed deps | Intake / snapshot | Blocker messages | Scope-aware | Partial |
| Form contract required fields | active_modules from PD | Form contract | Required list | Follows PD activation → **inherits coupling** | No |
| Live-calc / CPP lines | pricing | Commercial | Money lines | Live-calc ignores subset (pytest fail) | **No** |
| BOM costable filter | BOM build | Cost/BOM | Materials/ops | RETURN-only OK; FACE-only empty | Conflicted |
| Execution sold-scope reader | plan preview | Execution | Task inclusion | Filters when scope present | Yes when wired |
| Dossier completeness language | PS UI | Documentation | Soft warnings | Full product doc | OK if non-blocking |

**Detected anti-patterns:**

- Required parent modules enforced when not selected (face/back with return-only).  
- Warnings / missing fields from complete-product assumptions.  
- `always_on` modules that should be mode-dependent.  
- Quote/live-calc blockers or lines from inactive modules.  
- Global field lists driven by unscoped PD.

---

## 9. Dependency classification

| Dependency | Type | Example | Encoded today as | Correct encoding? |
|------------|------|---------|------------------|-------------------|
| Perimeter geometry for return | Hard technical | RETURN-CANT needs PERIMETER | `derive_calc_modules` | Yes |
| Geometry file for any sold subset | Hard technical (calc) | GEOMETRY calc module | Always with any sold | Yes |
| Paint/color on return | Conditional | Painted return finish | Finish fields | Partial |
| Face↔return bonding | Composition | Complete volumetric letters | Parent ops / Aggregate | Often treated as universal — **incorrect for return-only** |
| Face area for face commercial line | Commercial | FACE measurement | FACE_AREA calc | OK when FACE sold |
| LED count | Commercial / conditional | ELECTRICAL | LED_COUNT calc | OK when electrical sold |
| Mount bars / ACM | Composition / conditional | Support under letters | `structura_suport` | OK when gated |
| Full Letters module set | Composition (template) | Default full_product | PD always_on | **Incorrect as universal** |

---

## 10. ProductDefinition audit

| Expectation | Current | Verdict |
|-------------|---------|---------|
| Receives selected scope | Workspace payload may contain `offer_scope` | Present in payload; **not used in `_resolve_module_state`** |
| Activates only selected + real prerequisites | Activates face/back/return/finisaje when analysis ready | **FAIL** |
| Does not activate full template automatically | Default path ≈ full Letters operational set | **FAIL** for independence |
| Missing fields only for active scope | Missing collected for always_on/active set | **FAIL** when scope subset |
| Distinguishes standalone vs composed | No first-class mode flag in PD | **FAIL** |
| Preserves provenance | Source context present | OK |
| Readiness specific to active scope | Tied to unscoped activation | **FAIL** |

Architectural principle (activation for concrete configuration) is stated correctly in docs; **runtime PD still validates full parent operational set**.

**Additional PD evidence (explore agents):**

- `pending` modules sit in `optional`, not `inactive` → their required bindings **still block** readiness.
- `mounting_system` remains required via `finisaje` even when `structura_suport` is inactive.
- Form-contract `valid_combinations` / `invalid_combinations` are **documentation only** — PD does not execute them.
- PD `always_on` for `modelare_cant` ≠ cost-graph activation (cost needs `volum_aluminum` composition node).
- Empty finish tends `_is_illuminated` toward true → LED often `pending` rather than inactive.
- Logo: no live modular PD form path. ACM: separate standalone PD builder (`structura_suport` only), not Letters mini-module subset.

---

## 11. ProductAggregate audit

| Expectation | Current | Verdict |
|-------------|---------|---------|
| Emit only selected components/materials/ops/measurements | `product_aggregate_service` merges parent + dossier + linked modules; **no sold_scope filter in service** | **FAIL / gap** |
| Cost projection filter | `resolve_cost_active_modules` intersects offer_scope when present | Partial downstream |
| Task rules | From dossier `task_rules_json` (full product) | Risk of inactive ops unless execution filter applied |
| Parent/dossier merge | Explicit merge design | Coupling vector for standalone |

Standalone Aggregate = **not native**; filtering is deferred to cost/CPP/execution layers unevenly.

**Additional Aggregate / CPP / Execution evidence:**

- Explicit composition graph **keeps all `provenance=parent` BOM** — only inactive registry children are stripped.
- Workspace attach calls commercial measurements with `active_modules=None` → **no module_gate filtering** on Aggregate bundle (face/back/finish/LED quantities can resolve latently).
- CPP still prices only sold runtime modules when offer_scope resolves (return-only → `modelare_cant_aluminiu`); over-broad measurements stay latent if `_rule_applies` skips them.
- Execution sold-scope: includes `vector_prep` always; `return_face_bonding` aliased to `modelare_cant` (Aggregate tags bonding as `asamblare`).
- No dedicated return-paint commercial line — painting maps to `finisaje` and drops in return-only scope.
- `DOSSIER_COMPONENT_MINI_MODULE` in Aggregate service is **dead**; live map is `DOSSIER_COMPONENT_TO_MODULE` in registry.

---

## 12. CPP / commercial audit

| Item | RETURN-CANT only | Notes |
|------|------------------|-------|
| Measurement | Return profile ML (perimeter × depth semantics) | Rule `modelare_cant_aluminiu` |
| Pricing key / rule | Commercial rules volumetric v2 + registry lookups | Do not invent missing rates — gap if registry empty |
| Unit | ML / profile | |
| Unrelated lines must be absent | face, back, LED, PSU, support, mounting, print | **Required** |
| BOM filter evidence | `test_return_cant_only_bom_excludes_face` **PASS** | Good path |
| FACE-only BOM | **FAIL** (empty modules) | Over-filter defect |
| Live-calc offer_scope | **FAIL** — still emits `debitare_fata`, `modelare_cant`, `debitare_spate`, `finisaje` | Under-filter defect |
| CPP authority | Remains monetary authority (7G) | Keep |
| Minutes as price | Forbidden (TE2E-028) | Preserve |

**STANDALONE MODULE PRICING = CONFLICTED** (path-dependent).

---

## 13. Execution audit

| Item | Truth |
|------|-------|
| Operations source | Aggregate / dossier task rules |
| Sold-scope filter | `execution_sold_scope_reader_service` + include helpers |
| Preview vs materialize | Preview/read-only only in this audit — no live task materialization |
| RETURN-only expectation | Only return-related ops/tasks when snapshot carries sold_scope |
| Risk | Unscoped Aggregate + missing snapshot scope → inactive tasks appear |
| Verdict | **ACTIVE_OPERATIONS_ONLY** when filter wired; **CONFLICTED** if scope not frozen into snapshot |

---

## 14. Warning register

### Group A — Full-template assumption warnings (one defect group)

All readiness/missing-field/commercial/execution warnings caused by treating Letters as always fully active while `offer_scope=component_subset`:

- PD missing fields for unsold face/back/finisaje  
- Form contract required fields inherited from unscoped PD  
- Live-calc commercial lines for unsold modules  
- Dossier/Aggregate completeness language misread as blockers  
- Quote gates that assume full product  

**Do not open one micro-task per message — fix at activation/filter authority.**

### Other classifications

| Class | Examples |
|-------|----------|
| Relevant active-scope | Missing perimeter for RETURN-CANT; invalid offer_scope contract |
| Irrelevant inactive-module | Face material missing when FACE not sold |
| Compatibility | Logo root offerability fail-closed |
| Internal-confidence | Analyzer confidence soft notices |
| Commercial blocker | Empty pricing set from validation errors; live-calc pollution |
| Execution blocker | `blocked_missing_sold_scope` when plan requires frozen scope |
| Dead/legacy | Second dossier route (redirected); ghost FACE TPL codes |

---

## 15. Letters / Logo / ACM status

### Letters

```text
LETTERS COMPONENTS = PARTIAL
```

- Composed full product: strong.  
- Slice1 sold chips: UI representable.  
- Independence law: broken at PD + Aggregate + live-calc.  
- Modeled return: PARTIAL (best candidate).

### Logo

```text
LOGO COMPONENTS = BLOCKED (as commercial root) / PARTIAL (composition children)
```

- Not offerable root; no Slice1 sold-module path equivalent.  
- Child templates exist; commercial ownership gap as root.  
- Do not invent activation.

### ACM

```text
ACM COMPONENTS = PARTIAL
```

- Boxed mounting support linked under Letters / optional standalone support template.  
- FINISH/MOUNTING deferred from component_subset V1.  
- Full casseted ACM product out of activation scope.  
- Not yet a first-class independent sell module in offer_scope.

---

## 16. Current vs target diagrams

### Current truth

```text
Operator → Product Template (Letters)
         → Intake defaults look fully configured
         → offer_scope subset (optional UI)
              ├─ FE field visibility: scoped  ✓
              ├─ ProductDefinition activation: FULL TEMPLATE  ✗
              ├─ ProductAggregate merge: PARENT+DOSSIER GRAPH  ✗
              ├─ Live-calc CPP lines: FULL MODULE SET  ✗
              ├─ BOM/CPP filter: sometimes scoped  ~ 
              └─ Execution preview: scoped IF snapshot has sold_scope  ~
```

### Target truth

```text
Request scope
  → selected modules/components (sold + hard calc prerequisites only)
  → module-owned settings
  → active-scope ProductDefinition
  → selected ProductAggregate graph
       ├→ selected commercial measurements → CPP 7G
       └→ selected operations → ExecutionPlan preview
Inactive modules: no missing, no warning, no line, no task.
```

---

## 17. UI entry-model options

| Model | Description | Fit today | Recommendation |
|-------|-------------|-----------|----------------|
| PRODUCT_FIRST | Pick complete product, configure modules | Default PS + Intake | Insufficient alone |
| MODULE_FIRST | Pick standalone service (return only) from catalog | Not in PS index | Premature as sole model |
| HYBRID | Start product **or** module; both compile to same module contracts | Offer-scope subset exists under Letters product | **Recommend for current scope** |

**Recommendation:** **HYBRID** — keep Letters product as composer; use `component_subset` as module/service entry; make PD/Aggregate/CPP/Exec share one active-scope authority. Do not implement in this audit.

---

## 18. Modules / Governance impact (corrections prepared — not applied)

Exact corrections for a later docs-only / CC update:

1. Add Control Center truth: **Active-scope readiness law** (unselected ≠ incomplete).  
2. Document Slice1 sold modules ↔ runtime mini-modules map.  
3. State independence status: Letters PARTIAL; Logo BLOCKED as root; ACM PARTIAL linked.  
4. Flag PD always_on face/back/return/finisaje as **known coupling defect**.  
5. Flag live-calc vs BOM filter conflict.  
6. Keep Inventory `/inventory` and Pricing `/inventory/pricing` as external owners.  
7. Do not claim independent module calculation until PD is scoped.

---

## 19. Recommended coherent build (after owner GO)

**One build — not micro-fixes:**

`ACTIVE_SCOPE_MODULE_INDEPENDENCE_V1` (Letters Slice1 only)

1. PD activation respects `resolve_offer_scope` runtime sold set + calc prerequisites.  
2. Unify live-calc / BOM / CPP on `resolve_pricing_active_modules`.  
3. Aggregate emit or hard-filter by active modules before measurements/ops handoff.  
4. Prove modeled-return-only E2E: Intake → PD → Aggregate → CPP → Quote dry-run → Execution preview with **zero** unrelated lines/tasks/warnings.  
5. Update Modules/Governance truth after proof.  

Out of bounds until later: new templates, Logo root activation, ACM cassette product, Pricing Registry 7I, renderer expansion, schema.

---

## 20. Owner decision pack (APPROVED)

```text
MODULE INDEPENDENCE MODEL = REWORK
INTAKE ENTRY MODEL = HYBRID
ACTIVE-SCOPE READINESS = REWORK
STANDALONE MODULE PRICING = CONFLICTED
STANDALONE MODULE EXECUTION = ACTIVE_OPERATIONS_ONLY / CONFLICTED
MODELED RETURN STANDALONE = PARTIAL
LETTERS COMPONENTS = PARTIAL
LOGO COMPONENTS = BLOCKED
ACM COMPONENTS = PARTIAL
AUDIT COMMIT = DA
RUNTIME IMPLEMENTATION = STOP
```

Permanent owner law:

```text
UN MODUL NEALES NU ESTE O PROBLEMA.
UN MODUL ALES TREBUIE SA SE SUSTINA SINGUR.
TEMPLATE-UL COMBINA MODULE — NU LE TINE CAPTIVE.
```

Documentation governance (post-audit registration build):

```text
OFFICIAL CURRENT DOCUMENTATION = /modules + /governance
UNREGISTERED SYSTEM = may be audited; may not be SoT / E2E / production-ready
```

---

## 21. Code / contract consumers (actual runtime)

| Concern | Primary consumers (runtime) |
|---------|-----------------------------|
| Product Families | Availability, Intake binding labels |
| Product Templates | Availability, PD, Aggregate, PS UI |
| Mini-modules | Form contract, PD activation, commercial module_code, cost projection |
| Offer scope | FE visibility/readiness; `offer_scope_resolver_service`; BOM/CPP/cost filters; execution sold-scope reader |
| ProductDefinition | Intake preview, form required fields, composition blockers |
| ProductAggregate | CPP measurements, ExecutionPlan task_contract, cost graph |
| Commercial rules | CPP 7G |
| Dossier | Aggregate task rules metadata; Blueprint UI |

JSON field existence alone is insufficient — offer_scope on PD path is the clearest non-consumer example.

---

## 22. Pytest evidence (this audit)

| Suite | Result | Meaning |
|-------|--------|---------|
| `test_return_cant_only_bom_excludes_face` | PASS | BOM can scope return-only |
| `test_return_cant_perimeter_rows_without_face_pricing` | PASS | Return materials without face ops |
| `test_face_only_bom_excludes_other_modules` | FAIL | FACE-only → empty modules |
| `test_face_and_return_cant_bom` | FAIL | Face missing from dual set |
| `test_live_calc_paths_filter_by_offer_scope[*]` | FAIL | Live-calc still full module set |
| Live PD workspace probe | Full selected set without offer_scope | PD coupling |

---

## 23. Files created

- `docs/audits/2026-07-17_product_system_module_independence_e2e_audit.md` (this file)  
- `docs/worklog/realignment/2026-07-17_product_system_module_independence_e2e_audit.md`

## 24. Commit status

```text
AUDIT COMMIT = DA (owner-approved)
RUNTIME IMPLEMENTATION = STOP
```

This file is Level-3 evidence. It does not override `/modules` + `/governance`.
