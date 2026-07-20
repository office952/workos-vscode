# WORKOS_VOLUMETRIC_LETTERS_AUTHORITY_INSTANCE_PLACEMENT_V1

| Field | Value |
|-------|--------|
| Status | **IMPLEMENTED — awaiting owner review** |
| Mode | Scope A implementation after owner GO |
| Date | 2026-07-20 |
| Build | **Build 1** (audit verdict B) |
| AcmPanel closed HEAD | `56217a9` — do not reopen |
| Worklog | `docs/worklog/realignment/2026-07-20_volumetric_letters_authority_instance_placement_v1.md` |
| Evidence | `docs/audits/_evidence/2026-07-20_volumetric-letters-authority-instance-placement/` |

---

## 1. Verdict

Build 1 is ready to plan as:

```text
LetterGroupInstance authority
+ stable UUID identity
+ artwork suggest/confirm rules
+ materials/finish/lighting on instance
+ commercial quantity builder as CPP SoT
+ ComponentPlacement persist (minimal)
+ one-way legacy projection
```

**Recommended implementation scope: A** — authority + lifecycle + quantities + placement representation in **one** coherent build, with a hard STOP if `IntakeV6ReviewStep.tsx` grows beyond a thin helper wiring budget.

Not B (placement-only split creates partial truth).  
Not C (contract-only fails round-trip / autosave criteria).

Logic can be explained simply (see §3). If owner demands a generic component framework → **STOP**.

---

## 2. Compound Engineering workstreams

| ID | Focus | Outcome used in synthesis |
|----|-------|---------------------------|
| CE-1 | Lifecycle R/W map | Persist via finish-setup PUT; wipe on SVG replace; merge-by-key; no create-time groups |
| CE-2 | Product System ownership | Family/template kept; FACE/BACK/LED/FINISH not live-seeded — do not pretend |
| CE-3 | Artwork + identity | **UUID + `group_key` join**; SVG hash = stale only |
| CE-4 | Materials / lighting | Per-group finishes exist; lighting workspace-global today → copy onto instance |
| CE-5 | Quantities / CPP | Measurement builder owns commercial resolution; CPP official; CostEngine legacy |
| CE-6 | Placement | Persist + thin ACM-target adapter; no ACM relations rewrite |
| CE-7 | Intake impact | ReviewStep ~3991 lines; STOP >~25 net lines / any new state/effect |
| CE-8 | Tests / runtime | Multi-group real (gradi-curat); IV6 fixtures listed |

**Contradiction resolution:** CE-3 wants confirmed preservation across fill change; CE-1 documents today’s merge **wipes** finishes when `source_fill_color` changes. **Truth:** current code wipes. **Target Build 1:** keep `instance_id`, preserve confirmed commercial fields, flag color drift (do not silent wipe). That is an intentional behavior fix inside letter merge helper — not ReviewStep growth.

---

## 3. Logic model

### What is a letter group?

One commercial configuration shared by a set of letter paths from one confirmed SVG **face** layer (or equivalent manual row). Today: one `letter_group_finishes[]` row keyed by `group_key` (= `layerKey`, e.g. `pseudo:maria`).

### What differentiates two groups?

Different `group_key` / layer identity — and therefore they may differ in materials, depth, lighting, geometry metrics, placement. No equality assumed.

### When one vs many?

| Case | Groups |
|------|--------|
| Single text “ACME” | 1 |
| Main + subtitle | 2 |
| Logo + text | Logo → artwork path; text → letter group(s) |
| gradi-curat (Maria/Soare/Ana/Grădinița) | 4 |
| Non-lit / illuminated | Same groups; lighting differs |
| Wall / ACM / frame / Totem A·B | Same groups; **placement** differs |

### Ownership in one glance

| Belongs to | Examples |
|------------|----------|
| **LetterGroupInstance** | Face/cant/back finish, depth, confirmed, lighting, per-group geometry metrics |
| **Artwork** | SVG ref, layer ids, observed metrics, hash, stale flag — **suggest only** |
| **ComponentPlacement** | wall / acm_panel / metal_frame / totem_face + target id/face |
| **Product Template** | Composition, defaults at create, allowed variants |
| **Quantity builder** | Commercial ml/m²/buc for CPP aliases |
| **Operator sees** | Existing cards (finisaje) — not IDs/provenance/aliases |

```text
Product Template → compose + defaults
LetterGroupInstance → concrete config
Artwork analysis → suggest
Operator → confirm
Quantity builder → commercial quantities
CPP 7G → consume
ComponentPlacement → support relation
```

---

## 4. Current read/write map

| Stage | Writes `letter_group_finishes`? | Notes |
|-------|--------------------------------|-------|
| Create/bootstrap | No | No finish_setup yet |
| SVG new hash | **Wipes** finish_setup | Full loss |
| Derive analyzer | In-memory | `group_key` = layerKey |
| Merge | Structure = derived; overlay saved by key | Orphans dropped; fill mismatch wipes finishes |
| Autosave PUT | Yes (full array) | Authority today |
| Confirm | finish_setup.confirmed | Per-row confirmed often false |
| PD | Read blob | Opaque copy |
| Aggregate | Globals mostly | Per-group colors weak |
| CPP | Reads geometry + finish | Via measurements / paths |

**Identity today:** `group_key` only — not array index. Unstable if pseudo-key regenerates.

---

## 5. Target ownership

```text
WRITE authority: letter_group_instances[]
READ:            instances if valid else one-time legacy hydrate
PROJECTION:      instances → letter_group_finishes[] (one-way, temporary)
PLACEMENT:       finish_setup.component_placements[]
QTY AUTHORITY:   build_volumetric_letters_commercial_quantities / letters_commercial_measurement_service
PRICING:         CPP 7G (official)
LEGACY PARALLEL: CostEngine (V6 must not treat as override)
```

---

## 6. LetterGroupInstance

**Schema:** `volumetric_letter_group_instance_v1`  
**Storage:** `finish_setup.letter_group_instances[]` (same PUT as finish — **no migration** unless later GO)

| Field | Current source | Why needed | Owner | Required B1? | Default/fallback |
|-------|----------------|------------|-------|--------------|------------------|
| `schema` | — | Pin | instance | Yes | constant |
| `instance_id` | new UUID | Stable identity | instance | Yes | mint once |
| `source_group_key` | `group_key` | Analysis join | instance | Yes | layerKey |
| `source_layer_ids[]` | analyzer if available | Artwork link | instance | Optional | `[group_key]` |
| `artwork_reference` | `{ layer_key, source_svg_hash?, binding_id? }` | Associate art | instance | Yes (minimal) | from workspace hash |
| `geometry` | face_area_m2, perimeter_m, element_count, source_fill_color | Commercial inputs | instance | Yes | from derive |
| `construction.return_depth_mm` | per-group | Depth | instance | Yes | null/default |
| `materials` / `finish` | face_*, return_*, backing_mode | Operator config | instance | Yes | from merge |
| `lighting` | copy workspace finish lighting | Owner: on instance | instance | Yes | global → copy |
| `confirmed` | row confirmed | Operator | instance | Yes | false |
| `provenance` | `{ source, updated_at? }` | Diagnostics later | instance | Yes (thin) | hydrated_legacy / analysis |

**Rejected (speculative):** readiness engine, Totem fields, coordinate model, universal ComponentInstance schema, inventing live FACE/BACK/LED/FINISH seeds.

`component_template_code`: label only (root letters or FACE bind code) — **not** claim live Component Template row.

---

## 7. Stable identity

**Chosen strategy: C — persisted UUID + `group_key` join**

| Rule | Detail |
|------|--------|
| Authority id | `instance_id` (UUID) |
| Analysis join | `source_group_key` (= today’s `group_key`) |
| Stale signal | `artwork_reference.source_svg_hash` (= workspace `file_hash`) — **not** part of id |
| Generated | First derive or legacy hydrate when missing |
| Saved | Inside instance on every finish-setup write |
| Never | Array index; regenerate UUID on reorder; bake SVG hash into id |
| Artwork change | Keep instance_id; refresh geometry suggestions; preserve confirmed finishes; mark stale if hash mismatch; rebind group_key if layer renamed |

---

## 8. Multi-group

```text
letter_group_instances[]
rule: one relevant legacy row → one instance
```

CE found no case where one finish row maps to multiple independent commercial groups. Re-analysis may drop/add keys — orphans become unbound/stale instances, not silent deletes of confirmed commercial state.

Groups may differ in materials, lighting, depth, artwork, placement. Advanced UI = Build 2.

---

## 9. Artwork authority

```text
analysis suggests → merge into empty/unconfirmed fields
operator confirms → instance owns
re-analysis → may update geometry suggestions
             → must not wipe confirmed materials/finish/depth/lighting
```

| Analysis owns | Instance owns |
|---------------|---------------|
| SVG bytes, file_hash | Confirmed finishes |
| Layer discovery, pseudo ids | Depth, colors, backing |
| Observed metrics, source_fill | Lighting, confirmed flag |

Fill-color change: **flag drift** + keep confirmed (Build 1 target; differs from today’s wipe).

---

## 10. Materials

Keep existing per-group fields under instance materials/finish:

- Face: `face_finish_type`, Oracal codes/names, vinyl roll width  
- Cant: `return_finish_type`, Oracal  
- Back: `backing_mode`  
- Depth: `return_depth_mm`

Do not pretend FACE/BACK templates are live-seeded.

## 11. Finish

Same block + `confirmed`. No new taxonomy.

## 12. Lighting

```text
lighting stays on LetterGroupInstance
```

| Phase | Behavior |
|-------|----------|
| First hydrate | Copy workspace-global lighting onto each instance |
| After write | Instance lighting is authority |
| Global finish lighting | Compatibility projection only if old consumers require; prefer quantity builder reading instances |
| Non-lit | `illuminated=false` |
| Emblem/logo LED split | Leave workspace legacy fields; no redesign in B1 |

No generic Lighting component.

---

## 13. Product Template boundary

| Bag/field | Keep as default | Copy at create | Temporary compatibility | Retire later |
|-----------|-----------------|----------------|-------------------------|--------------|
| Module links / composition | Yes | — | — | No |
| Canonical template variants | Yes | Into instances | — | Soft |
| Global face/return invent in `finishFromPayload` | — | — | Read hydrate | Build 2 |
| `letter_group_finishes` write SoT | — | — | Projection target | Build 2 |
| Global lighting fields | Default source | Copy → instances | Projection | Build 2 |
| Other product templates | Untouched | — | — | — |

---

## 14. Read authority

```text
if letter_group_instances[] valid:
    use instances
else:
    hydrate once from letter_group_finishes + workspace lighting
    mint instance_id
```

## 15. Write authority

```text
write letter_group_instances[] (+ component_placements[])
omit must not wipe (AcmPanel-style coalesce)
```

Who may write legacy array: **projection helper only**, not operator path as SoT.

## 16. Legacy hydration

One-time / on-read conversion when instances missing. Tests: old workspace opens; IDs stable after first save.

## 17. Legacy projection

```text
instances → letter_group_finishes[]  (one-way)
FORBIDDEN: legacy ↔ instances bidirectional sync
FORBIDDEN: stale legacy overwrite of newer instances
```

Migration warnings: logs/diagnostics only — never operator UI.

---

## 18. Commercial quantities

| Quantity | Current producer | Formula / source | Unit | Consumer | Recommended owner |
|----------|------------------|------------------|------|----------|-------------------|
| letter_perimeter_m | quote_geometry (outer) | SVG outer peri | ml | CPP face/cant | Quantity builder |
| letter_face_area_m2 | quote_geometry / sum groups | Face area | m² | CPP spate/finisaje | Builder (prefer instance sum if safe) |
| letter_return_perimeter_ml | enrich | outer+holes if return | ml | Breakdown / CE | Builder (document) |
| cnc_cutting_perimeter_ml | enrich | CNC | ml | CostEngine | Builder input; not CPP |
| led_module_count | FE+BE (pitch conflict 250 vs 100) | perimeter/pitch | buc | CPP LED | Builder → BE prefer 250 for V6 |
| mounting_template_area_m2 | finish | operator | m² | CPP sablon | Product/mounting (out of letter body) |
| ACM qty | AcmPanel | deduction/DXF | — | CPP acm_* | AcmPanel (unchanged) |

```text
LetterGroupInstance + quote_geometry facts
  → build_volumetric_letters_commercial_quantities / letters_commercial_measurement_service
  → CPP adapter aliases
```

UI does not calculate money. Rates stay in CPP catalog.

## 19. CPP boundary

- Official consumer: **CPP 7G** (`CommercialPriceProposalService`)  
- Build 1: builder is **single resolution path** for commercial aliases (stop Aggregate vs payload race)  
- No rate edits  

## 20. CostEngine legacy status

```text
CostEngine = legacy parallel producer/consumer for QuoteWizard path
V6 official path must not let CostEngine override CPP quantities
Outer (CPP) vs CNC/return (CostEngine) unification = Build 2 if still needed
```

After Build 1: **one function owns commercial resolution for CPP**; geometry enrich remains fact input, not a second commercial SoT.

---

## 21. Placement contract

```text
schema: component_placement_v1
component_placements[]
- placement_id
- source_instance_id          # letter instance_id
- target_kind                 # wall | acm_panel | metal_frame | totem_face | none
- target_instance_id          # null for wall/none
- target_face                 # A | B | null
- mounting_method?            # optional
- alignment?                  # optional default center
- offset_x_mm? / offset_y_mm? # optional store-only
```

**Build 1 depth:** contract + **persist** + **minimal adapter** (if ACM instance id present → optional placement `acm_panel`; else `none`/`wall`). Do not rewrite `acm_panel_instance.relations`.

No coordinate engine / Totem UI / MetalFrame invent.

---

## 22. Intake V6 impact

| Allowed | Forbidden |
|---------|-----------|
| Helpers: hydrate, merge, project, coalesce | Substantial new logic in ReviewStep |
| Minimal call sites (AcmPanel hydrate pattern) | Parallel form / form builder |
| Regression tests | Technical badges / diagnostics in operator UI |
| | Pricing logic in React |

**STOP threshold (concrete):**

| Signal | STOP if |
|--------|---------|
| Net new lines in `IntakeV6ReviewStep.tsx` | **> ~25** (prefer ≤15) |
| New `useState` for instances/placements | **any** |
| New dedicated `useEffect` for instance sync | **any** |
| Parallel letter editor | **immediate** |

Existing helpers to reuse: `intakeV4LetterGroups.ts`, finish sync/hydration, `finishSetupAcmHydrate.ts` pattern, `letterGroupFinishSectionHelpers.ts`.

## 23. Operator UI boundary

Build 1: existing cards keep working. Operator must **not** see instance IDs, provenance, migration status, raw aliases, placement IDs, legacy projection. Major visual simplification = Build 2.

## 24. Diagnostics boundary

No diagnostics page now. Inventory for later `/intake-v6/:id/diagnostics`: raw instances, artwork source, provenance, merge decisions, projection, quantities, CPP aliases, placements, conflicts, stale. Same truth, different lens.

---

## 25. Compatibility phases

| Phase | Owner | Writers | Readers | Tests | Rollback | Stop |
|-------|-------|---------|---------|-------|----------|------|
| **1** Legacy hydrate → new authority | Adapter | First save mints instances | Old WS open | Legacy hydrate | Keep reading legacy | Hydrate fails |
| **2** Authority + one-way projection | Instance write | Autosave instances | Old consumers via projection | Round-trip + omit preserve | Disable write instances | Circular sync detected |
| **3** Build 2 composition proof | Product | — | E2E | ACM+letters | — | Proof fail |
| **4** Legacy retirement decision | Owner GO | Stop projection | Instances only | Retirement suite | Re-enable projection | Consumers break |

No permanent compatibility layer.

---

## 26. Test matrix

Cover owner W18: identity, lifecycle, legacy, artwork, materials/lighting, quantities, placement, regression (incl. AcmPanel closed path untouched, Review/Confirm/PD/Aggregate, letters±ACM, CPP, gates).

Critical additions from CE:

- Fill-color drift preserves confirmed  
- `backing_mode` round-trips (gap in today’s merge)  
- Omit `letter_group_instances` on PUT does not wipe  
- SVG replace policy documented (today wipes finish — B1 must not silently improve unless scoped)

## 27. Runtime fixtures

| Case | Fixture hint |
|------|----------------|
| Legacy letters-only | `IV6-BB8EE3F8` / gradi-curat docs |
| Multi-group | gradi-curat 4 groups |
| Illuminated / non-lit | same + lighting flags |
| Letters + ACM | `IV6-DB2F86B7` (read ACM id only) |
| Measured ACM regression | `IV6-13D39D32` — **must stay measured** |
| Reload/autosave/re-analysis/CPP | After implement on above |

Report: workspace id, route, before/after, instance ids, quantities, authority, gates, writes.

## 28. Risks

| Risk | Prob | Impact | Detection | Mitigation | STOP |
|------|------|--------|-----------|------------|------|
| Identity drift / pseudo-key change | Med | High | Re-analysis tests | UUID authority + rebind | Confirmed finishes lost |
| Re-analysis overwrite | High (today) | High | Fill-change test | Preserve confirmed | Silent wipe remains |
| Legacy projection loop | Med | High | Write-spy tests | One-way only | Bidirectional detected |
| Global lighting overwrite | Med | Med | Multi-group lighting test | Instance authority | Global clobbers instances |
| Dual quantity authority | High | High | Dry-run path audit | Builder sole CPP resolve | Two writers same alias |
| Product Template still ops owner | Med | Med | Field ownership review | Defaults-only after create | Template still written as SoT |
| ReviewStep growth | Med | High | Diff line count | Helper-only wiring | >25 lines / new state |
| Multi-group corruption | Low | High | 4-group fixture | Keyed merge | Groups merge incorrectly |
| Incomplete autosave omit | Med | High | Omit-field test | Coalesce preserve | Wipe like old ACM bug |
| Placement overengineering | Med | Med | Scope review | Tiny fields only | Coordinate engine creep |
| False live CT claims | Med | Med | Seed audit | Labels only | FACE/LED seeded without GO |

## 29. Recommended implementation scope

### A — One coherent Build 1

Authority + lifecycle + quantity builder/CPP boundary + placement persist/minimal adapter.

**Why not B/C:** Placement without persist fails completion criteria; splitting quantities from lifecycle leaves dual write windows; ReviewStep risk controlled by STOP threshold, not by dropping placement.

## 30. Implementation units

| Unit | Objective | Likely files | Depends | Tests | Runtime | Rollback | Gate |
|------|-----------|--------------|---------|-------|---------|----------|------|
| **U1** | Contract + stable identity | new letter instance module; `intake_v4` schema touch | — | identity suite | mint on hydrate | revert schema | identity strategy |
| **U2** | Legacy hydrate + one-way projection | FE/BE adapters; coalesce on save | U1 | legacy + omit | old WS open | disable projection | R/W authority |
| **U3** | Artwork/materials/finish/lighting authority | merge helper fix; lighting copy | U1–U2 | artwork + lighting | multi-group | revert merge | merge rules |
| **U4** | Quantity builder + CPP boundary | `letters_commercial_measurement_service` | U1 | qty + dry-run | CPP dry-run | previous extract | qty/CPP |
| **U5** | Placement persist + ACM-target adapter | placements array; thin mirror | U1 | placement cases | ACM WS read-only | clear placements | placement scope |
| **U6** | Tests/runtime/worklog/commits | evidence dir | U1–U5 | full matrix | fixture table | — | completion |

## 31. Files likely touched

- `backend/schemas/intake_v4.py` (or thin imported schema)
- New BE: letter group instance + placement + coalesce
- `letters_commercial_measurement_service.py` (thin ownership)
- `intake_v6_workspace_service.py` (preserve on save — careful)
- FE: `letterGroupInstance*.ts`, merge updates in `intakeV4LetterGroups.ts`
- ReviewStep: **≤~15–25 lines call sites only**
- Tests + `docs/worklog/...` + evidence

**Forbidden touch:** AcmPanel deduction/metrics/attachment; rate seeds; Offer/Order writers; Product Template seed reorg.

## 32. Commit strategy

1. `feat(volumetric-letters): letter group instance authority and placement`  
2. `docs(volumetric-letters): Build 1 worklog and runtime evidence`

## 33. Owner gates — STOP

Need GO on:

1. Logic model (§3)  
2. Exact LetterGroupInstance fields (§6)  
3. Stable identity = UUID + group_key (§7)  
4. Multi-group mapping (§8)  
5. Artwork merge / confirmed preservation (§9)  
6. Materials/finish/lighting ownership (§10–12)  
7. Read/write authority (§14–15)  
8. Legacy projection one-way (§17)  
9. Quantity builder authority (§18–19)  
10. CPP vs CostEngine boundary (§20)  
11. Placement = persist + minimal adapter (§21)  
12. Intake STOP threshold (§22)  
13. Units U1–U6 + scope A (§29–30)

## 34. Opinia sinceră

Cel mai mic model onest este **autoritatea pe instanță peste rândurile care există deja**, nu un al doilea univers. Identitatea UUID este obligatorie — `group_key` singur moare la re-pseudo. Iluminarea per-grup e corectă, dar Build 1 trebuie să **copieze** din global, nu să deschidă UI nou. Unificarea perimetrelor CPP/CostEngine într-un singur număr fizic este capcană — Build 1 trebuie doar **un singur resolver comercial pentru CPP**. ReviewStep este deja plin; disciplina de linii este mai importantă decât ambitia de features.

## 35. Build 2 handoff

Operator UI closure · AcmPanel+Letters composition proof · Review/Confirm E2E · retire legacy projection · optional perimeter unification · diagnostics page · visual de-noise.

## 36. Roadmap checkpoint

```text
AcmPanel commercial ………… DONE (56217a9)
Letters completion audit … DONE (B)
Letters Build 1 plan …… THIS DOC → await GO
Letters Build 1 impl …… after GO
Letters Build 2 …………… after B1 PASS
```

## 37. Direcție stabilită

**80/100** — model unic, grounded in CE; risk is execution discipline (ReviewStep, no AcmPanel reopen), not conceptual fog.

---

## Hard boundaries (reaffirm)

PLAN ONLY · CE read-only · no product code/commits/seeds/migrations · no Product Template/CPP/CostEngine/Intake UI edits in this step · no AcmPanel reopen · no Banner/Totem/MetalFrame/illuminated impl · no generators · no coordinate engine · no generic framework · no form builder · no diagnostics page · no rates · no Offer/Order/Execution · no hourly pricing.

---

**STOP — implementation complete; awaiting owner review (report in chat + worklog).**
