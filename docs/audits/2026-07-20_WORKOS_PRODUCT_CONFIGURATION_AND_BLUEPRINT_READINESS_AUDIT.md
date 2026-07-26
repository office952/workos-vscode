# WORKOS_PRODUCT_CONFIGURATION_AND_BLUEPRINT_READINESS_AUDIT

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Mode | Read-only audit — **no code, no UI, no remediation writes, no blueprint implementation** |
| Prerequisite | Owner PASS on `INTAKE_V6_SVG_TRUTH_CONTRACT_REPAIR_V1` (`727430b`) |
| Runtime fixtures | `IV6-379CEB03` (ACM), `IV6-B6C01680` (gradi) |
| Evidence | `docs/audits/_evidence/2026-07-20_product-config-blueprint-readiness/` |
| Inventory | 210 Intake V6 workspaces on local `backend/dev.db` via API `:8001` |

---

## 1. Rezumat executiv

Reparatia SVG truth (`727430b`) face **direcția** corectă: Panoul Alucobond este declarat ca componentă Product System (`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`, rol `SUPPORT_CONTOUR`), segmentele sunt nested sub `finish_setup.segmented_background`, iar literele/logo rămân ownership extern. **Instanțierea operațională pe workspace-ul ACM reparat este încă incompletă** față de modelul dorit „sibling real”:

- există `layer_role_setup.support_panel` + composition recommendation `letters_plus_support` + `segmented_background` **PROPOSED** (2 panouri, assembly 2000×350);
- **lipsesc** `svg_component_bindings[SUPPORT_CONTOUR]`, `svg_support_selection`, `mounting_solution`, composition confirmation, `element_bindings` litere↔panou.

Concluzie: Product Truth reparat este **pregătit parțial** pentru un viitor blueprint schematic (Nivel 1) ca *read model derivat*, dar **nu** ca SoT complet al panoului. `finish_setup.segmented_background` **nu** este (și nu trebuie să fie) owner-ul canonic al panoului — contractul o spune; runtime-ul actual încă *se sprijină* pe el ca principal payload vizibil pentru multi-panel.

**Scor direcție stabilită: 61/100** (contract + geometrie propusă + composition sibling intent: da; component shell confirmat + mounting/structure/finish ownership unificat + relații montaj persistate: nu).

---

## 2. Model operational Panou Alucobond

### Model dorit (owner)

```text
Produs
├── Litere / grupuri de litere
├── Vector Logo-uri reale
├── Panou Alucobond casetat          ← sibling component
│   ├── Segment 1 / 2                 ← nested geometries
│   ├── Structura / Finisaj / Prindere
└── Relatii de montaj
```

### Cum apare azi în configurarea operațională

| Strat | Realitate pe `IV6-379CEB03` | Aliniere |
|-------|----------------------------|----------|
| Contract bindable | `owner_label="Panou Alucobond casetat"`, `SUPPORT_CONTOUR` MAX_ONE, nested panels allowed | **Da** (catalog) |
| Layer roles | `support_panel` confirmed pe `pseudo:fill-c5c6c6` | **Da** (rol) |
| Composition recommendation | `letters_plus_support` + item `support` / `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | **Da** (sugestie sibling) |
| Composition confirmation | gol | **Nu** |
| Binding `SUPPORT_CONTOUR` | **absent** (doar `LETTER_VECTOR_SET`) | **Nu** — gap CFG |
| `svg_support_selection` / `mounting_solution` | absente | **Nu** |
| `segmented_background` | PROPOSED, 2 panels, host template ACM, `operator_confirmed=false` | **Parțial** — nested OK, status neconfirmat |
| ProductDefinition / Aggregate | neproiectate (seg PROPOSED gated; fără mounting) | **Nu** |

**Verdict model:** direcția „componentă reală sibling” este **declarată** în Product System + composition, dar pe fixture-ul reparat panoul există în principal ca **rol + proposal segmented + recommendation**, nu ca instanță de componentă confirmată. Segmentele sunt corect modelate ca nested (nu N produse). `segmented_background` este persistence envelope pentru multi-panel, **nu** owner canonic al identității panoului — însă în absența binding/mounting, UI/operator citesc de facto din el.

---

## 3. Ownership matrix

Clasificare: **PO** product-owned · **CO** component-owned · **SO** segment-owned · **INH** inherited · **AP** analyzer-proposed · **OC** operator-confirmed · **BC** backend-calculated · **DRM** derived read model.

| Valoare | Owner canonic dorit | Stare actuală | Clasificare |
|---------|---------------------|---------------|-------------|
| Identitate Panou Alucobond | `SUPPORT_CONTOUR` binding + template ACM | Recommendation + layer role; **fără** binding pe fixture ACM | PO/CO intent; **DRM/AP** în practică |
| Instantiere | Composition item `support` + binding CONFIRMED | Recommendation only | DRM |
| Dimensiuni ansamblu | Assembly confirmată (apoi mounting) | `segmented_background.assembly_dimensions` AP | AP → OC when CONFIRMED |
| Segmente (W/H/position) | Nested under ACM shell | `panels[]` PROPOSED | SO nested / AP |
| Material ACM | Component mounting config | **lipsă** pe fixture; default seed 3 mm când există mounting | CO / implicit |
| Grosime ACM | `mounting_solution.configuration.acm_thickness_mm` | lipsă | CO |
| Volum casetare / depth | `casing_profile` / `return_depth_mm` | lipsă | CO |
| Intoarcere spate | casing L2 / rear lip | lipsă | CO |
| Finisaj panou | Face treatments pe shell ACM | neinstanțiat | CO |
| Structură interioară | `internal_frame*` pe mounting | lipsă | CO |
| Decupări | `CUTOUT_*` / insert roles pe același template | candidați CCC existenți; neasociați | AP → CO |
| Operații | Template seed ACM ops (CUT/V-groove/fold/assemble/mount) | catalog only; segmented `no_pricing` | CO catalog / BC later |
| Sistem montaj | `mounting_solution` + commercial scope separat | lipsă pe fixture | CO (+ commercial) |
| Litere ↔ panou | `element_bindings` interface only; letters ownership EXTERNAL | `element_bindings=[]` | lipsă relație OC |
| Litere ownership | Letter bindings / letter template | `LETTER_VECTOR_SET` CONFIRMED | CO / OC |
| Logo ownership | `LOGO_VECTOR_SET` / artwork finishes | pe gradi: 2 bindings + 2 artwork; pe ACM: 0 | CO / OC |
| Provenance geometrie | `sourceGroupIds` / `elementIds` pe layers | prezent post-repair | AP persistat |

---

## 4. Adevaruri paralele si stale paths

| Locație | Rol | Owner canonic? | Verdict |
|---------|-----|----------------|---------|
| `svg_analysis_json` | Geometry + CCC + layers + provenance | Nu — proposal source | **AP**; păstrează |
| `layer_role_setup` | Roluri operator | Parțial pentru rol, nu pentru component identity | **OC** roles; stale dacă e folosit ca SoT panou |
| `finish_setup.segmented_background` | Nested multi-panel assembly | Nu pentru identitate panou; da pentru members când CONFIRMED | **Projection nested**; PROPOSED = non-authoritative for PD |
| `finish_setup.svg_component_bindings` SUPPORT | Identitate componentă | **Da** (dorit) | **Stale/missing** pe ACM reparat |
| `finish_setup.svg_support_selection` | Contur + casing tipizat | **Da** (cu binding) | absent |
| `finish_setup.mounting_solution` | Config comercial/tehnic shell | **Da** pentru thickness/fold/frame | absent; risc defaults FE dacă se activează târziu |
| Composition recommendation | Sibling UI/readiness | Nu | **DRM** |
| Composition confirmation | Operator accept composition | Da pentru „ce e în produs” | gol |
| ProductDefinition / Aggregate | Downstream projection | Nu — derived | gated; empty fără CONFIRMED+mounting |
| Product Template seed | Ops/defaults catalog | Catalog authority | OK |
| Pricing / CPP | Template rates când ACM linked-child | Nu din segmented | segmented `no_pricing` corect |
| UI client state | Optimistic patches | Nu | risc race: sync letter bindings poate șterge SUPPORT dacă state React nu a absorbit încă patch-ul (suspect pentru gap-ul CFG pe Confirm All) |

**Eliminare graduală (propusă, neexecutată):**

1. Nu trata `layer_role_setup.support_panel` ca suficient pentru instanțierea panoului.
2. Unifică write-path: orice Confirm support → **obligatoriu** SUPPORT binding + selection/mounting hydrate + segmented propose (atomic).
3. PD citește doar CONFIRMED segmented + binding CONFIRMED (deja gated).
4. Marchează `segmented_background` ca nested config, nu composition item.

---

## 5. Blueprint readiness matrix

### Geometrie

| Câmp | Stare | Owner / schemă | Consumatori |
|------|-------|----------------|-------------|
| source geometry | există (SVG + CCC) | analysis | Analyzer, overlay |
| normalized geometry | parțial (mm pe CCC) | CCC `width_mm`/`height_mm` + scale meta | segmented propose |
| bounding box | **există pe CCC**; **lipsă pe layers** (`bbox=null`) | CCC | blueprint L1 poate folosi CCC; layers insuficiente |
| width / height | layers + CCC + panels | mixed | UI metrics, segmented |
| position X/Y | panels `position`; CCC `bbox`/`centroid`; layers **fără** x/y | segmented / CCC | L1 relative OK pentru panouri; litere nesigure din layers |
| rotation | **lipsă** (implicit 0) | — | — |
| contour / panel IDs | CCC `contour_id`; panels `panel_id` | segmented | assembly |
| sourceGroupIds / elementIds | există pe layers post-repair | analysis layers | reopen Straturi, provenance |
| scale/unit provenance | CCC `mm_per_vbu_*`, `unit_ambiguity` | analysis | scaling trust |

### Relatii

| Câmp | Stare |
|------|-------|
| parentComponentId / belongsToAssemblyId | **lipsă** ca IDs unificate; `assembly_id` pe segmented |
| mountsOnComponentId | **lipsă** |
| containsComponentIds | **lipsă** (composition items sunt DRM) |
| panel bindings / letter-to-panel / logo-to-panel | `element_bindings` **gol** |
| ordering / z-index | panel `order`; nu z-index operațional cross-component |
| alignment / offsets | **lipsă** (doar positions panouri) |

### Adevar tehnic

| Câmp | Stare |
|------|-------|
| material / thickness / depth / finish / structure / mounting | **lipsă** pe fixture ACM (necesită mounting_solution / treatments) |
| illumination | pe litere (în afara acestui audit detail); nu pe panou |
| production operations | catalog template; nu materializate din segmented |
| dimensions confirmed vs detected | detected: CCC/panels PROPOSED; confirmed: **nu** |

**Blueprint L1 readiness:** geometrie panouri + provenance + composition sibling **derivabile**; relații montaj și truth tehnic shell **nu**.

---

## 6. Contract minim `ProductAssemblyBlueprintReadModel`

Read-only, derivat din Product Truth. **Nu** owner. Nu include CNC/DXF/LED/manufacturing.

```text
ProductAssemblyBlueprintReadModel
├── meta
│   ├── workspace_id, workspace_code
│   ├── schema_version
│   ├── derived_at
│   ├── truth_status: partial | composition_ready | operator_confirmed
│   └── sources[]: { path, authority: proposed|confirmed|catalog|derived }
├── assembly
│   ├── assembly_id?
│   ├── overall_width_mm, overall_height_mm
│   ├── dimension_status: detected | confirmed | unknown
│   └── view_box_2d: { min_x, min_y, width, height, unit }
├── components[]                          # siblings
│   ├── component_id                      # stable derived id
│   ├── kind: letters | vector_logo | alucobond_panel | other
│   ├── template_code?
│   ├── label
│   ├── color_token                       # legend only
│   ├── geometry_2d: { bbox, width_mm, height_mm, x_mm?, y_mm?, rotation_deg? }
│   ├── geometry_status: detected | confirmed | missing
│   ├── children[]?                       # segments for alucobond only
│   │   ├── segment_id, order, width_mm, height_mm, x_mm, y_mm, contour_ref?
│   └── technical_summary?                # material/thickness/depth if confirmed — else omitted
├── relations[]
│   ├── type: mounts_on | contains | interfaces_panel | joint
│   ├── from_id, to_id
│   ├── status: proposed | confirmed | unknown
│   └── note?
├── callouts[]                            # dimensions / labels for schematic
│   ├── target_id, kind: overall | component | segment | gap
│   └── text, value_mm?
├── legend[]                              # component color + label + status chip
└── validation
    ├── blockers[], warnings[], infos[]
    └── missing_for_level_1[]
```

**Reguli:**

- Derive only from confirmed Product Truth when marking `confirmed`; otherwise `detected`/`proposed`.
- Alucobond = **one** component; segments = `children[]`, never top-level product rows.
- Empty `element_bindings` → relations `unknown`, nu inventa mounts.

---

## 7. Nivel 1 / 2 / 3 feasibility

| Nivel | Scop | Disponibil acum | Lipsă |
|-------|------|-----------------|-------|
| **1 — Schematic** | Operator, ofertare, verificare compoziție | Layers + roles; CCC geom; segmented panels PROPOSED; composition recommendation; letter/logo bindings (gradi); provenance | SUPPORT binding confirmat; composition confirmation; element_bindings; layer bbox/xy; mounting/finish pe shell; unified component IDs |
| **2 — Tehnic** | Cote, secțiuni, volum, rosturi, structură, montaj, electric | Joints vertical pe segmented; CCC perimeter/area; casing fields in selection path (când există) | Confirmed casing/structure; rosturi reale; electric; sections; offsets letter-on-panel |
| **3 — Manufacturing** | DXF, CUT/FOLD, nesting, BOM, CNC | Nesting preview endpoints există separat; template ops catalog | Nu din Product Truth actual; segmented `no_task_materialization` / `no_pricing` by design |

**Fezabil acum:** prototip Nivel 1 **read-only** pe date propuse, cu badge-uri detected/proposed. **Nu** GO pentru implementare din acest audit.

---

## 8. Runtime proof

### ACM — `IV6-379CEB03` / `646b746d-94c8-41e1-be27-baaeabd26457`

| Check | Rezultat |
|-------|----------|
| Support assembly | **Da (PROPOSED):** `assembly_id=asm_el-1_el-2`, host `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Două panel geometries | **Da:** `panel_1`/`panel_2` 1000×350, positions (0,0)/(1000,0), contour `el-1`/`el-2` |
| Provenance | **Da:** support layer `sourceGroupIds=[gravare-cnc-135gr]`, `elementIds=[el-1,el-2]`; letters `decupare-cnc-outside`/`el-3` |
| Litere distincte | **Da:** face layer separat de support |
| Relație litere ↔ panou | **Nu persistată** (`element_bindings=[]`); doar co-prezență + CCC containment hints |
| Zero artwork phantom | **Da** (`artwork_finishes=0`) |
| Sibling component binding | **Nu** — gap CFG (fără SUPPORT_CONTOUR) |

### Gradi — `IV6-B6C01680` / `3f7d1c7a-a12b-488e-8f70-12df8de0795f`

| Check | Rezultat |
|-------|----------|
| Patru grupuri litere | **Da:** maria, soare, ana, gradinita (`face`) |
| Două logo-uri | **Da:** `logo_instance_001/002` = `printed_artwork` + `LOGO_VECTOR_SET` |
| Zero support fals | **Da** (no `support_panel`, no segmented) |
| Relații / poziție relativă | Dimensiuni per layer (W×H); **bbox/xy pe layers = null** → poziție relativă **doar parțial** (derivabilă nesigur din CCC/elements, nu din layer SoT) |

---

## 9. Inventar remediation

Scan local complet: **210** workspace-uri Intake V6 (`include_archived=true`).

| Metrică | Count |
|---------|------:|
| Scanned | 210 |
| Suspecte **P1** (support confirmed, segmented absent) | **18** |
| Suspecte **P2** (logo layer as support_panel) | **2** |
| Suspecte **P3** (heuristic artwork_finishes + support, fără rol artwork/logo) | **67** |
| Suspecte **P7** (step intent mismatch în payload) | **0** |
| CFG: support/segmented fără SUPPORT_CONTOUR binding | **20** (din care 2 cu segmented prezent: `IV6-379CEB03`, `IV6-54B66A17`) |
| Cu Offer (quote_exists pe P1/P2/CFG) | **0** |
| Cu Order legat de acești suspects | **0** |
| ExecutionPlan pe acești suspects | **0** |
| Cost/pricing potențial afectat (suspects) | **Scăzut local** — niciun quote pe setul P1/P2/CFG; P3 CONFIRMED sample 0/20 quote |
| Auto-reparabile (candidați) | P1 propose segmented; P3 strip finishes fără ambiguitate comercială |
| Necesită review operator | P2; CFG binding; composition; element_bindings |
| Doar marcate | PROPOSED segmented fără confirm; INFO flags |

**Limite:**

- Doar DB locală `backend/dev.db` + API `:8001` — **nu** inventar prod/staging.
- `quotes` leagă `intake_code`, nu workspace UUID; `quote_snapshots_v2.workspace_id` are **3** legături (workspace-uri curate, fără flaguri P1/P2).
- Orders: 11; execution_plan: 9 — majoritar gate/test; 3 orders V6 legate de snapshot workspace-uri **non-suspect**.
- Heuristica P3 poate supra-conta residual `artwork_finishes` pe support-only jobs.

Evidență: `_evidence/2026-07-20_product-config-blueprint-readiness/full-remediation-inventory.json`, `inventory-summary.json`, `p1-p2-cfg-commercial.json`.

---

## 10. Categorii remediation (propuse — neexecutate)

### Safe auto-repair
- Re-propose `segmented_background` din CCC când `support_panel` confirmed și seg lipsește, **fără** quote/order/snapshot.
- Șterge `artwork_finishes` phantom când nu există roluri artwork/logo și `logo_presence` false, fără downstream comercial.

### Operator review
- P2: reclasificare logo vs support.
- CFG: re-asociere Contur suport → SUPPORT_CONTOUR + selection/mounting.
- Confirmare composition `letters_plus_support`.
- Completare `element_bindings` litere/logo → panel.

### Commercial review
- Orice workspace cu `quote_exists` / snapshot frozen + flaguri P1/P2/P3 (în local: **niciun** suspect curent).
- Nu rescrie totals; re-price doar după owner GO.

### Locked historical
- `orders` locked/in_production + `execution_plan` + `quote_snapshots_v2` frozen — **nu** rescrie adevărul istoric automat; marchează variance / supersede doar pe GO explicit.

---

## 11. Riscuri

1. **Gap CFG post-repair:** Confirm All poate lăsa segmented PROPOSED **fără** SUPPORT binding (observat pe `IV6-379CEB03`) — panoul nu e sibling instanțiat.
2. **Trei oglinzi** selection ↔ binding ↔ mounting — divergență dims/thickness când se activează.
3. **Composition din layer roles** poate afișa Panou fără contour binding.
4. **`element_bindings` goale** → blueprint relații inventate = risc.
5. **P3 heuristic zgomot** — remediation oarbă poate șterge finishes valide.
6. **Race bindings sync** (useEffect letter sync vs support persist) — stale path plauzibil pentru pierderea SUPPORT.
7. **Blueprint pe PROPOSED** citit ca confirmat → ofertare greșită.

---

## 12. Handoff pentru UI system audit

Poate prelua (fără stil vizual final în acest audit):

1. **Configurarea componentelor** ca siblings: Litere / Vector Logo / Panou Alucobond.
2. **Panoul Alucobond** ca rând de componentă (nu doar toggle finish / segmented blob).
3. **Segmente** ca children expandabile sub panou.
4. Stările **detectat → propus → confirmat** pe rol, binding, segmented, composition.
5. **Preview** ansamblu 2D schematic (viitor consumer al read model-ului de mai sus).
6. **Blueprint schematic** (Nivel 1) ca view read-only — nu editor manufacturing.
7. **Validation** blockers: support fără SUPPORT_CONTOUR; segmented fără host binding; artwork phantom.
8. **Component rows** + provenance (`sourceGroupIds` / `elementIds`).
9. **Operator corrections**: roluri, asociere contur, confirm segmented, element_bindings.
10. Explicit: **nu** nesting CNC / DXF în UI audit-ul următor.

**Handoff obligatoriu 21st (accelerator UI, nu Product Truth):**  
[`2026-07-20_WORKOS_UI_SYSTEM_21ST_BLUEPRINT_INTEGRATION_HANDOFF.md`](./2026-07-20_WORKOS_UI_SYSTEM_21ST_BLUEPRINT_INTEGRATION_HANDOFF.md) — backlog S1–S12 pentru `WORKOS_UI_SYSTEM_21ST_BLUEPRINT_INTEGRATION_AUDIT`.

---

## 13. Recomandarea unica

**Nu implementa blueprint încă.** Înainte de UI system audit sau Nivel 1 blueprint, închide gap-ul de instanțiere: orice cale care scrie `segmented_background` pentru support trebuie să persiste atomic și **SUPPORT_CONTOUR + selection/mounting hydrate**, apoi abia derivează un `ProductAssemblyBlueprintReadModel` read-only. Remediation istorică rămâne owner-gated pe categoriile de mai sus; local nu există presiune comercială pe suspects.

---

## 14. Cat suntem in directia stabilita: **61/100**

| Pilon | Score parțial |
|-------|---------------|
| Contract sibling + nested segments | 90 |
| Runtime SVG roles/provenance repair | 85 |
| Instanțiere componentă ACM (binding/mounting) | 35 |
| Relații montaj persistate | 20 |
| Truth tehnic shell (material/depth/finish/structure) | 25 |
| Blueprint L1 derivabil fără ambiguitate | 45 |

---

## Owner gate

Audit încheiat. **Fără** implementare blueprint, UI, remediation writes, redesign, 21st.dev.

Aștept decizia ta.
