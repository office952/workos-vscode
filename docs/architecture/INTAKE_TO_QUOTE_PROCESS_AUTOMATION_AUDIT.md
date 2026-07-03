# Intake-to-Quote Process — Automation & Flow Simplification Audit

**Date:** 2026-06-07  
**Branch:** `master`  
**HEAD:** `841cc96` (includes vector pathway hard audit chain `990a086` → `0971a06`)  
**Type:** Audit only — no runtime changes in this build.

---

## Executive summary

The intake-to-quote journey works end-to-end but asks operators for **too much, too early**, and **repeats the same decisions** across Quick Start, side panel, spec editor, Vector Studio, and quote tab. Several panels appear **before their preconditions are met** (terrain on generic unresolved, template confirm before work type, geometry blockers before vector fast-ask completes).

**Core recommendation:** adopt **progressive disclosure** with three explicit gates:

1. **Identity gate** — client, work type, description, channel (Quick Start)
2. **Quote estimate gate** — geometry + cost drivers sufficient for `simulate-cost` (not production metadata)
3. **Commercial quote gate** — vector readiness, Oracal/RAL production metadata, template confirmed (existing backend `quote_gate`)

Do **not** remove blockers that protect pricing integrity or WI-SMOKE-P001 baseline (844,41 EUR).

---

## Phase 0 — Pre-flight

| Item | Value |
|------|-------|
| Branch | `master` |
| HEAD | `841cc96` |
| Git status | clean |
| Backend :8000 | healthy (`development`) |
| Frontend :3000 | up |
| Counts | intakes **22**, quotes **7**, orders **8** |

---

## Phase 1 — Browser journey inventory

### Flow A — New volumetric intake (Quick Start → workspace)

| step | current UI | operator action | input requested | logical here? | problem | automation opportunity |
|------|------------|-----------------|-----------------|---------------|---------|------------------------|
| 1 `/intake` | List + Cerere Nouă | Open dialog | — | yes | — | — |
| 2 Client step | Mode + client pick/create | Select client | client, contact | yes | email/address/city in state but not in UI | prefill contact from client registry |
| 3 Details step | Work type picker | Select Litere volumetrice | work type, channel, priority, delivery, description | yes | delivery asked again in workspace | auto-sync delivery to side panel |
| 4 Create | — | Submit | — | yes | — | set `product_family`, default `quantity:1` |
| 5 Workspace | Volumetric modular shell | — | — | yes | template confirm still required | auto-confirm when Quick Start selected volumetric + template code known |
| 6 Pathway | 3 cards | Click Din fișier vector | pathway | yes | was unstable pre-841cc96 | auto-persist pathway (done) |
| 7 SVG pick | Fast ask file button | Select file | SVG file | yes | filename/layers must appear immediately | auto metadata + layer detect (exists) |
| 8 Layer roles | Per-layer dropdowns | Confirm roles | layer role mapping | yes | asked before apply AND again in Vector Studio | single mapping surface |
| 9 Fast ask | 5 decision dropdowns | Answer colantare/cant/depth/light | finish intents | partial | depth/lighting also in sections 4–7 | prefill from layer mapping + template defaults |
| 10 Apply | Button | Click Aplică | — | yes | unlocks 8 accordion sections — feels like second form | treat as “review auto-fill” not new data entry |
| 11 Full spec | Sections 1–9 | Fill geometry, cost fields | area, perimeter, count, PSU, paint, mounting | partial | **geometry not from SVG** (by design) | LED module count from perimeter (exists); defer production-only |
| 12 Save | Salvează specificația | Save | full spec | yes | duplicate with auto-save on pathway/file | clarify “save rest of spec” |
| 13 Simulate | Quote tab | Open + Calculează | cost options overrides | yes | simulate blocked until geometry complete | show simulate with explicit missing list |
| 14 Ready | Side panel | Marchează gata | assignee, template, envelope | partial | envelope required before geometry in vector path | split “draft ready” vs “quote ready” |
| 15 Quote create | Quote tab gate | Create commercial quote | final quote metadata | yes | — | keep backend gate |

### Flow B — Existing volumetric intakes

| Intake | URL | Notes |
|--------|-----|-------|
| IR-MQ3C869E | `/intake/IR-MQ3C869E` | Draft with vector file history; modular workspace; template confirmed |
| IR-MQ3JV8GD | `/intake/IR-MQ3JV8GD` | Vodafone; vector pathway; file pick race fixed in 841cc96 |
| WI-SMOKE-P001 | `/intake/WI-SMOKE-P001` | Smoke baseline; manual geometry; **844,41 EUR** simulate baseline — read-only reference |

### Flow C — Generic unresolved (`IR-MQ3E7K2V`)

| step | current UI | operator action | input requested | logical here? | problem | automation opportunity |
|------|------------|-----------------|-----------------|---------------|---------|------------------------|
| Load | Generic legacy layout | — | — | yes | not modular workspace | route message clear |
| Action map | Confirm template / teren links | — | — | **no** | template/terrain CTAs before work type | hide until family selected |
| Assignee + delivery | Top bar + side inputs | Edit | assigned_to, delivery | partial | OK for ops | inherit from Quick Start |
| Identity | CUI lookup | Optional fiscal | CUI | **no** | fiscal lookup before work type | defer until client fiscal needed |
| Work type | Unresolved section | Alege tip lucrare | — | yes | — | scroll to template assist |
| Product spec | — | — | — | yes | hidden correctly | — |
| **Audit teren** | Full terrain section | Address, photos, power | site audit fields | **no** | shown while `delivery_install` but **before** work type/template | **hide until** `delivery_install` AND volumetric/resolved |
| Ready | Marchează gata | — | — | **no** | blockers include template/spec/dimensions not applicable yet | show only unresolved-relevant blockers |

### Flow D — Quotes page

| step | current UI | logical? | problem | note |
|------|------------|----------|---------|------|
| `/quotes` | Quote list | yes | — | separate from intake workspace |
| Ofertă nouă | Generic QuoteWizard | yes | intentionally not volumetric editor | must remain separate (verified in routing tests) |

---

## Phase 2 — Full input inventory (summary)

Detailed field-level table lives in **Appendix A**. Classifications used:

- **Keep visible** — operator must see/decide now
- **Auto-fill** — system can set without asking
- **Infer** — derive from other data (show as read-only or editable prefill)
- **Ask conditionally** — only when predicate true
- **Move later** — production prep / post-order
- **Hide behind advanced** — collapse or “Detalii producție”
- **Hide behind tooltip** — replace always-visible banners
- **Remove from flow** — duplicate elsewhere
- **Keep but rename** — clarity only
- **Split quote vs production** — same data, two lifecycle stages

### Quick Start (`NewIntakeDialog`)

| input | required? | needed for | recommendation | reason |
|-------|-----------|------------|----------------|--------|
| Client mode + client | yes | intake identity | keep visible | routing + comms |
| CUI (fiscal new) | if fiscal | accounting | ask conditionally | not needed for draft quote |
| Contact / phone | no | client comms | auto-fill from client | optional override |
| Work type | yes | template routing | keep visible | core fork |
| Channel | yes | intake identity | keep visible | low friction |
| Priority | no | internal ops | hide behind advanced | rarely blocks quote |
| Delivery type | no (default) | ready + terrain trigger | keep visible | drives install audit predicate |
| Description | yes | ready + context | keep visible | operator narrative |

### Side panel (volumetric workspace)

| input | required? | needed for | recommendation | reason |
|-------|-----------|------------|----------------|--------|
| Client / contact | read-only | context | keep | no re-entry |
| Asignat | yes (ready) | internal assignment | auto-fill current user | confirm editable |
| Livrare | yes (ready) | delivery + terrain | auto-fill from Quick Start | avoid duplicate ask |
| Template status | read-only | guidance | keep | replaces confusing confirm? |
| Readiness blockers | read-only | guidance | ask conditionally | filter by pathway stage |

### Pathway selector

| input | required? | needed for | recommendation | reason |
|-------|-----------|------------|----------------|--------|
| vector / manual / quick_estimate | yes | UX disclosure | keep visible | legitimate fork; auto-persist pathway |

### Vector fast ask (vector pathway)

| input | required? | needed for | recommendation | reason |
|-------|-----------|------------|----------------|--------|
| Vector file | yes | vector metadata + final quote | keep visible | core artifact |
| File quality notes | no | production | hide behind advanced | post-quote |
| Layer role per layer | soft | final quote mapping | infer (medium) + confirm | SVG names often hint role |
| Layer alignment | no | production review | ask conditionally | only if unknown layers |
| Face colantare | no | cost path | ask conditionally | drives Oracal fields later |
| Cant finish | no | cost + production | ask conditionally | drives RAL/Oracal side |
| Letter depth | no | simulate | auto-fill 60mm default (high) | template default; confirm |
| Lighting intent | no | production + PSU | infer medium | can default halo for volumetric |

### Product001 sections 1–9 (after fast-ask apply)

| section | dominant need | recommendation |
|---------|---------------|----------------|
| 1 Ce trebuie produs | production | move later / hide behind advanced |
| 2 Dimensiuni | ready envelope + quote | keep; auto-fill height from SVG viewBox height (medium, confirm) |
| 3 Geometrie | simulate | keep for vector until parser validated; **never auto-calc area from SVG today** |
| 4 Construcție | cost + production | keep; hide bevel/miter behind advanced |
| 5 Finisaj față | cost + final quote | keep conditional on colantare answer |
| 6 RAL | final quote + production | ask conditionally if paint path |
| 7 Iluminare | cost (PSU) + production | keep PSU visible; notes → advanced |
| 8 Montaj | cost | keep; bar fields conditional on mounting_system |
| 9 Vector Studio | final quote | **merge with fast ask** — duplicate file/layer/review |

### Quote simulation tab

| input | required? | needed for | recommendation |
|-------|-----------|------------|----------------|
| Embedded spec summary | read-only | context | keep |
| Cost options panel | varies | simulate | keep; prefill from spec |
| Geometry in wizard | simulate | keep read-only in embedded mode |
| Commercial quote button | final quote | keep gated |

---

## Phase 3 — Automation opportunity audit (ranked)

| input | manual today | automation source | confidence | auto-fill? | needs confirmation? | proposed behavior |
|-------|--------------|-------------------|------------|------------|---------------------|-------------------|
| `delivery_type` | Quick Start + side panel | Quick Start create payload | **high** | yes | no | single write; side panel read-only until changed |
| `intake_input_pathway` | card click | vector file present / user click | **high** | yes | no | done in 841cc96 |
| `vector_file_name` + metadata | file pick | SVG file object | **high** | yes | no | done; show immediately |
| `vector_detected_layers` | file pick | SVG parser | **high** | yes | medium for roles | pre-map roles; operator confirms |
| `return_depth_mm` | fast ask / §2 | template default 60mm | **high** | yes | yes | preselect 60mm |
| `selected_psu_watts` | §7 | perimeter → LED count heuristic | **medium** | suggest | yes | show computed suggestion |
| `paint_tube_count` | §6 | letter count / area heuristic | **medium** | suggest | yes | estimator only |
| `letter_face_area_m2` / `perimeter` / `count` | §3 manual | SVG geometry | **none** today | no | — | **do not fake** until validated parser |
| `width_mm` / `height_mm` envelope | §2 | SVG viewBox | **low–medium** | suggest | yes | show cm dimensions as hint only |
| `face_finish_type` | fast ask | fast ask answer | **high** | yes | yes | already mapped on apply |
| `mounting_system` | §8 | template default `direct_wall` | **medium** | suggest | yes | prefill most common |
| `assigned_to` | side panel | auth session user | **medium** | suggest | yes | prefill logged-in operator |
| Oracal color / roll width | §5 | face_finish_type | **high** | conditional | yes | only show if Oracal selected |
| RAL code | §6 | cant finish = paint | **high** | conditional | yes | only show if paint path |
| Terrain audit | §terrain | `delivery_install` | **high** | hide | — | hide unless install delivery AND resolved template |
| CUI fiscal lookup | Identity | client has CUI | **medium** | auto-fill | yes | skip step if known |
| Template confirm button | workspace | Quick Start `templateCode` | **high** | auto-confirm | optional | one-click if family matches TPL |

---

## Phase 4 — Duplicate / illogical UI

| issue | where | why illogical | impact | proposed correction |
|-------|-------|---------------|--------|---------------------|
| Terrain audit before work type | generic unresolved `IntakeDetail` | install audit irrelevant until product + delivery known | operator confusion, false blockers | hide `AuditTerenSection` until resolved family + `delivery_install` |
| Template confirm CTA before work type | generic action map | no template to confirm | dead click | hide until `product_family` set |
| Delivery asked twice | Quick Start + workspace | duplicate data entry | friction | auto-sync; show “from cerere” label |
| Vector file asked twice | fast ask + Vector Studio §9 | same filename/mappings | fatigue | single vector surface; §9 read-only summary |
| Layer mapping twice | fast ask layers + Vector Studio | duplicate mapping UI | errors / drift | one mapping UI; studio shows summary |
| Manual labels on vector path | section headers after apply | “Verificare” vs “manual” wording | user thinks pathway switched | rename to “Verificare specificație” (partially done) |
| Geometry blockers before fast-ask done | side readiness | spec incomplete while still in fast ask | premature red warnings | stage blockers: “Completează fast ask” first |
| Production fields in intake | text, font, notes §1 | not needed for simulate | noise | collapse §1 by default on vector path |
| Always-on warning banners | fast ask amber text | implies file attached when not | false confidence | fixed in 841cc96 — keep pattern |
| Save vs auto-save | pathway/file auto-save + Salvează | unclear what save does | operator skips save | label: “Salvează restul specificației” |
| Quote blockers in 3 places | side panel, quote tab, §10 prep | duplicate lists | anxiety | single canonical missing list component |
| `priority` | Quick Start | never surfaces in readiness | clutter | advanced optional |
| Envelope width/height/depth for ready | readiness | blocks before quote-relevant geometry | vector path stuck early | ready gate = ops only; geometry gate = simulate |

---

## Phase 5 — Ideal streamlined flow

```
New Intake (Quick Start)
  → client + work type + description + channel + delivery
  → create draft

IF generic unresolved:
  → show ONLY: client summary, assignee, delivery, "Alege tip lucrare"
  → hide: template confirm, terrain, spec editor, quote CTAs, fiscal unless needed

IF volumetric (litere_volumetrice):
  → auto-route to modular workspace
  → auto-confirm template when Quick Start selected volumetric (optional confirm chip)

  → choose input method:
     VECTOR:
       1. Upload SVG
       2. Auto: filename, viewBox, layers, suggested roles
       3. Operator: confirm roles + 3–5 decision questions (colantare, cant, depth, light)
       4. Auto-apply to spec (review screen, not blank form)
       5. Operator: enter/confirm quote geometry (area, perimeter, count) — REQUIRED, manual until parser validated
       6. Auto-suggest: PSU, paint tubes, LED count
       7. Simulate (preliminary) — allowed without Oracal/RAL/production text
       8. Final quote gate: vector review, layer letters mapped, Oracal/RAL if applicable
       9. Production-only: font, text art, mounting notes → collapse until order

     MANUAL:
       1. Envelope dimensions
       2. Geometry
       3. Cost drivers (finish, mounting, PSU, paint)
       4. Simulate → final quote gate

     QUICK ESTIMATE:
       1. Text + envelope only
       2. Orientative simulate (watermarked non-final)
       3. must switch to manual/vector for commercial quote

Quote handoff:
  → embedded simulate in workspace tab (spec edits stay in Spec tab)
  → generic QuoteWizard remains separate entry on /quotes for non-intake flows

Production prep (later):
  → detailed text/font, mounting notes, CNC flags, vinyl roll details, site install execution
```

---

## Phase 6 — Prioritized implementation plan

| priority | build | purpose | risk | why now |
|----------|-------|---------|------|---------|
| P0 | **BUILD-INTAKE-GATE-CONDITIONAL** | Hide terrain, template CTAs, fiscal on unresolved; filter readiness blockers by stage | low | highest illogical UX; no pricing touch |
| P0 | **BUILD-DELIVERY-SYNC** | Single source for `delivery_type` Quick Start → detail page | low | removes duplicate ask |
| P1 | **BUILD-VECTOR-SINGLE-SURFACE** | Merge fast-ask layer mapping + Vector Studio summary; remove duplicate inputs | medium | reduces vector path fatigue — **resolved** (`docs/qa/BUILD_VECTOR_SINGLE_SURFACE.md`) |
| P2 | **BUILD-SVG-GEOMETRY-PARSER-MVP** | Safe bbox-based geometry suggestions with operator confirmation | medium | reduces manual dimension entry — **resolved** (`docs/qa/BUILD_SVG_GEOMETRY_PARSER_MVP.md`) |
| P1 | **BUILD-READINESS-STAGES** | Split ops-ready vs simulate-ready vs quote-ready messages | medium | clarifies what blocks what |
| P1 | **BUILD-VECTOR-REVIEW-NOT-REENTER** | After apply, show review card not 8 empty accordions | medium | fluidity |
| P2 | **BUILD-CONDITIONAL-FINISH** | Oracal/RAL fields only when finish path selected | low | removes irrelevant inputs |
| P2 | **BUILD-TEMPLATE-AUTOCONFIRM-QUICKSTART** | When work type = volumetric, pre-confirm TPL-VOLUMETRIC-LETTERS | medium | removes extra click |
| P2 | **BUILD-ASSIGNEE-PREFILL** | Prefill assignee from session | low | ops convenience |
| P3 | **BUILD-PSU-PAINT-SUGGEST** | Suggest PSU W + paint tubes from geometry | medium | must not change CostEngine formulas |
| P3 | **BUILD-SVG-ENVELOPE-HINT** | Show viewBox dimensions as hint only | low | no auto geometry |
| P4 | **BUILD-SVG-GEOMETRY-PARSER** | Validated area/perimeter extraction | **high** | only after parser accuracy proven; never fake |
| — | Reference Catalogs / new templates | — | — | **explicit non-goal** |

### Per-build PASS criteria (examples)

**BUILD-INTAKE-GATE-CONDITIONAL**
- `IR-MQ3E7K2V` shows no terrain section until work type selected
- volumetric + `pickup` shows “Teren: N/A”
- WI-SMOKE-P001 unchanged simulate baseline

**BUILD-VECTOR-SINGLE-SURFACE**
- SVG pick → layer map once → save → refresh persists
- no second file name field on same page

---

## Appendix A — Field inventory (Product001 + gates)

See codebase tags in `frontend/src/lib/volumetricIntakeFormPrep.ts`.

| area | input | current required? | needed for | recommendation |
|------|-------|-------------------|------------|----------------|
| §2 | width/height/depth mm | ready gate | ready + envelope | keep; hint from SVG |
| §3 | letter_face_area_m2 | simulate | quote estimate | keep manual |
| §3 | letter_perimeter_m | simulate | quote estimate | keep manual |
| §3 | letter_count | simulate | quote estimate | keep manual |
| §5 | face_finish_type | simulate/final | quote | conditional |
| §5 | face_vinyl_* | final quote | production | conditional Oracal |
| §6 | paint_ral_code | final quote | production | conditional paint |
| §6 | paint_tube_count | simulate | cost estimate | suggest |
| §7 | selected_psu_watts | simulate | cost estimate | suggest |
| §8 | mounting_system | simulate | cost estimate | keep |
| §9 | vector_file_name | final quote | production | auto |
| §9 | svg_layer_mappings | final quote | production | auto+confirm |
| §9 | vector_manual_review_approved | final quote | production | confirm after review |
| §1 | text/font/notes | no | production | move later |
| terrain | address/photos/power | ready if install | installation | conditional |
| ready | assignee | yes | ops | prefill |
| ready | description | yes | ops | from Quick Start |
| ready | template confirmed | yes | routing | auto from Quick Start |
| simulate | all `VOLUMETRIC_QUOTE_INPUT_FIELDS` | yes | simulate only | separate from production metadata |

---

## Explicit non-goals (this audit)

- No pricing / CostEngine / quote calculation changes
- No Reference Catalogs
- No new templates
- No quote/order creation during audit
- No fake geometry from SVG
- WI-SMOKE-P001 baseline **844,41 EUR** must remain valid

---

## Recommended next build

**BUILD-INTAKE-GATE-CONDITIONAL** — hide irrelevant panels and stage readiness blockers before work type / delivery predicates are met. Highest operator impact, lowest technical risk, no costing changes.
