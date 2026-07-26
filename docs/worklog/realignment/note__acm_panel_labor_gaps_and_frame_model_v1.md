# Note — AcmPanel: manoperă/servicii lipsă + model cadru v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Fixture** | Remus `doar-panou` 2000×500 mm · CPP provizoriu ~86.77 EUR |
| **Status prices** | `AGENT_PROPOSED_NOT_REGISTRY` — nu sunt rate owner în Pricing Registry până la GO |

## 1. Ce e deja în ofertă (owner-confirmed)

| Linie | Bază | Tarif | Remus ~ |
|-------|------|-------|---------|
| Debitare panou ACM | ml | 1.50 EUR/ml | 8.52 |
| Frezare V-groove | ml | 3.00 EUR/ml | 31.44 |
| Material față ACM | m² | 15.00 EUR/m² | 15.00 |
| Material canturi / întoarceri | m² | 15.00 EUR/m² | 6.81 |
| Asamblare casetat | m² + **min 20 EUR/produs** | 15.00 EUR/m² | **20.00** (min) |
| Șuruburi / prinderi | set | 5.00 EUR/set | 5.00 |
| **Total** | | | **~86.77** |

Notă UI: asamblarea arată 1 m² × 15 EUR/m² dar încasează min. 20 — afișaj corectat cu „min. 20 EUR/produs”.

## 2. Ordine atelier (OWNER_CONFIRMED) vs linii CPP

Din `MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md`:

| Pas atelier | În CPP acum? | Observație |
|-------------|--------------|------------|
| 1 Pregătire ArtCAM / fișier | Nu (linie comercială) | Acoperit parțial de asamblare min / internal EIC |
| 2 Frezare V-groove | Da (`acm_v_groove`) | |
| 3 Debitare finală | Da (`acm_panel_cut`) | |
| 4 Debavurare + îndoiri / formare | Parțial | Înglobat în `acm_boxed_assembly` (1 linie V1) |
| 5 Confecționare **cadru metalic** | **Nu** | Capability `internal_frame` — neprețuit |
| 6 Prindere cadru de casetă | **Nu** | Doar șuruburi panou (`acm_fasteners`) |
| 7 Autocolant față | Nu pe panou-alone | Shell finish separat |
| 8 Vopsire autoforante | Nu linie | XOR cu 7 |
| 9 Accesorii montaj site | Nu (opțional comercial) | Scope montaj separat |
| 10 Împachetare | Nu | AMBALARE opțional |

## 3. Prețuri propuse (agent) — de notat, nu de seed

Scop: panou casetat tip Remus 1 m²; atelier RO; **propuneri pentru discuție owner**.

| Cod propus | Ce acoperă | Bază propusă | Tarif propus | Remus ~ |
|------------|------------|--------------|--------------|---------|
| `acm_prep_artcam` | Pregătire fișier / nesting ArtCAM | fixed / job | **12 EUR/job** | 12 |
| `acm_fold_form` | Îndoire / formare casetă (manoperă după V) | ml fold sau m² | **4 EUR/ml fold** *sau* 8 EUR/m² | ~42 (pe 10.48 ml) / 8 |
| `acm_deburr` | Debavurare muchii | ml cut | **0.40 EUR/ml** | ~2.3 |
| `acm_frame_material` | Profil cadru (SKU TBD) | ml profil | **3.50 EUR/ml profil** | vezi §4 |
| `acm_frame_fab` | Debitare + sudură/asamblare cadru | ml profil *sau* fixed | **2.50 EUR/ml** *sau* **25 EUR/cadru** | ~25–40 |
| `acm_frame_mount` | Prindere cadru pe casetă | fixed / panou | **15 EUR/panou** | 15 |
| `acm_face_foil_apply` | Aplicare autocolant shell (dacă e) | m² | **8 EUR/m²** | 8 |
| `acm_screw_paint` | Vopsire capete autoforante (fără foil) | set | **6 EUR/set** | 6 |
| `acm_pack` | Împachetare panou | fixed | **8 EUR/job** | 8 |

**Sumă cadru (existentă):** `frame = panel − 2×grosime − 2 mm`  
Remus 2000×500×3 → cadru ~**1992×492**.  
Profil didactic 20×20: perimetru ~ 2×1992 + 2×(492−40) ≈ **4.9 ml** (+ traverse dacă e cazul).

| Scenariu cadru Remus (propus) | Calcul rough |
|-------------------------------|--------------|
| Material profil ~4.9 ml × 3.50 | ~17 EUR |
| Manoperă cadru min 25 | 25 |
| Montaj pe casetă | 15 |
| **Subtotal cadru propus** | **~57 EUR** |

**Total orientativ panou + cadru (propus):** ~87 + ~57 ≈ **~144 EUR** (fără foil, fără montaj site, fără ambalare).

> Nu seed în registry fără owner GO. Prefer linie comercială separată de asamblarea V1 existentă.

## 4. Cadru — root template sau nu?

**Recomandare: NU template root oferteabil.**

| Opțiune | Verdict |
|---------|---------|
| **Template root „doar cadru”** | Nu — clientul nu cumpără cadru izolat ca produs de ofertă tipic; complică Form System / Intake |
| **Capability pe AcmPanel** (`internal_frame`) | OK tehnic pe termen scurt; **slab** pentru reutilizare pe litere/ACP și pentru preț |
| **Componentă / modul partajat** (recomandat) | Da — un `comp_metal_frame` / mini-template non-root, atașat la ACM, litere-on-support, ACP când e activ; SKU profil + linii material/manoperă/montaj |

Motiv:
- Docul de ownership: cadru = atelier, nu CNC; formulă dimensională partajată.
- Folosit pe **mai multe produse** → ownership pe componentă, nu pe un root ACM.
- Root oferteabil rămâne: **Panou Alucobond casetat** / **Litere** / compoziții; cadrul e **dependent capability**.

### Pași GO (dacă owner acceptă)

1. Confirmă prețurile propuse (sau corectează) → seed registry.  
2. Model: `internal_frame_enabled` → emit linii `acm_frame_*` (sau `frame_*` partajate).  
3. Nu crea `TPL-METAL-FRAME_v1` ca root Intake până există caz real „doar cadru”.  
4. UI: când cadru ON → arată linii + „în ofertă”; când OFF → „neinclus / neprețuit”.

## 5. Bug UI asamblare (reparat)

Afișaj: `1 m2 · 15 EUR/m2` + total `20 EUR` → acum adaugă `min. 20 EUR/produs` când minimum-ul CPP e activ.
