# GRADI-CURAT PRICING TRUTH AUDIT — FINAL OWNER REPORT

**Task:** WORKOS-GRADI-CURAT-PRICING-TRUTH-AUDIT-FINAL-OWNER-REPORT  
**Mode:** PLAN MODE + READ-ONLY RUNTIME AUDIT  
**Worktree:** `C:\w\psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Audit baseline HEAD:** `99d5c71` (matches current `HEAD`)  
**No product-code / pricing / registry / Product System / runtime writes in this phase.**

---

## 1. Verdict

| Field | Value |
|-------|-------|
| Audit classification | `GRADI_CURAT_PRICING_FIRST_BLOCKER_FOUND` |
| Commercial safety | `COMMERCIAL_PARTIAL_NOT_CONFIRMABLE` |
| Primary blocker category | `COMMERCIAL_RULE` |
| Primary symptom | Logo commercial pricing absent on letters+logo composition |
| Can operator Confirmare → commercial Quote now? | **NO** |

Live commercial total prices **letters only**. Logos contribute to **internal** material-breakdown cost but **not** to CommercialPriceProposal (CPP). Packaging and site-mount commercial lines are null/owner-required and excluded from the sum.

---

## 2. Repository truth

- Branch / HEAD: `feature/product-system-active-path-isolation-v1` @ `99d5c71`
- Protected areas not modified
- Seed file for logo exists in repo history (`backend/seeds/seed_tpl_volumetric_logo_v1.py`) — **not** proof of live DB registration
- Commercial catalog used at runtime: `commercial_rules_volumetric_v2` (temporary local catalog until step 7i)
- V6 missing-price predicate: [`backend/services/intake_v6_offer_scope_live_calc_service.py`](backend/services/intake_v6_offer_scope_live_calc_service.py) `_is_price_missing_material`

---

## 3. Runtime truth

| Surface | Value |
|---------|-------|
| Backend | `http://127.0.0.1:8001` (reused; not restarted) |
| Frontend | `http://127.0.0.1:3000` (reused; not restarted) |
| Auth probe | Bearer `__DEV_BYPASS_TOKEN__` |
| Canonical commercial read | `GET /api/v1/intake-v6/workspaces/{id}/priced-quote-dry-run` |
| Internal cost read | material-breakdown on workspace (EUR) |
| PD/PA root | letters `TPL-VOLUMETRIC-LETTERS_v2` |
| Logo standalone PD/PA | **404 / template_not_found** |
| Template availability | 8 templates; **`TPL-VOLUMETRIC-LOGO_v1` absent** |
| Direct CPP POST | `commercial_price_preview_not_found` (404) even for letters; dry-run still builds CPP internally |

---

## 4. Workspace truth

| Field | Value |
|-------|-------|
| Workspace id | `11891d68-c4c8-4719-acc5-f8fcb22a44af` |
| SVG fixture path (not dumped) | `C:\Users\offic\Desktop\fisiere-teste-svg\gradi-curat.svg` |
| Root template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Letter groups | `pseudo:maria`, `pseudo:soare`, `pseudo:ana`, `pseudo:gradinita` |
| Artwork | Logo 1 / Logo 2 (`logo_instance_001/002`), execution `print_laminate` |
| Backing | `forex_10_no_bevel` |
| Mounting | `installation_template` sentinel; `template_code: null` |
| Composition dry-run | letters + logo items both `status: suggested` |
| Linked PD segments | 2 logo segments; binding confirmed; finish pending; readiness **blocked** |

---

## 5. Current UI totals

### A) Commercial RON (authoritative for Confirmare)

| Field | Live value |
|-------|------------|
| Exact value (gross) | **2606.96 RON** |
| Net | **2154.51 RON** |
| VAT rate | **21%** |
| VAT amount | **452.45 RON** |
| Currency | RON |
| Source | `priced-quote-dry-run` → `commercial_totals` / authority `commercial_price_proposal_7g` |
| Net/gross | Net + VAT → gross |
| Completeness | **PARTIAL** (letters CPP only; logos commercially omitted; ambalare/montaj null) |
| Included | Letters commercial modules (face CNC, return, back, LED, PSU, finish, sablon) |
| Excluded | Logo 1/2 commercial; ambalare; montaj șantier |
| UI label | “Valoare estimată cu TVA” ← `commercial_totals.total_gross` |
| Label honesty | **Partially honest** on VAT; **misleading** as full-product commercial total |

### B) Internal EUR (not commercial)

| Field | Live value |
|-------|------------|
| Exact value | **725.16 EUR** |
| Source | material-breakdown `totals.material_cost_total` / `estimated_cost_total` |
| Completeness | Internal estimate with logo material/ops present |
| Label honesty | Must not be read as commercial RON equivalent |

### C) Stale / non-live values

| Value | Status |
|-------|--------|
| **2.587,94 RON** | **NOT** current live dry-run gross. Do not mix with 2606.96. Treat as older screenshot / prior config recollection only. |
| Diagnostic cost-plus gross **5922.74 RON** | `diagnostic_only: true`; not CPP authority |

### D) Quote write gates (live dry-run)

- `can_create_quote_snapshot`: **false**
- `can_write_quote_totals`: **false**
- `pricing_status`: `V6_PRICED_DRY_RUN_READY` (dry-run ready ≠ commercial complete for this product)

---

## 6. CommercialPriceProposal truth

**Path:** dry-run → CPP 7G (`commercial_rules_volumetric_v2`)  
**Subtotal commercial (priced lines):** **2154.506 RON** (= live net)  
**Currency:** RON (no FX on official path)  
**Active modules:** `debitare_fata`, `debitare_spate`, `finisaje`, `modelare_cant`, `sistem_led`

### Priced CPP lines (letters only)

| line key | description | component | rule | qty | unit | unit price | line total | currency | included |
|----------|-------------|-----------|------|-----|------|------------|------------|----------|----------|
| `debitare_fata` | Debitare față litere | `comp_face_litere` | `VOL_V2_FACE_CNC_ML` | 21.1675 | ml | 25.0 | 529.1875 | RON | yes |
| `modelare_cant_aluminiu` | Modelare cant aluminiu | `comp_lateral_litere` | `VOL_V2_RETURN_PROFILE_ML` | 21.1675 | ml | 30.0 | 635.025 | RON | yes |
| `debitare_spate` | Debitare spate litere | `comp_spate_litere` | `VOL_V2_BACK_CNC_M2_DEV_BRIDGE` | 1.2638 | m2 | 20.0 | 25.276 | RON | yes (dev bridge) |
| `sistem_led_module` | Sistem LED — module | `comp_led_litere` | `VOL_V2_LED_MODULE_PIECE` | 145 | buc | 5.0 | 725.0 | RON | yes |
| `sursa_led` | Sursă LED (PSU) | `comp_led_litere` | `VOL_V2_LED_PSU_PIECE` | 1.0 | buc | 150.0 | 150.0 | RON | yes (dev bridge) |
| `finisaje_colantare_vopsire` | Finisaje — colantare / vopsire | `comp_finisaj_litere` | `VOL_V2_FINISH_M2_OR_MINIMUM` | 1.2638 | m2 | 35.0 | 44.233 | RON | yes |
| `sablon_montaj_forex` | Șablon montaj — Forex | `comp_finisaj_litere` | `VOL_V2_SABLON_FOREX_DEV_BRIDGE` | 3.0523 | m2 | 15.0 | 45.7845 | RON | yes (dev bridge) |

### Null / owner-required CPP lines (excluded from sum)

| line key | rule | unit price | subtotal | notes |
|----------|------|------------|----------|-------|
| `ambalare` | `VOL_V2_PACKAGING_PENDING` | null | null | owner_decision_required |
| `montaj` | `VOL_V2_SITE_MOUNT_FUTURE` | null | null | owner_decision_required / future optional |

### Logo commercial lines

| Question | Answer |
|----------|--------|
| Logo 1 CPP lines | **none** |
| Logo 2 CPP lines | **none** |
| Null-price logo lines | **no** (omission, not null row) |
| Fallback letter lines for logos | **no** |
| Duplicated logo commercial lines | **no** |
| Linked-child lines entering CPP | **no** |

Composition dry-run lists logo item `TPL-VOLUMETRIC-LOGO_v1`, but CPP evaluation stays on letters catalog modules only.

---

## 7. EstimatedInternalCost truth

### A) Material-breakdown (primary internal EUR surface)

| Field | Value |
|-------|-------|
| Total | **725.16 EUR** |
| `contains_missing_prices` | **true** (see §21) |
| Logo materials | **present** |
| Logo operations | **present** (print / lamination / application × 2) |

### B) EIC trace on dry-run (secondary)

| Field | Value |
|-------|-------|
| Status | **blocked** |
| Estimated total | **~1515.90 RON** |
| Material / ops | ~441.93 / ~1073.97 RON |
| Provenance note | `logo_operations=0` on aggregate_cost_bom path |
| Meaning | Letters-oriented EIC path does **not** roll logo ops the same way MB does |

### Why internal logo rows exist while commercial logo rows do not

MB / live calc builds artwork geometry consumptions from workspace quote geometry and letters material keys (often reusing letter registry codes). CPP only evaluates `commercial_rules_volumetric_v2` against **letters** mini-modules. Linked logo child never contributes commercial rule evaluation → commercial omission with internal presence.

---

## 8. Currency truth

| Surface | Currency |
|---------|----------|
| CPP official | RON |
| Material-breakdown | EUR |
| EIC dry-run trace | RON |
| FX on official CPP | **NO** |
| Diagnostic FX | YES — `eur_to_ron_rate: 5.0` (settings), `diagnostic_only: true` |

**Classification:** `MIXED_CURRENCY_MISLEADING`

---

## 9. VAT / net / gross truth

| Field | Value |
|-------|-------|
| VAT rate | 21% |
| Commercial net | 2154.51 RON |
| VAT amount | 452.45 RON |
| Commercial gross | 2606.96 RON |
| Diagnostic cost-plus (non-authority) | net 4894.83 / VAT 1027.91 / gross 5922.74 RON |

---

## 10. Layer-to-template matrix

| layer | role | template (claimed) | PD | PA |
|-------|------|--------------------|----|----|
| pseudo maria | letter group | `TPL-VOLUMETRIC-LETTERS_v2` | parent components | parent materials/ops |
| pseudo soare | letter group | letters v2 | parent | parent |
| pseudo ana | letter group | letters v2 | parent | parent |
| pseudo gradinita | letter group | letters v2 | parent | parent |
| Logo 1 | printed_artwork linked segment | `TPL-VOLUMETRIC-LOGO_v1` (owning) | linked segment YES; standalone PD **404** | logo materials/ops **absent**; `linked_logo_segments: 0` |
| Logo 2 | printed_artwork linked segment | `TPL-VOLUMETRIC-LOGO_v1` | same | same |

---

## 11. Logo-template classification

### Live checklist for `TPL-VOLUMETRIC-LOGO_v1`

| Check | Result |
|-------|--------|
| Exists in DB | **UNPROVEN** via direct sqlite in this pass; Product System APIs behave as **absent** |
| Template registry / availability API | **NO** (not in 8-item availability list) |
| Product System UI offerable list | **NO** (availability drives UI) |
| Linked-child composition registration | **PARTIAL** — suggested in dry-run composition; not a live offerable/module parent_codes entry |
| ProductDefinition inclusion | Standalone **NO** (404). Letters PD linked segments **YES** (runtime mapping) |
| ProductAggregate inclusion | Standalone **NO** (`template_not_found`). Letters PA logo segments **0** |
| BOM/material rules (live PA logo) | **NO** |
| Operation rules (live PA logo) | **NO** |
| Commercial rules | **NO** (no logo CPP lines) |
| Internal-cost rules | **PARTIAL** via letters MB artwork rows (not logo-template catalog) |
| Quote-offerable as root | **NO** (policy + absence) |
| Linked-child-only support | **INTENDED in product policy / seeds; NOT live-complete** |
| Fallback-to-parent | Commercial: logos **omitted** (not priced as letters). Internal: geometry rolled into MB under artwork keys / some letter materials |
| Duplicate-processing risk | Commercial: low (omission). Internal: medium (artwork return length + letter return; nesting rolls appear twice per logo for print/lam families) |

**Final classification:** `PARTIAL_LINKED_CHILD`

---

## 12. ProductDefinition truth

- Root PD: `TPL-VOLUMETRIC-LETTERS_v2` **present**
- Linked segments: Logo 1/2 with `owning_template_code=TPL-VOLUMETRIC-LOGO_v1`, binding confirmed, finish pending → readiness blocked (`linked_segment_required_data_missing` / finish missing)
- Standalone logo PD: **404**
- Composition graph active modules: `volum_aluminum` (not logo)

---

## 13. ProductAggregate truth

- Root PA: letters v2 **present** (materials/ops from parent)
- Logo aggregate: **template_not_found**
- `linked_logo_segments: 0`
- No logo-specific PA materials/operations dumped for child template

---

## 14. Layer-to-CPP matrix

| layer | CPP line(s) | commercial inclusion | missing/duplicate |
|-------|-------------|----------------------|-------------------|
| pseudo maria | shared letter lines (face/return/back/LED/finish/sablon) | included (aggregated) | none |
| pseudo soare | shared letter lines | included | none |
| pseudo ana | shared letter lines | included | none |
| pseudo gradinita | shared letter lines | included | none |
| Logo 1 | **∅** | **OMITTED** | lineage stops before commercial rules |
| Logo 2 | **∅** | **OMITTED** | lineage stops before commercial rules |

---

## 15. Layer-to-EIC / MB matrix

| layer | EIC/MB lines | internal inclusion |
|-------|--------------|--------------------|
| letter groups | plexi face, forex back, return, CNC face/back, adhesives, LED, wires | yes |
| Logo 1 | plexi, forex (+20% waste), print vinyl, laminated vinyl; print/lam/application ops | yes |
| Logo 2 | same pattern | yes |

---

## 16. Material provenance (internal logos)

Logo 1/2 each:

- face plexi → `MAT-ACP-FATA-LITERE` (letter face code reused)
- forex back → `MAT-SPATE-PVC-LITERE` (+20% waste)
- print vinyl → `MAT-VINYL-PRINT`
- laminated vinyl → `MAT-VINYL-PRINT-LAMINATED`
- qty basis ≈ **0.4002 m²** bbox footprint (`quote_geometry.artwork_boxes`)

---

## 17. Operation provenance (internal logos)

Per logo: print_service 8.5 EUR/m², lamination 2.0, application 3.0 on **0.4802 m²** (waste-adjusted service qty).

Letters: CNC face 24.6488 ml, bevel same, CNC back 26.7471 ml, edge cant bond 31.6382 m.

---

## 18. Geometry reconciliation (live)

| Metric | Live value | Contributing | Notes |
|--------|------------|--------------|-------|
| Letter face area (sum groups) | **1.2638 m²** | 4 letter layers | matches CPP back/finish qty |
| Plexi face MB | **1.2638 m²** | letters | logos separate rows |
| Forex backing MB | **1.2638 m²** | letters | mirrored to face when backing area missing |
| Logo print/laminate base | **0.4002 m²** each | Logo 1/2 | +20% → 0.4802 for waste rows |
| Cant/return length MB | **31.6382 m** (base) / **37.9658** w/ 20% | letters + interiors + artwork | logos **included** in return material |
| CPP face/return ml | **21.1675 ml** | letters commercial metric | **≠** finish_summary perimeter sum 26.747 m — different commercial basis |
| CNC face perimeter MB | **24.6488 ml** | letters (+holes/passes as priced) | |
| CNC backing perimeter MB | **26.7471 ml** | letters | aligns with finish perimeter sum |
| Adhesive return | **53.4944 ml** | letters | |
| LED modules | **145** | letters commercial+internal | waste 20% → 174 priced qty internal |
| LED watts (info) | **108.75 W** | informational | drives false missing flag |
| PSU | **1** (160W class) | letters | |

Holes/internal contours: production_counts show `inner_hole_count: 8`, `cut_contour_count: 28` — affect CNC/perimeter paths more than commercial face ml.

---

## 19. LED truth

- Commercial: 145 modules × 5 RON + 1 PSU × 150 RON on **letters** component
- Internal: same 145 modules + watts informational + PSU 160W
- Logo illumination for this fixture: **not separately commercially priced**; owner gate G4 required before assuming logos are lit/sold

---

## 20. Logo commercial-pricing truth

**Break point:**

```text
SVG layers → linked runtime segments (PD) → composition suggests TPL-VOLUMETRIC-LOGO_v1
        → MB internal rows YES
        → PA logo child NO / linked_logo_segments 0
        → commercial_rules_volumetric_v2 modules (letters only)
        → CPP lines for Logo 1/2 = NONE
```

Root cause class: **COMMERCIAL_RULE** / commercial handoff incomplete for linked logo child (**OMITTED_COMPONENT** on commercial path). Compounded by live Product System absence of logo template (404 / not in availability).

---

## 21. contains_missing_prices root cause

| Field | Value |
|-------|-------|
| Live value | **true** |
| Predicate | `_is_price_missing_material`: qty>0 and both `estimated_cost` and `material_cost` are null |
| Exact missing row | `led_total_watts` qty 108.75, `price_source=informational_only` |
| Informational null row | **yes** — intended non-priced |
| Commercial null rows | ambalare/montaj (CPP) — **separate** from this flag |
| Classification | `FALSE_POSITIVE_INFORMATIONAL_ROW` |
| Role | **Secondary bug** — not primary commercial blocker; unrelated to logo commercial absence |

---

## 22. Duplicate / omission analysis

| Kind | Finding |
|------|---------|
| Commercial omission | Logos fully omitted from CPP |
| Commercial duplicate | None for logos |
| Internal duplicate risk | Nesting roll rows appear for both print and laminate families per logo; return length includes artwork with letter return |
| Partial | Letters commercially priced; logos only internal; packaging/site-mount pending |

---

## 23. Commercial readiness classification

**`COMMERCIAL_PARTIAL_NOT_CONFIRMABLE`**

---

## 24. Can operator confirm now?

**NO**

---

## 25. First blocker

| Field | Value |
|-------|-------|
| Category | `COMMERCIAL_RULE` |
| Exact gap | No commercial rules / CPP evaluation for linked logo child on letters+logo composition |
| Affected components | Logo 1, Logo 2 (`logo_instance_001/002`) |
| Affected total | Live commercial net/gross understates full product (letters-only 2154.51 / 2606.96 RON) |
| Expected source | Logo linked-child commercial rules → CPP lines |
| Actual source | Letters-only `commercial_rules_volumetric_v2` |
| First broken contract | Linked-child commercial evaluation / missing live logo template commercial handoff |
| Template creation required? | **Owner gate G2** — live registry absence proven at API layer; seed≠live |
| Registry entry required? | Likely **yes** if G2=YES for linked-child-only |
| CPP linked-child support missing? | **YES** (composition suggests logo; CPP ignores) |
| PD/PA lineage incomplete? | **YES** (PD segments partial; PA logo absent; standalone 404) |

---

## 26. Root-cause classification

`GRADI_CURAT_PRICING_FIRST_BLOCKER_FOUND` → primary **`COMMERCIAL_RULE`** (logo commercial omission), with secondary `FALSE_POSITIVE_INFORMATIONAL_ROW`, `MIXED_CURRENCY_MISLEADING`, packaging/site-mount owner-null lines.

---

## 27. Recommended one coherent correction

**Boundary:** Logo linked-child commercial pricing truth only.

1. Prove/fix live `TPL-VOLUMETRIC-LOGO_v1` registration as **linked-child-only** (if G2=YES).
2. Complete linked-child PD→PA provenance for logo segments into commercial evaluation inputs.
3. Register commercial rules for printed+laminated volumetric logos (method per G3).
4. Extend CPP to evaluate linked logo components without double-counting letter lines.
5. Emit Logo 1/2 commercial lines; refresh commercial totals completeness.
6. Targeted tests + same-workspace dry-run proof on `11891d68-…`.

**Explicitly out of scope for this correction:** broad Product System redesign; unrelated pricing registry cleanup; currency redesign; UI redesign; quote/order flow; Cost Engine refactor; legacy paths; packaging/site-mount unless G5 forces readiness dependency.

---

## 28. Scope included (next phase, after owner GO)

- Logo commercial rule + CPP linked-child evaluation
- Live linked-child registry truth if authorized
- Completeness of commercial total for logos
- Duplicate-count guards
- Tests + workspace dry-run verification

---

## 29. Scope forbidden (this audit + until gates)

- Build Locally / implementation without owner review
- Product-code changes in this phase
- Runtime writes / workspace mutation
- Pricing registry edits / logo seed activation without G2
- Quote/order creation
- Commit until owner review

---

## 30. Owner gates

### G1 — Logo commercial pricing correction as next blocker phase
- **YES** authorizes correction phase start (docs→implementation)
- **NO** keeps commercial confirm blocked
- DB/seed: none by itself
- Pricing: yes (subsequent)
- Runtime-write: none by itself
- Migration: none

### G2 — May `TPL-VOLUMETRIC-LOGO_v1` be registered/reactivated as linked-child-only?
- **YES** authorizes live registry/seed activation for linked-child-only
- **NO** keeps PS absence; requires alternate commercial handoff design
- DB/seed: **yes** if YES
- Pricing: enables rule attachment
- Runtime-write: seed/registry only if approved
- Migration: unlikely / follow existing seed patterns

### G3 — Commercial pricing method for printed+laminated volumetric logos
- **YES** (with chosen method) authorizes commercial rule definition
- **NO** / undecided keeps logo commercial lines blocked
- Pricing impact: **primary**
- DB/seed: rule catalog entries
- Runtime-write: none until implemented
- Migration: none expected

### G4 — Logo illumination included or excluded for gradi-curat fixture
- **INCLUDE** → LED commercial must account for logos or explicit logo LED rules
- **EXCLUDE** → document letters-only LED as intentional for this fixture
- Pricing impact: LED lines / quantities
- DB/seed: possibly LED rule scope
- Runtime-write: none in audit

### G5 — Packaging / site-install commercial lines deferred or required for readiness
- **DEFER** → ambalare/montaj remain null without blocking logo correction
- **REQUIRE** → commercial readiness also blocked on owner packaging/site rates
- Pricing impact: ambalare/montaj
- DB/seed: optional rate entries
- Runtime-write: none in audit

**Owner answers are not invented here.**

---

## 31. What becomes possible after correction

- Honest commercial total covering letters **and** logos
- Safer Confirmare / quote snapshot path for this composition
- Clear separation of deferred packaging/site-mount vs priced product body
- Residual secondary fixes (missing-price flag, currency labels) can be scheduled separately

---

## 32. Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Plan / owner report | `.compound-engineering/gradi-curat-pricing-truth-audit/plan.md` | finalized |
| Decision log | `.compound-engineering/gradi-curat-pricing-truth-audit/decision-log.md` | finalized |
| Worklog | `docs/worklog/realignment/2026-07-16_gradi_curat_pricing_truth_audit.md` | finalized |
| Evidence | `docs/qa/gradi-curat-e2e/pricing-truth-evidence.md` (JSON body; `.json` rename after owner GO if needed) | finalized |
| Live probes | `docs/qa/gradi-curat-e2e/_probe_*.json` | captured read-only |

---

## 33. Commit recommendation

**Docs-only commit:** YES (after owner review)  
**Includes:** CE plan pack, worklog, evidence (no product code)

---

## 34. Push / PR

**NO / NO**

---

## 35. Honest opinion

The UI commercial gross is a real CPP number, but it is **not** a complete commercial price for gradi-curat. Logos are physically and internally costed while commercially invisible. Confirmare would under-price the job. Fix the logo commercial handoff first; treat currency labeling and `contains_missing_prices` as secondary cleanup.

---

## 36. Roadmap awareness checkpoint

| Check | Result |
|-------|--------|
| Score | **8/10** alignment with established Intake V6 / Product System / CPP 7G direction |
| Exact roadmap position | After Step2 runtime closure (`99d5c71`); **before** commercial confirm / quote write for letters+logo |
| Dead pieces check | Logo template seed/policy exists; live PS registration + CPP linked-child path incomplete — not “dead code,” **partial wiring** |
| Forbidden scope confirmation | No Build Locally; no pricing implementation; no PS redesign; no Cost Engine; no quote/order |
| Cat sunt in directia stabilita | **75/100%** — correct authority (CPP 7G) and composition intent; commercial linked-child completion still required |

---

## Stop

No implementation. No Build Locally. No product-code changes. No commit until owner review of G1–G5.
