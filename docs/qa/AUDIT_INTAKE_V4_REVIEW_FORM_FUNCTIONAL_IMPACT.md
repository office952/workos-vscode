# AUDIT — Intake V4 Review Form Functional Impact

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `e719846f15b7f0b7103e143313311b5a4742cfd2`  
**Scope:** Functional audit only — no backend/ProductSystem/CostEngine changes in this build.

---

## Rezumat verdict

**Problema principală confirmată:** Calcul live, Materiale folosite (cantități breakdown), material breakdown complet, pricing preview, production dry-run și majoritatea task preview **citesc exclusiv payload-ul persistat** din workspace (`GET /material-breakdown`, etc.). Schimbările din dropdown-uri **actualizează state local** (`letterGroups`, `form`, `artworkFinishes`) dar **nu se propagă în breakdown/prețuri până la „Salvează draft”**.

`finishIdentityKey` include state local → declanșează refetch-uri API la fiecare schimbare, dar răspunsul backend rămâne identic (payload vechi) → **impresia că „nu se schimbă nimic”** în panoul din dreapta.

**Excepții locale (fără save):**
- Iluminare: `syncIntakeV4FinishLighting` recalculează module/watts/PSU în `form` local.
- Cant card: `operatorCantPerimeterM` din sumă layere (`letterGroups.perimeter_m`) — perimetru vector, nu cost.
- Materiale folosite — rând cant: `operatorCantPerimeterM` se actualizează local; costurile rămân din breakdown salvat.
- CNC față/spate draft: `shanfrenForex` local → refetch `cost-draft` imediat.
- Task preview: doar când **nu** există `letter_group_finishes` — query params parțiale (`face_finish_type`, `return_finish_type`, `illuminated`).

---

## Lanț state flow (generic)

```
UI input
  → local state (ReviewStep: form | letterGroups | artworkFinishes)
  → save draft (POST finish_setup) — OBLIGATORIU pentru breakdown backend
  → workspace.payload persistat
  → GET material-breakdown / task-preview / pricing-input / dry-runs
  → Calcul live + Materiale folosite + accordion tehnic
```

**Ruptură standard:** pasul 2→3 lipsă înainte de save.

---

## A. Finisaje litere — față

| Opțiune | UI state | Save payload | Breakdown | Calcul live cost | Materiale folosite qty | Tarif |
|---------|----------|--------------|-----------|------------------|------------------------|-------|
| `none` (plexiglas brut) | Da | Da, după save | Plexi rămâne; **fără** rând `face_vinyl_*` | Oracal → tarif lipsă / dispare cost | Plexi din breakdown | Plexi: registry `MAT-ACP-FATA-LITERE` — **pricing registry** |
| `oracal_651` | Da | Da | Adaugă `face_vinyl_651` m² | Oracal cost dacă owner price | Oracal 651 m² | Owner catalog **9 EUR/m²** (excl. TVA) — nu depinde de culoare |
| `oracal_8500` | Da | Da | Adaugă `face_vinyl_8500` m² | **Parțial** — breakdown da, rând Oracal din Calcul live **nu** (hint `"651"` only) | Oracal 8500 m² în Materiale folosite | Owner **20 EUR/m²** — `shared_vinyl_material_catalog` |
| `oracal_641` | Da | Da | `face_vinyl_641` | Da | Oracal 641 | Owner price 641 |
| `print_laminate` (litere) | Da | Da | Print rows dacă backend le generează pentru litere | Print+laminare | Agregat print | Registry print/laminat — **de obicei lipsă tarif** local |

**Verdict per opțiune față:** funcțional **după save**; **doar UI** înainte de save pentru cost/materiale breakdown.

**Persistență refresh:** da, dacă `saveFinishSetup` reîncarcă workspace; breakdown refetch când `workspace.updated_at` se schimbă.

**Task preview:** nu primește per-layer face când `letterGroups.length > 0` (vezi §14).

---

## B. Culoare Oracal

| Aspect | Comportament |
|--------|--------------|
| UI state | `face_oracal_code`, `face_oracal_name` pe `letter_group_finishes` |
| Save payload | Da |
| Material code breakdown | **Nu** — același `face_vinyl_651` indiferent de culoare |
| Preț | **Nu** — tarif pe **serie** (651/8500/641), nu pe cod culoare |
| Inventory | Nu există rând per culoare în breakdown Intake V4 |
| Task preview | Specificație producție / handoff — nu schimbă cost |

**Verdict:** **doar specificație producție** (+ nearest color UX). UI **nu comunică explicit** că prețul nu se schimbă la schimbarea culorii.

---

## C. Lățime rolă (mm)

| Aspect | Comportament |
|--------|--------------|
| UI state | `face_vinyl_roll_width_mm` per group + global |
| Save payload | Da |
| Cantitate ofertată plexi (sheet) | **Nu direct** — sheet nesting dominant |
| Roll vinyl area / nesting | **Da** — `roll_area_by_layer`, `compute_roll_nesting_vinyl_estimate` când roll nesting activ |
| Preț | Indirect prin suprafață vinyl dacă roll nesting contribuie |
| Metadata producție | Da — readiness/quote policy |

**Verdict:** parțial conectată; pe Ana Maria (sheet-first) impact **limitat** în breakdown. **Nu e doar metadata**, dar efectul e adesea invizibil în Calcul live fără save + fără roll nesting valid.

---

## D. Cant / volum

| Aspect | Sursă |
|--------|--------|
| UI | `IntakeV4ReturnCantFields` per layer + copiere la toate |
| Save | `return_finish_type`, `return_oracal_code`, `return_depth_mm` per group |
| Material breakdown | `return_material` + `edge_cant_oracal_651` (dacă wrapped) + consumabile adeziv |
| Cantitate | `quote_geometry.return_material_perimeter_ml` (persistat); UI card folosește **vector layer sum** |
| Preț cant | Registry profil `MAT-PROFIL-LATERAL-LITERE-{depth}MM` via `_apply_registry_prices` |
| Cant 0.00 EUR | `unit_price == null` → `price_source: missing` → `rowCost` → **„tarif lipsă”** |
| Task preview | `return_vinyl_application_workbench`, `return_face_bonding` via V3 catalog flags — **după save** |

**Copiere cant:** actualizează toate layerele în state local — da; breakdown după save.

**Verdict funcțional cant:** cantitate **da** (după save); cost **depinde de pricing registry** adesea lipsă în dev.

---

## E. Emblemă / policromie

| Aspect | Stare actuală |
|--------|---------------|
| Secțiune UI | `IntakeV4ArtworkFinishSection` — **fără** dropdown execuție/cant |
| Aplicare | Hardcoded „Print + laminare” + „Policromie” |
| Translucent / Transparent | Setează `print_transparency` + forțează `execution_type: print_laminate`, `color_mode: polychrome` |
| Cant emblemă | **Nu în UI** — `return_finish_type` rămâne default în model, fără editor |
| Layer policromie | Rol artwork (`printed_artwork` / logo) — **da** în analyzer; UI simplificat vs V2/V3 |
| Cost print | `_append_artwork_print_rows` după save + `execution_type` valid |
| Translucent/transparent cost | **Nu** — doar specificație (`print_transparency`) |

**Verdict:** flux policromie **parțial regresat** față de așteptarea operator (lipsește cant emblemă + selector execuție). Print apare în cost **după save** dacă artwork complexity/execution permite.

---

## F. Iluminare

| Opțiune | Local imediat | Breakdown după save |
|---------|---------------|---------------------|
| LED on/off | `illuminated` → recalc module | Gate seeds LED; consumabile `led_modules` |
| Sistem LED | form | metadata |
| Culoare lumină | form | metadata |
| Putere modul | recalc watts/PSU local | `led_modules` qty |
| Perimetru LED | `geometryMetrics.ledExteriorPerimeterM` (~outer parts) | `finish_setup|geometry_perimeter` |
| Cost LED Calcul live | **Nu** — `sumMaterialByHint` nu include `consumable_rows` (`led_modules`) |

**Verdict:** module/watts **local da**; **cost LED absent** din Calcul live (bug de agregare frontend).

---

## G. CNC față/spate

| Aspect | Comportament |
|--------|--------------|
| Șanfren Forex | `useIntakeV4FaceBackPrepCostDraft` — query `shanfren_forex` → refetch imediat |
| Operation breakdown | Backend cost-draft separat de material breakdown |
| manual_required | UI ascunde total/CNC invalid (`needsFaceBackPrepPerimeterVerification`) |
| Material breakdown CNC ops | `operation_rows` — tarife operație separate |

**Verdict:** față/spate draft **funcțional local** pentru toggle șanfren; perimeter verification state **coherent** în UI.

---

## H. Upload fișiere proiect

`IntakeV4ProjectFilesPlaceholder` — **100% placeholder**. Nu salvează, nu influențează materiale/taskuri.

---

## Tabel materiale / pricing registry

| Material | Cod registry | Breakdown key | Preț dev tipic | Status |
|----------|--------------|---------------|----------------|--------|
| Plexiglas 3 mm față | `MAT-ACP-FATA-LITERE` | `plexiglas_face` | pricing_registry sau missing | Cantitate da |
| Forex 10 mm spate | `MAT-SPATE-PVC-LITERE` | `forex_backing` | **missing** frecvent | Cantitate dacă backing activ |
| Oracal 651 față | owner `face_vinyl_651` | `face_vinyl_651` | **9 EUR/m²** owner | Funcțional |
| Oracal 8500 | owner `face_vinyl_8500` | `face_vinyl_8500` | **20 EUR/m²** owner | Funcțional — **schimbă cost vs 651** |
| Oracal 641 | owner `face_vinyl_641` | `face_vinyl_641` | owner catalog | Funcțional |
| Print vinyl | `MAT-VINYL-PRINT` | `*_print_vinyl` | missing | Cantitate da |
| Laminare | `MAT-VINYL-PRINT-LAMINATED` | `*_laminated_vinyl` | missing | Cantitate da |
| Cant profil | `MAT-PROFIL-LATERAL-LITERE-60MM` | `return_material` | **missing** frecvent | Cantitate da |
| Oracal cant wrap | owner edge cant | `edge_cant_oracal_651` | owner 651 area | Dacă `oracal_wrapped` |
| Adeziv cant | consumable | `adhesive_return_to_face` | owner consumable | Parțial |
| Module LED | `MAT-LED-MODULE` | consumable `led_modules` | **missing** | Qty da, **nu în Calcul live cost** |
| PSU | — | consumable `led_psu` | variabil | Rar priced |

---

## Calcul live — sursă și limitări

| Întrebare | Răspuns |
|-----------|---------|
| Sursă date | `GET material-breakdown` + `face-back-prep cost-draft` |
| State local? | **Nu** pentru costuri; parțial pentru cant perimeter (Materiale folosite) |
| Înainte de save? | **Nu** pentru cost/materiale breakdown |
| După save? | Da, când workspace `updated_at` + refetch |
| Cant 0.00 EUR | `return_material.estimated_cost == null` (tarif lipsă) — nu e cantitate 0 |
| Forex tarif lipsă | registry fără preț în dev inventory |
| Total intern draft indisponibil | `needsFaceBackPrepPerimeterVerification` sau draft null |

**Soluții (neimplementate — necesită confirmare):**
- **A:** preview local derivat din state + formule frontend (complex, risc drift)
- **B:** auto-save draft debounced + refetch breakdown (**recomandat minim**)
- **C:** endpoint `POST material-breakdown/preview` cu finish draft body

---

## Materiale folosite (secțiune nouă)

- Sursă: același breakdown + `operatorCantPerimeterM` local pentru cant
- **Actualizare cantitate cant:** local da
- **Actualizare Oracal/plexi/print qty:** doar după save
- Mobil: collapsible

---

## Task preview

| Aspect | Valoare |
|--------|---------|
| Engine | `v3_operation_catalog` via `build_v4_task_preview_response` |
| ProductSystem | **Nu** — catalog V3 seeds + `derive_operation_flags_from_v4_finish` |
| Hardcodat | Catalog ordine + seed codes — nu template dossier complet |
| Per-layer | Când `letter_group_finishes` există, **fără** query override frontend |
| Schimbare finisaj | Efect **după save** (persisted finish_setup) |
| Override parțial | Doar global când zero letter groups |

**Verdict:** **temporar / backend service V3 adapter** — nu ProductSystem contract final.

---

## Probleme confirmate (P0–P2)

| ID | Severitate | Problemă |
|----|------------|----------|
| P0-1 | Critical UX | Calcul live nu reflectă schimbări finisaj **înainte de save** |
| P0-2 | Critical UX | Refetch breakdown la fiecare keystroke/dropdown — **muncă inutilă**, același răspuns |
| P1-1 | High | Task preview ignoră per-layer draft când există letter groups |
| P1-2 | High | Emblemă: lipsă UI cant + execuție configurabilă |
| P1-3 | High | Calcul live **exclude** cost LED (consumables) |
| P1-4 | High | Calcul live rând Oracal: hint doar `"651"` — **8500/641** nu intră în sumă chiar după save |
| P2-1 | Medium | Culoare Oracal: fără mesaj „spec-only, preț pe serie” |
| P2-2 | Medium | `isIntakeV4SelectorStatePendingSave` nu detectează schimbări face per layer |
| P2-3 | Medium | `handleSave` nu refetch explicit breakdown (depinde de `updated_at`) |
| P2-4 | Medium | Print/laminare litere: tarif registry lipsă → tarif lipsă chiar cu cantitate |

---

## Fixuri recomandate pe faze

### Faza 1 — Frontend (fără backend)
1. Banner Calcul live: **„Previzualizare costuri după Salvează draft”** când `finishIdentityKey` ≠ payload hash salvat.
2. Extinde `isIntakeV4SelectorStatePendingSave` → compare `letterGroups` / `artworkFinishes` cu payload.
3. Oprește refetch breakdown pe identity key local — refetch doar post-save + `updated_at`.
4. Calcul live: include `consumable_rows` (LED, adeziv) în agregări.
5. Emblemă: readăugare cant fields (reuse `IntakeV4ReturnCantFields`) + notă spec-only pe culoare.

### Faza 2 — Backend (cu confirmare)
1. `GET material-breakdown?draft=1` sau POST preview cu finish_setup body.
2. Task preview cu `letter_group_finishes` în override.
3. Seed pricing registry dev pentru MAT-PROFIL, MAT-SPATE, print vinyl.

### Faza 3 — ProductSystem
1. Task preview din template dossier, nu V3 catalog mirror.
2. Contract finish → material intent → pricing unified.

---

## Teste rulate (2026-06-24)

```
vitest run
  IntakeV4LiveCalculationSummary.test.tsx        5/5 PASS
  IntakeV4LiveMaterialsUsedDisplay.test.ts       7/7 PASS
  IntakeV4EdgeCantReviewCard.test.tsx            1/1 PASS
  intakeV4GeometryMetricDisplay.test.ts          3/3 PASS
  IntakeV4OperatorGeometrySummaryCard.test.tsx   3/3 PASS
  IntakeV4FaceBackPrepCostDraftPanel.test.tsx      5/5 PASS
  IntakeV4LetterGroupFinishesSection.test.tsx      1/1 PASS
  IntakeV4ArtworkFinishSection.test.tsx          1/1 PASS
Total: 26/26 PASS
```

---

## Fișiere cheie (trace audit)

| Rol | Path |
|-----|------|
| Review state + fetch | `frontend/.../IntakeV4ReviewStep.tsx` |
| Breakdown API read-only payload | `backend/.../intake_v4_material_breakdown_service.py` |
| Identity key (local vs saved) | `frontend/.../intakeV4FinishPayloadSync.ts` |
| Calcul live | `frontend/.../IntakeV4LiveCalculationSummary.tsx` |
| Materiale folosite | `frontend/.../intakeV4LiveMaterialsUsedDisplay.ts` |
| Task preview | `backend/.../intake_v4_production_preview_service.py` |
| Oracal pricing | `backend/.../intake_v4_oracal_face_pricing_service.py` |
| Pending save (parțial) | `frontend/.../intakeV4FinishHydration.ts` |

---

## Boundary

- **Nu s-a modificat** backend, ProductSystem, CostEngine în acest audit.
- **Nu s-a implementat** recalculare live preview complexă.
- Document + teste existente rulate doar.

---

## Footprint source selector (2026-06-24 update)

### Înainte
- UI auto vs manual Corel; candidații (`face_union_bbox`, etc.) ascunși în accordion.
- Backend: doar `operator_manual_footprint` cu `useForQuoteEstimate` schimba qty; default `eligible_area_floor`.

### După implementare
- UI: radio selectabil — eligible, face union bbox, layout auto shelf, manual Corel.
- Persistență: `sheet_quote_override.selectedFootprintSource` + `useForQuoteEstimate: true`.
- Breakdown: `apply_operator_footprint_to_sheet_material_quantities` ridică **Plexi + Forex** la sursa aleasă.
- Calcul live: se actualizează după save + refetch breakdown (aceeași limitare ca finisaje).

| Sursă | Impact Plexi/Forex | Impact Oracal |
|-------|-------------------|---------------|
| eligible_area_floor | da (1.2638 m² Ana Maria) | nu — vinyl pe letter groups |
| face_union_bbox | da (2.5238 m²) | nu |
| layout_occupied_area | da | nu |
| operator_manual_footprint | da | nu |

**Oracal nu se recalculează** la schimb footprint — by design (suprafață vinyl ≠ sheet nesting).

### Teste footprint
- Backend: `test_intake_v4_sheet_footprint_override.py` — 15/15 PASS
- Frontend: `IntakeV4SheetFootprintOverridePanel.test.tsx`, `intakeV4SheetFootprintSource.test.ts` — PASS

---

## Cant UI cleanup (2026-06-24)

### Semantica perimetrelor (Ana Maria)

| Valoare | Semnificație | Folosit ca perimetru cant? |
|---------|--------------|----------------------------|
| 31.64 m | Vector litere (26.75) + emblemă cu cant activ (4.89) | **Da — principal operator** |
| 26.75 m | Sumă perimetru layere față / letter groups | Da — componentă litere |
| 4.89 m | Vector emblemă/logo (când cant activ) | Da — componentă emblemă |
| 20.97 m | LED exterior / outer parts / quote geometry vechi | **Nu** — LED / backend pending |
| 25.17 m | 20.97 m × 1.20 pierdere ofertare | **Nu** — cantitate preț, nu perimetru |

**Perimetru principal UI:** `resolveIntakeV4OperatorCantPerimeterDisplay().displayM`

### UI principal card Cant / Volum

- Perimetru cant total
- Finisaj
- Adâncime (mm)
- Preț cant (tarif lipsă sau cost EUR)

### Scos din UI principal

- LED exterior, quote geometry, breakdown cant, cant pentru preț, +20%, adeziv, operații preview

### Detalii tehnice

Accordion collapsed „Detalii tehnice cant” — valori etichetate explicit ca debug/backend pending.

### Calcul live

- Rând Cant: cost din breakdown (tarif lipsă dacă missing)
- Materiale folosite: `operatorCantPerimeterM` (31.64 / 26.75), **nu** 25.17 m cu pierdere

### Backend

Neatins — aliniere breakdown cant la vector total = build separat cu confirmare.
